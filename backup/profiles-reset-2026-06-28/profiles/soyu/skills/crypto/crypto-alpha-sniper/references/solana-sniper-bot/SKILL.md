---
name: solana-sniper-bot
description: "Build and operate Solana token sniper bots — signal-driven buy/sell automation with Jupiter DEX, position management (TP/SL/trailing), PnL tracking, Telegram notifications, and live dashboards."
triggers:
  - sniper bot
  - token sniper
  - buy/sell bot
  - Jupiter executor
  - auto-trading bot
  - signal-driven trading
  - Charon sniper
tags: [solana, sniper, jupiter, defi, trading, bot, charon, pnl, dashboard]
---

# Solana Sniper Bot

Build automated token sniper bots on Solana that consume external signal sources (Charon, Birdeye, custom scrapers), filter candidates, execute buys/sells via Jupiter aggregator, manage positions with TP/SL/trailing, and provide real-time dashboards.

## Architecture

```
Signal Source (Charon API, Birdeye, custom)
    ↓
Token Filter (holders, mcap, volume, age, bonding)
    ↓
Jupiter Executor (quote → swap → confirm)
    ↓
Position Manager (TP, SL, trailing, partial exit, max hold)
    ↓
PnL Tracker (daily stats, win rate, risk/reward)
    ↓
Notifications (Telegram) + Dashboard (Express + HTML)
```

## Module Structure

```
project/
├── index.js                    # Main loop (scan → filter → trade → manage)
├── config.json                 # All settings (mode, filter, trade, exit, risk, telegram)
├── server.js                   # Dashboard backend (Express)
├── ecosystem.config.cjs        # PM2 config (separate apps for bot + dashboard)
├── modules/
│   ├── signal-fetcher.js       # Fetch from external API with caching
│   ├── token-filter.js         # Qualify signals against thresholds
│   ├── jupiter-executor.js     # Buy/sell via Jupiter API
│   ├── position-manager.js     # Track positions, TP/SL/trailing
│   ├── pnl-tracker.js          # Daily PnL, cumulative stats
│   ├── telegram-notifier.js    # Send buy/sell/daily alerts
│   └── logger.js               # Colored console logger
├── data/
│   ├── positions.json          # Open + closed positions
│   └── daily-pnl.json          # Daily PnL history
└── public/
    └── index.html              # Dashboard frontend (dark theme)
```

## Key Implementation Patterns

### 1. Signal Fetching with Cache
```javascript
let _cache = { signals: [], ts: 0 };
export async function fetchSignals(config) {
  if (_cache.signals.length > 0 && Date.now() - _cache.ts < 30000) return _cache.signals;
  // ... fetch from API, update cache
}
```

### 2. Jupiter Buy/Sell

**⚠️ Jupiter API v1 (Jun 2026):** Old endpoints (`api.jup.ag/quote`, `quote-api.jup.ag/v6/swap`, `api.jup.ag/price/v2`) are ALL 404.

- Quote: `GET https://api.jup.ag/swap/v1/quote?inputMint=SOL&outputMint=TOKEN&amount=LAMPORTS&slippageBps=500`
- Swap: `POST https://api.jup.ag/swap/v1/swap` with quoteResponse + userPublicKey → returns `swapTransaction` (base64), NOT `txid`
- Price: DEAD — use quote-based fallback (see `charon-sniper-bot` skill)
- Sign flow: `VersionedTransaction.deserialize(base64)` → `tx.sign([keypair])` → `sendRawTransaction()` → `confirmTransaction()`
- Always check DRY_RUN mode before executing real swaps
- Use `dynamicComputeUnitLimit: true` and `prioritizationFeeLamports` for faster execution

### 3. Position Management Loop
Every cycle (30s recommended):
1. Check existing positions for exit conditions (SL, TP, trailing, max hold)
2. Execute exits
3. Risk checks (max positions, daily loss limit, consecutive loss pause)
4. Fetch new signals
5. Filter qualifying candidates
6. Pick best by quality score
7. Execute buy

