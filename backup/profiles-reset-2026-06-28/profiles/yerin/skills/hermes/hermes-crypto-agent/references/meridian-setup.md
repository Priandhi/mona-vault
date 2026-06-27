# Meridian Setup Reference (June 2026)

Verified setup for `https://github.com/yunus-0x/meridian` on VPS (Ubuntu, Node.js 22).

## CRITICAL: Meridian ≠ Mona

Meridian (Solana DLMM LP) and Mona (EVM futures) are **separate systems**. Do NOT merge configs, share cron jobs, or mix concepts. Each has its own Telegram topic, PM2 process, and wallet.

## Installation paths

- **Active instance**: `/home/ubuntu/mona-workspace/meridian/` (PM2 id=0, verified working June 8 2026)
- **Old reference**: `/home/ubuntu/meridian-agent/` (earlier clone, may be stale)
- **Fleet wallets**: `~/mona-workspace/vault/solana-fleet/` (wallet-2 through wallet-10)
- **Keys vault**: `~/mona-workspace/vault/.meridian_env`, `~/mona-workspace/vault/.solana_wallet`

## Prerequisites

- Node.js 22+, npm 10+
- PM2 (`npm i -g pm2`)
- Dependencies: `@meteora-ag/dlmm`, `@solana/web3.js`, `bn.js`, `bs58`, `dotenv`, `jsonrepair`, `node-cron`, `openai`

```bash
cd /home/ubuntu/meridian-agent && npm install
```

## Environment (.env)

Keys stored in `~/mona-workspace/vault/.meridian_env`. Copy to repo root:

```env
WALLET_PRIVATE_KEY=<base58 Solana private key>
RPC_URL=https://mainnet.helius-rpc.com/?api-key=<helius_key>
HELIUS_API_KEY=<helius_key>             # extract from RPC_URL after ?api-key=
OPENROUTER_API_KEY=<from ~/.hermes/.env>
TELEGRAM_BOT_TOKEN=<from ~/.hermes/.env>
TELEGRAM_CHAT_ID=-1003899936547         # group ID
TELEGRAM_ALLOWED_USER_IDS=1492210461    # operator user ID
DRY_RUN=true
LOG_LEVEL=info
```

### ⚠️ PITFALL: Using non-OpenRouter LLM providers (GeneralCompute, etc.)

When using a custom LLM provider (e.g. GeneralCompute for minimax-m2.7), you MUST add these to `.env`:

```env
LLM_BASE_URL=https://api.generalcompute.com/v1
LLM_API_KEY=<generalcompute_api_key>
```

And add `llmBaseUrl` and `llmApiKey` to `user-config.json`:
```json
{
  "llmBaseUrl": "https://api.generalcompute.com/v1",
  "llmApiKey": "<generalcompute_api_key>",
  "llmModel": "minimax-m2.7"
}
```

**CRITICAL**: The `ecosystem.config.cjs` must ALSO embed `LLM_BASE_URL` and `LLM_API_KEY` in the `env` block. PM2 does not load `.env` files — it only passes env vars from the ecosystem config or shell environment. The agent.js OpenAI client is initialized at module load time and reads `process.env.LLM_BASE_URL` / `process.env.LLM_API_KEY` directly.

### ⚠️ PITFALL: API key truncation by Hermes secret redaction

Hermes automatically redacts secrets in tool output. When writing files through `write_file` or terminal heredocs, API keys get **silently truncated** (e.g. `gc_lBNmLaEofJ2mW57pVFE64Ke25AHsQZ1o` → `gc_lBN...QZ1o` — 13 chars instead of 35). This causes **401 Invalid API key** errors that are hard to debug because the truncated key LOOKS correct in output.

**Workaround**: Always use a Python script that reads the full key from `~/.hermes/config.yaml` at runtime:

