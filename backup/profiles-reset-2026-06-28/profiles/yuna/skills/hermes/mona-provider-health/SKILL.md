---
name: mona-provider-health
description: "Monitor dan optimize Mona provider stack — MiMo primary, GeneralCompute backup (fastest!), OpenRouter free tier (5 providers). Health checks, latency benchmarks, provider testing."
when_to_use:
  - User tanya status provider Mona
  - Mau check provider health
  - Mau optimize cost atau latency
  - Mau setup monitoring cron
version: 1.0.0
---

# Mona Provider Health

Comprehensive monitoring untuk Mona provider stack.

## Provider Stack (Updated Status — June 11, 2026 16:10 UTC)

**CRITICAL INCIDENT — Kimchi Credit Exhausted:**
- All Kimchi models (minimax-m2.7, minimax-m2.5) → **402 Payment Required**
- Root cause: $50/month free credit limit reached
- Detection: Manual testing after user complained "enak mana sama kimchi"
- Impact: Primary chat model (kimchi/minimax-m2.7 via 9Router) completely dead
- Kiro OAuth tokens expired in 9Router (both Account 1 & 2 at 15:03 & 16:59)
- MiMo Omni returns empty content (bug or API change)
- **ONLY TokenRouter/MiniMax-M3 working** (1/6 providers functional)

```
Primary: TokenRouter MiniMax-M3 (via 9Router, FREE — only working provider)
Was Primary: Kimchi minimax-m2.7 (via 9Router) — ❌ 402 CREDIT EXHAUSTED
Vision:  MiMo Omni (mimo-v2-omni) — ⚠️ responds but content empty
Backup:  Groq llama-3.3-70b-versatile (fast, free)
Kiro: ❌ OAuth expired (both accounts)

9Router Hub (localhost:20128):
  - Kiro AI: 2 accounts, Round Robin ON (free Claude!)
  - Xiaomi MiMo: 1 account
  - Kimchi.dev: 1 account ($50/mo free: kimi-k2.5, minimax-m2.5, etc.)
  - 459 built-in free models

Fallback chain: mimo → groq → nemotron-super

NOTE: All agents (Mona, Meridian, Charon) route through 9Router as central LLM hub.

Config cleanup (June 10, 2026):
  - Removed: generalcompute, nemotron-ultra, gemma4 (unused providers)
  - Removed: custom_api_key, custom_base_url, model.base_url (legacy fields)
  - Removed: 10 unused personalities (kept: helpful, concise, creative, teacher)
  - Backup: ~/.hermes/config.yaml.backup.20260610_062805

OpenRouter Free Tier (shared OPENROUTER_API_KEY):
  ✅ nemotron-super  — nvidia/nemotron-3-super-120b-a12b:free (~0.8s, reliable)
  ✅ owl-alpha       — openrouter/owl-alpha (current group default, MiMo-based)

Groq (direct, via api.groq.com):
  ✅ llama-3.3-70b-versatile — fast, free, good quality

REMOVED (Jun 10, 2026):
  ❌ generalcompute — removed from config (unused, not in fallback chain)
  ❌ nemotron-ultra — removed from config (unused, 550B too slow)
  ❌ gemma4 — removed from config (unused)

RE-ENABLED (Jun 11, 2026):
  ✅ 9Router — back in service as central LLM hub (Kiro + MiMo + Kimchi + 459 free models)

NOT WORKING (Jun 10, 2026):
  ❌ MiMo UltraSpeed — all keys tried return 401/402. Needs platform API key from platform.xiaomimimo.com Console. Token Plan SGP key does NOT work for UltraSpeed. Endpoint `token-plan-sgp.xiaomimimo.com` returns 400 "Not supported model mimo-v2.5-pro-ultraspeed".

REMOVED (Jun 7-8, 2026):
  ❌ qwen3-coder — 429 rate limited (480B too popular on free tier)
  ❌ hermes-405b — 429 rate limited
  ❌ GEMINI_API_KEY — was placeholder "***" (3 chars), removed from .env
```

## MiMo UltraSpeed (ACTIVE — Beta Access Granted June 10, 2026)
- **Announcement:** Xiaomi MiMo-V2.5-Pro UltraSpeed × TileRT joint release
- **Speed:** 1,000+ tokens/s on 1T parameter MoE model
- **Hardware:** Standard 8-GPU node (no specialized accelerators like Cerebras/Groq)
- **Pricing:** 3x normal price for ~10x speed boost. Free chat experience (limited time).
- **Model ID:** `mimo-v2.5-pro-ultraspeed`
- **Status:** ✅ Beta access ACTIVE (confirmed via email June 10, 2026)
- **Web UI:** https://ultraspeed.xiaomimimo.com
- **API Docs:** https://platform.xiaomimimo.com/docs/en-US/model-intro/mimo-v2.5-pro-ultraspeed

