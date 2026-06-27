# Testing All 9Router Provider Connections

## Quick Test Script

Run this to test all connected providers through 9Router in one go:

```python
import urllib.request, json, http.cookiejar, time

# Login to 9Router dashboard API
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
login_data = json.dumps({"password": "Mona187"}).encode()
req = urllib.request.Request("http://localhost:20128/api/auth/login", data=login_data, headers={"Content-Type": "application/json"})
resp = opener.open(req)
resp.read()

def test_model(model, name):
    """Test a single model through 9Router. Handles SSE response format."""
    test_data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Say hello in one word"}],
        "max_tokens": 50,  # MiMo v2 Pro needs 50+ (reasoning tokens consume budget first)
        "stream": False
    }).encode()
    
    req = urllib.request.Request(
        "http://localhost:20128/v1/chat/completions",
        data=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    start = time.time()
    try:
        resp = opener.open(req, timeout=30)
        raw = resp.read().decode()
        elapsed = time.time() - start
        
        # Handle SSE format (data: prefix)
        if raw.startswith('data: '):
            data = json.loads(raw[6:].strip())
        else:
            data = json.loads(raw)
        
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        reasoning = data.get('choices', [{}])[0].get('message', {}).get('reasoning_content', '')
        model_used = data.get('model', 'unknown')
        usage = data.get('usage', {})
        
        # For thinking models, content may be empty but reasoning has the output
        if not content and reasoning:
            content = f"[thinking] {reasoning[:50]}"
        
        print(f"✅ {name} ({elapsed:.1f}s) — {model_used} — {content[:60]}")
        return True
    except Exception as e:
        elapsed = time.time() - start
        error_msg = str(e)
        if hasattr(e, 'read'):
            raw = e.read().decode()
            if raw.startswith('data: '):
                try:
                    data = json.loads(raw[6:].strip())
                    error_msg = data.get('error', {}).get('message', str(e))
                except:
                    error_msg = raw[:100]
        print(f"❌ {name} ({elapsed:.1f}s) — {error_msg[:80]}")
        return False

# Test all common models
models = [
    ("xmtp/mimo-v2-omni", "MiMo Omni (FASTEST)"),
    ("xmtp/mimo-v2-pro", "MiMo Pro"),
    ("kr/claude-sonnet-4.5", "Kiro Sonnet"),
    ("kr/claude-haiku-4.5", "Kiro Haiku"),
    ("kr/deepseek-3.2", "Kiro DeepSeek"),
    ("kimchi/minimax-m2.7", "Kimchi MiniMax"),
    ("kimchi/minimax-m2.5", "Kimchi MiniMax Fast"),
    ("tokenrouter/MiniMax-M3", "TokenRouter M3 (FREE)"),
]

print("=== Testing All 9Router Providers ===\n")
results = []
for model, name in models:
    results.append(test_model(model, name))

print(f"\n=== Summary: {sum(results)}/{len(results)} passed ===")
```

## What to Check

1. **Each provider returns 200** — not 401 (auth), 403 (blocked), or 500 (upstream error)
2. **Response has content** — thinking models (`mimo-v2.5-pro`, `kimi-k2.5`) may return empty `content` with `reasoning_content` instead
3. **Response time** — MiMo ~1.5s, Kimchi ~1.6s, Kiro ~2s (all reasonable)
4. **Model name matches** — response should show the actual model used

## Common Failure Modes

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | API key invalid/expired | Replace key via dashboard |
| 403 error 1010 | Cloudflare IP block | Use proxy or wait |
| 403 (no 1010) | Datacenter IP blocked | Use residential proxy |
| 500 Internal Error | Upstream provider down | Wait and retry |
| "Expecting value" | SSE parsing issue | Handle `data: ` prefix |
| Empty content | Thinking model | Check `reasoning_content` field |
| "No active credentials" | Wrong model prefix | Use `xmtp/` not `mimo/` for MiMo |
| "Missing API key" (ALL providers) | 9Router restart cleared API keys | Re-add API keys via dashboard, check `apiKeys` table has CLI secret |
| "Invalid token" (TokenRouter only) | Rate limit on direct API | Use 9Router proxy, not direct curl |

## API Key Loss After 9Router Restart

9Router restart clears API keys from `providerSpecificData` — connections show `key: False` even though they existed before restart. This affects ALL custom providers (TokenRouter, Kimchi, MiMo). Symptom: ALL `/v1/chat/completions` return `"Missing API key"` or `"Invalid API key"`.

**Root cause:** `requireApiKey` resets to `true` on restart AND stored API keys may be lost from connection data.

**Fix:**
1. Check `apiKeys` table has CLI secret: `curl -s "http://localhost:20128/api/keys" -b /tmp/cookies.txt`
2. If empty, login and re-add API keys to connections via dashboard
3. Verify each connection has `key: True`: `curl -s "http://localhost:20128/api/providers" -b /tmp/cookies.txt | python3 -c "import sys,json; [print(c['name'], c['providerSpecificData'].get('apiKey','')[:10]) for c in json.load(sys.stdin)['connections']]"`

**Prevention:** After adding connections, verify keys persist by checking `/api/providers` response shows non-empty apiKey fields.
