# API Key Validation — Direct Testing

When a service reports `401 Invalid API Key`, validate the key directly before assuming it's a config issue.

## The /models vs /chat/completions Trap

**Discovered Jun10:** Some providers (e.g., MiMo/xiaomimimo) return 401 on `/v1/models` even when the key is valid for `/v1/chat/completions`. The `/models` endpoint may not be supported or may use different auth.

**Always test the actual endpoint the service uses:**

```python
import urllib.request, json

def validate_api_key(base_url, api_key, model):
    """Test API key against the chat/completions endpoint."""
    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 5
    }).encode()
    
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return {"valid": True, "status": resp.status}
    except Exception as e:
        body = ""
        if hasattr(e, "read"):
            body = e.read().decode()[:200]
        return {"valid": False, "error": str(e), "body": body}

# Example usage:
result = validate_api_key(
    "https://token-plan-sgp.xiaomimimo.com/v1",
    "your-key-here",
    "mimo-v2.5-pro"
)
print(result)
```

## Gateway vs Direct Auth

**Discovered Jun10:** A key that works through the Hermes gateway (custom provider) may fail for direct API calls. The gateway may:
- Use a different auth mechanism (proxy, token exchange)
- Add headers the service doesn't expect
- Route through a different endpoint

When diagnosing:
1. Check if the service uses the key directly (like meridian) or through a gateway
2. Test the key the same way the service uses it
3. If gateway works but direct fails, the issue may be auth format, not key validity

## MiMo Provider Specifics

- Base URL: `https://token-plan-sgp.xiaomimimo.com/v1`
- Auth: `Authorization: Bearer <key>`
- Model: `mimo-v2.5-pro`
- `/v1/models` → may return 401 (not supported)
- `/v1/chat/completions` → works with valid key
- Keys can expire or be revoked — rotate in `user-config.json` (`llmApiKey` field)

## Quick Shell Test

```bash
# One-liner to test a key
curl -s -X POST "https://provider.example.com/v1/chat/completions" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"model-name","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
  | head -c 200
```

- Returns JSON with `choices` → key is valid
- Returns `{"error":{"code":"401",...}}` → key is invalid/expired
