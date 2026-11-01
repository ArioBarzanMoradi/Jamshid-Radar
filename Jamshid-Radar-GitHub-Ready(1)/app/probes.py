"""Outbound observations from this server. Results do not infer external reachability."""
from __future__ import annotations
import asyncio
import socket
import ssl
import struct
import subprocess
import time
import secrets
from typing import Any


def tcp_connect(host: str, port: int, family: int = socket.AF_UNSPEC) -> dict:
    start = time.monotonic()
    try:
        addresses = socket.getaddrinfo(host,port,family,socket.SOCK_STREAM)
        error = 'no address'
        for af,kind,proto,_,address in addresses[:8]:
            try:
                with socket.socket(af,kind,proto) as sock:
                    sock.settimeout(2.8)
                    sock.connect(address)
                return {'ok':True,'ms':round((time.monotonic()-start)*1000,1),'detail':'TCP handshake برقرار شد'}
            except OSError as exc:
                error = str(exc)
        return {'ok':False,'ms':None,'detail':error[:110]}
    except (socket.gaierror,OSError) as exc:
        return {'ok':False,'ms':None,'detail':str(exc)[:110]}


def dns_lookup() -> dict:
    start=time.monotonic()
    try:
        result=socket.getaddrinfo('example.com',443,type=socket.SOCK_STREAM)
        return {'ok':bool(result),'ms':round((time.monotonic()-start)*1000,1),
                'detail':'حل نام example.com' if result else 'بدون نتیجه'}
    except OSError as exc:
        return {'ok':False,'ms':None,'detail':str(exc)[:110]}


def https_request() -> dict:
    import http.client
    start=time.monotonic()
    conn=None
    try:
        conn=http.client.HTTPSConnection('www.google.com',timeout=3,context=ssl.create_default_context())
        conn.request('GET','/generate_204',headers={'User-Agent':'Jamshid/1.1'})
        res=conn.getresponse()
        res.read(1024)
        return {'ok':200<=res.status<400, 'ms':round((time.monotonic()-start)*1000,1),
                'detail':f'HTTPS پاسخ {res.status}'}
    except (OSError,ssl.SSLError,TimeoutError) as exc:
        return {'ok':False,'ms':None,'detail':str(exc)[:110]}
    finally:
        if conn: conn.close()


def ping(host: str, ipv6: bool=False) -> dict:
    args=['ping','-n','-6' if ipv6 else '-4','-c','1','-W','2',host]
    start=time.monotonic()
    try:
        res=subprocess.run(args,text=True,capture_output=True,timeout=3.2,check=False)
        if res.returncode!=0:
            return {'ok':False,'ms':None,'detail':'ICMP بی‌پاسخ یا محدود شده'}
        import re
        match=re.search(r'time[=<]([\d.]+)\s*ms',res.stdout)
        value=float(match.group(1)) if match else round((time.monotonic()-start)*1000,1)
        return {'ok':True,'ms':round(value,1),'detail':'ICMP echo پاسخ داد'}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {'ok':False,'ms':None,'detail':'ping در دسترس نیست یا مهلت پایان یافت'}


def stun_udp() -> dict:
    """A valid STUN binding response tests ONE UDP route, not generic UDP access."""
    start=time.monotonic()
    txid=secrets.token_bytes(12)
    request=struct.pack('!HHI',0x0001,0,0x2112A442)+txid
    try:
        infos=socket.getaddrinfo('stun.l.google.com',19302,socket.AF_INET,socket.SOCK_DGRAM)
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
            sock.settimeout(3)
            sock.sendto(request,infos[0][4])
            data,_=sock.recvfrom(2048)
        valid=len(data)>=20 and data[0:2]==b'\x01\x01' and data[4:8]==bytes.fromhex('2112a442') and data[8:20]==txid
        return {'ok':valid,'ms':round((time.monotonic()-start)*1000,1) if valid else None,
                'detail':'STUN UDP/19302 پاسخ معتبر' if valid else 'پاسخ نامعتبر STUN'}
    except OSError as exc:
        return {'ok':False,'ms':None,'detail':str(exc)[:110]}


async def call(func,*args) -> dict:
    try:
        return await asyncio.wait_for(asyncio.to_thread(func,*args),timeout=6)
    except (TimeoutError,Exception) as exc:
        return {'ok':False,'ms':None,'detail':('مهلت پاسخ پایان یافت' if isinstance(exc,TimeoutError) else str(exc)[:110])}


async def probe_target(target: dict) -> dict:
    host=target['host']
    port=int(target.get('port',443))
    tcp,icmp=await asyncio.gather(call(tcp_connect,host,port),call(ping,host))
    return {'id':target['id'],'name':target['name'],'country':target.get('country','GLOBAL'),
            'host':host,'port':port,'tcp':tcp,'icmp':icmp,'ok':tcp['ok'],
            'checked_at':int(time.time())}


async def check_all(targets: list[dict]) -> dict:
    active=[]
    for t in targets[:24]:
        if not t.get('enabled',True):
            continue
        try:
            good = (isinstance(t.get('host'),str) and bool(t['host'])
                    and 1<=int(t.get('port',443))<=65535
                    and isinstance(t.get('id'),str) and isinstance(t.get('name'),str))
        except (ValueError,TypeError,KeyError):
            good = False
        if good:
            active.append(t)
    global_names=['ipv4_tcp','ipv6_tcp','dns','https','icmp','udp_stun']
    tasks=[call(tcp_connect,'1.1.1.1',443,socket.AF_INET),
           call(tcp_connect,'2606:4700:4700::1111',443,socket.AF_INET6),
           call(dns_lookup),call(https_request),call(ping,'1.1.1.1'),call(stun_udp)]
    combined=await asyncio.gather(*tasks,*(probe_target(t) for t in active),return_exceptions=True)
    glob={name:(res if isinstance(res,dict) else {'ok':False,'ms':None,'detail':'خطا'})
          for name,res in zip(global_names,combined[:len(global_names)])}
    destinations=[res for res in combined[len(global_names):] if isinstance(res,dict)]
    return {'checks':glob,'targets':destinations,'checked_at':int(time.time())}
