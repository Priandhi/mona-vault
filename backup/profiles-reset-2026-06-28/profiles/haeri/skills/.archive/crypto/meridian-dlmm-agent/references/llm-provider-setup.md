# LLM Provider Setup for Meridian

## MiMo (Xiaomi) — Recommended

**Why:** No rate limits, fast response (3-7s), good reasoning quality, same provider as Mona.

### Setup
1. Get API key from `~/.hermes/config.yaml` → `custom_api_key` field
2. Set in `user-config.json`:
```json
{
  "llmModel": "mimo-v2.5-pro",
  "llmBaseUrl": "https://token-plan-sgp.xiaomimimo.com/v1",
  "llmApiKey": "<key from config.yaml>"
}
```
3. Remove `OPENROUTER_API_KEY` from `.env` (optional, keep for fallback)
4. Remove `LLM_BASE_URL` and `LLM_API_KEY` from `ecosystem.config.cjs` env block
5. `pm2 delete meridian && pm2 start ecosystem.config.cjs`

### Performance
- Response time: 3-7 seconds
- Screening cycle: ~2 minutes
- No rate limits observed
- Quality: good reasoning, detailed risk assessment

## OpenRouter — Rate Limited

**Why NOT:** All free models share per-account rate limits. After ~50 requests, ALL models return 429 for 10-30 minutes.

### Setup
```env
OPENROUTER_API_KEY=sk-or-...
```
Default model: `openai/gpt-oss-20b:free`

### Available Free Models (June 2026)
- `openai/gpt-oss-20b:free` — good quality, fast
- `openai/gpt-oss-120b:free` — better quality, slower
- `nousresearch/hermes-3-llama-3.1-405b:free` — best quality, slowest
- `meta-llama/llama-3.3-70b-instruct:free` — good balance
- `google/gemma-4-31b-it:free` — fast, decent quality

### Performance
- Response time: 10-16 seconds
- Screening cycle: ~5 minutes
- Rate limit: ~50 requests per session, then 429 for 10-30 minutes
- Quality: good but inconsistent across models

## GeneralCompute — Alternative

### Setup
```env
LLM_BASE_URL=https://api.generalcompute.com/v1
LLM_API_KEY=gc_...del: `minimax-m2.7`

### Performance
- Response time: 5-10 seconds
- Screening cycle: ~3 minutes
- Rate limits: unknown
- Quality: good

## Switching Providers

### Step-by-step
1. Clear old provider from `user-config.json`:
   - Set `llmBaseUrl` to empty string `""`
   - Set `llmApiKey` to empty string `""`
2. Remove old env vars from `.env`
3. Remove old env vars from `ecosystem.config.cjs` env block
4. Set new provider in `user-config.json`
5. `pm2 delete meridian && pm2 start ecosystem.config.cjs`
6. Verify: `pm2 logs meridian --lines 5` should show new model name

### Common mistakes
- **Forgetting ecosystem.config.cjs:** PM2 caches env vars. Must delete + start, not just restart.
- **Not clearing user-config.json:** `||=` operator means old values persist.
- **Not removing .env vars:** Old vars take precedence over user-config.json.
