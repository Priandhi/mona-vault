# VNC Remote Desktop Setup

Expose a visual desktop from a headless VPS for browser viewing from any device.

## Architecture

```
Xvfb (virtual display) → x11vnc (VNC server) → noVNC (web client) → tunnel → user browser
```

## Quick Setup

```bash
# 1. Xvfb virtual display
Xvfb :99 -screen 0 1920x1080x24 &

# 2. Window manager (REQUIRED for browser automation)
apt-get install -y fluxbox xdotool
DISPLAY=:99 fluxbox &

# 3. x11vnc
mkdir -p ~/.vnc
x11vnc -storepasswd YOUR_PASSWORD ~/.vnc/passwd
x11vnc -display :99 -rfbauth ~/.vnc/passwd -rfbport 5900 -noxrecord -noxfixes -noxdamage -shared -forever &

# 4. noVNC web client
websockify --web /usr/share/novnc/ 6080 localhost:5900 &
```

## Access Through Blocked Ports

Cloud providers often block ports except SSH. Use localhost.run SSH tunnel:

```bash
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 \
  -R 80:localhost:6080 nokey@localhost.run
```

Returns temporary HTTPS URL. URL changes on reconnect. Alternative: cloudflared quick tunnel (`cloudflared tunnel --url http://localhost:6080`) but less reliable.

## Launch Browser on VNC

```bash
DISPLAY=:99 /path/to/chrome --no-sandbox --disable-gpu --disable-dev-shm-usage --start-maximized "https://example.com"
```

## Key Pitfalls

- Always check which display number is in use: `ps aux | grep Xvfb`
- Fluxbox MUST start AFTER Xvfb and BEFORE Chrome
- `terminal(background=True)` Chrome needs DISPLAY in the command itself
- localhost.run tunnels expire on SSH disconnect — regenerate and re-pin URLs
- `pkill -f "localhost.run"` kills ALL tunnels — use specific PID to kill one
