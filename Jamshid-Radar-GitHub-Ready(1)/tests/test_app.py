import importlib
import json
import secrets
from pathlib import Path
from fastapi.testclient import TestClient
from app.auth import check_session,hash_password,session_for,verify_password
from app.collector import list_ports
from app.probes import tcp_connect


def conf():
    return {'username':'admin','password_hash':hash_password('this-is-a-safe-test-password'),
            'session_secret':secrets.token_hex(32),'base_path':'/radar-test92/','targets':[]}


def test_password_and_session():
    data=conf()
    assert verify_password('this-is-a-safe-test-password',data['password_hash'])
    assert not verify_password('wrong',data['password_hash'])
    token=session_for(data)
    assert check_session(token,data)
    assert not check_session(token+'x',data)
    assert not check_session(token,dict(data,session_secret=secrets.token_hex(32)))


def test_login_snapshot_logout(tmp_path,monkeypatch):
    main=importlib.import_module('app.main')
    path=tmp_path/'config.json'
    path.write_text(json.dumps(conf()))
    monkeypatch.setattr(main,'CONFIG_PATH',path)
    client=TestClient(main.app,base_url='https://radar.example.com')
    assert client.get('/api/snapshot').status_code==401
    assert client.get('/').status_code==200
    assert 'ورود به مرکز' in client.get('/').text
    assert client.post('/api/login',json={'username':'admin','password':'wrong'},headers={'origin':'https://radar.example.com'}).status_code==401
    assert client.post('/api/login',json={'username':'admin','password':'this-is-a-safe-test-password'}).status_code==403
    r=client.post('/api/login',json={'username':'admin','password':'this-is-a-safe-test-password'},headers={'origin':'https://radar.example.com'})
    assert r.status_code==200
    assert 'Secure' in r.headers['set-cookie']
    assert 'HttpOnly' in r.headers['set-cookie']
    assert 'SameSite=strict' in r.headers['set-cookie']
    assert 'Path=/radar-test92/' in r.headers['set-cookie']
    # TestClient calls the backend directly. Production Nginx adds the path before stripping it.
    client.cookies.set('nr_session',r.cookies['nr_session'],domain='radar.example.com',path='/')
    assert client.get('/').status_code==200
    assert 'مرکز فرمان شبکه' in client.get('/').text
    assert 'جمشید' in client.get('/').text
    assert 'data-theme-toggle' in client.get('/').text
    assert 'theme.js' in client.get('/').text
    assert 'Vazirmatn' in client.get('/').text
    snapshot=client.get('/api/snapshot')
    assert snapshot.status_code==200
    assert 'ports' in snapshot.json()['data']
    assert client.post('/api/logout',headers={'origin':'https://radar.example.com'}).status_code==200
    client.cookies.clear()
    assert client.get('/api/snapshot').status_code==401


def test_ports_parsing(monkeypatch):
    from app import collector
    def fake(args,timeout=2):
        return 'tcp LISTEN 0 4096 0.0.0.0:443 0.0.0.0:*\nudp UNCONN 0 0 [::]:51820 [::]:*\ntcp LISTEN 0 4096 127.0.0.1:22 0.0.0.0:*\n'
    monkeypatch.setattr(collector,'run',fake)
    rows=list_ports()
    assert len(rows)==3
    assert rows[0]['port']==22 and rows[0]['scope']=='فقط محلی'
    assert rows[-1]['family']=='IPv6' and rows[-1]['transport']=='UDP'


def test_tcp_local():
    import socket
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0));listener.listen()
        result=tcp_connect('127.0.0.1',listener.getsockname()[1])
        assert result['ok'] and result['ms'] is not None
