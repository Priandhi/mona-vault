# DRY RUN → LIVE Transition Reference

## Audit Commands

```bash
# PM2 status
pm2 list meridian

# Check DRY_RUN precedence
grep -n "DRY_RUN\|dryRun" .env user-config.json

# Verify LLM provider
grep -E "llmModel|llmBaseUrl|llmApiKey" user-config.json

# Wallet balance (terminal, NOT read_file — .env blocked)
curl -s -X POST https://mainnet.helius-rpc.com/?api-key=$(grep HELIUS_API_KEY .env | cut -d= -f2) \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getBalance","params":["WALLET_ADDRESS"]}'

# Recent errors (filter noise)
grep -i -E "error|fatal|crash" ~/.pm2/logs/meridian-error-0.log | grep -v "DeprecationWarning" | grep -v "punycode" | tail -10

# Restart count vs actual crashes
# SIGINT = config reload, NOT crash
pm2 list meridian | awk '{print $14}' # restart count
```

## Common Issues Found During Transition

### 1. DRY_RUN=true in .env overrides user-config.json
- `.env` DRY_RUN=true → config.js `||=` → user-config.json ignored
- Fix: Remove DRY_RUN from .env, set dryRun: false in user-config.json
- Must `pm2 delete && pm2 start` (not just restart)

### 2. Truncated API keys
- Check LLM API key length (should be ~35 chars for MiMo, ~50+ for OpenRouter)
- Check Helius key length (should be 36 chars)
- ecosystem.config.cjs may have old truncated keys in env block

### 3. Model name format
- MiMo: `mimo-v2.5-pro` (no org prefix)
- OpenRouter: `org/model:free` (exact format required)
- GeneralCompute: `minimax-m2.7` (no org prefix)

### 4. PM2 restart count misleading
- 10-15 restarts is NORMAL for a bot that's been running days
- SIGINT signals from config reloads count as restarts
- Check error logs for actual crashes vs just restart count

### 5. punycode DeprecationWarning
- `punycode` module deprecated in Node.js — NOT an error
- Filter out in monitoring: `grep -v "DeprecationWarning" | grep -v "punycode"`

## Safety Lock Pattern (Jun8 2026 — CRITICAL)

Darwin learning engine (`lessons.js:evolveThresholds()`) or threshold optimizer cron can set `dryRun: false` in user-config.json without user knowledge. On Jun8, this caused Meridian to go LIVE with real money while debugging 429 errors.

**Prevention — triple lock:**
1. **`.env`:** `DRY_RUN=true` — this is the PRIMARY lock because `config.js` uses `||=` (if DRY_RUN is already set in env, user-config.json value is IGNORED)
2. **`user-config.json`:** `dryRun: true` — secondary lock
3. **`ecosystem.config.cjs`:** Add `DRY_RUN: "true"` to env block — tertiary lock (survives pm2 restart)

**Verification after ANY config change:**
```bash
pm2 logs meridian --lines 5 | grep "Mode:"
# Must show: [STARTUP] Mode: DRY RUN
```

**If LIVE mode detected unexpectedly:**
1. Immediately: `python3 -c "import json; c=json.load(open('user-config.json')); c['dryRun']=True; json.dump(c,open('user-config.json','w'),indent=2)"`
2. Verify `.env` has `DRY_RUN=true`
3. `pm2 restart meridian`
4. Check logs for any real transactions that may have executed
