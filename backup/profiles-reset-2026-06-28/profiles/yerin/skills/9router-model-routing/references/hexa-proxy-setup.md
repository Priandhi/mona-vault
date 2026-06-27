# Hye-Jin VPS Proxy Setup

## Current Status (Jun 11, 2026)

**PERMISSION OBTAINED from sayang** to use Hye-Jin's VPS (13.211.42.29) as proxy for Kimchi.

Before using again in future sessions — ALWAYS ask permission first.

## Setup Details

- **VPS:** 13.211.42.29 (Hye-Jin's VPS, Singapore)
- **SSH Key:** `~/.ssh/id_ed25519` (passwordless)
- **Local Port:** 8888 (SOCKS5 proxy on our VPS)
- **Remote Port:** 8888 (on Hye-Jin's VPS, pre-configured proxy service)

## Start Tunnel
```bash
ssh -D 8888 -f -C -q -N \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -i ~/.ssh/id_ed25519 \
  ubuntu@13.211.42.29
```

## Verify Working
```bash
# Test proxy
curl --proxy http://localhost:8888 https://httpbin.org/ip

# Test Kimchi through proxy (use Python to avoid escaping issues)
python3 << 'PYEOF'
import urllib.request, json
key = open('/tmp/k1.txt').read().strip()  # Kimchi key
body = json.dumps({"model":"minimax-m2.7","messages":[{"role":"user","content":"say ok"}],"max_tokens":5}).encode()
req = urllib.request.Request(
    'https://llm.kimchi.dev/openai/v1/chat/completions',
    data=body,
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'}
)
proxy_handler = urllib.request.ProxyHandler({'http': 'http://localhost:8888', 'https': 'http://localhost:8888'})
opener = urllib.request.build_opener(proxy_handler)
resp = opener.open(req, timeout=15)
print("✅ Proxy works:", resp.read().decode()[:100])
PYEOF
```

## Why This Works
- Kimchi.dev blocks our VPS IP (43.163.85.51)
- Hye-Jin's VPS has a clean IP not blocked by Kimchi
- SSH tunnel routes our requests through Hye-Jin's IP

## Pre-existing State
- Hye-Jin had a SOCKS5 proxy already running on port 8888
- SSH tunnel connects our port 8888 → Hye-Jin's port 8888
- No additional setup needed on Hye-Jin's side

## ⚠️ Remember
This is Hye-Jin's resource. **Always ask sayang before using.**
If tunnel dies, restart: `sudo systemctl restart ssh-tunnel-proxy`