```python
import yaml, json

with open("/home/ubuntu/.hermes/config.yaml") as f:
    config = yaml.safe_load(f)

# Get full API key from hermes config (avoids redaction)
gc_key = ""
for p in config.get("custom_providers", []):
    if p.get("name") == "generalcompute":
        gc_key = p["api_key"]
        break

# Write .env with full key
with open("/path/to/meridian/.env", "w") as f:
    f.write(f"HELIUS_API_KEY=<full_key>\n")
    f.write(f"LLM_API_KEY={gc_key}\n")

# Write ecosystem.config.cjs with full key
with open("/path/to/meridian/ecosystem.config.cjs", "w") as f:
    f.write(f'module.exports = {{ apps: [{{ name: "meridian", script: "index.js", cwd: __dirname, interpreter: "node", instances: 1, exec_mode: "fork", autorestart: true, restart_delay: 5000, kill_timeout: 10000, max_restarts: 10, min_uptime: "10s", env: {{ NODE_ENV: "production", LLM_BASE_URL: "https://api.generalcompute.com/v1", LLM_API_KEY: "{gc_key}" }} }}] }};\n')

print(f"Keys written: Helius={len(helius_key)} chars, GC={len(gc_key)} chars")
```

**Verification**: After writing, always verify key lengths in the actual files:
```bash
python3 -c "
env = open('.env').read()
for line in env.split('\n'):
    if '=' in line:
        k, v = line.split('=', 1)
        print(f'{k}: {len(v)} chars')
"
```

### ⚠️ PITFALL: Model name format per provider

Different LLM providers use different model name formats:

| Provider | Format | Example |
|----------|--------|---------|
| OpenRouter | `provider/model-name` | `minimax/minimax-m2.7` |
| GeneralCompute | `model-name` (no prefix) | `minimax-m2.7` |
| GeneralCompute (alt) | `Model-Name` (title case) | `MiniMax-M2.7` |

**OpenRouter format (`minimax/minimax-m2.7`) will 404 on GeneralCompute.** The agent.js constructs the OpenAI client with `baseURL` from `LLM_BASE_URL`, so the model name must match what that specific API expects.

To verify: `curl -s -X POST $LLM_BASE_URL/chat/completions -H "Authorization: Bearer $LLM_API_KEY" -d '{"model":"<name>","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'` — if 404, try without the `provider/` prefix.

## Config Optimization Guide

### Key relationships (read before tuning)

| Parameter | Depends on | Rule |
|-----------|-----------|------|
| `deployAmountSol` | wallet SOL balance | Must be < (wallet - gasReserve). If wallet has 0.36 SOL and gasReserve 0.1, max deploy = 0.26 SOL |
| `minSolToOpen` | deployAmountSol | Must be ≤ deployAmountSol, otherwise positions never open |
| `positionSizePct` | deployAmountSol | `computeDeployAmount(wallet)` = clamp(deployable × positionSizePct, floor=deployAmountSol, ceil=maxDeployAmount) |
| `screeningIntervalMin` | market volatility | Lower = more candidates found, but more API calls. 15min for volatile, 30min for stable |
| `managementIntervalMin` | position count | Lower = faster OOR response. 5min with positions, 10min without |
| `temperature` | model reliability | 0.2 = deterministic (recommended), 0.373 = default, >0.5 = too noisy for financial decisions |
| `maxSteps` | model capability | 15 for fast models (minimax-m2.7), 20 for slower reasoning models |
| `darwinMinSamples` | position history | 5 for fast learning (new account), 10 for stable (proven track record) |

### Filter threshold relationships

The bot holder, top 10, and bundler filters are **independent gates** — a pool must pass ALL three. Lowering any one opens more candidates but increases scam risk.

| Filter | Conservative | Balanced (recommended) | Aggressive |
|--------|-------------|----------------------|------------|
| `maxTop10Pct` | 35% | 45% | 60% |
| `maxBundlePct` | 20% | 25% | 30% |
| `maxBotHoldersPct` | 20% | 25% | 30% |
| `minOrganic` | 70 | 55 | 40 |
| `minHolders` | 500 | 200 | 100 |
| `minTvl` | 20000 | 5000 | 2000 |
| `minMcap` | 200000 | 50000 | 20000 |

**Verified June 2026**: With balanced settings, the screener consistently finds 2-3 quality candidates per cycle. HUNTER-SOL was correctly filtered by the 25% bot threshold (had 28.15% bots). Aggressive settings let through more candidates but increase rug risk.

