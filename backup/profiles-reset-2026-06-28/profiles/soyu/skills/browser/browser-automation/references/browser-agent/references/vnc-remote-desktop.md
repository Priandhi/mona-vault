# VNC Remote Desktop — Browser Access from Anywhere

## Architecture

```
Xvfb (:99) → x11vnc (port 5900) → noVNC/websockify (port 6080) → nginx (port 80) → tunnel (external)
```

## Setup (already configured on VPS 43.163.85.51)

### 1. Xvfb — Virtual Framebuffer
```bash
# Already running on :99 (check with: ps aux | grep Xvfb)
Xvfb :99 -screen 0 1920x1080x24 &
```

### 2. x11vnc — VNC Server
```bash
# Set VNC password (one-time)
mkdir -p ~/.vnc
x11vnc -storepasswd mona123 ~/.vnc/passwd

# Start VNC server
x11vnc -display :99 -rfbauth ~/.vnc/passwd -rfbport 5900 \
  -noxrecord -noxfixes -noxdamage -shared -forever &
```

### 3. noVNC — Web-based VNC Client
```bash
# noVNC comes with websockify
# Start websockify on port 6080, proxying to VNC on 5900
websockify --web /usr/share/novnc/ 6080 localhost:5900 &
```

### 4. nginx Reverse Proxy (for port 80)
```nginx
# /etc/nginx/sites-available/novnc
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
```bash
sudo ln -sf /etc/nginx/sites-available/novnc /etc/nginx/sites-enabled/novnc
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

## Tunneling for External Access

**PROBLEM:** Tencent Cloud (and most cloud providers) block ports at the security group level. Ports 80, 6080, 5900 are not accessible externally even if firewall (ufw/iptables) allows them.

**SOLUTION:** Tunnel through an external service that provides a public URL.

### Option A: localhost.run (SSH-based, no install, RECOMMENDED)
```bash
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 \
  -R 80:localhost:6080 nokey@localhost.run
```
- Generates URL like `https://abc123.lhr.life`
- Free, no account needed
- URL changes on reconnect
- Supports WebSocket (required for VNC)
- Add `-f` to background (but loses URL output)

### Option B: Cloudflare Quick Tunnel (no account needed)
```bash
cloudflared tunnel --url http://localhost:6080
```
- Install: `sudo curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared && sudo chmod +x /usr/local/bin/cloudflared`
- Generates URL like `https://random-words.trycloudflare.com`
- **PITFALL:** May fail with `ERR Error unmarshaling QuickTunnel response: error code: 1101` — cloudflare server 500. Fallback to localhost.run.

### Option C: SSH Tunnel (from user's device)
```bash
# On user's phone (Termux) or PC:
ssh -L 6080:localhost:6080 ubuntu@43.163.85.51
# Then open: http://localhost:6080/vnc.html
```
- Requires SSH access
- Port stays local (no public URL)
- Works on iPhone via Termius app with port forwarding

### Option D: Open ports in Tencent Cloud Console
1. Login → Cloud Servers → Security Groups
2. Add Inbound Rule: Port 80, TCP, 0.0.0.0/0, Allow
3. Also open 6080 if nginx proxy not used

## Launching Chrome on VNC Display

### Using Playwright's Built-in Chromium (RECOMMENDED)
```bash
# Find Playwright chromium binary
CHROMIUM_PATH=$(find ~/.cache/ms-playwright/chromium-* -name "chrome" -type f | head -1)

# Launch on VNC display
DISPLAY=:99 $CHROMIUM_PATH \
  --no-sandbox \
  --disable-gpu \
  --disable-dev-shm-usage \
  --no-first-run \
  --disable-default-apps \
  --start-maximized \
  --user-data-dir=/path/to/profile \
  "https://example.com"
```

### With Extension (e.g. Rabby Wallet)
```bash
DISPLAY=:99 $CHROMIUM_PATH \
  --no-sandbox \
  --disable-gpu \
  --disable-dev-shm-usage \
  --disable-extensions-except=/path/to/extension \
  --load-extension=/path/to/extension \
  --start-maximized \
  --user-data-dir=/path/to/profile \
  "https://debank.com"
```

### Screenshot from VNC
```bash
# Install scrot if needed
sudo apt-get install -y scrot

# Capture entire VNC display
DISPLAY=:99 scrot /tmp/vnc_screenshot.png
```

## Window Manager for xdotool

**PROBLEM:** `xdotool search` returns empty on bare Xvfb without a window manager.

**FIX:** Install and start fluxbox:
```bash
sudo apt-get install -y fluxbox
DISPLAY=:99 fluxbox &
```

After fluxbox starts, `xdotool search --name "Chrome"` works correctly.

## Access from Mobile (iPhone/Android)

### Via Safari/Chrome (any phone)
1. Open tunnel URL (from localhost.run or cloudflared)
2. If directory listing appears, tap `vnc.html`
3. Enter VNC password: `mona123`
4. Browser desktop appears — pinch to zoom, drag to pan

### Via Termius SSH (iPhone)
1. New Host → Hostname: `43.163.85.51`, Port: `22`, Username: `ubuntu`
2. Port Forwarding → Local Port: `6080`, Destination: `localhost:6080`, Type: Local
3. Connect, then open `http://localhost:6080/vnc.html` in Safari
4. Enable Background App Refresh for Termius to stay connected

## Common Issues

| Issue | Cause | Fix |
|---|---|---|
| Chrome won't start | Wrong DISPLAY | Use `:99` not `:0` |
| `Missing X server or $DISPLAY` | Background process lost env | Set `DISPLAY=:99` in command, not env |
| `xdotool` returns empty | No window manager | Start `fluxbox` on `:99` |
| Tunnel URL shows directory listing | noVNC not at root | Navigate to `vnc.html` |
| `scrot` hangs | Display timeout | Install `scrot`, ensure DISPLAY is set |
| Port externally blocked | Cloud security group | Use tunnel (localhost.run/cloudflared) |
| Cloudflare tunnel 500 | Server-side error | Fallback to localhost.run |
| Chrome crashes immediately | Missing deps | Install: `sudo apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2` |
| noVNC shows gray screen | No app on display | Launch Chrome first |
