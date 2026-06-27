# Split Model Strategy: DM vs Group

## Problem
MiMo credits running low. User wants MiMo quality for DM (main chat with Mona) but free models for group chats (high volume, less critical).

## Solution: Global Default + Per-Session Override

### Setup Steps
```bash
# 1. Set global default to OpenRouter free (groups use this automatically)
hermes config set model.default "openrouter/owl-alpha"
hermes config set model.provider "openrouter"

# 2. Restart gateway
hermes gateway restart

# 3. In DM chat, user types: /model mimo-v2.5-pro
# This persists to session DB and survives restarts
```

### How It Works
- `model.default` in config.yaml = global default for ALL new sessions
- `/model <name>` in a chat = per-session override, persisted to SQLite `sessions` table (`model` column)
- Session override survives gateway restarts (loaded from DB on session resume)
- Group sessions use the free default automatically
- DM session gets MiMo via `/model` override

### Verification
```bash
# Check agent log for correct provider routing
grep "provider=" ~/.hermes/logs/agent.log | tail -5
# Should show: provider=custom:mimo base_url=https://token-plan-sgp.xiaomimimo.com/v1

# Check request dumps
python3 -c "
import json, glob
files = sorted(glob.glob('/home/ubuntu/.hermes/sessions/request_dump_*.json'))
with open(files[-1]) as f:
    data = json.load(f)
    req = data.get('request', {})
    body = req.get('body', {})
    if isinstance(body, str): body = json.loads(body)
    print('Model:', body.get('model'))
    print('URL:', req.get('url'))
"
# URL should be api.xiaomimimo.com, NOT openrouter.ai
```

## Pitfalls
1. **Per-session, not per-chat-type** — `/model` override is per-SESSION. If user starts new session (`/new` or `/reset`), override is lost. Must run `/model` again.
2. **Format matters** — Use just the model name (`mimo-v2.5-pro`), NOT `custom:mimo/mimo-v2.5-pro` for the `/model` command. The `custom:` prefix is only for config.yaml `model.default`.
3. **Restart required** — After changing `model.default` in config, gateway must be restarted for changes to take effect.
4. **Don't forget model.provider** — Set BOTH `model.default` AND `model.provider` when changing the global default. Without `model.provider`, requests may route to OpenRouter even with `custom:` prefix.
5. **API key type matters** — Token Plan SGP key (`tp-...`) works for `mimo-v2.5-pro` on `token-plan-sgp.xiaomimimo.com`. Does NOT work for `mimo-v2.5-pro-ultraspeed` (needs platform API key from `platform.xiaomimimo.com`).
6. **MiMo UltraSpeed API key** — Format: `sk-...` from platform.xiaomimimo.com Console. Token Plan key (`tp-...`) returns 401 on UltraSpeed endpoint.

## Confirmed Working Config (June 10, 2026)
```yaml
# config.yaml
model:
  default: openrouter/owl-alpha  # groups
  provider: openrouter

# custom_providers (MiMo for DM override)
- name: mimo
  api_key: tp-sl1ai8...  # Token Plan SGP key (updated Jun 10)
  base_url: https://token-plan-sgp.xiaomimimo.com/v1
  model: mimo-v2.5-pro
  api_mode: chat_completions
```
DM override: `/model mimo-v2.5-pro` (in DM chat, persists to DB)
Gateway log confirmation: `provider=custom:mimo base_url=https://token-plan-sgp.xiaomimimo.com/v1 model=mimo-v2.5-pro`

## 9Router Status
✅ REMOVED (June 10, 2026). Service stopped + disabled. Replaced by Hermes fallback_providers:
```yaml
fallback_providers: '["mimo", "groq", "nemotron-super"]'
```
This gives automatic failover: MiMo → Groq → OpenRouter free, without 9Router service.

## Groq Provider Added (June 10, 2026)
```yaml
- name: groq
  base_url: https://api.groq.com/openai/v1
  model: llama-3.3-70b-versatile
  api_mode: chat_completions
  api_key: (GROQ_API_KEY in .env)
```
Replaces 9Router's Groq routing. Direct to Groq API, no intermediary.

## User Context (June 10, 2026)
- User said "untuk grup semua topic jangan pake mimo credit ku mau habis"
- User wants MiMo API key specifically for Mona in DM only
- Groups should use OpenRouter free tier to preserve credits
- User also considering removing 9router (Hermes fallback_providers can replace it)

## Model Selection Notes (June 10, 2026)
- `openrouter/owl-alpha` — MiMo-based model on OpenRouter, good quality, free
- `nvidia/nemotron-3-super-120b-a12b:free` — 120B, reliable, fast (~0.8s)
- `xiaomi/mimo-v2.5:free` — MiMo on OpenRouter (NOT the same as custom:mimo direct)
- User prefers `openrouter/owl-alpha` for groups (tested, works well)
- All OpenRouter models share the same API key — rate limit on one may affect others