### Risk management presets

| Parameter | Conservative | Balanced | Aggressive |
|-----------|-------------|----------|------------|
| `stopLossPct` | -15% | -20% | -30% |
| `takeProfitPct` | 5% | 8% | 12% |
| `trailingTriggerPct` | 3% | 5% | 7% |
| `trailingDropPct` | 1.0% | 2.0% | 3.0% |
| `outOfRangeWaitMinutes` | 15 | 20 | 30 |

**Tradeoff**: Tighter stopLoss (-15%) preserves capital but exits volatile pools too early. Wider stopLoss (-30%) lets positions ride through dips but risks bigger losses. **-20% is the recommended sweet spot** for Solana DLMM LP positions — enough room for volatility, but caps max loss per position. User explicitly corrected: "-30% kegedean buat LP".

### Small wallet preset (< 0.5 SOL) — VERIFIED WORKING June 2026

For wallets with 0.2-0.5 SOL. Optimized for Meteora DLMM with minimax-m2.7 model.

```json
{
  "preset": "custom",
  "dryRun": true,
  "deployAmountSol": 0.15,
  "maxPositions": 3,
  "minSolToOpen": 0.2,
  "maxDeployAmount": 50,
  "gasReserve": 0.1,
  "positionSizePct": 0.4,
  "strategy": "bid_ask",
  "minBinsBelow": 35,
  "maxBinsBelow": 69,
  "defaultBinsBelow": 69,
  "timeframe": "5m",
  "category": "trending",
  "excludeHighSupplyConcentration": true,
  "minTvl": 5000,
  "maxTvl": 200000,
  "minVolume": 300,
  "minOrganic": 55,
  "minQuoteOrganic": 55,
  "minHolders": 200,
  "minMcap": 50000,
  "maxMcap": 15000000,
  "minBinStep": 80,
  "maxBinStep": 125,
  "minFeeActiveTvlRatio": 0.04,
  "minTokenFeesSol": 20,
  "maxBundlePct": 25,
  "maxBotHoldersPct": 25,
  "maxTop10Pct": 45,
  "blockedLaunchpads": [],
  "minClaimAmount": 3,
  "autoSwapAfterClaim": true,
  "outOfRangeBinsToClose": 10,
  "outOfRangeWaitMinutes": 20,
  "oorCooldownTriggerCount": 3,
  "oorCooldownHours": 12,
  "minVolumeToRebalance": 500,
  "stopLossPct": -20,
  "takeProfitPct": 8,
  "minFeePerTvl24h": 5,
  "minAgeBeforeYieldCheck": 45,
  "trailingTakeProfit": true,
  "trailingTriggerPct": 5,
  "trailingDropPct": 2.0,
  "pnlSanityMaxDiffPct": 5,
  "managementIntervalMin": 5,
  "screeningIntervalMin": 15,
  "healthCheckIntervalMin": 30,
  "temperature": 0.2,
  "maxTokens": 4096,
  "maxSteps": 15,
  "managementModel": "minimax-m2.7",
  "screeningModel": "minimax-m2.7",
  "generalModel": "minimax-m2.7",
  "darwinEnabled": true,
  "darwinWindowDays": 60,
  "darwinRecalcEvery": 5,
  "darwinBoost": 1.05,
  "darwinDecay": 0.95,
  "darwinFloor": 0.3,
  "darwinCeiling": 2.5,
  "darwinMinSamples": 5,
  "hiveMindPullMode": "auto"
}
```

