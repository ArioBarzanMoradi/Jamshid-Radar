#!/usr/bin/env bash
set -Eeuo pipefail
if [[ $(id -u) -ne 0 ]]; then echo 'Run with sudo.' >&2; exit 1; fi
if [[ $# -ne 1 || ! "$1" =~ ^[A-Za-z0-9.-]+$ ]]; then echo 'Usage: sudo bash scripts/enable-ssl.sh jamshid.example.com' >&2; exit 1; fi
DOMAIN="$1"
if ! command -v certbot &>/dev/null; then
    echo 'Installing Certbot and Nginx plugin from Ubuntu apt repositories...'
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y certbot python3-certbot-nginx
fi
certbot --nginx -d "$DOMAIN" --redirect
nginx -t
systemctl reload nginx
printf '\nTLS configured. Test certificate renewal: sudo certbot renew --dry-run\n'