**CRITICAL — Endpoint Mismatch:**
- Token Plan SGP (`token-plan-sgp.xiaomimimo.com/v1`) does NOT support UltraSpeed → returns `400: Not supported model mimo-v2.5-pro-ultraspeed`
- Platform API (`api.xiaomimimo.com`) returns 401 "Invalid API Key" with Token Plan key
- UltraSpeed needs a **platform API key** from Console, NOT the Token Plan key
- **All keys tried (June 10, 2026):** Both Token Plan key and new key `sk-s924...` return 401/402
- **User action needed:** Login to https://platform.xiaomimimo.com → Console → check if UltraSpeed API access is enabled for your account
- **Workaround:** Use `mimo-v2.5-pro` (Token Plan SGP) — works reliably, ~2.9s latency

**Model ID vs Endpoint Matrix:**
| Model ID | Endpoint | Status |
|----------|----------|--------|
| `mimo-v2.5-pro` | `token-plan-sgp.xiaomimimo.com/v1` | ✅ Works |
| `mimo-v2.5-pro-ultraspeed` | `token-plan-sgp.xiaomimimo.com/v1` | ❌ 400 Not supported |
| `mimo-v2.5-pro-ultraspeed` | `api.xiaomimimo.com/v1` | ⚠️ Needs platform API key |

**Setup needed:** Once user provides platform API key + correct base URL, add as new custom provider in config.yaml:
```yaml
- api_key: PLATFORM_KEY_HERE
  api_mode: chat_completions
  base_url: https://api.xiaomimimo.com/v1  # or correct endpoint
  model: mimo-v2.5-pro-ultraspeed
  name: mimo
```
Then set default: `hermes config set model.default "custom:mimo/mimo-v2.5-pro-ultraspeed"`
**CRITICAL:** Must use `custom:mimo/` prefix, NOT bare `mimo/` — see Custom Provider Routing Format pitfall below.

**VISION PROVIDER (Updated June 2026):**
- Primary vision: `mimo-v2-omni` via Xiaomi MiMo API (unlimited, free)
- Fallback vision: `gemini-2.5-flash` (free tier, quota-limited)
- Config path: `auxiliary.vision.provider` + `auxiliary.vision.model` in config.yaml
- MiMo Omni key: `custom_api_key` env var (same key as text models)
- MiMo Omni base URL: `https://token-plan-sgp.xiaomimimo.com/v1`

**CRITICAL**: Gemini key is RESTRICTED to `auxiliary.vision` and `auxiliary.image_gen` only. User explicitly said "apikey nya khusus buat scan gambar dan generate gambar aja ya bisa ? jangan di pake ke hal lain". NEVER route regular chat/coding/other tasks through Gemini.

## Benchmark Results (June 10, 2026 — Live Test)
| Provider | Model | Latency | tok/s | Status |
|----------|-------|---------|-------|--------|
| MiMo v2.5-pro | mimo-v2.5-pro | 1.0-5.7s | 25.7 | ✅ Active (primary) |
| Groq | llama-3.3-70b-versatile | Fast | N/A | ✅ Active (fallback 1) |
| Nemotron-Super | nemotron-3-super-120b:free | 0.8s | N/A | ✅ Active (groups default) |

## Quick Health Check
```bash
# Test ALL providers at once (Python — recommended)
python3 << 'PYEOF'
import json, urllib.request, socket, time, yaml
from dotenv import dotenv_values
socket.setdefaulttimeout(15)
with open('/home/ubuntu/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
env = dotenv_values('/home/ubuntu/.hermes/.env')
for p in cfg.get('custom_providers', []):
    name, model, url, key = p['name'], p['model'], p['base_url'].rstrip('/'), p['api_key']
    data = json.dumps({"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 3}).encode()
    req = urllib.request.Request(f"{url}/chat/completions", data=data, headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    start = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=12)
        print(f"✅ {name:20s} | {time.time()-start:5.1f}s | {model}")
    except urllib.error.HTTPError as e:
        print(f"❌ {name:20s} | HTTP {e.code} ({time.time()-start:.1f}s)")
    except Exception as e:
        print(f"❌ {name:20s} | {type(e).__name__} ({time.time()-start:.1f}s)")
    time.sleep(1)
PYEOF

# 9Router status
curl -s http://localhost:20128/v1/models | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Models: {len(d.get(\"data\",[]))}')"
```

## Provider Details

