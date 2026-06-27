# Kimchi.dev Provider Reference (9router-llm-router)

## ⚠️ CRITICAL: Auto-Generated Keys Are INVALID
Keys from Kimchidev.py script are REJECTED by Kimchi.dev (HTTP 401). Bot detection revokes them.
**Only manually-created keys work** — signup from phone browser at app.kimchi.dev.

## ⚠️ Always Test Keys Before Adding
NEVER add a key to 9Router without testing via curl first. Test DIRECT first (no proxy), then via proxy if blocked:
```bash
# Direct (try first — may work if VPS IP not blocked)
curl -s --max-time 10 \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -H "User-Agent: curl/8.5.0" \
  -d '{"model":"minimax-m2.7","messages":[{"role":"user","content":"ok"}],"max_tokens":3}' \
  "https://llm.kimchi.dev/openai/v1/chat/completions"

# Via proxy (only if direct returns 403/1010)
curl -s --proxy http://localhost:8888 --max-time 15 \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  "https://llm.kimchi.dev/openai/v1/chat/completions" \
  -d '{"model":"minimax-m2.7","messages":[{"role":"user","content":"test"}],"max_tokens":5}'
# 200 = works, 401 = invalid key, 403 = IP blocked OR User-Agent blocked

# From Python (MUST set User-Agent):
req = request.Request(url,
    data=json.dumps({...}).encode(),
    headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": "curl/8.5.0"  # REQUIRED
    }
)
```

Dashboard "Test Connection" can be unreliable — use curl as ground truth.

## ⚠️ Ask Permission Before Using External Resources
When using another VPS (e.g., Hye-Jin) as proxy, ALWAYS ask user first.
User correction: "kok gak bilang dulu?" — even if technically possible, ASK FIRST.

## API Details
- **Endpoint:** `https://llm.kimchi.dev/openai/v1`
- **Free Credits:** $50/month per account (reset)
- **Prefix in 9Router:** `kimchi/`
- **Best model:** `minimax-m2.7` (fastest + smartest)
- **Key format:** `castai_v1_<hex>_<hex>` (83 chars)

## Models (Verified Jun 2026 — Tested from Hye-Jin)

### Working Models
| Model | Speed | Status | Notes |
|-------|-------|--------|-------|
| `minimax-m2.7` | ~1.0s | ✅ BEST | Fastest + smartest, main workhorse |
| `minimax-m2.5` | ~2.0s | ✅ | Fast, decent quality |
| `nemotron-3-super-fp4` | ~1.1s | ✅ | Good instruction following, returns content + reasoning |

### Thinking Models (content depends on max_tokens)
| Model | Status | Notes |
|-------|--------|-------|
| `kimi-k2.5` | ⚠️ | Thinking model — see note below |
| `kimi-k2.6` | ❌ | Consistently times out (>15s), unreliable |

**⚠️ kimi-k2.5 behavior varies by max_tokens:** With low `max_tokens` (≤10), reasoning content consumes all tokens → `content: null`. With `max_tokens: 50+`, it returns proper `content` AND `reasoning_content`. Verified Jun11: `max_tokens: 50` → `content: " Hello! How can I help you today?"`. For main chat use, this is fine (Hermes uses higher max_tokens by default). For testing, always use ≥50 to verify content delivery.

**kimi-k2.6 is unusable** — consistently times out through Kimchi, even from clean IPs via proxy. Don't recommend it.

### Key Credits Priority
User emphasized: Kimchi has more credits than MiMo and Kiro. **Kimchi should be the primary workhorse**, not fallback. Route:
- Main chat → Kimchi (minimax-m2.7)
- Quick tasks → Kimchi (minimax-m2.5)
- Complex reasoning → Kiro (kr/claude-sonnet-4.5)
- Vision → MiMo (xmtp/mimo-v2-omni) — Kimchi has no vision model
- Fallback → MiMo (xmtp/mimo-v2.5-pro)

## Python User-Agent Blocking (CRITICAL)
Cloudflare blocks Python `urllib.request` default User-Agent on Kimchi.dev. Returns 403 even from clean IPs via proxy.

**Fix:** Set `User-Agent: curl/8.5.0` header:
```python
headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "User-Agent": "curl/8.5.0"  # REQUIRED — Python default UA blocked
}
```

**Why curl works:** `curl` sends `User-Agent: curl/8.5.0` by default. Cloudflare allows it. Python's `urllib.request` sends `Python-urllib/3.x` which is blocked.

**9Router itself is NOT affected** — It uses Node.js undici which has its own User-Agent. Only direct Python requests need the fix.

