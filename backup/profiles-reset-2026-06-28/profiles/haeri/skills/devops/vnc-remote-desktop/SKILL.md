---
name: vnc-remote-desktop
description: Set up VNC remote desktop on headless VPS — Xvfb + x11vnc + noVNC web client + tunnel through blocked ports. Use when user wants to view/control a remote desktop or browser from phone/PC, or when launching visible browser automation.
tags: [vnc, xvfb, novnc, remote-desktop, browser, tunnel, cloudflare]
triggers:
  - VNC
  - remote desktop
  - view browser from phone
  - noVNC
  - x11vnc
---

# VNC Remote Desktop Setup

Expose a visual desktop from a headless VPS so the user can view it from any device browser (phone, PC, tablet).

## Architecture

```
Xvfb (virtual display) → x11vnc (VNC server) → noVNC (web client) → nginx/tunnel → user browser
```

## Setup Steps

### 1. Xvfb — Virtual Display

```bash
# Check if already running
ps aux | grep Xvfb

# Start if not running (display :99 is convention, CHECK FIRST)
Xvfb :99 -screen 0 1920x1080x24 &
```

**⚠️ PITFALL: Always check which display number is in use!**
```bash
ps aux | grep Xvfb
# Output: Xvfb :99 ... means DISPLAY=:99, NOT :0
```

### 2. x11vnc — VNC Server

```bash
# Set password first (one-time)
mkdir -p ~/.vnc
x11vnc -storepasswd YOUR_PASSWORD ~/.vnc/passwd

# Start x11vnc
x11vnc -display :99 -rfbauth ~/.vnc/passwd -rfbport 5900 \
  -noxrecord -noxfixes -noxdamage -shared -forever &
```

### 2b. Fluxbox — Window Manager (REQUIRED for browser automation)

Without a window manager, `xdotool` can't find windows, browser windows don't get focus,
and `scrot` screenshots show raw content without window decorations.

```bash
# Install
sudo apt-get install -y fluxbox xdotool

# Start on same display
DISPLAY=:99 fluxbox &
```

**⚠️ MUST start AFTER Xvfb and BEFORE Chrome.** Without fluxbox:
- `xdotool search --name "Chrome"` returns empty
- Browser windows are unfocusable
- `scrot` works but shows flat content with no window chrome

### 3. noVNC — Web Client

```bash
# noVNC usually ships with websockify
# Start websockify on port 6080 proxying to VNC port 5900
websockify --web /usr/share/novnc/ 6080 localhost:5900 &
```

**Check ports:**
```bash
ss -tlnp | grep -E '5900|6080'
curl -s -o /dev/null -w "%{http_code}" http://localhost:6080/vnc.html
```

### 4. Access — Handle Blocked Ports

Cloud providers (Tencent Cloud, AWS, GCP) often block all ports except SSH (22) by security group rules.

**Option A: localhost.run SSH tunnel (recommended — no install)**
```bash
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 \
  -R 80:localhost:6080 nokey@localhost.run
```
Returns a temporary HTTPS URL like `https://xxxxx.lhr.life`

**⚠️ This is a foreground SSH session — run with `background=true` in terminal tool.**
**⚠️ URL changes on reconnect — inform user.**
**⚠️ Tunnels expire!** localhost.run free tunnels are temporary. They return HTTP 503 when the SSH connection drops (network timeout, server restart, process kill). To detect: `curl -sI https://XXXX.lhr.life` returns 503 or times out. To regenerate: kill old SSH process, start new one, extract new URL from log output, re-send + re-pin in Telegram.

**Option B: Open ports in cloud security group (permanent)**
- Tencent Cloud Console → Cloud Servers → Security Groups → Add Inbound Rule
- Port 80 TCP 0.0.0.0/0 Allow
- Port 6080 TCP 0.0.0.0/0 Allow

