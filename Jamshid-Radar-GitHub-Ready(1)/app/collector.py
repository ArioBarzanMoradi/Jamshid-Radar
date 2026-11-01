"""Read-only Linux collector; never shells out with untrusted arguments."""
from __future__ import annotations
import json
import platform
import re
import socket
import subprocess
import time
from pathlib import Path
import psutil

PORT_HINTS = {
  21:'FTP', 22:'SSH', 25:'SMTP', 53:'DNS', 80:'HTTP', 110:'POP3',
  123:'NTP', 143:'IMAP', 443:'HTTPS / TLS / VPN احتمالی', 465:'SMTPS',
  500:'IPsec IKE احتمالی', 587:'SMTP', 993:'IMAPS', 995:'POP3S',
  1194:'OpenVPN احتمالی', 1701:'L2TP احتمالی', 1723:'PPTP احتمالی',
  4500:'IPsec NAT-T احتمالی', 51820:'WireGuard احتمالی',
  8388:'Shadowsocks احتمالی', 2053:'TLS / پروکسی احتمالی',
  2083:'TLS / پروکسی احتمالی', 2087:'TLS / پروکسی احتمالی',
  8443:'TLS / پروکسی احتمالی', 2096:'TLS / پروکسی احتمالی',
}
VPN_UNIT_RE = re.compile(r'(wg-quick@|openvpn|xray|sing-box|hiddify|3x-ui|x-ui|hysteria|naiveproxy|shadowsocks|ssserver|ocserv|strongswan|ipsec|charon|xl2tpd|tailscaled|zerotier|v2ray|trojan|outline|amnezia)', re.I)


def run(args: list[str], timeout: float = 2) -> str:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False).stdout
    except (FileNotFoundError, PermissionError, subprocess.TimeoutExpired):
        return ''


def get_routes() -> dict:
    result = {'ipv4': [], 'ipv6': []}
    for family, cmd in [('ipv4',['ip','-j','route','show','default']),
                        ('ipv6',['ip','-j','-6','route','show','default'])]:
        try:
            result[family] = json.loads(run(cmd))[:8]
        except (ValueError, TypeError):
            pass
    return result


def get_dns() -> list[str]:
    try:
        lines = Path('/etc/resolv.conf').read_text().splitlines()
        return [line.split()[1] for line in lines if line.startswith('nameserver ')][:6]
    except OSError:
        return []


def list_ports() -> list[dict]:
    out = run(['ss','-H','-lntu'], timeout=3)
    entries = []
    for line in out.splitlines():
        fields = line.split()
        if len(fields) < 5 or fields[0] not in ('tcp','udp'):
            continue
        addr = fields[4]
        try:
            bind, raw_port = addr.rsplit(':',1)
            port = int(raw_port)
        except (ValueError, IndexError):
            continue
        v6 = '[' in bind or bind.count(':') > 1
        clean = bind.strip('[]')
        if clean in ('*','0.0.0.0','::'):
            scope = 'تمام رابط‌ها'
        elif clean.startswith('127.') or clean in ('::1','localhost'):
            scope = 'فقط محلی'
        else:
            scope = 'آدرس مشخص'
        entries.append({'transport':fields[0].upper(), 'family':'IPv6' if v6 else 'IPv4',
                        'port':port, 'bind':addr, 'scope':scope,
                        'hint':PORT_HINTS.get(port, 'نامشخص'), 'state':fields[1]})
    return sorted(entries, key=lambda p:(p['port'],p['transport'],p['family']))[:500]


def vpn_services() -> list[dict]:
    lines = run(['systemctl','list-units','--type=service','--all','--plain','--no-legend'], timeout=4)
    found = []
    for line in lines.splitlines():
        parts = line.strip().lstrip('● ').split(None,4)
        if len(parts) < 4 or not parts[0].endswith('.service'):
            continue
        if VPN_UNIT_RE.search(parts[0]):
            found.append({'name':parts[0].removesuffix('.service'), 'state':parts[2], 'substate':parts[3]})
    try:
        for iface in psutil.net_if_addrs():
            if iface.startswith(('wg','tun','tap','tailscale','zt')) and not any(e['name']==iface for e in found):
                found.append({'name':iface, 'state':'interface', 'substate':'موجود در سیستم'})
    except Exception:
        pass
    return found[:50]


class Collector:
    def __init__(self):
        self.last_time = None
        self.last_bytes = None

    def snapshot(self) -> dict:
        now = time.monotonic()
        pernic = psutil.net_io_counters(pernic=True)
        routes = get_routes()
        active_device = (routes['ipv4'] or routes['ipv6'])
        if active_device:
            dev = active_device[0].get('dev','')
        else:
            dev = next((n for n in pernic if n != 'lo'), '')
        counts = pernic.get(dev)
        rx_rate = tx_rate = 0.0
        if self.last_time is not None and counts and self.last_bytes and self.last_bytes[0] == dev:
            delta = max(now - self.last_time, .001)
            rx_rate = max(0,(counts.bytes_recv - self.last_bytes[1]) / delta)
            tx_rate = max(0,(counts.bytes_sent - self.last_bytes[2]) / delta)
        self.last_time = now
        self.last_bytes = (dev,counts.bytes_recv,counts.bytes_sent) if counts else None
        interfaces = []
        stats = psutil.net_if_stats()
        for name, addresses in psutil.net_if_addrs().items():
            item = stats.get(name)
            interfaces.append({'name':name,'up':bool(item and item.isup),
                               'speed_mbps':item.speed if item else 0,
                               'ipv4':[a.address for a in addresses if a.family == socket.AF_INET],
                               'ipv6':[a.address.split('%')[0] for a in addresses if a.family == socket.AF_INET6][:4],
                               'default':name==dev})
        ports = list_ports()
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return {
          'system':{'hostname':socket.gethostname(), 'os':platform.system()+' '+platform.release(),
                    'cpu':round(cpu,1), 'memory':round(mem.percent,1), 'disk':round(disk.percent,1),
                    'uptime':round(time.time()-psutil.boot_time())},
          'network':{'device':dev, 'rx_bps':round(rx_rate), 'tx_bps':round(tx_rate),
                     'ipv4_route':bool(routes['ipv4']), 'ipv6_route':bool(routes['ipv6']),
                     'routes':routes, 'dns':get_dns(), 'interfaces':interfaces},
          'ports':ports, 'vpn':vpn_services(),
          'counts':{'unique_ports':len({(p['transport'],p['port']) for p in ports}),
                    'tcp':sum(1 for p in ports if p['transport']=='TCP'),
                    'udp':sum(1 for p in ports if p['transport']=='UDP'),
                    'public':sum(1 for p in ports if p['scope']=='تمام رابط‌ها')},
          'collected_at':int(time.time())
        }