## Direct Connection for Secondary VPS (No 9Router Needed)
If the secondary VPS has a clean IP (not blocked by Kimchi), connect Hermes directly:
```yaml
# Hye-Jin config.yaml — direct to Kimchi
custom_providers:
  - api_key: <HYEJIN_KIMCHI_KEY>
    api_mode: chat_completions
    base_url: https://llm.kimchi.dev/openai/v1
    model: minimax-m2.7
    name: kimchi
routing:
  default_provider: kimchi
  default_model: minimax-m2.7
```
Only use 9Router tunnel when VPS IP is blocked (Error 1010).

## Proxy Setup (When IP Blocked)
See `9router-model-routing/references/hyejin-proxy-setup.md` for SSH tunnel via Hye-Jin VPS.
Each connection needs: `connectionProxyEnabled: true`, `connectionProxyUrl: "http://localhost:8888"`

## Key Validation (Always Test)
**Never trust a key without testing.** Even keys that show "active" in dashboard may be invalid.
Test pattern:
```python
# From Hye-Jin (clean IP) with correct User-Agent
import json
from urllib.request import Request, urlopen
req = Request(
    "https://llm.kimchi.dev/openai/v1/chat/completions",
    data=json.dumps({"model": "minimax-m2.7", "messages": [{"role": "user", "content": "ok"}], "max_tokens": 5}).encode(),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "curl/8.5.0"}
)
resp = urlopen(req, timeout=15)
# 200 = valid, 401 = invalid key, 403 = IP blocked
```

**Known key issues (Jun 2026):**
- Auto-generated keys (Kimchidev.py): ALL rejected (401)
- Kimchi key 1 (`castai_v1_3ecf1d08ab...`): EXPIRED (was valid Jun11, returned 401 later same day)
- Kimchi-02 key (`castai_v1_6795e9eb...`): Invalid (401 for all models)
- Kimchi-02 new (`castai_v1_53c8700568722e82...`): Valid ✅
- Kimchi-03 new (`castai_v1_ac7c5ab971f3defa...`): Valid ✅

## Credit Checking

**Kimchi has NO public credit API.** All endpoints return 404 HTML:
- `/v1/dashboard/billing/credit_grants`, `/subscription`, `/usage`
- `/api/user/info`, `/api/credit`, `/api/billing`

**Check via:** Web dashboard at https://app.kimchi.dev/overview/you
**Track via:** 9Router Usage page (request count × estimated cost)

## Batch Key Testing Script

```python
import sqlite3, json, subprocess
db = sqlite3.connect('/home/ubuntu/.9router/db/data.sqlite')
rows = db.execute("SELECT name, data FROM providerConnections WHERE name LIKE 'Kimchi%' ORDER BY name").fetchall()
for name, data_raw in rows:
    api_key = json.loads(data_raw).get('apiKey', '')
    auth = f"Authorization: Bearer *** = subprocess.run([
        'curl', '-s', '--max-time', '10',
        '-H', auth, '-H', 'Content-Type: application/json', '-H', 'User-Agent: curl/8.5.0',
        '-d', '{"model":"minimax-m2.7","messages":[{"role":"user","content":"say ok"}],"max_tokens":3}',
        'https://llm.kimchi.dev/openai/v1/chat/completions'
    ], capture_output=True, text=True)
    try:
        resp = json.loads(result.stdout)
        status = "✅" if 'choices' in resp else "❌"
        err = resp.get('error', {}).get('message', '') if 'error' in resp else ''
        print(f"  {status} {name}" + (f": {err[:60]}" if err else ""))
    except:
        print(f"  ❌ {name}: no response")
```

**Key replacement workflow:**
1. User provides new keys → test each via proxy (Hye-Jin)
2. Insert new connections via DB with proxy settings (`connectionProxyEnabled: True`)
3. Disable old broken connections (`isActive = 0`)
4. Restart 9Router → test round-robin (3-4 requests)
5. Verify models show in `/v1/models` or at least work via `/v1/chat/completions`

**DB insert template (with proxy):**
```python
data = {
    "apiKey": new_key,
    "testStatus": "active",
    "providerSpecificData": {
        "baseUrl": "https://llm.kimchi.dev/openai/v1",
        "prefix": "kimchi",
        "apiType": "chat",
        "nodeName": "Kimchi-XX",
        "connectionProxyEnabled": True,
        "connectionProxyUrl": "http://localhost:8888",
        "connectionNoProxy": ""
    },
    "defaultModel": "minimax-m2.7",
    "backoffLevel": 0,
    "lastError": None,
    "lastErrorAt": None
}
```