**Why these values** (differences from moderate preset):
- `deployAmountSol: 0.15` — wallet has 0.36 SOL, need room for gas
- `minSolToOpen: 0.2` — was 0.55 which BLOCKED all deploys (wallet < 0.55!)
- `gasReserve: 0.1` — 0.2 too conservative for small wallet
- `positionSizePct: 0.4` — more aggressive compounding to grow small wallet
- `minTvl: 5000` — 10k too restrictive, missed quality pools
- `minHolders: 200` — 500 too strict for Solana memecoins
- `minMcap: 50000` — 150k too high for early-stage pools
- `maxTop10Pct: 45` — 60% too permissive, let through whale-dominated pools
- `stopLossPct: -20` — -15% too tight (false close on volatile pools), -30% too loose (max rugi 0.045 SOL per posisi, 3 posisi barengan = 0.135 SOL = terlalu banyak). -20% = max rugi 0.03 SOL per posisi. User explicitly corrected: "-30% kegedean buat LP"
- `takeProfitPct: 8` — 5% too tight, exits before real gains
- `trailingTriggerPct: 5` — wait for more profit before trailing starts
- `screeningIntervalMin: 15` — 30min too slow for volatile Solana pools
- `temperature: 0.2` — more deterministic LLM decisions
- `darwinMinSamples: 5` — learn faster from fewer trades

### Moderate preset (0.5-2 SOL) — for reference

```json
{
  "preset": "moderate",
  "dryRun": true,
  "deployAmountSol": 0.3,
  "maxPositions": 3,
  "maxDeployAmount": 10,
  "minSolToOpen": 0.35,
  "gasReserve": 0.2,
  "positionSizePct": 0.35,
  "strategy": "bid_ask",
  "timeframe": "30m",
  "minTvl": 10000,
  "maxTvl": 150000,
  "minVolume": 1000,
  "minOrganic": 60,
  "minHolders": 500,
  "minMcap": 150000,
  "maxMcap": 10000000,
  "minFeeActiveTvlRatio": 0.15,
  "minTokenFeesSol": 30,
  "stopLossPct": -15,
  "takeProfitPct": 5,
  "trailingTriggerPct": 3,
  "trailingDropPct": 1.5,
  "managementIntervalMin": 10,
  "screeningIntervalMin": 30,
  "temperature": 0.373,
  "maxSteps": 20,
  "darwinMinSamples": 10
}
```

### Config rationale

- **5m timeframe** (small wallet) vs **30m** (moderate): smaller wallets need faster screening to catch opportunities before they expire
- **bid_ask strategy**: widest range coverage for volatile pools
- **Trailing TP (5%/2.0%)**: locks in profits after 5% gain, drops 2% triggers exit — wider than moderate preset to let volatile pools breathe
- **Darwin enabled**: self-learning signal weights evolve every 5 closes
- **minimax-m2.7 model**: cheap, fast, reliable. Via GeneralCompute API (`api.generalcompute.com/v1`). Use `minimax-m2.7` (no prefix) — NOT `minimax/minimax-m2.7` which is OpenRouter format.
- **temperature 0.2**: LLM makes more consistent pool selection decisions. Higher temps cause inconsistent candidate ranking across cycles.

## DEPRECATED MODELS (do NOT use)

- `openrouter/healer-alpha` → 404, was stealth model, now revealed as MiMo-V2-Pro
- `openrouter/hunter-alpha` → 404, same fate
- `stepfun/step-3.5-flash:free` → used as fallback in agent.js, may also be dead

Use `minimax-m2.7` (no prefix) via GeneralCompute, or current free models from OpenRouter.

## PM2 Setup

```bash
cd /home/ubuntu/meridian-agent
npm run pm2:start    # uses ecosystem.config.cjs — do NOT use "pm2 start index.js"
pm2 save
```

PM2 ecosystem: `ecosystem.config.cjs` pins cwd to repo root, auto-restart on crash, max 10 restarts.

```bash
pm2 restart meridian --update-env   # after .env changes (may not clear cached env)
pm2 delete meridian && pm2 start ecosystem.config.cjs --update-env  # reliable: fully clears cached env
pm2 logs meridian --lines 50        # check logs
pm2 status                          # verify running
```

## Telegram Integration — Two Architectures

### Architecture A: Separate bot token (RECOMMENDED)

Give Meridian its own bot (e.g. `@DinoCantik_Bot` — **active June 2026**, token in Meridian `.env`) so polling doesn't conflict with Hermes/Mona. This is the **GitHub-default** way and the currently deployed architecture.