### MiMo (Primary)
- **Base URL:** https://token-plan-sgp.xiaomimimo.com/v1
- **Model:** mimo-v2.5-pro (lowercase! NOT MiMo-V2.5-Pro)
- **API Key:** tp-sl1ai8juglke9devy14lkp3xyd8nint3z87y7lssr3113fxo (Token Plan SGP)
- **Latency:** ~1.0-5.7s (varies, cache helps — 99-100% hit rate)
- **Cost:** User's credit (free)
- **Status:** Active

### Groq (Fallback 1 — Added June 10, 2026)
- **Base URL:** https://api.groq.com/openai/v1
- **Model:** llama-3.3-70b-versatile
- **API Key:** GROQ_API_KEY in .env
- **Latency:** Fast (free tier)
- **Cost:** Free
- **Status:** ✅ Active
- **Added:** Replaced 9Router's Groq routing. Direct provider, no intermediary.

### 9Router ✅ ACTIVE (Re-enabled June 11, 2026)
- **Status:** ✅ RUNNING — re-enabled with Kiro AI (2 accounts), MiMo, Kimchi.dev
- **Port:** 20128
- **Service:** systemd (`sudo systemctl restart 9router`), NOT PM2
- **Providers connected:**
  - Kiro AI: 2 accounts, Round Robin ON (double rate limit)
  - Xiaomi MiMo: 1 account (token-plan-sgp)
  - Kimchi.dev: multiple accounts ($50/mo free credits each) — custom OpenAI-compatible
  - 459 built-in free models (DeepSeek V4, Gemini 3 Flash, Claude Sonnet 4.6, etc.)
- **Hermes config:** `custom_provider_base_url: http://localhost:20128/v1`
- **Dashboard:** Cloudflare tunnel URL (changes on restart), password: 123456
- **Was:** Stopped June 10 to save API keys; re-enabled June 11 with expanded providers
- **Service management:** `sudo systemctl restart 9router` (systemd, NOT pm2!)
- **All agents route through 9Router:** Mona, Meridian (Dino Cantik), Charon

**CRITICAL:** 9Router runs as a **systemd service** (`9router.service`), NOT PM2. Commands:
```bash
sudo systemctl restart 9router   # restart
sudo systemctl status 9router    # check status
pgrep -a 9router                 # check process
```

**9Router Dashboard API (for automation):**
- Login: `POST /api/auth/login` with `{"password":"123456"}` → returns auth cookie
- List providers: `GET /api/providers` (needs auth cookie)
- List nodes: `GET /api/provider-nodes` (needs auth cookie)
- Create node: `POST /api/provider-nodes` with `{name, prefix, apiType, baseUrl, type}`
- Validate key: `POST /api/providers/validate` with `{provider, apiKey}`
- **Dashboard JS does NOT expose connection save endpoint** — bulk add requires DB insert

**9Router SQLite DB:** `/home/ubuntu/.9router/db/data.sqlite`
- `providerNodes` — provider config (id, name, type, data JSON)
- `providerConnections` — API key connections (id, provider FK, authType, name, priority, data JSON)

**Bulk API Key Insertion (proven working June 2026):**
```python
import sqlite3, uuid, json
from datetime import datetime, timezone

PROV_ID = "<provider-node-id>"  # get from: sqlite3 db "SELECT id FROM providerNodes WHERE name='Kimchi'"
API_KEY = "castai_v1_..."
DB_PATH = "/home/ubuntu/.9router/db/data.sqlite"

conn_id = str(uuid.uuid4())
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
data = json.dumps({
    "apiKey": API_KEY, "testStatus": "active",
    "providerSpecificData": {"connectionProxyEnabled": False, "connectionProxyUrl": "", "connectionNoProxy": ""},
    "lastError": None, "lastErrorAt": None
})
db = sqlite3.connect(DB_PATH)
db.execute(
    "INSERT INTO providerConnections (id,provider,authType,name,priority,isActive,data,createdAt,updatedAt) VALUES (?,'"+PROV_ID+"','apikey','Name',1,1,?,?,?)",
    (conn_id, data, now, now))
db.commit()
db.close()
# Then: sudo systemctl restart 9router
```
- Full script: `scripts/kimchi_bulk_add.py`

**Provider node prefix pitfall:** The `prefix` field in provider node data MUST be a single word (e.g. `kimchi`), NOT model names. Wrong prefix like `"kimi-k2.6 minimax-m2.7"` causes "Missing base URL" errors. Model ID format is `{prefix}/{model}` (e.g. `kimchi/kimi-k2.5`).

