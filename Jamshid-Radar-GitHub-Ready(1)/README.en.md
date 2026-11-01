# JAMSHID — Network Radar for Ubuntu

[فارسی](README.md) · [Project website](docs/index.html) · [Installation guide (Persian)](راهنمای-فارسی.md)

**JAMSHID v1.1** is a self-hosted, read-only dashboard for Linux network observability, designed for administrators who need to inspect connectivity **from their Ubuntu server** toward foreign destinations. It features a charcoal dark theme, ivory light theme, Google-inspired accents, glass-like UI, RTL Persian labels, and the Vazirmatn font (loaded from Google Fonts when available).

![Dark dashboard — illustrative sample data](assets/dashboard-dark.png)

### Current capabilities

- Local TCP/UDP listening sockets (`ss`), IP interfaces and addresses.
- Live server health and network bandwidth statistics.
- Separate outbound TCP and ICMP checks for configurable foreign endpoints.
- DNS, HTTPS, IPv4, IPv6, and UDP/STUN diagnostic probes.
- Best-effort systemd VPN/proxy service discovery (does **not** guarantee a working tunnel).
- Admin login behind an Nginx reverse proxy, customizable secret path, Let's Encrypt via Certbot.
- Local CLI commands for account changes and session invalidation.

### Install

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/ArioBarzanMoradi/Jamshid-Radar.git
cd Jamshid-Radar
sudo bash scripts/install.sh
sudo bash scripts/enable-ssl.sh jamshid.example.com
```

Replace `USERNAME` and the example domain. The installer requests a dedicated subdomain, web path, administrator username, and password. For complete prerequisites, safety notes, and upgrade instructions, see [technical README](README.technical.md).

### Security and measurement scope

Listening port ≠ inbound network reachability. An outbound connection test does not prove a VPN or proxy configuration works. To validate inbound international connectivity, a separate authenticated remote agent is needed. Do not commit production configuration, secrets, TLS keys, or client VPN credentials. The GitHub Pages site is only a product introduction, not the monitoring service.

### Repository website

The `docs/` folder is a standalone static landing page. To publish it, configure **Settings → Pages → Deploy from a branch → main → /docs**. See [publication guide](GITHUB-PUBLISH-FA.md).

No distribution license has been selected yet; choose one before encouraging third-party redistribution.