```env
# .env — Meridian's own bot
TELEGRAM_BOT_TOKEN=<meridian_bot_token>
TELEGRAM_CHAT_ID=-1003899936547
TELEGRAM_ALLOWED_USER_IDS=1492210461
TELEGRAM_MESSAGE_THREAD_ID=947
```

No code changes needed — Meridian polls its own bot, Mona polls hers. Zero conflict.

**Setup steps:**
1. Chat @BotFather → `/newbot` → get token
2. Add new bot to group as admin with "Manage Topics" permission
3. Send any message to the new bot (registers chat)
4. Set `TELEGRAM_CHAT_ID`, `TELEGRAM_ALLOWED_USER_IDS`, `TELEGRAM_MESSAGE_THREAD_ID` in `.env`
5. Update `user-config.json`: `"telegramChatId": "-1003899936547"`
6. `pm2 restart meridian --update-env`

### Architecture B: Shared bot token with TELEGRAM_NO_POLL

When you can't create a second bot, disable Meridian's polling while keeping its send-only notifications:

```env
# .env
TELEGRAM_NO_POLL=true
TELEGRAM_MESSAGE_THREAD_ID=947
```

Then modify `telegram.js` `startPolling()`:
```javascript
export function startPolling(onMessage) {
  if (!TOKEN) return;
  if (process.env.TELEGRAM_NO_POLL === "true") {
    log("telegram", "Polling disabled (TELEGRAM_NO_POLL) — Hermes handles incoming messages");
    return;
  }
  _polling = true;
  poll(onMessage);
  registerCommands();
  log("telegram", "Bot polling started");
}
```

Also inject `message_thread_id` into `postTelegram()` (see forum topic section below).

**Tradeoff**: Meridian can SEND notifications but CANNOT receive commands (/positions, /close). User must go through Mona for commands.

### Forum Topic Routing (both architectures)

Meridian's default `telegram.js` does NOT include `message_thread_id`. Without modification, notifications go to the group's general chat.

**Add THREAD_ID constant** — after `let chatId = process.env.TELEGRAM_CHAT_ID || null;`:
```javascript
const THREAD_ID = process.env.TELEGRAM_MESSAGE_THREAD_ID || null;
```

**Inject into postTelegram body**:
```javascript
// OLD:
body: JSON.stringify({ chat_id: chatId, ...body }),
// NEW:
body: JSON.stringify({ chat_id: chatId, ...(THREAD_ID ? { message_thread_id: Number(THREAD_ID) } : {}), ...body }),
```

This routes ALL notifications (deploy, close, swap, OOR, live messages, screening/management reports) to the topic.

**Do NOT modify `postTelegramRaw`** — only used for `answerCallbackQuery`.

### ⚠️ PITFALL: Polling conflict with shared bot token

If two processes poll the same bot token via `getUpdates`, one process silently misses messages. Symptoms: Hermes stops responding to chat, or Meridian commands (/positions) don't work. **Fix**: Either use Architecture A (separate bot) or Architecture B (TELEGRAM_NO_POLL).

### ⚠️ PITFALL: Meridian notifications go to general chat without `message_thread_id`

Always apply the `postTelegram` patch when integrating with a Telegram forum group.

### ⚠️ PITFALL: config.js env override with `||=`

`config.js` line 38-39:
```javascript
if (u.llmBaseUrl) process.env.LLM_BASE_URL ||= u.llmBaseUrl;
if (u.llmApiKey)  process.env.LLM_API_KEY  ||= u.llmApiKey;
```

- Empty string `""` in user-config.json is falsy → won't override env var
- But if env var is UNDEFINED and user-config has a value → it WILL set the env var
- **Switching providers**: when changing from GeneralCompute to OpenRouter, you MUST remove `llmBaseUrl` and `llmApiKey` from user-config.json (set to `""`), not just change .env. Otherwise the old values persist.

### ⚠️ PITFALL: PM2 env caching after ecosystem.config.cjs changes

PM2 caches env vars from `ecosystem.config.cjs` at process start. `pm2 restart --update-env` does NOT always clear cached vars. **Reliable fix**:
```bash
pm2 delete meridian          # fully remove cached env
pm2 start ecosystem.config.cjs --update-env  # fresh start
```

