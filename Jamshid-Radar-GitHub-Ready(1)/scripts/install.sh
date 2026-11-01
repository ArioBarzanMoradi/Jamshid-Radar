#!/usr/bin/env bash
set -Eeuo pipefail
if [[ $(id -u) -ne 0 ]]; then echo 'Run: sudo bash scripts/install.sh' >&2; exit 1; fi
if [[ ! -f requirements.txt || ! -d app ]]; then echo 'Run from extracted project root.' >&2; exit 1; fi
if [[ ! -f /etc/os-release ]]; then echo 'Ubuntu Linux required.' >&2; exit 1; fi
. /etc/os-release
if [[ "$ID" != "ubuntu" ]]; then echo 'Installer is tested for Ubuntu. Aborting.' >&2; exit 1; fi
if [[ -e /etc/systemd/system/network-radar.service ]]; then echo 'An installation already exists. Refusing to overwrite credentials.' >&2; exit 1; fi
printf '\n Jamshid (جمشید) / Ubuntu installer\n --------------------------------\n'
read -rp 'Dedicated domain (e.g. radar.example.com): ' DOMAIN
if [[ ! "$DOMAIN" =~ ^[A-Za-z0-9][A-Za-z0-9.-]{3,250}[A-Za-z0-9]$ || "$DOMAIN" != *.* ]]; then echo 'Invalid domain'; exit 1; fi
read -rp 'Web path token (min 6, e.g. monitor-k93x7): ' SEGMENT
if [[ ! "$SEGMENT" =~ ^[A-Za-z0-9-]{6,64}$ ]]; then echo 'Invalid path'; exit 1; fi
read -rp 'Admin username [A-Za-z0-9_.-; 3..32]: ' ADMIN
if [[ ! "$ADMIN" =~ ^[A-Za-z0-9_.-]{3,32}$ ]]; then echo 'Invalid username'; exit 1; fi
read -rsp 'Admin password (min 12 characters): ' PASSWORD; echo
read -rsp 'Repeat password: ' PASSWORD2; echo
if [[ "$PASSWORD" != "$PASSWORD2" || ${#PASSWORD} -lt 12 ]]; then echo 'Passwords mismatch or too short'; exit 1; fi
read -rp 'Confirm DNS points here and port 80 is reachable? [y/N] ' CONFIRM
if [[ "$CONFIRM" != 'y' && "$CONFIRM" != 'Y' ]]; then echo 'Please configure DNS and firewall first.'; exit 1; fi
unset PASSWORD2
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip nginx iproute2 iputils-ping ca-certificates
if ! id netradar &>/dev/null; then useradd --system --home-dir /opt/network-radar --shell /usr/sbin/nologin netradar; fi
install -d -m 755 /opt/network-radar
cp -a app requirements.txt /opt/network-radar/
chown -R root:root /opt/network-radar
python3 -m venv /opt/network-radar/.venv
/opt/network-radar/.venv/bin/pip install --no-cache-dir -r /opt/network-radar/requirements.txt
install -d -m 750 -o root -g netradar /etc/network-radar
cp config.example.json /etc/network-radar/config.json
export RADAR_INSTALL_USERNAME="$ADMIN" RADAR_INSTALL_BASE="/$SEGMENT/" RADAR_INITIAL_PASSWORD="$PASSWORD"
unset PASSWORD
python3 - <<'PY'
import json,os,secrets,sys
sys.path.insert(0,'/opt/network-radar')
from app.auth import hash_password
p='/etc/network-radar/config.json'
d=json.load(open(p))
d['username']=os.environ['RADAR_INSTALL_USERNAME'];d['base_path']=os.environ['RADAR_INSTALL_BASE']
d['password_hash']=hash_password(os.environ['RADAR_INITIAL_PASSWORD'])
d['session_secret']=secrets.token_hex(32)
with open(p,'w') as f:json.dump(d,f,ensure_ascii=False,indent=2)
PY
unset RADAR_INITIAL_PASSWORD
chown root:netradar /etc/network-radar/config.json
chmod 640 /etc/network-radar/config.json
install -m 750 scripts/radarctl.py /usr/local/sbin/radarctl
ln -sfn /usr/local/sbin/radarctl /usr/local/sbin/jamshidctl
cat > /etc/systemd/system/network-radar.service <<'UNIT'
[Unit]
Description=Jamshid Network Radar Dashboard
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=netradar
Group=netradar
WorkingDirectory=/opt/network-radar
Environment=RADAR_CONFIG=/etc/network-radar/config.json
ExecStart=/opt/network-radar/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 18764 --workers 1 --no-server-header
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
CapabilityBoundingSet=
LockPersonality=true
UMask=0077
[Install]
WantedBy=multi-user.target
UNIT
# Preserve existing Nginx virtual hosts and default site.
DOMAIN="$DOMAIN" SEGMENT="$SEGMENT" python3 - <<'PY'
import os
p='/etc/nginx/sites-available/network-radar.conf'
d=os.environ['DOMAIN'];s=os.environ['SEGMENT']
text=f'''server {{
    listen 80;
    listen [::]:80;
    server_name {d};
    client_max_body_size 4k;
    location = /{s} {{ return 301 /{s}/; }}
    location ^~ /{s}/ {{
        proxy_pass http://127.0.0.1:18764/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 3s;
        proxy_read_timeout 20s;
        add_header X-Content-Type-Options nosniff always;
    }}
    location / {{ return 404; }}
}}
'''
open(p,'w').write(text)
PY
ln -s /etc/nginx/sites-available/network-radar.conf /etc/nginx/sites-enabled/network-radar.conf
nginx -t
systemctl daemon-reload
systemctl enable --now network-radar
systemctl enable --now nginx
systemctl reload nginx
printf '\nCore service installed. Next MUST enable HTTPS before logging in:\n'
printf '  sudo bash scripts/enable-ssl.sh %s\n' "$DOMAIN"
printf '\nDashboard after SSL: https://%s/%s/\n' "$DOMAIN" "$SEGMENT"
printf 'CLI: sudo jamshidctl passwd | sudo jamshidctl username | sudo jamshidctl rotate-sessions\n'
