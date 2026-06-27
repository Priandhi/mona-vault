# kimi.dev Direct API Setup (Not via OpenRouter)

## Docs Reference

From https://platform.kimi.ai/docs/api/overview:
- API is OpenAI-compatible (Chat Completions format)
- Direct HTTP: `https://api.moonshot.ai/v1/chat/completions`
- SDK base_url: `https://api.moonshot.ai/v1`

From https://www.kimi.com/code/docs/en/:
- Kimi Code API base URL: `https://api.kimi.com/coding/v1`
- Key format: `sk-kimi-...` (keys prefixed `sk-kimi-` auto-route to Kimi Code API)
- Compatible with OpenAI and Anthropic protocols

## Two kimi.dev Products

| Product | Base URL | Key Format | Models |
|---------|----------|------------|--------|
| Kimi AI (general) | `https://api.moonshot.ai/v1` | `sk-...` | kimi-k2.5, kimi-k2.6, kimi-latest |
| Kimi Code (coding) | `https://api.kimi.com/coding/v1` | `sk-kimi-...` | kimi-for-coding |

## Hermes Config for kimi.dev Direct

```yaml
model: kimi/kimi-k2.5  # or kimi/kimi-k2.6
providers:
  kimi:
    type: openai
    base_url: https://api.moonshot.ai/v1
    api_key: sk-...your-key...
    models:
      - kimi/kimi-k2.5
      - kimi/kimi-k2.6
      - kimi/kimi-latest
```

Or for Kimi Code (coding-focused):
```yaml
model: kimi/kimi-k2.5
providers:
  kimi-code:
    type: openai
    base_url: https://api.kimi.com/coding/v1
    api_key: sk-kimi-...your-key...
    models:
      - kimi-for-coding  # or whatever model name kimi.dev assigns
```

## Test from VPS

```bash
# Test general kimi API
curl -s -w '\nHTTP:%{http_code}' -X POST 'https://api.moonshot.ai/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-...' \
  -d '{"model":"kimi-k2.5","messages":[{"role":"user","content":"say OK"}],"max_tokens":3}' \
  --connect-timeout 10 --max-time 20

# Test Kimi Code API
curl -s -w '\nHTTP:%{http_code}' -X POST 'https://api.kimi.com/coding/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-kimi-...' \
  -d '{"model":"kimi-for-coding","messages":[{"role":"user","content":"say OK"}],"max_tokens":3}' \
  --connect-timeout 10 --max-time 20
```

## User Preference (Hye-Jin)

User said "gausah pake openrouter langsung dari vps nya aja sesuai docs kimi.dev" — wants Hye-Jin (on VPS 13.211.42.29) to call kimi.dev directly from that VPS, not routed through OpenRouter. Pending: user to provide kimi.dev API key.

## Model Name Validation

**CRITICAL:** Model names MUST match what kimi.dev recognizes. Invalid model IDs return:
```
HTTP 400: kimi/kimi-k2.5 is not a valid model ID
```

Before configuring, test with `/v1/models` endpoint or a simple completion request.