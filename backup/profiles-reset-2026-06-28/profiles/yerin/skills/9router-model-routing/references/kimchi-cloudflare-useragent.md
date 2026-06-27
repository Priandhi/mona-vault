# Kimchi Cloudflare User-Agent Filtering (Jun 2026)

## Problem
Cloudflare blocks Python's default `urllib.request` User-Agent with error 1010, but allows curl. Same key, same IP, same proxy — different results.

## Root Cause
Cloudflare bot detection flags Python's default User-Agent string (`Python-urllib/3.x`). curl's User-Agent (`curl/8.x`) is whitelisted.

## Verified Test (Jun 11, 2026)
- Direct from VPS: Python urllib → 403 error 1010
- Direct from VPS: curl → 200 OK
- Through Hye-Jin proxy: Python urllib → 403 error 1010
- Through Hye-Jin proxy: Python urllib + `User-Agent: curl/8.5.0` → 200 OK
- Through Hye-Jin proxy: curl → 200 OK

## Fix
Add `User-Agent: curl/8.5.0` header to ALL Python requests to Kimchi:

```python
from urllib.request import Request, urlopen, ProxyHandler, build_opener

# With proxy
proxy = ProxyHandler({'http': 'http://localhost:8888', 'https': 'http://localhost:8888'})
opener = build_opener(proxy)

req = Request(
    'https://llm.kimchi.dev/openai/v1/chat/completions',
    data=json.dumps({'model': 'minimax-m2.7', 'messages': [{'role': 'user', 'content': 'ok'}], 'max_tokens': 5}).encode(),
    headers={
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'User-Agent': 'curl/8.5.0'  # CRITICAL
    }
)
resp = opener.open(req, timeout=15)
```

## Key Expiry Pattern
Kimchi keys can expire/revoked suddenly (not rate limit). Symptoms:
- Key works in morning, 401 by afternoon
- `HTTP 401 Authorization Required` (HTML page, not JSON)
- Both direct and proxy requests fail

**Mitigation:** Keep 2+ active Kimchi connections in round-robin. If one fails, others continue.

## kimi-k2.5/kimi-k2.6 Thinking Models
These return `content: null` with reasoning in `reasoning_content` field. 9Router/Hermes cannot parse this. **Always use `minimax-m2.7` as default Kimchi model.**
