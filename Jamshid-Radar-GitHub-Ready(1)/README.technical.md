# Jamshid / جمشید — Ubuntu Network Intelligence

**Version 1.1 · Persian / RTL · charcoal / ivory themes · Vazirmatn · Google-inspired colors & glass UI**

A working self-hosted dashboard for Ubuntu **22.04 / 24.04 / 26.04** (systemd, Nginx), built using FastAPI, psutil and built-in OS tools. Runs read-only under an unprivileged `netradar` system account. No external JavaScript, analytics, account services, Docker, or remote dashboard dependencies. **Vazirmatn is fetched by the user’s browser from Google Fonts** when reachable; if blocked, CSS falls back to Tahoma. The monitoring app itself still runs without the font CDN.

## What this version actually measures

| Function | Mechanism | Interpretation |
|---|---|---|
| TCP/UDP listening ports, bind, IPv4/IPv6 | `ss -H -lntu` | Local listening sockets, **not** proof of firewall or Internet reachability |
| Incoming/outgoing traffic | `psutil.net_io_counters` on default route interface | Bytes per second calculated between samples; graph resets on app restart |
| CPU, RAM, disk, uptime | psutil | Live local server health |
| Network interfaces, IPv4/IPv6 addresses | psutil | Interfaces, links and addresses visible to monitoring user |
| Default routes, DNS | `ip -j route`, `/etc/resolv.conf` | Kernel routes; DNS stub address possible |
| Systemd VPN/proxy units | `systemctl list-units` and tunnel interface names | Presence / active state only. Cannot assert Xray or WireGuard **tunnel traffic** works |
| Foreign destinations | TCP handshake + separate ICMP echo | Tests **from the Iranian Ubuntu server outbound**, not inbound from the destination |
| DNS | `getaddrinfo(example.com)` | Success of current resolver, not DNS integrity or all DNS servers |
| HTTPS | Verified TLS request to `www.google.com/generate_204` | TLS + HTTP response status |
| IPv4/IPv6 | Direct TCP to Cloudflare DNS IPs on port 443 | Separate IPv4 and IPv6 egress tests |
| UDP | STUN binding to `stun.l.google.com:19302` | Tests that specific outbound UDP flow, not any arbitrary UDP port or VPN tunnel |
| Events | In-memory state changes | Only since process start, no long-term database or notification delivery |

`SSL` with Let's Encrypt via Certbot; login cookie is HttpOnly/Secure/SameSite Strict and limited to the chosen path. Password stored as salted scrypt hash. CLI changes rotate all signed sessions. The dashboard does **not** modify firewall, expose credentials, create tunnels, open ports, or execute commands from the browser.


### Appearance & accessibility (v1.1)

- Product name in both pages: **جمشید / JAMSHID**. Systemd unit and config paths retain `network-radar` names for backward compatibility with the earlier package; **do not install both versions separately** on the same machine.
- Default dark mode: charcoal `#202124`. Light mode: warm ivory `#F5F1E8`. Buttons and cards retain glass / frosted blur effects and Google-color accents.
- The moon/sun toggle is on the login page and dashboard; it persists to **that browser's localStorage**, without storing theme preference on the server.
- The **Vazirmatn** font is loaded through the browser using Google Fonts (`fonts.googleapis.com` / `fonts.gstatic.com`). If these resources are unavailable on the connecting client, fallback fonts render; monitoring and authentication continue normally. Self-hosting a font later requires downloading it separately under its license and adjusting CSS/CSP.

### Updating an existing 1.0 installation (without resetting credentials)

The **installer intentionally refuses to overwrite an existing installation**. To upgrade code while preserving existing users and credentials, first back up `/etc/network-radar/config.json`, then run on the host from the extracted project root:

```bash
sudo cp /etc/network-radar/config.json /root/network-radar-config.backup.json
sudo cp -a app /opt/network-radar/
sudo systemctl restart network-radar
# Optionally install the new CLI command alias:
sudo ln -sfn /usr/local/sbin/radarctl /usr/local/sbin/jamshidctl
```

This only replaces app code/static assets; it keeps the same SSL certificate, Nginx path, credentials and dashboard URL. If the existing install used a nonstandard folder or service name, adjust these commands.

### Requirements

- Ubuntu server with `sudo` and internet access to Ubuntu apt/PyPI (or a configured local mirror / wheelhouse); Python >=3.10
- A dedicated subdomain resolving to the server, e.g. `jamshid.example.com`; A record correct, AAAA only if publicly reachable via IPv6.
- TCP **80** reachable **inbound** for Let's Encrypt HTTP-01 validation and **443** reachable inbound for dashboard access (security group, UFW and provider firewall). If your server in Iran is not reachable for ACME from Let's Encrypt, prefer DNS-01 using your DNS provider plugin; the provided automatic script assumes HTTP-01.
- The installer **preserves** existing Nginx sites. You must use a dedicated subdomain not already served by another Nginx virtual host; if the server already runs websites on this domain, integrate the `location` manually instead of running the unmodified installer.
- Existing services occupying port **18764 on loopback** conflict with this app: change that port in the unit and Nginx if needed.

