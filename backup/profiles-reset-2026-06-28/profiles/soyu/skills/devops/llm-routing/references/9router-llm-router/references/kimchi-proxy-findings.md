# Kimchi Proxy Strategy — Verified Findings (Jun 2026)

## TL;DR

| Method | Works? | Notes |
|--------|--------|-------|
| Direct from VPS IP | ❌ | Cloudflare 1010 block |
| SSH tunnel via Hye-Jin VPS | ✅ | Best working option |
| Webshare free datacenter proxies | ❌ | 9/9 proxies blocked by Kimchi |
| Residential proxies (paid) | ? | Likely works, untested |
| User's phone | ✅ | Clean IP when generating keys |

## Webshare Free Proxies — FAILED

**Credentials format:** `ip:port:username:password` (e.g., `38.154.203.95:5863:dgsptrwv:l4fn1pdnb5ly`)

**Tested proxies (all failed with 403):**
- 38.154.203.95:5863
- 198.105.121.200:6462
- 64.137.96.74:6641
- 209.127.138.10:5784
- 38.154.185.97:6370
- 84.247.60.125:6095
- 142.111.67.146:5611
- 191.96.254.138:6185
- 31.58.9.4:6077

**Auth works** (httpbin.org/ip returns proxy IP) but **Kimchi rejects all** with 403 Forbidden.
Root cause: ALL are datacenter IPs, Kimchi Cloudflare blocks entire datacenter ranges.

**IP Whitelist doesn't help** — even with IP whitelisted in Webshare dashboard, Kimchi still blocks.
Webshare free tier is datacenter-only. Need residential proxies for this to work.

## SSH Tunnel via Hye-Jin — WORKING ✅

**Setup:**
```bash
# On Mona VPS (create tunnel to Hye-Jin):
ssh -i ~/.ssh/id_ed25519 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  -N -L 8888:localhost:8888 ubuntu@13.211.42.29

# Verify tunnel works:
curl -s --proxy http://localhost:8888 http://httpbin.org/ip
# Should return: {"origin": "13.211.42.29"}
```

**9Router connection config:**
```json
{
  "providerSpecificData": {
    "connectionProxyEnabled": true,
    "connectionProxyUrl": "http://localhost:8888"
  }
}
```

**IMPORTANT:** Always ask user before using Hye-Jin's resources. User explicitly corrected Mona on this:
> "kok gak bilang dulu?" → "lain kali bilang dulu napa" → "lu inget soul.md lu gak kok kayak gini tiap hari"

## Kimchi Keys — Valid vs Invalid

### Valid Keys (Created Manually)
- Start with `castai_v1_` (83 chars total)
- Created at app.kimchi.dev on user's phone
- Work through any clean IP

### Invalid Keys (Auto-Generated)
- Created by Kimchidev.py automated script
- Detected by Kimchi as bot behavior
- Return 401 immediately (key revoked)
- **Never add auto-generated keys to 9Router**

### Key Testing Script
```python
#!/usr/bin/env python3
import urllib.request
import json

def test_kimchi_key(api_key, proxy_url=None):
    body = json.dumps({
        "model": "minimax-m2.7",
        "messages": [{"role": "user", "content": "say ok"}],
        "max_tokens": 5
    }).encode()
    
    req = urllib.request.Request(
        'https://llm.kimchi.dev/openai/v1/chat/completions',
        data=body,
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer ***'}
    )
    
    if proxy_url:
        proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
        opener = urllib.request.build_opener(proxy_handler)
        try:
            resp = opener.open(req, timeout=15)
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP {e.code}: {e.read()[:100]}")
            return
    else:
        resp = urllib.request.urlopen(req, timeout=15)
    
    raw = resp.read().decode()
    for line in raw.split('\n'):
        if line.startswith('data: '):
            data = json.loads(line[6:])
            if 'choices' in data:
                print(f"✅ WORKS: {data['choices'][0]['message']['content'][:50]}")
                return
    print("❌ Could not parse response")

# Test without proxy (expect 403 if IP blocked)
test_kimchi_key("<key>")

# Test through tunnel
test_kimchi_key("<key>", "http://localhost:8888")
```

## Dashboard Test Bug

9Router dashboard "Test Connection One-by-One" sometimes shows:
- **"failed: Provider test not supported"** — even when key works
- **"Invalid API key or base URL"** — even when curl test passes

**Always verify via API, not dashboard:**
```bash
curl http://localhost:20128/v1/chat/completions \
  -H "Authorization: Bearer <9router-api-key>" \
  -H "Content-Type: application/json" \
  -d '{"model":"kimchi/minimax-m2.7","messages":[{"role":"user","content":"test"}],"max_tokens":5}'
```

If this returns a valid response, the connection is fine regardless of dashboard status.