Verify with: `cat /proc/$(pm2 pid meridian)/environ | tr '\0' '\n' | grep LLM_BASE`

### ⚠️ PITFALL: Switching from custom LLM provider back to OpenRouter

When reverting from GeneralCompute (or any custom provider) to OpenRouter:

1. Remove from `.env`: `LLM_BASE_URL`, `LLM_API_KEY`
2. Add to `.env`: `OPENROUTER_API_KEY=<key from ~/.hermes/.env>`
3. Set in `user-config.json`: `llmBaseUrl: ""`, `llmApiKey: ""`, model to OpenRouter format
4. Remove from `ecosystem.config.cjs` env block: `LLM_BASE_URL`, `LLM_API_KEY`
5. `pm2 delete meridian && pm2 start ecosystem.config.cjs --update-env`

**Model name format matters**: OpenRouter uses `provider/model:free` (e.g. `openai/gpt-oss-20b:free`), GeneralCompute uses `model-name` (e.g. `minimax-m2.7`). Using wrong format → 404.

### Verified free OpenRouter models (June 2026)

```
openai/gpt-oss-20b:free          # 20B, fast, good for screening
openai/gpt-oss-120b:free         # 120B, slower but smarter
nvidia/nemotron-3-super-120b-a12b:free
nvidia/nemotron-3-ultra-550b-a55b:free
nousresearch/hermes-3-llama-3.1-405b:free
google/gemma-4-31b-it:free
meta-llama/llama-3.3-70b-instruct:free
moonshotai/kimi-k2.6:free
```

Test with: `curl -s https://openrouter.ai/api/v1/models -H "Authorization: Bearer $OPENROUTER_API_KEY" | python3 -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin)['data'] if m.get('pricing',{}).get('prompt')=='0']"`

## Telegram Topic Integration (Legacy — see "Two Architectures" above)