### Installation

Unzip and run from the project's root:

```bash
sudo bash scripts/install.sh
```

The installer asks for:

- Dedicated domain name: `jamshid.example.com`
- Secret web path token: `jamshid-c7a8k9` (minimum 6 ASCII letters/digits/dashes)
- Dashboard username and password (12+ characters, hidden from terminal)

It creates `/opt/network-radar/`, `/etc/network-radar/config.json`, `network-radar.service`, Nginx proxy config and `/usr/local/sbin/radarctl` and the `jamshidctl` alias. The app binds to **127.0.0.1:18764** only; Nginx is the sole public frontend. HTTP is installed only as the temporary ACME bootstrap. **Do not attempt login until HTTPS is issued.** Secure cookies prevent plain HTTP login sessions.

After DNS and firewall are configured:

```bash
sudo bash scripts/enable-ssl.sh jamshid.example.com
sudo certbot renew --dry-run
```

This script installs the Ubuntu apt version of Certbot and its Nginx plugin if absent, then configures HTTPS + redirect. The Ubuntu and Certbot projects alternatively recommend the snap distribution (`sudo snap install --classic certbot`) when available. Do not install conflicting Certbot versions.

Your URL is:

```
https://jamshid.example.com/jamshid-c7a8k9/
```

This URL is **illustrative** and not usable until you supply a real DNS name.

### Credentials (Ubuntu CLI)

```bash
sudo jamshidctl passwd
sudo jamshidctl username
sudo jamshidctl rotate-sessions
sudo jamshidctl show
```

`passwd`, `username`, and `rotate-sessions` invalidate previous login sessions. Changing credentials does not require any change to the Nginx configuration.

### Customize global targets to include your VPS servers

Open the configuration file:

```bash
sudo nano /etc/network-radar/config.json
```

Edit the `targets` list to add, for example:

```json
{"id":"my-de","name":"My Germany VPS","country":"DE","host":"203.0.113.10","port":443,"enabled":true}
```

`203.0.113.10` is **documentation-only**, not an actual reachable IP. Replace it with your VPS real IP or domain and a port actually listening there. For Iran → Germany/Switzerland/Türkiye/USA, define **one or more endpoints in each destination country** on infrastructure you own. This permits per-country reachability comparisons without inferring geolocation from commercial CDNs. After changes:

```bash
sudo systemctl restart network-radar
```

**Safeguard:** Config is root-writeable and readable to netradar only; never add public user-entered test hosts as an unauthenticated API. The target test is limited to a maximum of 24 destinations.

### Operations

```bash
sudo systemctl status network-radar --no-pager
sudo journalctl -u network-radar -n 80 --no-pager
sudo nginx -t
sudo ss -lntup | grep -E ':80|:443|:18764'
```

To update installed files manually, copy `app` and `requirements.txt` from a trusted release into `/opt/network-radar`, update the venv and restart. Do not overwrite credentials without backing up the config.

### Limitations / security notes

1. **Listening != open from outside**; the dashboard does not perform an external reverse port scan. For accurate inbound reachability, a separate probe agent on a foreign server would be required. An Iranian server cannot reliably infer which networks can reach it solely through local sockets.
2. **Protocol heuristics != protocol identification**. Port 443 can be HTTPS, Trojan, VLESS TLS, Reality, a custom binary service, etc.; number alone cannot differentiate them. Systemd detection is best-effort, especially with Docker/3x-ui.
3. An unprivileged service cannot inspect protected WireGuard peer secrets/configurations or all socket PIDs. This is intentional, to avoid granting root to a web-facing application.
4. The ping subprocess needs ICMP sockets permitted by the host kernel; a failed ping with a successful TCP connect can be normal.
5. UDP STUN failures may mean a blocked STUN service, DNS trouble, firewall, or timeout; not a proof that WireGuard is blocked.
6. Default route traffic metrics only reflect one chosen network interface. Overlay/tunnel traffic may use another interface. Time series and events are **in memory**, and data starts empty after restart.
7. Running HTTPS on a subpath alone isn't isolation or a substitute for proper authentication. Protect your domain and ideally restrict dashboard ingress to your admin VPN/IP if possible; keep OS and dependencies updated.
8. The web panel reports from the point of view of **this one server**; testing country-specific traffic and inbound connectivity can be added later with authenticated probes from foreign VPSs.
9. If Let's Encrypt HTTP-01 is inaccessible (including due to upstream blocks), request certificates using DNS-01 or your provider's DNS plugin. The provided SSL script does not automatically provide DNS-01.

### Developer smoke tests

```bash
python3 -m pip install -r requirements.txt pytest httpx
python3 -m pytest -q
```

Development example config is a placeholder and **does not include a functional default password**. Production credentials must be created by the installer. This avoids shipping a default credential.
