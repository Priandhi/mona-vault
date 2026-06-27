# Tunneling & Remote Access Reference

## Problem

Cloud providers (Tencent Cloud, AWS, GCP, Azure, DigitalOcean) block inbound ports at the **security group** level. The OS firewall (`ufw`, `iptables`) is a SECOND layer — even with it disabled, ports are inaccessible externally.

**Key insight:** You cannot open security group ports from the VPS itself. You need either:
- Cloud provider web console / API / CLI credentials
- Outbound tunneling (bypasses inbound port restrictions entirely)

## Tunneling Services Comparison

### localhost.run (RECOMMENDED — Primary)
- **Type:** SSH-based reverse tunnel
- **Install:** None (uses existing SSH)
- **Reliability:** High — rarely fails
- **URL format:** `https://XXXX.lhr.life`
- **Limitations:** Anonymous tunnels get recycled; no custom domains on free tier

```bash
# Basic usage
ssh -o StrictHostKeyChecking=no -R 80:localhost:6080 nokey@localhost.run

# With keepalive (recommended for long sessions)
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 \
  -R 80:localhost:6080 nokey@localhost.run

# Background with output capture (run via terminal background=true)
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 \
  -R 80:localhost:6080 nokey@localhost.run 2>&1
```

**Gotcha:** Output includes ANSI escape codes and QR code. Parse the URL from the line containing `.lhr.life`.

### Cloudflare Tunnel (Secondary)
- **Type:** Cloudflare daemon
- **Install:** Binary download (~37MB)
- **Reliability:** Medium — quick tunnels (account-less) can fail with `500 Internal Server Error`
- **URL format:** `https://XXXX.trycloudflare.com`

```bash
# Install
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared

# Quick tunnel (no account needed)
cloudflared tunnel --url http://localhost:6080

# Named tunnel (requires Cloudflare account + DNS)
cloudflared tunnel create mytunnel
cloudflared tunnel route dns mytunnel vnc.example.com
cloudflared tunnel run mytunnel
```

**Gotcha:** `error code: 1101` / `500 Internal Server Error` on quick tunnels. This is a Cloudflare server-side issue, not your config. Fall back to localhost.run.

### bore (Tertiary)
- **Type:** Rust-based tunnel server
- **Install:** Binary download from GitHub releases
- **Reliability:** Medium
- **URL format:** `bore.pub:PORT`

```bash
# Install
curl -L https://github.com/ekzhang/bore/releases/latest/download/bore-v0.5.2-x86_64-unknown-linux-musl.tar.gz \
  -o /tmp/bore.tar.gz && tar xzf /tmp/bore.tar.gz -C /usr/local/bin/

# Usage
bore local 6080 --to bore.pub
```

### serveo.net (Legacy)
- **Type:** SSH-based (like localhost.run)
- **Status:** Sometimes down; less reliable than localhost.run

```bash
ssh -o StrictHostKeyChecking=no -R 80:localhost:6080 serveo.net
```

### ngrok (Paid)
- **Type:** Binary daemon
- **Reliability:** High but requires auth token
- **Free tier:** Limited, requires account

```bash
# Install + auth
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok-v3-stable-linux-amd64.tgz | tar xz -C /usr/local/bin
ngrok config add-authtoken YOUR_TOKEN
ngrok http 6080
```

## nginx Reverse Proxy (Required for WebSocket)

noVNC uses WebSocket connections. Direct port forwarding without nginx breaks WebSocket upgrade:

```nginx
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:6080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;      # CRITICAL for WebSocket
        proxy_set_header Connection "upgrade";        # CRITICAL for WebSocket
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;                     # 24h timeout for VNC sessions
    }
}
```

## Mobile Access Patterns

### iPhone (Termius)
1. Install Termius from App Store
2. New Host: Hostname=VPS_IP, Port=22, Username=ubuntu, Password=VPS_PASS
3. Port Forwarding: Local Port=6080, Destination=localhost:6080, Type=Local
4. Connect → keep background (Settings → Termius → Background App Refresh → ON)
5. Safari: `http://localhost:6080/vnc.html`

**Gotcha:** iOS kills background SSH aggressively. Enable Background App Refresh. Use tmux on VPS for session persistence.

### Android (Termux)
```bash
pkg update && pkg install openssh tmux
# Create persistent session
tmux new -s vnc
ssh -L 6080:localhost:6080 ubuntu@VPS_IP
# Ctrl+B, D to detach
# tmux attach -t vnc to reconnect
```

### Desktop (any SSH client)
```bash
# Simple tunnel
ssh -L 6080:localhost:6080 ubuntu@VPS_IP

# With compression (slow networks)
ssh -C -L 6080:localhost:6080 ubuntu@VPS_IP

# Background tunnel (Linux/Mac)
ssh -f -N -L 6080:localhost:6080 ubuntu@VPS_IP
```

## Detection Script

Run this to diagnose port accessibility:

```bash
#!/bin/bash
# diagnose-ports.sh
echo "=== Local Services ==="
ss -tlnp | grep -E 'LISTEN' | awk '{print $4}' | sort

echo -e "\n=== Local Access Test ==="
for port in 80 6080 5900; do
  code=$(timeout 3 curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/ 2>/dev/null)
  echo "Port $port: HTTP $code"
done

echo -e "\n=== External Access Test ==="
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "unknown")
for port in 80 6080 5900; do
  result=$(timeout 3 curl -s -o /dev/null -w "%{http_code}" http://$PUBLIC_IP:$port/ 2>/dev/null)
  if [ "$result" = "000" ] || [ -z "$result" ]; then
    echo "Port $port: BLOCKED (security group)"
  else
    echo "Port $port: HTTP $result (open)"
  fi
done

echo -e "\n=== Firewall Status ==="
sudo ufw status 2>/dev/null || echo "ufw not available"
```