### MiMo Omni (Vision — Primary)
- **Provider:** custom
- **Model:** mimo-v2-omni (lowercase! NOT mimo-v2-omni)
- **Base URL:** https://token-plan-sgp.xiaomimimo.com/v1
- **API Key:** `custom_api_key` env var (same as MiMo text)
- **Latency:** ~5-10s for vision tasks
- **Cost:** Free (user's credit)
- **Status:** Active ✅
- **Capabilities:** Image analysis, color detection, OCR, scene description
- **Limitation:** URL-based images return 400 — MUST use base64 encoding
- **Test:** `python3 -c "import urllib.request,json,base64,os; key=os.environ['custom_api_key']; ..."` (see scripts/)

### Gemini (Auxiliary — Vision Fallback) ⚠️ KEY BROKEN
- **Provider:** gemini
- **Model:** gemini-2.5-flash (updated from gemini-2.0-flash)
- **Config path:** `auxiliary.vision.provider` + `auxiliary.image_gen.provider` in config.yaml
- **Env var:** `GEMINI_API_KEY` in `~/.hermes/.env`
- **Vault backup:** `~/mona-workspace/vault/.gemini_key.txt` (chmod 600)
- **Cost:** Free tier (Google AI Studio) — **15 RPM, 1500 RPD limit**
- **Status:** ❌ KEY IS PLACEHOLDER (3 chars "***") — needs real key from https://aistudio.google.com/apikey
- **PITFALL:** gemini-2.0-flash free tier quota = 0 when exhausted. Switch to gemini-2.5-flash (different quota pool).
- **PITFALL:** gemini-1.5-flash/pro return 404 (deprecated/removed from API).
- **RESTRICTION:** Vision + image gen ONLY. Not for chat, coding, fallback, or any other task.
- **Setup:** `hermes config set auxiliary.vision.provider gemini` + `hermes config set auxiliary.vision.model gemini-2.5-flash`

### OpenRouter Free Tier Providers
All use the same `OPENROUTER_API_KEY` from `.env` (73 chars, `sk-or-v1-...`).
Config: `~/.hermes/config.yaml` under `custom_providers:`.
Base URL: `https://openrouter.ai/api/v1`

| Name | Model | Speed | Best For |
|------|-------|-------|----------|
| nemotron-ultra | nvidia/nemotron-3-ultra-550b-a55b:free | ~5.7s | Heavy reasoning (550B) |
| nemotron-super | nvidia/nemotron-3-super-120b-a12b:free | ~0.8s | Fast general (120B) |
| gemma4 | google/gemma-4-31b-it:free | ~1.6s | Multimodal, fastest (44.7 tok/s) |
| qwen3-coder | qwen/qwen3-coder:free | — | Coding (480B, often rate limited) |
| hermes-405b | nousresearch/hermes-3-llama-3.1-405b:free | — | Agentic/tool-use (often rate limited) |

**PITFALL:** OpenRouter free tier models with 400B+ params (Qwen3-Coder, Hermes-405B) are frequently 429 rate limited due to high demand. Don't rely on them as primary. Use Nemotron-Super or Gemma-4 as reliable backups.
**PITFALL:** All 5 share the same API key — rate limit on one may indicate key-level throttling.
**PITFALL:** `yaml.dump()` can truncate API keys in config.yaml. Known case: key was 73 chars but after yaml.dump it became 13 chars (`sk-or-...f4f6`). Always verify key length after config changes: `python3 -c "import yaml; cfg=yaml.safe_load(open('config.yaml')); print([len(p['api_key']) for p in cfg['custom_providers']])"`.
**PITFALL:** Hermes secret redaction truncates API keys written through `write_file` or terminal heredocs. A 35-char key like `gc_lBNmLaEofJ2mW57pVFE64Ke25AHsQZ1o` becomes `gc_lBN...QZ1o` (13 chars). This causes silent 401 errors that are hard to debug. **Workaround**: Use Python scripts that read full keys from `~/.hermes/config.yaml` at runtime and write them to target files. Always verify key byte-lengths after writing: `python3 -c "print(len(open('.env').read().split('KEY=')[1].split('\n')[0]))"`.
**PITFALL:** Default model in config.yaml must be updated when changing primary provider. Set both `model.default` AND `model.provider` to match.

**CRITICAL PITFALL — Cron Jobs + Custom Providers (June 10, 2026):**
Cron jobs with `no_agent: false` (AI agent-driven) do NOT automatically inherit the custom provider routing. They inherit the model NAME from the default config but route through **OpenRouter** as the provider. This causes: `HTTP 400: mimo/mimo-v2.5-pro is not a valid model ID` — because MiMo is a custom endpoint, not an OpenRouter model.

**Symptom:** Cron job `last_status: "error"`, errors.log shows `BadRequestError` with `provider=openrouter base_url=https://openrouter.ai/api/v1 model=mimo/mimo-v2.5-pro`

**FIX:** For every cron job with `no_agent: false`, explicitly set the model override:
```python
cronjob(action='update', job_id='...', model={'model': 'mimo-v2.5-pro', 'provider': 'custom:mimo'})
```

**Detection:** When diagnosing cron failures, check `errors.log` for the `provider=` field in the error line. If it says `provider=openrouter` but the model is a custom one (like `mimo-v2.5-pro`), this is the root cause.

**Prevention:** When creating new cron jobs that use AI agents, ALWAYS specify `model` and `provider` explicitly. Do not rely on default inheritance for custom providers.

**Quick fix pattern — batch update all cron jobs:**
```python
# List all jobs, then update each one
cronjob(action='list')
cronjob(action='update', job_id='JOB_ID_1', model={'model': 'mimo-v2.5-pro', 'provider': 'custom:mimo'})
cronjob(action='update', job_id='JOB_ID_2', model={'model': 'mimo-v2.5-pro', 'provider': 'custom:mimo'})
```
Always verify with `cronjob(action='list')` after updates — check `last_status` field for errors.

**CRITICAL PITFALL — Cron Job Model ID Must Match Provider Endpoint (June 10, 2026):**
Cron jobs using `mimo-v2.5-pro-ultraspeed` as model ID will FAIL with `400: Not supported model mimo-v2.5-pro-ultraspeed` when routed to `token-plan-sgp.xiaomimimo.com/v1`. UltraSpeed is ONLY available via `api.xiaomimimo.com` (platform API), NOT the Token Plan SGP endpoint.

**Symptom:** Cron job error: `RuntimeError: Error code: 400 - {'error': {'code': '400', 'message': 'Not supported model mimo-v2.5-pro-ultraspeed', 'param': 'Param Incorrect'}}`

**FIX:** Update all cron jobs to use `mimo-v2.5-pro` (not `mimo-v2.5-pro-ultraspeed`):
```python
cronjob(action='update', job_id='...', model={'model': 'mimo-v2.5-pro', 'provider': 'custom:mimo'})
```

**Model ID vs Endpoint Matrix:**
| Model ID | Endpoint | Status |
|----------|----------|--------|
| `mimo-v2.5-pro` | `token-plan-sgp.xiaomimimo.com/v1` | ✅ Works |
| `mimo-v2.5-pro-ultraspeed` | `token-plan-sgp.xiaomimimo.com/v1` | ❌ 400 Not supported |
| `mimo-v2.5-pro-ultraspeed` | `api.xiaomimimo.com/v1` | ⚠️ Needs platform API key (not Token Plan key) |

**Rule:** Always verify which endpoint a model ID is supported on before setting it in cron jobs.
**CRITICAL PITFALL:** NEVER change the default model without explicit user permission. Incident (June 2026): During testing, the default model was switched from MiMo to Nemotron Ultra and not reverted. User complained about extreme slowness (150s+ response time). Always revert config changes after testing. MiMo v2.5-pro is the PRIMARY DEFAULT and must stay that way unless user explicitly requests a change.

**CRITICAL PITFALL (June 10, 2026):** OpenRouter `qwen/qwen3-coder:free` was added back to config as `model.default` without user knowledge. User complained Mona was "lemot" and "muter-mulu" (slow/thinking too long). Root cause: qwen3-coder free tier frequently hits 429 rate limits. **FIX:** Immediately revert `model.default` to `mimo-v2.5-pro` using `hermes config set model.default mimo-v2.5-pro`. User explicitly said "konsisten" — do NOT change models without explicit user request. MiMo v2.5-pro stays as primary DEFAULT permanently unless user says otherwise.

**CRITICAL PITFALL — Custom Provider Routing Format (June 10, 2026):**
When `model.default` uses format `mimo/mimo-v2.5-pro-ultraspeed`, Hermes interprets `mimo` as an OpenRouter model prefix (format: `provider/model`), so ALL requests route to `https://openrouter.ai/api/v1/chat/completions` instead of the custom MiMo endpoint.

**Symptom:** Request dumps show correct model name but wrong URL (`openrouter.ai` instead of `api.xiaomimimo.com`). User notices no difference in behavior but API calls go to wrong provider.

**Root cause:** Hermes routing logic:
- `provider/model` → OpenRouter (treated as OpenRouter model ID)
- `custom:provider/model` → Custom provider (routes to `custom_providers[].base_url`)

**FIX:**
```bash
hermes config set model.default "custom:mimo/mimo-v2.5-pro-ultraspeed"
```

**Verification:** Check request dumps to confirm correct routing:
```bash
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
```
URL should be the custom provider base_url, NOT `openrouter.ai`.

**CRITICAL PITFALL (June 10, 2026):** `model.default` alone is NOT enough. Must also set `model.provider` for custom providers.

**Incident:** Set `model.default: custom:mimo/mimo-v2.5-pro-ultraspeed` but requests still routed to OpenRouter. Root cause: without `model.provider`, Hermes falls back to OpenRouter as the provider regardless of the `custom:` prefix.

**FIX — always set BOTH:**
```bash
hermes config set model.default "custom:mimo/mimo-v2.5-pro-ultraspeed"
hermes config set model.provider "mimo"
```

**Verification:** Check gateway logs for correct routing:
```bash
grep "provider=custom:mimo" ~/.hermes/logs/agent.log | tail -5
# Should show: provider=custom:mimo base_url=https://...xiaomimimo.com/v1
```

**Also applies to cron jobs:** Cron jobs with `no_agent: false` need explicit model override with `provider: 'custom:mimo'` (see cron pitfall above).

**CRITICAL PITFALL — API Key Security (June 10, 2026):**
User sent Groq API key directly in Telegram chat. Keys in chat history are visible and can be leaked. ALWAYS:
1. Redirect user to paste key in Termius terminal directly: `echo 'GROQ_API_KEY=sk-...' >> ~/.hermes/.env`
2. If key is already in chat, immediately add to .env and warn user to rotate if concerned
3. NEVER echo API keys back in responses — use `***` redaction

**CRITICAL PITFALL — `/model` Command Format vs Config Format:**
- `/model mimo-v2.5-pro` → CORRECT (bare model name for session override)
- `/model custom:mimo/mimo-v2.5-pro` → MAY NOT WORK (session override expects bare name)
- `model.default: custom:mimo/mimo-v2.5-pro` → CORRECT (config.yaml format with provider prefix)
- `model.default: mimo-v2.5-pro` → WRONG for config (routes to OpenRouter without provider hint)

**Rule:** Config.yaml needs `custom:provider/model` format. `/model` command needs bare model name.

**CRITICAL PITFALL:** NEVER change the default model without explicit user permission.

**USER FRUSTRATION SIGNALS:** When user says "masih muter-mutu", "gak kayak kemarin", "kenapa lemot?", "setiap hari minta maaf?" — these are HIGH PRIORITY signals. Do NOT give lengthy explanations. Diagnose → Fix → Report result. User wants execution, not apologies.

**USER STYLE: "udah" = STOP EXPLAINING.** When user says "udah", "udah lah", "udah astaga" — they are frustrated with repeated explanations. STOP explaining immediately. Just execute the fix and report the result in 1-2 lines. No bullet points, no tables, no "kemungkinan" lists. User values "nurut" (obedience) — when they say stop, you stop.

### Kimchi.dev (Custom OpenAI-Compatible)
- **Base URL:** https://llm.kimchi.dev/openai/v1
- **Auth:** API key format `castai_v1_...`
- **Credits:** $50/month free per account
- **Route via 9Router:** `kimchi/{model}`
- **Working model:** `kimchi/kimi-k2.5` ✅
- **Available models:** kimi-k2.5, kimi-k2.6, minimax-m2.5, minimax-m2.7, qwen3-coder-next-fp8, nemotron-3-super-fp4, smollm2-360m, smollm2-135m
- **Bulk add script:** `scripts/kimchi_bulk_add.py` (edit API_KEYS list, run)
- **Setup:** Add provider node via dashboard UI, then bulk-insert keys via script or dashboard
- **Dashboard:** Providers → Kimchi → Add API Key → Check → Save
- **Model list endpoint:** `GET /openai/v1/models` (with Bearer auth)

### GeneralCompute ✅ ACTIVE (as of June 7, 2026)
- **Base URL:** https://api.generalcompute.com/v1
- **Model:** minimax-m2.7
- **Key:** gc_lBNmLaEofJ2mW57pV...5AHsQZ1o (35 char, in .env as GC_API_KEY)
- **Latency:** ~0.5s (FASTEST provider!)
- **Status:** ✅ ACTIVE — previously thought dead (403) but confirmed working
- **Note:** Only 1 of the 3 original keys tested. Others may still be dead.

### Blueminds (SAVED — NOT ACTIVE ⏳)
- **Base URL:** https://api.bluesminds.com/v1
- **Key:** BLUEMINDS_API_KEY in .env (51 chars, sk-...PuGe)
- **Models listed:** 40+ (minimax-40-m4, deepseek-v4-flash, qwen-30-4k, zhipu-glm-4.7, moonshot-v1-8k, etc.)
- **Status:** ⏳ SAVED but NO models working — all return "No available channel for model X under group default (distributor)"
- **Auth:** ✅ Valid (returns proper error, not 401)
- **Action:** Keep key saved. Re-test periodically. Do NOT add to config until at least one model responds.
- **Added:** June 8, 2026

### Pioneer (DEAD ❌)
- **Base URL:** https://api.pioneer.ai/v1
- **Status:** ❌ DEAD — API returns 403 Forbidden
- **Key:** pio_sk_19... (invalid)
- **Action:** Remove from provider stack config

### Groq via 9Router (DEAD ❌)
- **Status:** ❌ All models return 401 Invalid API Key
- **Action:** Need fresh Groq API key from groq.com, or remove from 9Router

## Auto-Recovery
- MiMo: Xiaomi API — stable, no auto-recovery needed
- Gemini: Free tier quota resets every 24h — just wait if exhausted
- 9Router: systemd service auto-restart on failure (but models need valid keys)

## Cost Optimization
- **MiMo:** Free (Token Plan SGP) — use for daily tasks
- **GeneralCompute:** Free (minimax-m2.7) — use for fast responses (0.5s!)
- **Gemma-4:** Free via OpenRouter — use for multimodal or when MiMo is slow
- **Nemotron-Super:** Free via OpenRouter — reliable fast backup
- **MiMo UltraSpeed:** 3x price for ~10x speed — apply by June 23, 2026

## Cost-Saving: Split Model Strategy (DM vs Group)

When MiMo credits are low, split by chat type: free default for groups, MiMo override for DM.

**Setup:** Set global default to OpenRouter free, then `/model mimo-v2.5-pro-ultraspeed` in DM chat. Session override persists to DB, survives restarts.

**Full guide:** `references/split-model-strategy.md`

## Monitoring Scripts
- `~/mona-workspace/scripts/mona-dashboard.sh` — Full dashboard with all services
- `~/mona-workspace/scripts/mona-provider-monitor.sh` — Full health check
- `~/mona-workspace/scripts/mona-status.sh` — Quick status
- `~/mona-workspace/scripts/mona-startup.sh` — Auto-start all services

## Testing New Provider Workflow

When user gives a new API provider + key:

1. **Save key first** — write to `~/.hermes/.env` immediately
2. **Test auth** — `curl /v1/models` or simple prompt. If auth fails (401), key is wrong
3. **Test 3-5 models** — use simple prompt ("Say OK"), check for "No available channel" or similar
4. **Report honestly** — if no models work, tell user. Don't pretend
5. **Save for later** — keep key in .env even if dead. User may want to re-test later
6. **Never switch primary** — unless user explicitly says so

**PITFALL:** System auto-redacts ALL API keys in chat to `***`. Keys sent via Telegram/chat get truncated. Solution: user must paste the `echo 'KEY=...' >> .env` command directly in Termius. Ask for "command sekali jalan" (one consolidated command block) — user prefers this over multi-step instructions.

**PITFALL:** Some providers (e.g. Blueminds) list many models in `/v1/models` but have NO active backends. Auth works, but every model returns "No available channel". Always test actual inference, not just model listing.

## Troubleshooting

### Cron Job 400 Error: "Not supported model"
**Symptom:** `RuntimeError: Error code: 400 - {'error': {'code': '400', 'message': 'Not supported model mimo-v2.5-pro-ultraspeed', 'param': 'Param Incorrect'}}`
**Cause:** Cron job using `mimo-v2.5-pro-ultraspeed` but endpoint is `token-plan-sgp.xiaomimimo.com` (doesn't support UltraSpeed)
**Fix:** Update cron job to use `mimo-v2.5-pro`:
```python
cronjob(action='update', job_id='JOB_ID', model={'model': 'mimo-v2.5-pro', 'provider': 'custom:mimo'})
```
**Prevention:** Always verify model ID is supported on the target endpoint. See Model ID vs Endpoint Matrix above.

### Cron Job 401/402 Error: Invalid API Key
**Symptom:** `HTTP 401: Invalid API Key` or `HTTP 402: Payment Required`
**Cause:** API key expired, revoked, or wrong key type (e.g., Token Plan key used for platform API)
**Fix:**
1. Check if key is still valid: `curl -s -H "Authorization: Bearer KEY" https://token-plan-sgp.xiaomimimo.com/v1/models`
2. If invalid, get new key from platform.xiaomimimo.com Console
3. Update in `~/.hermes/.env` and restart gateway

### Gemini 429 Quota Exhausted
**Symptom:** `HTTP Error 429: You exceeded your current quota` with `RESOURCE_EXHAUSTED`
**Cause:** Free tier quota for gemini-2.0-flash exhausted (limit: 0)
**Fix:**
1. Switch to gemini-2.5-flash (different quota pool): `sed -i 's/gemini-2.0-flash/gemini-2.5-flash/g' ~/.hermes/config.yaml`
2. Or wait 24h for quota reset
3. Or use MiMo Omni for vision instead (unlimited)
**PITFALL:** gemini-1.5-flash/pro are DEPRECATED — return 404. Always use gemini-2.5-flash or newer.

### MiMo Vision Returns 400
**Symptom:** `HTTP Error 400: Bad Request` when sending image URL to mimo-v2-omni
**Cause:** MiMo Omni does NOT support URL-based images
**Fix:** Always use base64 encoding for images:
```python
import base64
with open('image.png', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()
# Send as: {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}}
```

### MiMo Omni Not Responding
**Symptom:** 502 Bad Gateway or timeout on mimo-v2-omni
**Cause:** MiMo Omni model may be temporarily unavailable
**Fix:** Fall back to Gemini vision (if quota available) or retry after 30s

### MiMo Error
```bash
# Check MiMo status
curl -s -X POST https://token-plan-sgp.xiaomimimo.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer tp-svz...9f" \
  -d '{"model":"mimo-v2.5-pro","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```

### 9Router — Re-enabled (June 11, 2026)
9Router is back in service as central LLM hub. All agents route through it.
**Full auth troubleshooting guide:** `references/9router-auth-troubleshooting.md`
```bash
# Check 9Router status (systemd, NOT pm2!)
sudo systemctl status 9router

# Restart if needed
sudo systemctl restart 9router

# Quick health test
curl -s -X POST http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"kimchi/kimi-k2.5","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'

# Check dashboard (via Cloudflare tunnel)
curl -s http://localhost:20128/api/auth/login -X POST -H "Content-Type: application/json" -d '{"password":"123456"}' -c /tmp/cookies.txt
curl -s -b /tmp/cookies.txt http://localhost:20128/api/providers | python3 -m json.tool
```

### GeneralCompute Test
```bash
# Test active key
python3 -c "
import urllib.request, json
req = urllib.request.Request(
    'https://api.generalcompute.com/v1/chat/completions',
    data=json.dumps({'model':'minimax-m2.7','messages':[{'role':'user','content':'hi'}],'max_tokens':3}).encode(),
    headers={'Content-Type':'application/json','Authorization':'Bearer gc_lBNmLaEofJ2mW57pV5AHsQZ1o'}
)
try:
    resp = urllib.request.urlopen(req, timeout=10)
    print(f'✅ OK: {resp.status}')
except Exception as e:
    print(f'❌ {e}')
"
```

## Auto-Start on Boot
```bash
# 9Router — managed via systemd (NOT pm2)
sudo systemctl status 9router  # check if running
sudo systemctl restart 9router # restart if needed

# PM2 managed services
pm2 list
```

## Twitter/X Access Limitation (June 2026)

**Twitter/X is completely inaccessible from VPS.** All methods fail:
- `web_extract` — backend doesn't support X URLs
- `web_search` — may return 402/payment required
- `browser` — X requires login; VPS IP is blocked by Twitter bot detection
- Nitter instances — blocked (private network) or down

**CRITICAL: Twitter login from VPS is BLOCKED.** When attempting to log in to x.com via browser from VPS IP (43.163.85.51), Twitter shows: *"We've temporarily limited your login. Please try again later."* This is IP-based bot detection — NOT a credential issue. The VPS IP is permanently flagged.

**Workaround:** User must copy-paste tweet content or send screenshots. When user shares an X link, immediately ask for the content rather than trying multiple failed access methods. Do NOT waste tokens on repeated failed attempts.

**Twitter Auth Recovery:** If Twitter credentials (auth_token + ct0) are needed:
1. User must extract cookies from their LOCAL browser (not VPS)
2. Use DevTools → Application → Cookies → x.com → copy `auth_token` and `ct0`
3. Or use "Get cookies.txt LOCALLY" Chrome extension
4. Save to `~/.hermes/vault/.x_auth_token` and `~/.hermes/vault/.x_ct0`
5. Note: These files were found EMPTY in June 2026 — credentials were lost/never properly saved
6. Full extraction guide: `references/twitter-cookie-extraction.md`

## Support Files
- `references/provider-testing-methodology.md` — Safe testing pattern, benchmark template
- `references/gemini-auxiliary-setup.md` — Gemini vision + image gen only config (user-restricted)
- `references/mimo-ultraspeed-june2026.md` — MiMo UltraSpeed specs, pricing, apply process (Jun 2026)
- `references/split-model-strategy.md` — DM vs group cost-saving strategy (Jun 2026)
- `references/9router-replacement-guide.md` — Replace 9Router with Hermes fallback_providers (Jun 2026)
- `scripts/provider-health-check.sh` — Quick health check script
- `scripts/kimchi_bulk_add.py` — Bulk insert Kimchi API keys to 9Router via DB (Jun 2026)
