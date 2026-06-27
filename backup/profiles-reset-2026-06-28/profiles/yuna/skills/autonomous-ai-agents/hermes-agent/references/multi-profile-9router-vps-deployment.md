# 9Router VPS Deployment Reference

## Verified Setup (Jun 2026)

VPS: AWS Ubuntu (Hye-Jin bot, 13.211.42.29)
Image: `decolua/9router:latest` (v0.4.71)
Container ID: b6656224700b

## Docker Install (Confirmed Working)

```bash
# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Run 9Router
sudo docker run -d \
  --name 9router \
  --restart unless-stopped \
  -p 20128:20128 \
  -v $HOME/.9router:/app/data \
  -e DATA_DIR=/app/data \
  decolua/9router:latest

# Verify
sudo docker ps | grep 9router
curl -s http://localhost:20128/  # returns "/dashboard"
curl -s http://localhost:20128/v1/models | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d[\"data\"])} models available')"
```

## npm Install — FAILS on VPS

```
# DO NOT USE on headless VPS:
npm install -g 9router
9router --no-browser  # still crashes, restart loop (counter at 16+)
```

Root cause: 9Router is Next.js app, tries to open browser on startup. `--no-browser` flag doesn't fully prevent it. **Always use Docker on headless VPS.**

## Dashboard Access Options

### Option 1: SSH Tunnel (Quick Local Access)

From local machine:
```bash
ssh -L 20128:localhost:20128 user@vps-ip
# Then open http://localhost:20128/dashboard in browser
```

To expose to other devices on network (e.g., phone):
```bash
ssh -g -L 0.0.0.0:20128:localhost:20128 user@vps-ip
# Then open http://LOCAL_IP:20128/dashboard
```

**Pitfall:** Default SSH tunnel binds to 127.0.0.1 only. Must use `-g` flag AND `0.0.0.0:` prefix to make it accessible from other devices. Also requires `GatewayPorts yes` in `/etc/ssh/sshd_config` on the local machine — without it, `-g` is silently ignored.

### Option 2: Cloudflare Tunnel (Best for Mobile/Remote — No Port Opening)

No port opening needed. Creates a public HTTPS URL instantly:

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Run tunnel (foreground — shows URL in output)
cloudflared tunnel --url http://localhost:20128

# Or background:
nohup cloudflared tunnel --url http://localhost:20128 > /tmp/cf-tunnel.log 2>&1 &
sleep 5
grep trycloudflare.com /tmp/cf-tunnel.log  # extract URL
```

Output: `https://<random>.trycloudflare.com/dashboard`

**Pitfalls:**
- Quick tunnels (no Cloudflare account) have no uptime guarantee, URL changes every restart
- For persistent URL, need Cloudflare account + named tunnel
- This is the BEST option when user is on phone and can't open ports (AWS Security Group blocks most ports by default)

### Option 3: Nginx Reverse Proxy (Persistent, via Existing Web Server)

If nginx is already running on port 80, add a location block:

```nginx
# /etc/nginx/sites-available/9router
server {
    listen 80;
    server_name _;
    location /9router/ {
        proxy_pass http://127.0.0.1:20128/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

Then: `sudo ln -sf /etc/nginx/sites-available/9router /etc/nginx/sites-enabled/ && sudo nginx -t && sudo systemctl reload nginx`

Access at: `http://YOUR_IP/9router/dashboard`

**Pitfall:** `server_name _` may conflict with existing default server. Check existing nginx configs first. Use `server_name your-domain.com;` if conflict.

### Option 4: Open Port Directly

```bash
sudo ufw allow 20128/tcp
# + open in cloud security group (AWS: Inbound Rules → TCP 20128 from 0.0.0.0/0)
```

**Pitfall:** AWS Security Group and UFW are SEPARATE firewalls. Both must allow the port. UFW alone is not enough on AWS.

### Option 5: API Management (No Dashboard Needed)

```bash
# List models
curl -s http://localhost:20128/v1/models | jq '.data[].id'

# Test completion
curl -s http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"kimi/kimi-k2.5","messages":[{"role":"user","content":"hello"}]}'
```

## Free Providers Available (Jun 2026)

Total models: 350+ from 50+ providers. Many are FREE with no API key.

Top free picks for agent bots:
1. `kimi/kimi-k2.5` — Moonshot AI, strong reasoning, tool calling support
2. `glm/glm-5.1` — Zhipu AI, solid general capability
3. `opencode-go/kimi-k2.5` — Kimi via OpenCode Free (no auth)
4. `opencode-go/glm-5.1` — GLM via OpenCode Free
5. `kr/claude-sonnet-4.5` — FREE Claude via Kiro AI!
6. `opencode-go/mimo-v2-pro` — Xiaomi MiMo
7. `tokenrouter/MiniMax-M3` — MiniMax M3 via TokenRouter (free tier)
8. `kimchi/minimax-m2.7` — Kimchi direct (requires API key in 9Router connection)

### Kimchi via 9Router — Connection Setup

When adding Kimchi as a custom connection in 9Router dashboard:
- **Base URL:** `https://llm.kimchi.dev/openai/v1` (NOT `api.kimchi.dev/v1`)
- **API Type:** Chat (OpenAI-compatible)
- **Prefix:** `kimchi`
- **Default Model:** `minimax-m2.7`
- **API Key format:** `castai_v1_<hex>_<hex>` (~80+ chars)
- Test status may show `unavailable` briefly but key works — keep it

> ⚠️ **Kimchi has two endpoints:** `api.kimchi.dev/v1` → ❌ fails everywhere. `llm.kimchi.dev/openai/v1` → ✅ works. Always use the `llm.` subdomain.

## Model Name Format

9Router uses `provider/model` format:
- ✅ `kimi/kimi-k2.5`
- ✅ `glm/glm-5.1`
- ❌ `kimi-k2.5` (missing provider prefix)

## Docker Management

```bash
# Check status
sudo docker ps | grep 9router

# View logs
sudo docker logs 9router --tail 50

# Restart
sudo docker restart 9router

# Stop
sudo docker stop 9router

# Update to latest
sudo docker pull decolua/9router:latest
sudo docker stop 9router
sudo docker rm 9router
# Re-run with same flags
```

## Hermes Config Integration

See main SKILL.md section "Configure 9Router in Hermes config.yaml" for full config example.

Key points:
- `type: openai` (OpenAI-compatible endpoint)
- `base_url: http://localhost:20128/v1`
- `api_key: dummy` (9Router doesn't validate for built-in providers)
- Model names must use `provider/model` format
- Set `routing.default_provider: 9router`
- Keep OpenRouter as fallback in routing.fallback