### 4. Quality Scoring
```javascript
let score = 0;
score += Math.min(holders / 200, 3);
score += Math.min(volume / 50000, 3);
score += Math.min(mcap / 50000, 2);
score += Math.min(liquidity / 10000, 2);
score += sources * 0.5;
score += trending ? 2 : 0;
```

### 5. Trailing Stop Logic
```
if (peakPct >= trailingTriggerPct) {
  if (dropFromPeak <= -trailingDropPct) → EXIT
}
```

### 6. Risk Management
- Min balance reserve (don't trade below threshold)
- Max daily loss (pause bot)
- Consecutive loss pause (3 losses → pause 1 hour)
- Cooldown between buys (2 minutes)
- Daily trade limit
- Emergency stop loss (hard exit at -30%)

## Config Template

**Default (conservative):**
```json
{
  "mode": "DRY_RUN",
  "trade": { "deployAmountSol": 0.05, "maxPositions": 3, "maxDailyTrades": 10, "cooldownMs": 120000, "slippageBps": 500 },
  "exit": { "stopLossPct": -20, "takeProfitPct": 50, "trailingEnabled": true, "trailingTriggerPct": 25, "trailingDropPct": 10, "maxHoldMinutes": 240 },
  "risk": { "minBalanceSol": 0.15, "maxDailyLossSol": 0.05, "emergencyStopLossPct": -30, "pauseAfterLosses": 3, "pauseDurationMs": 3600000 }
}
```

**Optimized for small wallet (0.3-0.4 SOL) + tight SL (data-driven, Jun8):**
```json
{
  "mode": "DRY_RUN",
  "trade": { "deployAmountSol": 0.04, "maxPositions": 3, "maxDailyTrades": 8, "cooldownMs": 180000, "slippageBps": 500, "priorityFee": 100000 },
  "exit": {
    "stopLossPct": -15, "takeProfitPct": 30,
    "trailingEnabled": true, "trailingTriggerPct": 12, "trailingDropPct": 8,
    "maxHoldMinutes": 120,
    "breakEven": { "enabled": true, "triggerPct": 15, "lockAtPct": 5 },
    "partialExit": { "enabled": true, "triggerPct": 12, "sellPct": 35 }
  },
  "risk": { "minBalanceSol": 0.20, "maxDailyLossSol": 0.05, "emergencyStopLossPct": -30, "pauseAfterConsecutiveLosses": 3, "pauseDurationMinutes": 60 }
}
```

Risk-reward: 1:2 per trade. **Exit flow:** partial exit at +12% (sell 35%) → break-even lock at +5% when +15% → trailing sells remaining at ~+10% (peak +18%, drop -8%). Net: ~+10.7% avg.

**⚠️ WHY THESE VALUES (Jun8 real data):** Charon signal micro-caps typically peak at +15-20%. Old defaults (break-even +10%, partial +25%, trailing +20%) meant partial exit and trailing NEVER triggered, and break-even killed profit at +2% instead of +10-12%. Always set triggers BELOW typical peak (~60-70% of observed average). See `charon-sniper-bot` skill `references/exit-strategy-optimization.md` for full analysis.

**⚠️ breakEven and partialExit require CODE implementation** — they are NOT built into generic position-manager.js. See `charon-sniper-bot` skill's `references/exit-strategy-implementation.md`.

## Dashboard Pattern

Separate Express server (different port from bot) with:
- `/api/pnl` — daily PnL summary
- `/api/trades` — today's closed trades
- `/api/positions` — open positions
- `/api/config` — safe config (redact tokens/keys)
- Dark-themed HTML frontend, auto-refresh every 15s
- Use `localhost.run` SSH tunnel for mobile access: `ssh -R 80:localhost:PORT nokey@localhost.run`

## Pitfalls

**NOTE:** For Charon API-specific details (signal fields, advanced filtering, Jupiter v1 migration, LIVE mode infrastructure), see `charon-sniper-bot` skill — it has the authoritative, session-tested reference. This skill covers the generic Solana sniper bot architecture.

1. **Port conflicts**: Each dashboard needs a unique port. Use 3456, 3457, 3458 etc. Check with `lsof -i :PORT` before starting.
2. **MiMo empty responses**: If using MiMo model, increase temperature (0.3) and reduce maxSteps (10) to avoid blank responses wasting cycles.
3. **Jupiter API rate limits**: Add delays between quote calls. Cache prices for 30s.
4. **DRY_RUN token amounts**: When simulating, use real Jupiter quotes for realistic amounts, not invented numbers.
5. **Position file corruption**: Always use try/catch when reading JSON data files. Return fallback empty arrays on parse errors.
6. **Cron delivery targeting**: Always set explicit `deliver: "telegram:CHAT_ID:THREAD_ID"` for cron jobs — never use "origin" for bot-specific notifications.
7. **Bot separation**: Charon sniper (buy/sell tokens) and Meridian DLMM (liquidity provision) are DIFFERENT strategies with DIFFERENT dashboards. Don't merge them.
8. **Break-even & partial exit are config-only (CRITICAL):** Config fields `exit.breakEven.*` and `exit.partialExit.*` are NOT implemented in code by default. You must add the logic to `position-manager.js` yourself. Without this, these configs are silently ignored. See `charon-sniper-bot` skill for implementation.
9. **Position file race condition:** If `checkExits()` loads positions, processes exits (which saves), then saves again with old data at the end — all close changes are overwritten. Fix: reload positions after exits before final save.
10. **DRY RUN sell returning 0:** When `getTokenPrice()` returns null for micro-caps, DRY RUN sell returns `amountOut: 0` → PnL = -100% → triggers daily loss limit. Best fix: use Jupiter quote API for sell simulation (`getQuote(mint, SOL_MINT, tokenAmount, slippage)`) → `amountOut = quote.outAmount / 1e9`. Fallback: `tokenAmount * price` (NO `* 1e-9` — price is already per raw unit). The `* 1e-9` multiplication is a common bug that makes values 1 billion times too small. See `charon-sniper-bot` skill for full fix history.
11. **Config key: `maxPositions` not `maxOpenPositions`:** Code reads `config.trade.maxPositions`. Wrong key → `undefined` → position count check fails silently.
12. **Config key: `filter` not `filters`:** Code reads `config.filter` (SINGULAR). If you write `filters` (plural), the filter module crashes with `Cannot read properties of undefined (reading 'blockedSymbols')` on every cycle.
13. **`blockedSymbols` required:** Token filter checks `f.blockedSymbols?.includes(sym)` in ADDITION to `blockedMints`. Include both in config: `"blockedSymbols": ["USDC", "USDT", "SOL", "WSOL", "MSOL"]` and `"blockedMints": [...]`.
14. **API key in config.json:** Signal provider API key (e.g. Charon) must be in `config.json` → `charon.apiKey`, NOT just in .env. Without this, API returns 401.
15. **Jupiter API v1 migration (Jun 2026):** ALL old Jupiter endpoints are 404. Use `/swap/v1/quote` and `/swap/v1/swap`. Price API is dead — use quote-based calculation. Swap returns `swapTransaction` (base64), NOT `txid`. Must deserialize → sign → send → confirm.
16. **Private keys in .env only:** Never put wallet private keys in `config.json`. Use `.env` with manual parser (no dotenv needed). Pattern: `WALLET_PRIVATE_KEY=base58...` and `HELIUS_API_KEY=...` in `.env`, load at startup.
17. **LIVE mode balance guard:** Check `getSolBalance()` every cycle against `minBalanceSol`. If below → pause 24h. Also check `balance < deployAmountSol + 0.01` before buy (deploy + gas buffer). Without this, bot wastes cycles on failed transactions.
18. **Pre-deployment verification (CRITICAL):** User hates bugs caught after deployment. Before reporting any fix as "complete": (1) test sell function with known token → verify amountOut is realistic, (2) verify config keys match code expectations, (3) check file persistence after position changes, (4) check error logs. Never say "beres" without running at least one end-to-end test. Fix silently if user catches a bug — don't apologize repeatedly.
