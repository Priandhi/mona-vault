# Config Precedence Debugging — "Key Works But Process Gets 401"

When you validate an API key directly (Python/Node/curl) and it works, but the running process still gets `401 Invalid API Key`, the process is loading a DIFFERENT key than the one you tested.

## The Layered Config Problem

Most Node.js services load config from multiple sources with precedence:

```
Shell env vars (inherited by PM2 daemon)
  ↓ overridden by
PM2 ecosystem config env:{} block
  ↓ overridden by
App-level config (user-config.json, config.js)
  ↓ overridden by
dotenv (.env file) — only sets vars that DON'T already exist
```

The critical trap: **dotenv uses `||=` semantics** — it only sets a var if it's not already set. If `config.js` does `process.env.LLM_API_KEY ||= userConfig.llmApiKey`, and `user-config.json` has a value, that value wins over `.env`.

## Real-World Example (Jun10 — Meridian)

**Symptom:** Meridian agent got `401 Invalid API Key` on every screening cycle for ~1.5 hours.

**What we found:**
- `.env` had `OPENROUTER_API_KEY=sk-or-v1-...` (valid, 73 chars)
- `user-config.json` had `llmApiKey: "tp-svzt..."` (expired xiaomimimo key)
- `config.js` did: `if (u.llmApiKey) process.env.LLM_API_KEY ||= u.llmApiKey`
- `agent.js` did: `apiKey: process.env.LLM_API_KEY || process.env.OPENROUTER_API_KEY`

**Result:** `LLM_API_KEY` was set to the expired xiaomimimo key from `user-config.json`, which took precedence over the valid OpenRouter key in `.env`.

**Testing confirmed:**
- Python test with OpenRouter key → HTTP 200 ✅
- Python test with xiaomimimo key → HTTP 401 ❌
- Node test loading `.env` directly → HTTP 200 ✅
- Running process → HTTP 401 ❌ (because it loaded `LLM_API_KEY` from user-config)

## Debugging Sequence

When a process reports 401 but the key looks valid:

### Step 1: Identify ALL config sources
```bash
# Check .env
cat /path/to/service/.env | grep -i "key\|token\|secret"

# Check user-config.json or similar app config
python3 -c "import json; c=json.load(open('user-config.json')); print({k:v for k,v in c.items() if 'key' in k.lower() or 'api' in k.lower()})"

# Check ecosystem config
cat ecosystem.config.cjs | grep -A5 "env"

# Check PM2 env (what the process inherited)
pm2 env <id> 2>/dev/null | grep -i "key\|api"

# Check /proc env (only shows inherited vars, NOT dotenv-loaded)
cat /proc/<PID>/environ | tr '\0' '\n' | grep -i "key\|api"
```

### Step 2: Trace the precedence chain
```bash
# Find where env vars are set in the codebase
grep -rn "process.env.*||=" /path/to/service/ --include="*.js" | head -10
grep -rn "process.env.*=.*config\|process.env.*=.*user" /path/to/service/ --include="*.js" | head -10
```

### Step 3: Test the ACTUAL key the process uses
```python
# Read the key from the config source that takes precedence
import json
config = json.load(open('user-config.json'))
actual_key = config.get('llmApiKey') or config.get('apiKey')
actual_base = config.get('llmBaseUrl') or config.get('baseUrl')

# Test THIS key, not the one from .env
import urllib.request
req = urllib.request.Request(
    f'{actual_base}/chat/completions',
    data=json.dumps({"model": "model-name", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}).encode(),
    headers={"Authorization": f"Bearer {actual_key}", "Content-Type": "application/json"}
)
try:
    resp = urllib.request.urlopen(req, timeout=15)
    print(f"Key valid: HTTP {resp.status}")
except Exception as e:
    print(f"Key invalid: {e}")
```

### Step 4: Fix
Either:
- Update the key in the config source that takes precedence
- Remove the override from the higher-precedence config (let it fall back to .env)
- Update .env AND the higher-precedence config to use the same valid key

**After fixing:** `pm2 restart <process>` (dotenv reloads .env on restart)

## Common Config Precedence Patterns

| Service | .env key | Override source | Override field |
|---------|----------|----------------|----------------|
| Meridian | OPENROUTER_API_KEY | user-config.json | llmApiKey |
| Meridian | LLM_BASE_URL | user-config.json | llmBaseUrl |
| Charon | (check ecosystem) | ecosystem.config.cjs | env:{} |

## Key Insight

**Never trust "the key is in .env so the process has it."** Always verify which config source the process actually reads for a given setting. The code's precedence chain (`||=`) determines the real value.
