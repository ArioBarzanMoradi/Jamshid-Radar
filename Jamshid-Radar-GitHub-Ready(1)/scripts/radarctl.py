#!/usr/bin/env python3
"""Root-only administrative CLI; do not expose as web routes."""
import argparse
import getpass
import json
import os
import re
import secrets
import sys
from pathlib import Path

# Runs in installed venv so the project is importable.
sys.path.insert(0,'/opt/network-radar')
try:
    from app.auth import hash_password
except ImportError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from app.auth import hash_password

DEFAULT=Path(os.environ.get('RADAR_CONFIG','/etc/network-radar/config.json'))

def update(path, func):
    data=json.loads(path.read_text())
    func(data)
    temp=path.with_suffix('.new')
    with temp.open('w') as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
        f.write('\n')
    os.chmod(temp,0o640)
    original = path.stat()
    os.chown(temp, original.st_uid, original.st_gid)
    os.replace(temp,path)
    print('Saved. Restarting will refresh all login sessions.')
    if path==Path('/etc/network-radar/config.json'):
        os.system('systemctl restart network-radar.service')


def main():
    parser=argparse.ArgumentParser(prog='jamshidctl')
    parser.add_argument('--config',type=Path,default=DEFAULT)
    sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('passwd',help='change dashboard password and invalidate sessions')
    sub.add_parser('username',help='change dashboard username and invalidate sessions')
    sub.add_parser('rotate-sessions',help='invalidate every login session')
    sub.add_parser('show',help='show non-secret configuration')
    args=parser.parse_args()
    if os.geteuid()!=0:
        parser.error('Run with sudo/root to protect credentials')
    if args.action=='show':
        data=json.loads(args.config.read_text())
        print(json.dumps({k:v for k,v in data.items() if k not in ('password_hash','session_secret')},ensure_ascii=False,indent=2))
        return
    if args.action=='passwd':
        pw=getpass.getpass('New password (min 12 chars): ')
        confirm=getpass.getpass('Repeat new password: ')
        if pw!=confirm:parser.error('Passwords do not match')
        if len(pw)<12:parser.error('Minimum 12 characters')
        update(args.config,lambda d:d.update(password_hash=hash_password(pw),session_secret=secrets.token_hex(32)))
    elif args.action=='username':
        value=input('New username [A-Za-z0-9_.-; 3..32]: ').strip()
        if not re.fullmatch('[A-Za-z0-9_.-]{3,32}',value):parser.error('Invalid username')
        update(args.config,lambda d:d.update(username=value,session_secret=secrets.token_hex(32)))
    else:
        update(args.config,lambda d:d.update(session_secret=secrets.token_hex(32)))

if __name__=='__main__':main()
