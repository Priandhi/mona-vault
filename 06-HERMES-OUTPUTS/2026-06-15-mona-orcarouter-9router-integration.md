---
type: receipt
date: 2026-06-15
tags:
  - receipt
---

# 2026-06-15 — Orcarouter.ai Integration to 9Router

## Task
Add 2 Orcarouter.ai API keys to 9Router as load-balanced LLM provider. Default model = `deepseek/deepseek-v4-flash`.

## Result
**✅ FULLY WORKING**

- 2 `providerConnections` added to 9Router: `OrcaRouter-01` & `OrcaRouter-02` (load-balanced, round-robin)
- 2 `providerNodes` created: `openai-compatible-chat-orcarouter-01` & `orcarouter-02`
- Real-call verified via 9Router:
  - `orcarouter/deepseek/deepseek-v4-flash` → "PONG" ✓
  - `orcarouter/anthropic/claude-haiku-4.5` → "PONG" ✓
- Default model updated: `tokenrouter/MiniMax-M3` → `orcarouter/deepseek/deepseek-v4-flash` (top-level in config.yaml, replace_all)

## Decisions

### 1. Base URL = `https://api.orcarouter.ai/v1` (NOT `https://orcarouter.ai/v1`)
- Marketing site is `orcarouter.ai` (no API)
- API is at `api.orcarouter.ai` (subdomain)
- Original .env had wrong base URL — caused "Invalid token" for 3 keys × 6+ auth methods
- Discovered via docs at `https://orcarouter.ai/docs` → "Point your SDK at `https://api.orcarouter.ai/v1`"

### 2. Model format = `provider/model` (OpenRouter-style)
- Orcarouter uses OpenRouter naming (e.g. `deepseek/deepseek-v4-flash`, `anthropic/claude-haiku-4.5`)
- 9Router requires prefix to route: `orcarouter/deepseek/deepseek-v4-flash`
- 9Router strips `orcarouter/` prefix → calls orcarouter with `deepseek/deepseek-v4-flash`

### 3. Settings already prepared for orcarouter
- 9Router `settings` table had pre-existing strategies for `orcarouter-01` & `orcarouter-02` (round-robin)
- Just needed to create the actual nodes + connections — no settings change needed

### 4. Default model change
- `config.yaml` top-level `model: tokenrouter/MiniMax-M3` → `orcarouter/deepseek/deepseek-v4-flash`
- Sub-purpose models (memory flush, etc.) kept on their existing models
- Current session still on old model until reload — next session uses new default

## Issues

### "Invalid token" mystery (resolved)
- Tested 3 keys × 6+ auth methods: Bearer, X-API-Key, raw, body, Origin header, HTTP/1.1, etc.
- All failed with "Invalid token"
- User confirmed key "active, $5 balance" in dashboard
- **Root cause: wrong base URL** (`orcarouter.ai` vs `api.orcarouter.ai`)
- 9Router settings already had orcarouter strategy, suggesting earlier debugging was on right track

### 9Router cached /v1/models
- `/v1/models` returns cached list, doesn't show orcarouter models
- But `/v1/chat/completions` works — routing by prefix functions

## Architecture Summary

```
User → 9Router (port 20128) → prefix match "orcarouter/"
  → providerConnections: OrcaRouter-01 (api.orca1) | OrcaRouter-02 (api.orca2)
  → providerNodes: openai-compatible-chat-orcarouter-0{1,2}
  → baseUrl: https://api.orcarouter.ai/v1
  → real model: deepseek/deepseek-v4-flash
```

## Next Steps

1. **Test current session with new default** — current session still uses `tokenrouter/MiniMax-M3`. Will only switch after restart or new request
2. **Monitor usage** — 2 keys × $5 = $10 total balance, should last a while
3. **Consider other orcarouter models** — Zyloo Opus 4.6 was previous fallback; can add orcarouter equivalent for redundancy
4. **Update skill** — save base-URL confusion as pitfall in hermes-provider-health or similar

## Key files changed
- `/home/ubuntu/.hermes/.env` — added ORCA_KEY_1, ORCA_KEY_2; fixed ORCA_BASE_URL
- `/home/ubuntu/.hermes/config.yaml` — top-level default model
- `/home/ubuntu/.9router/db/data.sqlite` — 2 nodes + 2 connections
