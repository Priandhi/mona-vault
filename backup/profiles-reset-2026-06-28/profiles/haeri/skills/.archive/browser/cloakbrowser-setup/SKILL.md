---
name: cloakbrowser-setup
description: Setup and use CloakBrowser with extensions (MetaMask, Rabby, etc.), VNC remote desktop, and Playwright automation on a headless VPS.
tags: [browser, metamask, vnc, cloakbrowser, automation, web3]
---

# CloakBrowser Setup & MetaMask Integration

## Prerequisites

```bash
# 1. Install CloakBrowser binary
python3.12 -m cloakbrowser install

# 2. Install CloakBrowser Python package
uv pip install cloakbrowser

# 3. Xvfb (virtual display) — must be running
Xvfb :99 -screen 0 1920x1080x24  # background
export DISPLAY=:99
```

## VNC Remote Desktop

```bash
# Install
sudo apt-get install -y x11vnc novnc websockify

# Set password
x11vnc -storepasswd YOUR_PASS ~/.vnc/passwd

# Start VNC server (background)
x11vnc -display :99 -rfbauth ~/.vnc/passwd -rfbport 5900 \
  -noxrecord -noxfixes -noxdamage -shared -forever

# Start noVNC web client (background)
websockify --web /usr/share/novnc 6080 localhost:5900

# Access: http://YOUR_IP:6080/vnc.html
```

### Cloud Port Blocking (CRITICAL)

**Cloud providers (Tencent Cloud, AWS, GCP, Azure) block ports at the SECURITY GROUP level, NOT the OS firewall.** `ufw inactive` + `iptables` clean does NOT mean ports are open. Even port 80/443 may be blocked by default.

**Detection:**
```bash
# Test from VPS itself (always works)
curl -s -o /dev/null -w "%{http_code}" http://localhost:6080/vnc.html

# Test externally (times out = blocked)
timeout 3 curl -s http://YOUR_PUBLIC_IP:6080/
```

**Solutions (in order of preference):**
1. **Open ports in cloud console** — requires user to login to cloud provider web UI
2. **nginx reverse proxy on port 80** — combine with tunnel if port 80 also blocked
3. **SSH tunnel** — user runs `ssh -L 6080:localhost:6080 user@vps` from their device
4. **Cloudflare Tunnel / localhost.run** — outbound tunnel, no inbound ports needed (see below)

### nginx Reverse Proxy for noVNC

Required for WebSocket support and using standard ports:

```bash
sudo apt-get install -y nginx

sudo tee /etc/nginx/sites-available/novnc << 'EOF'
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:6080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
}
EOF
sudo ln -sf /etc/nginx/sites-available/novnc /etc/nginx/sites-enabled/novnc
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

### Tunneling Services (When Ports Blocked)

When cloud security group blocks all inbound ports, use outbound tunneling. **Fallback chain:**

```bash
# Option 1: localhost.run (SSH-based, no install, most reliable)
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 \
  -R 80:localhost:6080 nokey@localhost.run
# → Gives HTTPS URL like https://abc123.lhr.life

# Option 2: Cloudflare Tunnel (needs install, sometimes 500 errors)
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
cloudflared tunnel --url http://localhost:6080
# → Gives URL like https://xxx.trycloudflare.com

# Option 3: bore (Rust-based, needs install)
# Download from https://github.com/ekzhang/bore/releases
bore local 6080 --to bore.pub
```

**Pitfall:** `cloudflared` quick tunnels (account-less) can fail with `error code: 1101` / `500 Internal Server Error`. Use `localhost.run` as primary fallback — it's SSH-based and almost always works.

### Mobile Access (iPhone/Android)

**iPhone (Termius app):**
1. Install Termius from App Store
2. New Host → Hostname: VPS_IP, Port: 22, Username: ubuntu, Password: VPS_PASSWORD
3. Port Forwarding → Local Port: 6080, Destination: localhost:6080, Type: Local
4. Connect, keep Termius in background (Settings → Termius → Background App Refresh → ON)
5. Safari: `http://localhost:6080/vnc.html`

**Android (Termux):**
```bash
pkg update && pkg install openssh
ssh -L 6080:localhost:6080 ubuntu@VPS_IP
# Keep Termux running (notification → Acquire wakelock)
# Chrome: http://localhost:6080/vnc.html
```

## Loading Extensions (CRITICAL)

Extensions MUST use `ExtensionSpec` objects, NOT raw strings:

```python
import sys
sys.path.insert(0, "/path/to/browser-agent/scripts")
from browser_engine import BrowserAgent, BrowserConfig
from extensions import ExtensionSpec, download_webstore_crx, unpack_crx

# Download MetaMask from Chrome Web Store
METAMASK_ID = "nkbihfbeogaeaoehlefnkodbefgpgknn"
crx_path = download_webstore_crx(METAMASK_ID, "~/.hermes/browser-data/extensions/metamask.crx")
unpacked = unpack_crx(crx_path, "~/.hermes/browser-data/extensions/metamask")

# Launch with extension
cfg = BrowserConfig(
    headless=False,  # Must be False for extensions
    cloaking=True,   # Use CloakBrowser stealth
    extensions=[ExtensionSpec.from_folder(str(unpacked), "metamask")],
)

async with BrowserAgent(cfg) as b:
    # Extension info
    print(b.loaded)  # [ResolvedExtension(name='metamask', version='...')]
    
    # Open MetaMask popup
    popup = await b.open_popup("metamask")
    
    # Navigate
    await b.goto("https://app.uniswap.org")
```

