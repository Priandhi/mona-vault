# Direct API Provider Setup for Secondary Bots

## Pattern: Skip 9Router, Use Direct API

When secondary bot runs on a different VPS, prefer direct API over 9Router tunnel.

### When to use direct API:
- Bot VPS IP is NOT blocked by the provider (most AWS/GCP IPs are fine)
- Provider has its own API endpoint (Kimchi.dev, OpenRouter, etc.)
- You want to avoid tunnel dependency

### When to use 9Router tunnel:
- Bot VPS IP IS blocked by the provider (rare)
- You want to share a single API key across multiple bots
- Provider requires specific IP whitelist

## Example: Kimchi.dev Direct Setup

### Config (config.yaml):
```yaml
model:
  api_mode: chat_completions
  base_url: https://llm.kimchi.dev/openai/v1  # ✅ CORRECT — api.kimchi.dev FAILS
  default: minimax-m2.7
  provider: kimchi

custom_providers:
  - name: kimchi
    api_key: <YOUR_KIMCHI_API_KEY>
    base_url: https://llm.kimchi.dev/openai/v1
    api_mode: chat_completions
```

### Verify from VPS:
```bash
# Test API key works from this VPS
curl -s -w "\n%{http_code}" -X POST "https://llm.kimchi.dev/openai/v1/chat/completions" \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"model":"minimax-m2.7","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
# Should return HTTP 200
```

### Restart gateway:
```bash
# On remote VPS
ssh -i ~/.ssh/id_ed25519 ubuntu@VPS-IP '
kill $(pgrep -f "hermes.*gateway") 2>/dev/null
sleep 2
nohup ~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main --profile <name> gateway run > /tmp/hermes.log 2>&1 &
sleep 5
tail -20 /tmp/hermes.log
'
```

## Example: OpenRouter Direct Setup

```yaml
model:
  api_mode: chat_completions
  base_url: https://openrouter.ai/api/v1
  default: nousresearch/hermes-3-llama-3.1-405b:free
  provider: openrouter

custom_providers:
  - name: openrouter
    api_key: <YOUR_OPENROUTER_KEY>
    base_url: https://openrouter.ai/api/v1
    api_mode: chat_completions
```

## Real-World Example: Hye-Jin Kimchi Setup (Jun 2026)

VPS: 13.211.42.29 (AWS Sydney), Profile: `hyejin`

### Config locations updated:
1. **Main config** (`~/.hermes/config.yaml`): `model: kimchi/minimax-m2.7`, `provider: 9router` (using 9Router as local proxy)
2. **Profile config** (`~/.hermes/profiles/hyejin/config.yaml`): `model: kimchi/minimax-m2.7`, `provider: 9router`
3. **Custom providers** in both configs:
```yaml
custom_providers:
  - name: kimchi
    api_key: <KIMCHI_API_KEY>
    base_url: https://llm.kimchi.dev/openai/v1  # ✅ CORRECT
    api_mode: chat_completions
    model: minimax-m2.7
```

### Token format:
Kimchi tokens look like: `castai_v1_<hex>_<hex>` (long strings, ~80+ chars)

### Test command:
```bash
curl -s -w "\n%{http_code}" -X POST "https://llm.kimchi.dev/openai/v1/chat/completions" \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"model":"minimax-m2.7","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
```

### Key learning:
- `https://api.kimchi.dev/v1` → ❌ HTTP 000 (connection refused from everywhere)
- `https://llm.kimchi.dev/openai/v1` → ✅ WORKS — use this endpoint
- Always test from remote VPS first before configuring — AWS IPs may have connectivity issues to some endpoints

## Pitfalls

- **`custom_providers` format:** MUST be YAML list with `- name:`, NOT dict. See main skill pitfalls section.
- **API key validation:** Always test with curl before restarting gateway. Saves debugging time.
- **Model name format:** Kimchi uses bare model names (`minimax-m2.7`), not prefixed (`kimchi/minimax-m2.7`) when using direct provider. Check provider docs for exact model IDs.
- **Telegram token separate issue:** If gateway starts but bot doesn't respond, check telegram token first — it's often revoked/expired, unrelated to API provider config.
- **Config key names differ:** Main config uses `model.default` + `model.provider`, profile config also uses these keys. Both must be updated.
- **Herms version matters:** Kimchi direct setup was tested on hermes v0.4.71 (Hye-Jin VPS).