Meridian reports to **topic 947** in group `-1003899936547` (separate from Mona's topic 387).

### Step 1: Add env vars to `.env`

```env
TELEGRAM_BOT_TOKEN=<bot_token>
TELEGRAM_CHAT_ID=-1003899936547
TELEGRAM_ALLOWED_USER_IDS=1492210461
TELEGRAM_MESSAGE_THREAD_ID=947
```

Also update `user-config.json`:
```json
{ "telegramChatId": "-1003899936547" }
```

### Step 2: Modify `telegram.js` to support forum topics

Meridian's `telegram.js` does NOT include `message_thread_id` by default. Without this modification, all notifications go to the group's general chat, NOT the topic.

**Add THREAD_ID constant** — after line `let chatId = process.env.TELEGRAM_CHAT_ID || null;`:
```javascript
const THREAD_ID = process.env.TELEGRAM_MESSAGE_THREAD_ID || null;
```

**Inject message_thread_id into postTelegram** — change the body line in `postTelegram()`:
```javascript
// OLD:
body: JSON.stringify({ chat_id: chatId, ...body }),

// NEW:
body: JSON.stringify({ chat_id: chatId, ...(THREAD_ID ? { message_thread_id: Number(THREAD_ID) } : {}), ...body }),
```

This single change routes ALL notifications (deploy, close, swap, OOR, live messages, screening reports, management reports) to the topic — because `sendMessage`, `sendHTML`, `editMessage`, `createLiveMessage`, and all `notify*` functions go through `postTelegram`.

**Do NOT modify `postTelegramRaw`** — it's only used for `answerCallbackQuery` which doesn't need topic routing.

### Step 3: Restart and verify

```bash
pm2 restart meridian --update-env
sleep 5
pm2 logs meridian --lines 20  # should show "[TELEGRAM] Bot polling started" with no errors
```

Test with Python:
```python
import base64, httpx, os
with open(os.path.expanduser('~/mona-workspace/vault/.telegram_bot')) as f:
    token = base64.b64decode(f.read().strip()).decode()
resp = httpx.post(f"https://api.telegram.org/bot{token}/sendMessage", json={
    "chat_id": "-1003899936547",
    "message_thread_id": 947,
    "text": "🌊 Meridian test notification",
    "parse_mode": "HTML"
}, timeout=10)
print(f"OK: {resp.json().get('ok')}")  # Should be True
```

### Step 4: Create topic (if new)

```bash
BOT_TOKEN=$(grep '^TELEGRAM_BOT_TOKEN=' ~/.hermes/.env | tail -1 | cut -d'=' -f2)
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/createForumTopic" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "-1003899936547", "name": "Meridian LP Agent", "icon_color": 13338331}'
```

### ⚠️ PITFALL: Meridian notifications go to general chat without `message_thread_id`

The default `telegram.js` in the Meridian repo does NOT support forum topics. Without the Step 2 modification, all deploy/close/swap/OOR notifications land in the group's general chat, cluttering Mona's conversation. Always apply the `postTelegram` patch when integrating with a Telegram forum group.

## Verified CLI commands

```bash
cd /home/ubuntu/meridian-agent

node cli.js balance       # wallet SOL + tokens + USD
node cli.js candidates    # pool discovery (can be slow, 60s+)
node cli.js positions     # open DLMM positions
node cli.js screen        # one AI screening cycle
node cli.js manage        # one AI management cycle

npm run dev               # dry-run autonomous agent (interactive REPL)
npm start                 # live autonomous agent
```

## Meteora API endpoints (verified June 2026)

Old endpoint `dlmm-api.meteora.ag` returns 403/404. Use `datapi.meteora.ag`:

```
Pool Discovery:  https://pool-discovery-api.datapi.meteora.ag/pools?page_size=N&filter_by=...&timeframe=5m&category=trending
DLMM search:     https://dlmm.datapi.meteora.ag/pools?query={mint}&sort_by=tvl:desc
Pool detail:     https://dlmm.datapi.meteora.ag/pools/{pool_address}
Portfolio:       https://dlmm.datapi.meteora.ag/portfolio/open?user={wallet}
Positions PnL:   https://dlmm.datapi.meteora.ag/positions/{pool}/pnl?user={wallet}&status=open&pageSize=100&page=1
```

## Architecture (key concepts for config tuning)

### ReAct Agent Loop
LLM → tool call → observe → repeat (max 20 steps). Role-based tool filtering: SCREENER (11 tools), MANAGER (6 tools), GENERAL (all). ONCE_PER_SESSION lock prevents double-deploy.

### Decision Log (`decision-log.json`)
Every action logged: type, actor, pool, summary, reason, risks[], rejected[]. Max 100 entries. Injected into system prompt.

### Lessons System (`lessons.json`)
Auto-derives lessons from closed positions. Confidence scoring 0.22-0.88. Auto-evolution every 5 closes adjusts screening thresholds.

### Darwinian Signal Weights (`signal-weights.json`)
13 signals tracked. Predictive lift: winners vs losers. Top quartile +5%, bottom -5%. Rolling 60-day window, min 10 samples.

### Pool Memory (`pool-memory.json`)
Per-pool history: deploys, win_rate, avg_pnl, cooldowns. Auto-cooldown after 3x OOR close (12h).

### Smart Wallets (`smart-wallets.json`)
Track KOL/alpha wallets. Check if in target pools → confidence boost.

### HiveMind
Shared learning via Agent Meridian API (`api.agentmeridian.xyz`). Non-blocking failures.

## Critical: SOL balance

Minimum for DLMM deploy: ~0.5 SOL per position with GitHub defaults. With the **small wallet preset**, minimum is ~0.25 SOL (0.15 deploy + 0.1 gas). Current wallet: 0.364 SOL → can deploy 1 position, not 3.

**Hitungan kasar (small wallet, 0.15 SOL deploy, SL -20%):**
- Max rugi per posisi: 0.03 SOL (~$4)
- 3 posisi kena SL barengan: 0.09 SOL rugi
- Sisa: 0.274 SOL (masih cukup deploy 1 posisi baru)

## Multi-wallet scaling

Single-wallet only. To scale: run separate instances with different `WALLET_PRIVATE_KEY`. Fleet wallets (2-10) in `~/mona-workspace/vault/solana-fleet/`.