**Option C: nginx reverse proxy on port 80 (if port 80 is open)**
```nginx
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:6080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

**Option D: SSH tunnel from phone (iPhone Termius, Android Termux)**
- Local Port: 6080 → Destination: localhost:6080
- Then browse: http://localhost:6080/vnc.html

**Option E: cloudflared quick tunnel (no account needed)**
```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
cloudflared tunnel --url http://localhost:6080
```
⚠️ Quick tunnels often fail with `500 Internal Server Error` / `error code: 1101`. **localhost.run (Option A) is significantly more reliable** — it's SSH-based, needs no install, and almost always works.

### 5. Launch Browser on VNC Display

**⚠️ CRITICAL: Use the correct DISPLAY number!**
```bash
# Check display
ps aux | grep Xvfb
# Then launch with that display
DISPLAY=:99 /path/to/chrome --no-sandbox --start-maximized "https://example.com"
```

**With MetaMask extension:**
```bash
DISPLAY=:99 /path/to/chrome \
  --no-sandbox \
  --disable-gpu \
  --disable-dev-shm-usage \
  --no-first-run \
  --disable-default-apps \
  --disable-extensions-except=/path/to/metamask \
  --load-extension=/path/to/metamask \
  --start-maximized \
  --user-data-dir=/path/to/profile \
  "https://example.com"
```

**Playwright's Chromium path:**
```bash
~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome
```

### 6. Screenshots from VNC

```bash
# Install scrot if needed
sudo apt-get install -y scrot

# Take screenshot
DISPLAY=:99 scrot /tmp/vnc_screenshot.png
```

Then use `vision_analyze` to inspect the screenshot.

## User Experience Notes

- noVNC web client: user opens URL in any browser, enters password
- On iPhone: Safari works fine, no app needed
- Left sidebar in noVNC has keyboard/mouse controls
- Mobile: pinch to zoom, use sidebar for modifier keys (Ctrl, Alt, etc.)

## Troubleshooting

| Issue | Fix |
|---|---|
| Black screen | Nothing running on display — launch a browser/app |
| "Missing X server or $DISPLAY" | Wrong display number — check `ps aux \| grep Xvfb` |
| Port timeout externally | Cloud security group blocking — use localhost.run tunnel |
| cloudflared 500 error | Use localhost.run instead |
| npm install fails | Use `sudo dpkg --configure -a` first if dpkg interrupted |
| noVNC shows directory listing | User needs to click `vnc.html` link |
| Chrome crashes on launch | Add `--no-sandbox --disable-gpu --disable-dev-shm-usage` |
| `terminal(background=True)` Chrome fails with "Missing X server" | DISPLAY must be in the command itself, not exported before background |
| Playwright can't find extension page | Launch Chrome with `--remote-debugging-port=9222`, then `p.chromium.connect_over_cdp("http://localhost:9222")` |
| Chrome needs remote debugging | Add `--remote-debugging-port=9222` to Chrome launch command, verify with `curl -s http://localhost:9222/json` |

## Multi-Tunnel Pattern (Multiple Dashboards)

When exposing multiple local services (e.g., Charon dashboard on :3458, Meridian on :3457):

```bash
# Start each as a separate background process
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:localhost:3458 nokey@localhost.run  # Charon
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:localhost:3457 nokey@localhost.run  # Meridian
```

Each returns a different `https://XXXX.lhr.life` URL. Track which URL maps to which service.

**PITFALL: Regenerating one tunnel kills all.** `pkill -f "localhost.run"` kills ALL tunnels. To regenerate just one, find its specific PID: `ps aux | grep "localhost:3458" | grep -v grep`.

**PITFALL: Telegram pinning after regeneration.** After regenerating a tunnel and sending the new URL to a Telegram forum topic, pin it immediately. Each bot can only pin messages it sent — if message was sent by @Monaa_Ai_Bot, only that bot's token can pin it. If sent by @DinoCantik_Bot, use that bot's token. To pin: `curl -s "https://api.telegram.org/bot${BOT_TOKEN}/pinChatMessage" -d '{"chat_id":"GROUP_ID","message_id":MSG_ID}'`.