## BrowserAgent API

```python
# Key attributes
b.ctx          # BrowserContext (NOT b.context)
b.page         # Current page
b.loaded       # List of loaded extensions

# Key methods (all async)
await b.goto(url)
await b.open_popup("metamask")
await b.discover_extensions()
await b.find_extension("metamask")
await b.screenshot("name")
await b.click_text("button text")
await b.fill("selector", "value")
await b.snapshot()  # accessibility tree
```

## MetaMask Onboarding Flow

```python
# After opening MetaMask popup:
# 1. Click "Get started"
# 2. Click "Import an existing wallet"
# 3. Click "No thanks" (metrics)
# 4. Enter seed phrase (12/24 words)
# 5. Set password
# 6. Click "Import my wallet"
# 7. Click "Got it" → "Next" → "Done"

# Selectors (may change with MetaMask versions):
"[data-testid='onboarding-get-start']"
"[data-testid='import-wallet-button']"
"[data-testid='metametrics-no-thanks']"
"[data-testid='import-srp__srp-word-{idx}']"
"[data-testid='create-password-new']"
"[data-testid='create-password-import']"
```

## Rabby Wallet (Preferred over MetaMask)

User preference: "Rabby aja metamask berat dan lemot". Rabby is lighter, auto-switches chains, and has security simulation.

**Download from GitHub releases:**
```bash
curl -sL "https://api.github.com/repos/RabbyHub/Rabby/releases/latest" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); \
  [print(a['browser_download_url']) for a in d['assets'] if 'zip' in a['name'].lower()]"
curl -L "<URL>" -o /tmp/rabby.zip
mkdir -p ~/.hermes/browser-data/extensions/rabby
unzip -o /tmp/rabby.zip -d ~/.hermes/browser-data/extensions/rabby/
```

**Launch Chrome + Rabby:**
```bash
DISPLAY=:99 ~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome \
  --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --disable-extensions-except=~/.hermes/browser-data/extensions/rabby \
  --load-extension=~/.hermes/browser-data/extensions/rabby \
  --start-maximized --remote-debugging-port=9222 \
  --user-data-dir=~/.hermes/browser-data/vnc-browser-rabby \
  "chrome-extension://<EXT_ID>/index.html"
```

**Bulk wallet import:** Use CDP (`connect_over_cdp("http://localhost:9222")`) to automate. See `browser-agent` skill → `references/rabby-wallet-automation.md` for full automation patterns, extension hash routes, and import flow.

**Key routes:** `#/password` (set PW), `#/unlock` (unlock), `#/import` (import method), `#/no-address` (add address)

## Pitfalls

1. **`extensions` param takes ExtensionSpec objects, NOT strings** — will crash with `'str' object has no attribute 'detect_kind'`
2. **`b.context` doesn't exist** — use `b.ctx` for BrowserContext, `b._context()` also works (method, not property)
3. **headless=False required for extensions** — Chrome extensions don't load in headless mode
4. **Cloudflare blocks headless browsers** — even with CloakBrowser stealth, some sites still detect. Use VNC to manually solve challenges.
5. **MetaMask selectors change between versions** — always verify with screenshot before automating
6. **EPIPE errors** — Playwright can crash if browser context is used after close. Always use `async with` pattern.
7. **Cloud provider port blocking** — `ufw inactive` does NOT mean ports are accessible. Tencent Cloud/AWS/GCP block at security group level. Always test with `timeout 3 curl http://PUBLIC_IP:PORT/` from outside, not just localhost.
8. **cloudflared quick tunnels unreliable** — Account-less tunnels can fail with `500 Internal Server Error`. Use `localhost.run` as primary tunnel (SSH-based, no install, almost always works).
9. **noVNC needs WebSocket proxy** — Direct port forwarding without nginx breaks WebSocket connections. Always proxy through nginx with `Upgrade` and `Connection` headers.
10. **iPhone Termius background kill** — iOS aggressively kills background SSH. Enable Background App Refresh for Termius. For persistent tunnels, use tmux on VPS side so reconnect is instant.

## File Locations

```
~/.hermes/browser-data/
├── extensions/
│   ├── metamask.crx          # Packed extension
│   └── metamask/             # Unpacked extension
├── profiles/
│   └── metamask/             # Persistent browser profile (cookies, wallet state)
├── screenshots/              # Screenshot storage
└── cache/                    # Browser cache
```

## References

- `references/tunneling-and-remote-access.md` — Cloud port blocking detection, tunneling fallback chain (localhost.run → cloudflared → bore), nginx WebSocket proxy, mobile access via Termius/Termux, diagnostic scripts
- `references/metamask-automation-pattern.md` — MetaMask v13 automation module pattern, onboarding selectors, dApp connection flow, network switching, known v13 SPA conflicts
