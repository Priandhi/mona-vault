# Kimchi API — Key Formats, Endpoints & Discovery

## Current Working Credentials (Jun 2026)

**Kimchi base URL:** `https://llm.kimchi.dev/openai/v1`
**Key format:** `castai_v1_<hex_long>_<hex_short>`
**Model:** `minimax-m2.7`
**Auth:** Bearer token in `Authorization` header

## Known Key Pairs

| Profile | Key Prefix | Base URL Used | Status |
|---------|-----------|---------------|--------|
| Local Mona (local .9router DB) | `castai_v1_6e8b7a...599dffe4` | `https://llm.kimchi.dev/openai/v1` | ✅ Works |
| Hye-Jin (VPS 13.211.42.29) | `castai_v1_a97ba3...332a2_c32d013b` | `https://llm.kimchi.dev/openai/v1` | ✅ Works |

## Endpoint Discovery — CRITICAL PITFALL

Kimchi has **TWO API endpoints**, only ONE works:

```
https://api.kimchi.dev/v1       ❌ HTTP 000 — connection refused from everywhere
https://llm.kimchi.dev/openai/v1  ✅ HTTP 200 — works from everywhere
```

**Always test from the target VPS before configuring:**
```bash
curl -s -w '\nHTTP:%{http_code}' -X POST 'https://llm.kimchi.dev/openai/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <KEY>' \
  -d '{"model":"minimax-m2.7","messages":[{"role":"user","content":"OK"}],"max_tokens":3}' \
  --connect-timeout 10 --max-time 20
```

Expected: `{"choices":...}` + `HTTP:200`

## Key Format Pattern

All Kimchi keys follow: `castai_v1_<32-char-hex>_<6-char-hex>`

Example (masked): `castai_v1_a97ba3f52cbeaefd035650ff149119b4c63a3b483ae8de86575c749a694332a2_c32d013b`

When embedding in configs, the full key must be used — truncated keys fail silently.

## Kimchi Key via 9Router DB

On the local machine, Kimchi keys are stored in the 9Router SQLite DB:

```bash
sqlite3 ~/.9router/db/data.sqlite \
  "SELECT json_extract(data,'$.apiKey'), json_extract(data,'$.defaultModel'), json_extract(data,'$.providerSpecificData.baseUrl') FROM providerConnections WHERE name='Kimchi-01';"
```

## Testing Kimchi via 9Router

```bash
# Get 9Router CLI secret
KEY=$(cat ~/.9router/auth/cli-secret)

# Test
curl -s -X POST http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KEY" \
  -d '{"model":"kimchi/minimax-m2.7","messages":[{"role":"user","content":"say hi"}],"max_tokens":5}' \
  --connect-timeout 10 --max-time 20
```

Expected: `{"id":"chatcmpl-...","choices":[...]}` + HTTP 200

## Token Refresh Pattern

When Kimchi issues a new key (old one expired or revoked):

1. **Get new key** from Kimchi dashboard or API
2. **Update ALL locations** — Kimchi keys appear in:
   - `~/.9router/db/data.sqlite` (local 9Router provider connection)
   - `~/.hermes/config.yaml` → `custom_providers[].api_key` (for direct-use bots)
   - `~/.hermes/.env` → `KIMCHI_API_KEY=...` (if using env var)
3. **Test via 9Router first** — validate the new key works before deploying
4. **Restart gateway** on all affected bots

## 9Router Token for API Access

9Router's own API (for managing providers/connections) uses the CLI secret:
```bash
cat ~/.9router/auth/cli-secret
```

Format: 64-char hex (no `castai_v1_` prefix).

This token authenticates to `http://localhost:20128/v1/chat/completions` as `Authorization: Bearer <cli-secret>`.