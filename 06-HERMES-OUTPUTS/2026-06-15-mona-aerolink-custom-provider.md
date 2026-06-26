---
type: receipt
date: 2026-06-15
tags:
  - receipt
  - ai
  - research
  - prompt-injection
---

# 2026-06-15 — Aerolink Custom Provider Setup (1-Day Override)

## Task
Set Hermes default model to Aerolink Opus 4.8 for 1 day. User wants to "habisin credit" Aerolink.

## Result
**✅ Custom provider `aerolink` configured. New sessions will use Opus 4.8 by default.**

## Architecture
```
Hermes session
  → http://localhost:20129/v1/chat/completions  (local proxy, PM2-managed)
    → POST /v1/messages  (Anthropic native)
      → Aerolink Claude Opus 4.8
        → Real Claude response, translated back to OpenAI format
```

## Files Created
- `~/aerolink_openai_server.py` — Local OpenAI-compat proxy (178 lines)
  - Listens on `0.0.0.0:20129`
  - Endpoints: `/v1/chat/completions`, `/v1/models`, `/health`
  - Translates OpenAI → Anthropic format
  - Strips `aerolink/` prefix defensively
  - Round-robin keys from `~/.hermes/.env` (AEROLINK_KEY_1, AEROLINK_KEY_2)
  - Concatenates multiple system messages
  - Maps stop_reason end_turn → "stop", else "length"
- `~/aerolink-pm2.config.js` — PM2 ecosystem config
  - autorestart: true, max_restarts: 50
  - Logs to /tmp/aerolink_server.{out,err}.log

## Config Changes
- `~/.hermes/config.yaml`:
  - `model.default: aerolink/claude-opus-4-8`
  - `model.provider: aerolink`
  - Added `custom_providers` entry:
    ```yaml
    - name: aerolink
      base_url: http://localhost:20129/v1
      api_key: not-needed
      api_mode: chat_completions
      model: claude-opus-4-8
    ```

## Verified
- Server health: `{"status": "ok"}` at /health
- Real Opus 4.8 responses (Indonesian, multi-turn, system messages)
- Both `aerolink/claude-opus-4-8` and bare `claude-opus-4-8` model names work
- PM2 restart-loops on crash (autorestart, max 50)

## How User Activates
- **/new** in Telegram → next session loads with Opus 4.8 as default
- This session still uses M3 (can't swap mid-flight)
- After 1 day (2026-06-16), revert with:
  ```bash
  hermes config set model.default "tokenrouter/MiniMax-M3"
  hermes config set model.provider "9router"
  pm2 delete aerolink-openai
  ```

## Pitfalls Found
- **Address already in use** — old background processes (from `terminal background=true`) hold the port. Must `pkill -9 -f` them before PM2 can bind.
- **9Router doesn't support anthropic native** — that's why we need this local proxy. Local proxy translates OpenAI → Anthropic.
- **Aerolink OpenAI-format endpoint is broken** — server returns malformed "hiService Unavailable". This proxy bypasses that by calling Anthropic native directly.

## Next Steps
1. /new to activate
2. Watch Aerolink credit usage via Aerolink dashboard (login required)
3. If credit runs out: swap to next Aerolink account or fall back to Zyloo Opus 4.6
4. After 1 day, revert config (see above)

## Backup Plan
If `m` shortcut or local proxy fails, can still use:
- `m "task"` — direct call to `~/bin/m` (Aerolink direct)
- Or switch to 9Router Zyloo Opus 4.6 (already configured)
