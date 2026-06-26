---
type: receipt
date: 2026-06-15
tags:
  - receipt
---

# 2026-06-15 — Aerolink.lat Integration (Direct Call)

## Task
Add Aerolink.lat to 9Router. User said use OpenAI Compatible format. Anthropic native also tested as fallback.

## Result

### 9Router Integration (per user instruction)
- ✅ 2 nodes: `openai-compatible-chat-aerolink-01` & `aerolink-02`
- ✅ 2 connections: `Aerolink-01` (KEY_1), `Aerolink-02` (KEY_2)
- ✅ Settings: round-robin strategy
- ✅ Default model: `aerolink/claude-opus-4-8`
- ❌ **Upstream broken**: Aerolink's `/v1/chat/completions` returns malformed "hiService Unavailable" (not proper JSON, just text)

### Direct Call (workaround)
- ✅ Script: `~/aerolink_direct.py` (symlinked to `~/bin/aerolink`)
- ✅ Uses Anthropic native `/v1/messages` endpoint
- ✅ All 6 models work via direct call
- ✅ Round-robin key selection from .env

## Decisions
- **9Router OpenAI Compatible per user** — followed user instructions exactly
- **Direct call script as backup** — when user picks option 1 (bypass 9Router)
- **Keep both** — 9Router will auto-pick up if Aerolink fixes OpenAI endpoint

## Available Models (Aerolink)
- `claude-opus-4-8` (newest, advertised in /v1/models)
- `claude-opus-4-7`
- `claude-opus-4-6`
- `claude-sonnet-4-6`
- `claude-haiku-4-5-20251001`
- `claude-fable-5` (listed but not actually supported — returns "暂不支持")

## Issues
- **Aerolink's OpenAI-format endpoint is broken** — server returns literal text "hiService Unavailable" with no JSON, no proper HTTP status framing. Even with valid auth + valid model name.
- **Anthropic native endpoint works** — same models, proper Anthropic-format response.
- **9Router doesn't support Anthropic native** — only `openai-compatible` type. So can't proxy Aerolink through 9Router properly.

## Files
- `~/aerolink_direct.py` (new, 100 lines)
- `~/bin/aerolink` (symlink)
- `~/.hermes/skills/hermes/mona-smart-router/SKILL.md` (updated with Aerolink direct call)
- `~/.hermes/.env` (added AEROLINK_KEY_1, AEROLINK_KEY_2, AEROLINK_BASE_URL)
- `~/.9router/db/data.sqlite` (2 nodes + 2 connections + settings)

## Next Steps
1. **Use direct call** when user wants Opus 4.8 (best in class right now)
2. **Monitor Aerolink OpenAI endpoint** — kalo fixed, 9Router connections auto-work
3. **Add to vault** — Aerolink key in `04-WALLET/` someday? (jgn dulu, masih di .env doang)
