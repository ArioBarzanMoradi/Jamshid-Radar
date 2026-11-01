"""FastAPI entrypoint, using only read-only monitoring API operations."""
from __future__ import annotations
import asyncio
import json
import os
import time
from collections import defaultdict,deque
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from .auth import check_session, load_config, session_for, verify_password
from .collector import Collector
from .probes import check_all

CONFIG_PATH=Path(os.environ.get('RADAR_CONFIG',str(Path(__file__).resolve().parent.parent/'config.example.json')))
STATIC=Path(__file__).resolve().parent/'static'
collector=Collector()
probe_cache={'checks':{},'targets':[],'checked_at':0}
sample_cache={}
history=deque(maxlen=70)
events=deque(maxlen=30)
previous_states={}
login_attempts=defaultdict(deque)


def config() -> dict:
    return load_config(CONFIG_PATH)


def is_authed(request: Request, conf: dict|None=None) -> bool:
    return check_session(request.cookies.get('nr_session'),conf or config())


def unavailable() -> JSONResponse:
    return JSONResponse({'error':'Authentication required'},status_code=401,headers={'Cache-Control':'no-store'})


async def probe_loop():
    global probe_cache
    while True:
        try:
            new=await check_all(config().get('targets',[]))
            for key,result in new['checks'].items():
                prev=previous_states.get('check:'+key)
                current=bool(result['ok'])
                if prev is not None and prev != current:
                    events.appendleft({'time':int(time.time()),'type':'restored' if current else 'failure',
                                       'message':f'وضعیت {key} تغییر کرد'})
                previous_states['check:'+key]=current
            for item in new['targets']:
                key='target:'+item['id']; prev=previous_states.get(key); current=item['ok']
                if prev is not None and prev!=current:
                    events.appendleft({'time':int(time.time()),'type':'restored' if current else 'failure',
                                       'message':f'دسترسی به {item["name"]} تغییر کرد'})
                previous_states[key]=current
            probe_cache=new
        except Exception as exc:
            events.appendleft({'time':int(time.time()),'type':'warning','message':'خطای موقت در اجرای تست‌ها'})
        await asyncio.sleep(15)


async def sample_loop():
    global sample_cache
    while True:
        try:
            sample_cache = await asyncio.to_thread(collector.snapshot)
            history.append({'t': int(time.time()),
                            'rx':sample_cache['network']['rx_bps'],
                            'tx':sample_cache['network']['tx_bps']})
        except Exception:
            events.appendleft({'time':int(time.time()),'type':'warning',
                               'message':'خطا در جمع‌آوری داده محلی'})
        await asyncio.sleep(3)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    tasks=[asyncio.create_task(probe_loop()),asyncio.create_task(sample_loop())]
    try:
        yield
    finally:
        for task in tasks:task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)


app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)
app.mount('/static',StaticFiles(directory=str(STATIC)),name='static')

@app.middleware('http')
async def headers(request:Request, call_next):
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy']=("default-src 'none'; style-src 'self' https://fonts.googleapis.com; script-src 'self'; "
                                                "img-src 'self' data:; connect-src 'self'; font-src 'self' https://fonts.gstatic.com; "
                                                "base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
    if request.url.path.startswith('/api') or request.url.path=='/':
        response.headers['Cache-Control']='no-store'
    return response


@app.get('/',response_class=HTMLResponse)
async def home(request:Request):
    conf=config()
    if not is_authed(request,conf):
        page=(STATIC/'login.html').read_text(encoding='utf-8')
    else:
        page=(STATIC/'index.html').read_text(encoding='utf-8')
    page=page.replace('__BASE__',conf['base_path'])
    return HTMLResponse(page)


def origin_is_same(request:Request)->bool:
    # Nginx adds Host; browsers include Origin on fetch POST. No cross-site posts.
    origin=request.headers.get('origin','')
    if not origin:
        return False
    from urllib.parse import urlsplit
    parsed=urlsplit(origin)
    return parsed.scheme=='https' and parsed.netloc==request.headers.get('host','')


@app.post('/api/login')
async def login(request:Request):
    conf=config()
    if not origin_is_same(request):
        return JSONResponse({'error':'HTTPS Origin required'},status_code=403)
    ip=request.headers.get('x-real-ip',request.client.host if request.client else 'unknown')[:80]
    # x-real-ip is overwritten by the supplied Nginx reverse proxy; app is localhost only.
    now=time.monotonic()
    bucket=login_attempts[ip]
    while bucket and now-bucket[0]>600: bucket.popleft()
    if len(bucket)>=8:
        return JSONResponse({'error':'تلاش‌های زیاد؛ ۱۰ دقیقه بعد دوباره امتحان کنید'},status_code=429)
    try:
        if int(request.headers.get('content-length','0'))>4096:
            return JSONResponse({'error':'درخواست بیش از حد بزرگ'},status_code=413)
        body=await request.json()
        username=body.get('username','')
        password=body.get('password','')
        if not isinstance(username,str) or not isinstance(password,str) or len(password)>512:
            raise ValueError('invalid input')
    except (ValueError,TypeError):
        return JSONResponse({'error':'ورودی نامعتبر'},status_code=400)
    from hmac import compare_digest
    if not (compare_digest(username,conf['username']) and verify_password(password,conf['password_hash'])):
        bucket.append(now)
        await asyncio.sleep(.25)
        return JSONResponse({'error':'نام کاربری یا رمز عبور نادرست است'},status_code=401)
    bucket.clear()
    res=JSONResponse({'ok':True})
    res.set_cookie('nr_session',session_for(conf),max_age=12*3600,path=conf['base_path'],
                   secure=True,httponly=True,samesite='strict')
    return res


@app.get('/api/session')
async def session(request:Request):
    if not is_authed(request):return unavailable()
    c=config()
    return {'username':c['username'],'base_path':c['base_path'],'hostname':os.uname().nodename}


@app.post('/api/logout')
async def logout(request:Request):
    if not is_authed(request):return unavailable()
    if not origin_is_same(request):return JSONResponse({'error':'Origin rejected'},status_code=403)
    res=JSONResponse({'ok':True})
    res.delete_cookie('nr_session',path=config()['base_path'],secure=True,httponly=True,samesite='strict')
    return res


@app.get('/api/snapshot')
async def snapshot(request:Request):
    if not is_authed(request):return unavailable()
    data=sample_cache or await asyncio.to_thread(collector.snapshot)
    return {'version':'1.1.0','data':data,'probes':probe_cache,'history':list(history),
            'events':list(events),'poll_seconds':3,'probe_interval_seconds':15}


@app.get('/healthz')
async def healthz():
    return {'ok':True}
