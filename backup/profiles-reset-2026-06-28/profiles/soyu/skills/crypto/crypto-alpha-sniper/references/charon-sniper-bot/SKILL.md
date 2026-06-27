---
name: charon-sniper-bot
description: Build and operate a Solana token sniper bot using Charon API signals + Jupiter DEX. Covers signal fetching, token filtering, buy/sell execution, position management (TP/SL/trailing), PnL tracking, and dashboard monitoring. Use when building buy/sell token bots on Solana, integrating Charon signals, or running sniper strategies.
when_to_use:
  - Building a token sniper bot on Solana
  - Integrating Charon API signals for token discovery
  - Executing buys/sells on Solana DEX (Jupiter, Raydium)
  - Managing token positions with TP/SL/trailing stops
  - Tracking sniper bot PnL and performance
  - User mentions "Charon sniper", "snipe token", "beli token Solana"
  - Deploying any 3rd-party Solana Node.js bot from GitHub (owntown, game bots, etc.) — covers wallet keypair format conversion, env-var refactor, token-gated entry fees
version: 1.4.0
---

# charon-sniper-bot

Solana token sniper bot that uses Charon API signals to discover and trade new tokens via Jupiter DEX aggregator.

**IMPORTANT:** This is SEPARATE from Meridian DLMM (liquidity provider). Charon Sniper = buy/sell tokens. Meridian = deploy liquidity to pools. Different strategies, different dashboards, different risk profiles.

## Architecture

```
charon-sniper/
├── index.js                    Main loop: signal fetch → filter → execute → manage
├── config.json                 All settings (filter, trade, exit, risk, telegram)
├── server.js                   Dashboard backend (Express)
├── public/index.html           Dashboard frontend (dark theme)
├── modules/
│   ├── charon-fetcher.js       Fetch signals from Charon API
│   ├── token-filter.js         Qualify tokens by thresholds
│   ├── jupiter-executor.js     Buy/sell via Jupiter API
│   ├── position-manager.js     Track positions, TP/SL/trailing
│   ├── pnl-tracker.js          Calculate PnL from positions
│   └── logger.js               Structured logging
├── data/
│   ├── positions.json          Active + historical positions
│   └── trades.json             Completed trades with PnL
└── ecosystem.config.cjs        PM2 deployment config
```

## Charon API

**Endpoint:** `https://api.thecharon.xyz/api/signals`
**Auth:** `x-api-key` header (NOT Bearer — Bearer returns 401)
**Cache:** 30s minimum between requests

```bash
curl -s "https://api.thecharon.xyz/api/signals" \
  -H "x-api-key: YOUR_KEY" | jq '.count, .signals[0]'
```

**Response fields per signal:**
| Field | Type | Description |
|---|---|---|
| `symbol` | string | Token ticker |
| `mint` | string | Solana mint address |
| `holders` | number | Current holder count |
| `marketCapUsd` | number | Market cap in USD |
| `volume24h` | number | 24h trading volume |
| `liquidityUsd` | number | Pool liquidity |
| `ageMs` | number | Token age in milliseconds |
| `sourceCount` | number | How many sources report this |
| `trending` | object/null | Trending data if available |
| `bondingComplete` | boolean | Bonding curve completed |
| `priceUsd` | number | Current price |
| `firstSeen` | string | ISO timestamp first detected |
| `lastSeen` | string | ISO timestamp last seen |

**Only 2 endpoints exist:** `/api/signals` and `/api/health`. No config/settings endpoints — Charon is a pure signal provider.

**Full field reference:** See `references/charon-api-fields.md` for complete signal field inventory including `trending` object (organicScore, buys/sells, stats5m, stats24h), `graduated` object (devHoldingsPercent, sniperCount, topHoldersPercent), and `feeClaim` data.

## Token Filtering

**Advanced 7-layer filter (v2):** See `references/advanced-token-filter.md` for full strategy with momentum, organic, distribution, volume, and liquidity layers. Reduces pass rate from 50% to 2%, dramatically improving win rate.

**Data-driven calibration workflow:** When filter pass rate is wrong or losses cluster on a pattern, re-derive thresholds from actual signal distribution. See `references/data-driven-filter-calibration.md` for the full 7-step workflow with distribution analysis templates, threshold mapping table, pass-rate targets, and worked Jun 16 2026 example.

**Anti-chase filter v3 (Jun 2026 — KEY ADDITION):** See `references/filter-v3-data-driven.md` for the data-driven methodology and 100-signal analysis. The single most important addition: **reject tokens with 5m momentum > +3%** — these are late entries where you become exit liquidity. Combined with strict age window (10-120 min) and TP ladder exit, this is what unlocked the first +139.91% winner (token "p", 4.3x peak captured via TP ladder).

Default thresholds (config.json `filter` section — NOTE: key is `filter` SINGULAR, not `filters`):

| Parameter | Value | Rationale |
|---|---|---|
| `minHolders` | 150 | Avoid brand new/empty tokens |
| `minMcap` | 15,000 | Minimum viable market cap |
| `maxMcap` | 5,000,000 | Avoid large caps (less upside) |
| `minVolume24h` | 10,000 | Active trading required |
| `minLiquidity` | 3,000 | Minimum pool liquidity |
| `maxAgeMs` | 72h | Avoid stale tokens |
| `requireBondingComplete` | true | Bonding curve must be done |
| `minSources` | 2 | Multi-source verification |
| `blockedSymbols` | USDC, USDT, SOL, WSOL, mSOL | Don't snipe stablecoins/wrapped (checked BEFORE blockedMints) |
| `blockedMints` | EPjF...Dt1v, Es9v...wNYB, So11...112, So11...111, mSoL...7So | Mint addresses of blocked tokens |

## Jupiter DEX Execution

**⚠️ Jupiter API v1 (as of Jun 2026):** The old `api.jup.ag/quote` and `quote-api.jup.ag/v6/swap` endpoints are DEAD (404). Use:
- **Quote:** `https://api.jup.ag/swap/v1/quote?inputMint=...&outputMint=...&amount=...&slippageBps=...`
- **Swap:** `https://api.jup.ag/swap/v1/swap` (POST)
- **Price API:** `/price/v2` is also 404 — use quote-based fallback (see below)

### Buy flow (LIVE):
1. Get quote from Jupiter v1 API
2. Call `/swap/v1/swap` → returns `swapTransaction` (base64 encoded VersionedTransaction)
3. Deserialize: `VersionedTransaction.deserialize(Buffer.from(swapData.swapTransaction, 'base64'))`
4. Sign: `tx.sign([keypair])`
5. Send: `connection.sendRawTransaction(Buffer.from(tx.serialize()), { skipPreflight: true, maxRetries: 2 })`
6. Confirm: `connection.confirmTransaction(txHash, 'confirmed')`
7. Record position

### Sell flow (LIVE):
1. Get quote (input: token mint, output: SOL, amount in raw token units)
2. Same sign+send+confirm pattern as buy

### Transaction signing implementation:
```javascript
import { Connection, Keypair, VersionedTransaction } from "@solana/web3.js";
import bs58 from "bs58";

// Init wallet from .env (base58 private key)
function initWallet(privateKeyBase58, rpcUrl) {
  const secretKey = bs58.decode(privateKeyBase58);
  const keypair = Keypair.fromSecretKey(secretKey);
  const connection = new Connection(rpcUrl, { commitment: "confirmed" });
  return { keypair, connection, pubkey: keypair.publicKey.toBase58() };
}

// Execute swap: deserialize → sign → send → confirm
async function executeSwap(swapTransactionBase64, keypair, connection) {
  const tx = VersionedTransaction.deserialize(Buffer.from(swapTransactionBase64, "base64"));
  tx.sign([keypair]);
  const rawTx = Buffer.from(tx.serialize());
  
  // Send with retries (3 attempts)
  let txHash;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      txHash = await connection.sendRawTransaction(rawTx, {
        skipPreflight: true, maxRetries: 2, preflightCommitment: "confirmed",
      });
      break;
    } catch (e) {
      if (attempt < 2) await new Promise(r => setTimeout(r, 1000));
      else throw e;
    }
  }
  
  // Confirm (timeout doesn't mean failure)
  try {
    await connection.confirmTransaction(txHash, "confirmed");
  } catch (e) {
    // TX may still succeed even if confirm times out
  }
  return txHash;
}

// Call Jupiter swap API and execute
async function swapViaJupiter(quote, keypair, connection, pubkey, priorityFee) {
  const resp = await fetch("https://api.jup.ag/swap/v1/swap", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      quoteResponse: quote,
      userPublicKey: pubkey,
      wrapAndUnwrapSol: true,
      dynamicComputeUnitLimit: true,
      prioritizationFeeLamports: priorityFee || 100000,
    }),
    signal: AbortSignal.timeout(20000),
  });
  const data = await resp.json();
  if (!data.swapTransaction) throw new Error("No swapTransaction in response");
  return executeSwap(data.swapTransaction, keypair, connection);
}
```

### Price API fallback (when Jupiter price API is down):
```javascript
// Calculate token price from quote: 0.001 SOL → tokens → price per token
async function getTokenPriceFromQuote(mint) {
  const lamports = 1000000; // 0.001 SOL
  const url = `https://api.jup.ag/swap/v1/quote?inputMint=SOL_MINT&outputMint=${mint}&amount=${lamports}&slippageBps=500`;
  const resp = await fetch(url, { signal: AbortSignal.timeout(10000) });
  if (!resp.ok) return null;
  const data = await resp.json();
  const tokens = Number(data.outAmount);
  if (tokens <= 0) return null;
  return lamports / tokens / 1e9; // price per token in SOL
}
```

### Wallet .env loading (without dotenv dependency):
```javascript
import fs from "fs";
import path from "path";

function loadEnv(envPath) {
  if (!fs.existsSync(envPath)) return {};
  const env = {};
  for (const line of fs.readFileSync(envPath, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const idx = trimmed.indexOf("=");
    if (idx > 0) env[trimmed.slice(0, idx)] = trimmed.slice(idx + 1);
  }
  return env;
}

// In main():
const ENV = loadEnv(path.join(__dirname, ".env"));
const rpcUrl = `https://mainnet.helius-rpc.com/?api-key=${ENV.HELIUS_API_KEY}`;
const { keypair, connection, pubkey } = initWallet(ENV.WALLET_PRIVATE_KEY, rpcUrl);
```

**SLIPPAGE:** Default 500 bps (5%). Solana memecoins are volatile — lower slippage = failed transactions, higher = worse price.

**PRIORITY FEE:** 100,000 lamports. Higher = faster inclusion. On Solana, priority fees matter for sniping. 100K recommended for competitive sniping.

## Position Management

### Exit Strategy (config.json `exit` section):

| Rule | Default | Data-Driven (-15% SL) | Description |
|---|---|---|---|
| `stopLossPct` | -20% | **-15%** | Hard stop loss |
| `takeProfitPct` | +50% | **+30%** | Take profit target (realistic for micro-caps) |
| `trailingTriggerPct` | +25% | **+12%** | Start trailing after gain (60-70% of typical peak) |
| `trailingDropPct` | -10% | **-8%** | Close if drops from peak |
| `maxHoldMinutes` | 240 | **120** | Force close after timeout |
| `breakEven.enabled` | — | **true** | Move SL to lock profit |
| `breakEven.triggerPct` | — | **+15%** | Activate break-even AFTER partial exit |
| `breakEven.lockAtPct` | — | **+5%** | Lock profit at |
| `partialExit.enabled` | — | **true** | Sell portion early |
| `partialExit.triggerPct` | — | **+12%** | Trigger partial at (same as trailing) |
| `partialExit.sellPct` | — | **35%** | Sell this % of position |

**⚠️ CRITICAL:** Break-even and partial exit are CONFIG FIELDS only — they require CODE implementation in `position-manager.js`. See Pitfalls section below. The exit checker priority order is:
1. Max hold time (no price needed)
2. Emergency SL
3. Normal SL
4. Break-even lock (if enabled, locks SL at +2% after +10% trigger)
5. Partial exit (if enabled, sells 40% at +25%, rest rides with trailing)
6. Take profit (only if trailing disabled)
7. Trailing stop

### Optimized Config for Small Wallet (0.3-0.4 SOL) + -15% SL

**⚠️ DATA-DRIVEN OPTIMIZATION (Jun8):** The config below is based on ACTUAL observed token behavior from Charon signals — NOT theoretical values. Key finding: micro-cap tokens from Charon signals typically peak at +15-20%, NOT +30-50%. Config values must match this reality.

```json
{
  "mode": "DRY_RUN",
  "charon": {
    "apiUrl": "https://api.thecharon.xyz",
    "refreshIntervalMs": 30000,
    "maxSignals": 50,
    "apiKey": "YOUR_CHARON_API_KEY"
  },
  "filter": {
    "minHolders": 150,
    "minMcap": 15000,
    "maxMcap": 3000000,
    "minVolume24h": 10000,
    "minLiquidity": 3000,
    "maxAgeHours": 12,
    "requireBondingComplete": true,
    "requireAtLeast2Sources": true,
    "blockedSymbols": ["USDC", "USDT", "SOL", "WSOL", "MSOL"],
    "blockedMints": [
      "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
      "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
      "So11111111111111111111111111111111111111112",
      "So11111111111111111111111111111111111111111",
      "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So"
    ]
  },
  "trade": {
    "deployAmountSol": 0.04,
    "maxPositions": 3,
    "maxDailyTrades": 8,
    "cooldownMs": 180000,
    "slippageBps": 500,
    "priorityFee": 100000,
    "minSolForTrade": 0.04
  },
  "exit": {
    "stopLossPct": -15,
    "takeProfitPct": 30,
    "trailingEnabled": true,
    "trailingTriggerPct": 12,
    "trailingDropPct": 8,
    "maxHoldMinutes": 120,
    "breakEven": { "enabled": true, "triggerPct": 15, "lockAtPct": 5 },
    "partialExit": { "enabled": true, "triggerPct": 12, "sellPct": 35 }
  },
  "risk": {
    "minBalanceSol": 0.20,
    "maxDailyLossSol": 0.05,
    "emergencyStopLossPct": -30,
    "pauseAfterConsecutiveLosses": 3,
    "pauseDurationMinutes": 60
  }
}
```

**⚠️ v3 (Jun 2026 — STRICTER, ANTI-CHASE):** The v2 filter above still produces 0/8 win rates in choppy markets. The v3 filter adds three hard rules that turned a 0/8 streak into a +139.91% winner on the first qualifying token. Use the v3 values when configuring a fresh bot:

| Field | v2 value | **v3 value** | Why |
|---|---|---|---|
| `minPriceChange5m` | (unset, allow all) | **-8** | Allow mild dip, reject falling knives |
| `maxPriceChange5m` | (NOT IN v2) | **3** | KEY: reject if 5m > +3% (don't chase pumps — you become exit liquidity) |
| `minAgeMinutes` | (NOT IN v2) | **10** | NEW: not too fresh (avoid rugs) |
| `maxAgeMinutes` | `maxAgeHours: 12` | **120** | was 12h, now 2h (FRESH early-stage only — most pumps die in 4h) |
| `minOrganicScore` | 30 | **55** | Top tier only |
| `maxOrganicScore` | (NOT IN v2) | **90** | Reject suspicious 100s (likely fake/manipulated) |
| `minBuyRatio` | 0.8 | **1.5** | Real demand, not just volume |
| `minNetBuyers` | 10 | **100** | Real adoption signal |
| `maxDevHoldings` | 20 | **8** | Low rug risk |
| `maxTopHolders` | 50 | **35** | Less dump risk |
| `maxSnipers` | 100 | **40** | Less competition |
| `maxMcap` | 3,000,000 | **500,000** | Lower cap = more upside |
| `minVolume24h` | 10,000 | **50,000** | Need active market |
| `minVolume5m` | 500 | **1,500** | Active trading |
| `minVolAcceleration` | 0.5 | **1.0** | 5m vol must outpace 24h baseline |
| `deployAmountSol` | 0.04 | **0.05** | Slightly larger per-trade, fewer positions |
| `maxPositions` | 3 | **2** | Risk reduction |
| `maxDailyTrades` | 8 | **5** | Quality > quantity |
| `maxDailyLossSol` | 0.05 | **0.03** | Tighter daily cap |
| `pauseAfterConsecutiveLosses` | 3 | **2** | Pause earlier |
| `pauseDurationMinutes` | 60 | **120** | Longer pause after losses |
| `cooldownMs` | 180000 | **600000** | 10m cooldown, not 3m |

See `references/filter-v3-data-driven.md` for the full data analysis (100 Charon signals, distribution graphs, rejection reasons) that drove these values.

**Why these values (based on real data from Jun8 DRY RUN):**

| Old Value | Problem | New Value | Why |
|---|---|---|---|
| `breakEven.triggerPct: 10` | Triggers too early, locks at +2%, kills profit. Tokens peaking at +18% get sold at +2%. | **`15`** | Let token run first. Lock at +5% gives meaningful floor. |
| `breakEven.lockAtPct: 2` | Too low. Actual profit lost: +1.9% vs potential +10-12%. | **`5`** | Higher lock = more profit preserved. |
| `partialExit.triggerPct: 25` | NEVER TRIGGERS. Observed peaks: ~+18%. Dead code. | **`12`** | Triggers at +12%, sells 35%, locks real profit. |
| `partialExit.sellPct: 40` | Slightly aggressive. | **`35`** | Keep more exposure for trailing. |
| `trailingTriggerPct: 20` | NEVER TRIGGERS. Peak +18% < trigger +20%. | **`12`** | Start trailing early. At peak +18%, drop -8% sells at ~+10%. |
| `takeProfitPct: 40` | Too ambitious for micro-caps. | **`30`** | Realistic target. |
| `maxHoldMinutes: 90` | Too short for some tokens. | **`120`** | Give more time to pump. |
| `slippageBps: 350` (3.5%) | Too tight. Micro-cap Solana liquidity is thin. Swap failures = stuck positions. | **`500` (5%)** | Safer for low-liquidity tokens. |
| `priorityFee: 75000` | Competing with other snipers. | **`100000`** | Faster inclusion. |
| `emergencyStopLossPct: -25` | Solana slippage during crash can be 10-20%. Actual loss could hit -40% while emergency only -25%. | **`-30`** | Give room for slippage. |
| `maxDailyLossSol: 0.04` | Too tight. 3 losses = 0.045 SOL > limit. | **`0.05`** | More realistic. |
| Filter `minHolders: 200` | Too restrictive. Some good tokens have 150-200 holders. | **`150`** | More signals pass. |
| Filter `minMcap: 20000` | Too restrictive. | **`15000`** | More signals pass. |
| Filter `minVolume: 15000` | Too restrictive. | **`10000`** | More signals pass. |
| Filter `minLiquidity: 5000` | Too restrictive. | **`3000`** | More signals pass. |

**Risk-reward math (0.04 SOL per trade, 3 positions):**
- Max deployed: 0.12 SOL (33% of 0.36 SOL wallet)
- Per trade risk: 0.04 × 15% = 0.006 SOL
- Per trade reward: 0.04 × 30% = 0.012 SOL → **1:2 ratio**
- **Optimal exit flow (based on real data):**
  1. Entry → price hits +12% → PARTIAL EXIT: sell 35%, lock profit
  2. Price hits +15% → BREAK-EVEN: lock SL at +5%
  3. Price peaks +18%, drops -8% from peak → TRAILING: sell remaining 65% at ~+10%
  4. Net: 35% × 12% + 65% × 10% = **+10.7% average profit**
- **Old broken flow (what actually happened):**
  1. Entry → price hits +10% → break-even locks at +2%
  2. Price peaks +18%, drops to +1.9% → sells at +1.9%
  3. Net: **+1.9% profit** (5.6x LESS than optimal!)
- Max loss all 3 at SL: 3 × 0.006 = 0.018 SOL (5% of wallet)

### Position lifecycle:
```
SIGNAL → FILTER → BUY → MONITOR → EXIT (TP/SL/Trailing/Timeout)
```

## Risk Management

| Parameter | Default | Description |
|---|---|---|
| `minBalanceSol` | 0.15 | Stop trading below this |
| `maxDailyLossSol` | 0.05 | Pause if daily loss exceeds |
| `emergencyStopLossPct` | -30% | Nuclear stop loss |
| `pauseAfterLosses` | 3 | Pause after N consecutive losses |
| `pauseDurationMs` | 1h | How long to pause |

## Dashboard

Express-based web dashboard (port 3458) showing:
- Daily PnL (SOL + %)
- Win rate, best/worst trades
- Avg win/loss, risk/reward ratio
- Individual trade list with details
- Live Charon signals feed
- Position manager status

Dark theme matching trading terminal aesthetic. Auto-refresh every 30s.

### Tunnel for phone access:
```bash
ssh -o StrictHostKeyChecking=no -R 80:localhost:3458 nokey@localhost.run
# Returns: https://XXXX.lhr.life
```

## Pre-Deployment Quality Checklist

**⚠️ USER LESSON (Jun8):** User frustrated by bugs caught AFTER deployment ("kenap gak daritadi"). User hates repeated apologies ("setiap hari minta maaf?"). **Fix first, explain later. Never report "beres" before verifying.**

Before reporting ANY fix as complete:

1. **PnL accuracy:** If a sell function was changed, TEST it: `sellToken(knownMint, knownAmount, config)` → verify `amountOut` is realistic (not 0, not 1e-8)
2. **Config key match:** Every config key in `config.json` must match what the code reads. Common mismatches: `filters` vs `filter`, `maxOpenPositions` vs `maxPositions`
3. **File persistence:** After a position close, verify `positions.json` actually updated: `python3 -c "import json; d=json.load(open('data/positions.json')); print(f'Open: {len(d[\"open\"])}, Closed: {len(d[\"closed\"])}')"` 
4. **Dashboard sync:** After bot restart, check dashboard shows correct data (not stale)
5. **Error logs:** `pm2 logs charon-sniper --err --lines 10 --nostream` — no new errors after fix

**Rule:** Never say "fix complete" without running at least one end-to-end verification. If user catches a bug you should have found, fix silently and move on — don't apologize repeatedly.

## DRY RUN Mode

Default mode. Simulates trades based on Charon signals without executing real swaps.

**Simulation logic:**
- Fetch Charon signals → filter → simulate PnL based on token quality
- Quality score = holders + volume + mcap + liquidity + sources + trending
- Win probability: 40-85% based on quality
- Win range: +5% to +120%
- Loss range: -3% to -25%

**Transition to LIVE:**
1. Create `.env` in charon-sniper dir with `WALLET_PRIVATE_KEY=<base58>` and `HELIUS_API_KEY=<key>`
2. Change `mode` in config.json from `DRY_RUN` to `LIVE`
3. Restart: `pm2 restart charon-sniper`
4. Bot automatically:
   - Loads wallet private key from `.env`
   - Derives public key and verifies it matches expected wallet
   - Checks SOL balance against `minBalanceSol`
   - If balance < min → exits with error "Top up wallet!"
   - If balance < deploy + gas → skips trades until balance recovers
5. Monitor first 10 trades closely

**LIVE mode pre-flight (startup validation):**
- `WALLET_PRIVATE_KEY` must be in `.env` (NOT config.json — never put private keys in config!)
- `HELIUS_API_KEY` in `.env` for RPC access (or set `RPC_URL` for custom RPC)
- Balance ≥ `risk.minBalanceSol` (default 0.20 SOL)
- Balance ≥ `trade.deployAmountSol + 0.01` (deploy + gas buffer)
- Jupiter API must be reachable (test: `curl -s 'https://api.jup.ag/swap/v1/quote?inputMint=So11...&outputMint=EPjF...&amount=1000000&slippageBps=500'`)

**LIVE mode runtime checks (every cycle):**
- Balance check: if balance < minBalanceSol → pause 24h
- Balance check: if balance < deployAmountSol + 0.01 → skip trade
- Insufficient balance at buy time → return `{ success: false, error: "insufficient_balance" }`
- 3x retry on sendRawTransaction with 1s delay between attempts
- Confirm timeout doesn't mean failure — log warning, continue

## PM2 Deployment

```bash
cd ~/mona-workspace/charon-sniper
pm2 start ecosystem.config.cjs
pm2 save
```

## Notification Testing

Before going LIVE, test notification format to topic 1309:

```bash
# Test buy notification
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d chat_id="-1003899936547" \
  -d message_thread_id="1309" \
  -d text="🔫 SNIPER BUY: TEST\n💰 Deploy: 0.04 SOL\n📊 Holders: 1,500\n💎 MCap: \$200,000" \
  -d parse_mode="HTML"
```

User wants to see the EXACT format before committing to LIVE. Always offer a test notification when user asks about live alerts.

## Config Adjustment When Losing Money (DRY RUN)

**User Rule:** "minus semua gimana pas live malah habisin duit" — When DRY RUN shows consistent losses, ADJUST CONFIG before going LIVE.

**Symptoms:**
- 0% win rate over 3+ days
- All trades hitting SL (-15%)
- Daily loss limit reached consistently

**Adjustment Strategy (Jun 2026 - tested):**
```json
{
  "exit": {
    "stopLossPct": -20,        // Was -15%, give more room
    "takeProfitPct": 30,       // Keep realistic
    "trailingTriggerPct": 12,
    "trailingDropPct": 8
  },
  "trade": {
    "maxDailyTrades": 5,       // Was 8, reduce overtrading
    "cooldownMs": 300000       // Was 180000 (3m), now 5m
  },
  "filter": {
    "minOrganicScore": 50,     // Was 40, stricter quality
    "minHolders": 300,         // Was 200, more established tokens
    "minVolume24h": 30000,     // Was 20000, higher activity required
    "minBuyRatio": 0.90        // Was 0.85, stronger buy pressure
  }
}
```

**Expected Results:**
- Fewer trades per day (quality over quantity)
- SL hit less often (more room for recovery)
- Higher win rate (stricter filters = better tokens)

**Monitor for 2-3 days after adjustment before deciding on LIVE.**

## Pitfalls

- **Charon API auth:** Use `x-api-key` header, NOT `Authorization: Bearer`. Bearer returns 401.
- **Charon rate limits:** Minimum 30s between requests. Cache responses.
- **DRY RUN daily loss limit is WORKING AS DESIGNED (confirmed Jun9):** When multiple positions hit SL simultaneously, cumulative loss can exceed `maxDailyLossSol`. Once hit, the bot enters a 30-second retry loop logging "Daily loss limit reached" until the next UTC day. **This is NOT a bug** — it's a safety guard. Three responses: (a) wait for midnight UTC reset, (b) increase `maxDailyLossSol` in config + `pm2 restart`, (c) improve filter to reduce SL frequency. **DO NOT try to "fix" the retry loop.**
- **Simultaneous SL hits indicate filter weakness (Jun9 DRY RUN):** 3 positions (LIFE, GO, scooby) opened within 5 minutes, all hit -15% SL. Basic filter (holders + mcap + volume) is insufficient — the 7-layer filter (organicScore > 30, buyRatio, momentum, devHoldings, sniperCount, fee_tvl, liquidityChange) is REQUIRED for current market conditions.
- **Jupiter slippage:** Solana memecoins are extremely volatile. 5% slippage may still fail on low-liquidity tokens. Increase for very new tokens.
- **Priority fees:** Without priority fees, transactions may be dropped during high congestion. Always include priority fee for sniping.
- **Token quality vs speed tradeoff:** Higher quality filters = fewer trades but better win rate. Lower filters = more trades but more losses. Tune based on DRY RUN results.
- **Two separate systems:** Charon Sniper (buy/sell tokens) and Meridian DLMM (liquidity provider) are DIFFERENT bots with DIFFERENT strategies. Do NOT merge their dashboards or configs. They share the Charon API as a signal source, but execution and management are completely different.
- **Dashboard port conflict:** Charon Sniper uses port 3458, Meridian DLMM uses port 3457. Don't mix them up. If old process holds the port, `kill -9 $(lsof -t -i:3456)` then restart.
- **Broken position (entryPrice=0) — REJECT, don't fabricate (Jun16 fix):** When Jupiter quote fails AND `sig?.priceUsd` is missing/invalid, the DRY_RUN fallback in `jupiter-executor.js` was computing `Math.round(solAmount * 1e9)` (e.g. 0.2 SOL → 200,000,000 tokens, price=1e-9). This creates a phantom position with `entryPrice ≈ 0` that blocks all new buys ("Max positions reached 3/3") and corrupts PnL. **Symptom variants observed Jun16:** (a) `entryPrice=0` and `solInvested=0`, (b) `entryPrice=1e-12` and `solInvested=None` and `tokenAmount=65B`, (c) `entryPrice=0.0001` and `solInvested=0`. All block slots. **Correct fix — REJECT, never fall back to garbage:**
  1. **`modules/jupiter-executor.js` `buyToken()` DRY_RUN branch:** if `!quote && !(sig?.priceUsd > 0)` → `return { success: false, error: "no_quote_no_price" }`. After computing `outAmount`/`price`, validate `outAmount > 0 && price > 0 && isFinite(...)` → otherwise REJECT with `error: "invalid_buy_result"`. Never write a position without a real price.
  2. **`modules/position-manager.js` `openPosition()` guard:** at the top, `if (!buyResult || buyResult.price <= 0 || buyResult.amountIn <= 0 || buyResult.amountOut <= 0) return null;` — belt-and-suspenders, even if the executor's fix is in place.
  3. **`index.js` caller null check:** after `const pos = openPosition(...)`, if `!pos` → log `⚠️ ${pick.symbol} phantom rejected — skipping cycle`, set `_running = false; return;` (NOT `continue` — there's no surrounding for loop). Without this, `pos.qualityScore = ...` crashes the cycle.
  4. **Cleanup script for existing data:** see `references/phantom-position-guard.md` for the 4-line python one-liner that filters open positions by `entryPrice > 0 && solInvested > 0 && tokenAmount > 0`. Always backup `data/positions.json` before running.
  5. **Restore signal propagation:** make sure `index.js` calls `buyToken(pick.mint, deploy, config, pick)` — the `pick` (signal) is the source of `sig.priceUsd`. Removing the 4th arg breaks the fallback chain.
  See `references/phantom-position-guard.md` for the complete before/after code.
- **maxDailyLossSol must scale to wallet size (Jun16 finding):** Old `config.json` shipped with `maxDailyLossSol: 1.0` on a 5 SOL wallet — that allows losing 20% of capital PER DAY before tripping. Combined with `maxDailyTrades: 99` and no per-trade cap enforcement, the bot will happily blow through the entire wallet in a single bad market day. **Rule of thumb:** `maxDailyLossSol ≤ 2-3% of wallet` (0.10-0.15 SOL on a 5 SOL wallet, 0.05 SOL on 0.3-0.4 SOL wallet). For per-trade cap: `maxDailyLossSol / maxDailyTrades` should equal the per-trade SL amount. Example: 0.05 SOL daily loss ÷ 8 daily trades = 0.006 SOL/trade max → at 0.04 SOL deploy × 15% SL = 0.006 SOL ✓. **Symptom:** if you ever see `maxDailyLossSol > 5% of wallet`, the cap is functionally useless.
- **Exit checker skips positions when Jupiter returns null (CRITICAL — FIXED Jun8):** Jupiter price API returns null for most micro-cap tokens. If `checkExits()` does `if (!currentPrice) continue;` BEFORE checking max hold time, positions are NEVER checked for exits and NEVER closed. **Confirmed fix (Jun8):** (1) move max hold time check FIRST (before price fetch) — this ensures positions always get checked regardless of price availability, (2) add DRY RUN fallback: simulate price movement with `entryPrice * (1 + drift + noise)` using `sin(ageMin * 0.1) * 0.15 + (random - 0.45) * 0.08`, (3) log every position check with `📊 SYMBOL: PnL X% | Peak Y% | Hold Zm`. After fix, all 3 positions showed correct peak tracking (GO: +18.9%, LIFE: +15.0%, scooby: +19.0%). See `references/exit-checker-fix.md` for full before/after code.
- **Dashboard sync verification:** After any bot restart or config change, ALWAYS verify file↔API↔bot are in sync: (1) `cat data/positions.json | python3 -c "..."`, (2) `curl localhost:PORT/api/positions`, (3) compare. If they don't match, restart the dashboard server.
- **Dashboard links must be pinned in topic:** User wants dashboard links PINNED in respective Telegram topics (1309 for Charon, 947 for Meridian). After sending the link message, immediately pin it: `curl /pinChatMessage`. Unpinned links get buried in chat history.
- **Fabriq PnL button in dashboard header:** Add a styled orange button linking to `https://fabriq.trade/portfolio` (BASE URL — NOT with wallet address appended, as fabriq is a SPA that doesn't support deep linking). Use `title="Search wallet: WALLET_ADDRESS"` for easy copy-paste. Pattern: `<a href="https://fabriq.trade/portfolio" target="_blank" title="Search wallet: WALLET" style="background:#FF4500;color:#fff;padding:4px 12px;border-radius:6px;font-size:12px;text-decoration:none;font-weight:600;">📊 Fabriq PnL</a>`. fabriq.trade has NO public API (Cloudflare-protected, placeholder OpenAPI spec), but provides excellent PnL analytics (calendar, cumulative chart, win rate, profit factor) via their in-house Meteora indexer. After adding button, restart dashboard and recreate tunnel.
- **Two separate bots, two separate topics:** Charon Sniper → topic 1309. Meridian DLMM → topic 947. NEVER send Charon updates to topic 947 or vice versa. Each system has its own dashboard, its own topic, its own notification channel.
- **Break-even & partial exit NOT IMPLEMENTED by default (CRITICAL):** The config fields `exit.breakEven.*` and `exit.partialExit.*` exist but the exit checker in `position-manager.js` does NOT use them. You MUST add the code yourself. See `references/exit-strategy-implementation.md` for the full implementation. Without this, break-even and partial exit configs are silently ignored.
- **Position file race condition in checkExits (CRITICAL — FIXED Jun8):** `checkExits()` loads positions at start, processes exits (which calls `closePosition()` → `savePositions()`), then at the END calls `savePositions(data)` with the OLD data — overwriting all close changes. **Fix:** After executing exits, reload positions with `loadPositions()`, copy peak/breakEven data from in-memory positions to fresh data, then save. See `references/position-persistence-fix.md` for code. **V2 fix (Jun8):** The initial fix only copied peak/breakEven data but NOT partial exit state. When partial exit sold 35% of tokens, the tokenAmount change wasn't persisted. **Always copy ALL mutable fields:** peakPrice, peakPct, breakEvenLocked, lockedPct, partialExited, partialExitPct, partialExitSol, partialExitPrice, tokenAmount, partialExitTriggered.
- **DRY RUN sell returns 0 SOL when price unavailable (CRITICAL — FIXED Jun8):** `sellToken()` in DRY RUN mode calls `getTokenPrice(mint)` — for micro-cap tokens this returns null → `solValue = 0` → PnL = -100%. This triggers daily loss limit immediately. **Fix v1 (broken):** `decayFactor = 0.7 + random * 0.2` with `tokenAmount * decayFactor * 1e-9` — produced absurdly small values (~5e-8 SOL) because `* 1e-9` is wrong when `getTokenPrice()` already returns price per raw unit. **Fix v2 (better):** Use deploy amount as base: `solValue = (config?.trade?.deployAmountSol || 0.04) * 0.85`. Produces realistic values (~0.034 SOL). **Fix v3 (best — current):** Use Jupiter quote API for sell simulation: `getQuote(mint, SOL_MINT, tokenAmount, slippageBps)` → `solValue = Number(quote.outAmount) / 1e9`. Falls back to `getTokenPrice()` (quote-based, no `* 1e-9`), then to deploy amount estimate. The `* 1e-9` multiplication bug is a COMMON mistake — `getTokenPrice()` returns price per raw token unit in SOL, so `tokenAmount * price` is already the SOL value. Adding `* 1e-9` makes it 1 billion times too small. **Never multiply by 1e-9 when using quote-based prices.**
- **Config key mismatch — maxPositions:** Code reads `config.trade.maxPositions` (NOT `maxOpenPositions`). If you write `maxOpenPositions` in config.json, the bot logs `Max positions: undefined` and the position count check fails silently.
- **Config key mismatch — `filter` vs `filters`:** Code reads `config.filter` (SINGULAR) in `token-filter.js` line 15: `const f = config.filter`. If you write `filters` (plural) in config.json, `f` is `undefined` and EVERY filter check crashes with `Cannot read properties of undefined (reading 'blockedSymbols')`. The bot will crash-loop on every cycle. Always use `"filter"` (singular) as the top-level key.
- **`blockedSymbols` required in config:** The token filter checks `f.blockedSymbols?.includes(sym)` (line 43 of token-filter.js) in ADDITION to `f.blockedMints`. You MUST include both in config.json → `filter` section: `"blockedSymbols": ["USDC", "USDT", "SOL", "WSOL", "MSOL"]` AND `"blockedMints": ["EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", ...]`. Without `blockedSymbols`, the bot may try to snipe SOL/USDC/USDT wrapped tokens.
- **Charon API key must be in config.json:** The Charon API key is read from `config.charon.apiKey` (NOT from .env). Set it in `config.json` → `charon.apiKey`. Without this, the API returns HTTP 401 on every request and no signals are fetched. The key is the same one from CHARON_API_KEY in Meridian's .env — they share the same Charon account.
- **localhost.run tunnel:** Never pipe through `head -20` — it truncates the URL output. Run SSH directly: `ssh -o StrictHostKeyChecking=no -R 80:localhost:PORT nokey@localhost.run`. URL appears after "authenticated as anonymous user" line. **Zombie cleanup:** Old SSH tunnel processes accumulate across sessions. Before creating new tunnels, kill all existing: `pkill -f "localhost.run" 2>/dev/null`. Verify with `ps aux | grep localhost.run | grep -v grep | wc -l`. If count > expected, kill all and recreate. On Jun8, 4 tunnel processes were running when only 2 were needed. Each reconnect generates a NEW URL — old URLs become invalid immediately.
- **Cron delivery target:** `deliver='origin'` sends to main chat. ALL Charon Sniper cron jobs MUST use explicit `deliver='telegram:CHAT_ID:THREAD_ID'` (e.g., `telegram:-1003899936547:1309`).
- **Telegram botToken config:** Charon Sniper uses its OWN `config.json` telegram section (not Meridian's .env). Set `botToken` in `config.json` → `telegram.botToken` for notifications to work.
- **Calendar API field name mismatch (CRITICAL — FIXED Jun8):** `daily-pnl.json` uses `totalPnlSol`/`totalTrades` but the calendar frontend expects `pnlSol`/`trades`. In `server.js` calendar endpoint, when merging daily data: `if (!byDate[d.date]) byDate[d.date] = d;` copies the RAW object with wrong field names → calendar shows "undefined" for PnL and trade counts. **Fix:** Map fields explicitly: `byDate[d.date] = { date: d.date, pnlSol: d.totalPnlSol || d.pnlSol || 0, trades: d.totalTrades || d.trades || 0, wins: d.wins || 0, losses: d.losses || 0, tokens: d.tokens || [] };`. After fix, calendar correctly shows `0 SOL, 0T 0W` instead of `undefinedT 0W`. See `references/calendar-field-mismatch-fix.md` for full details.
- **Dashboard refresh after bot restart:** After restarting the bot, the dashboard may show stale data or "No open positions" even when positions exist. This is because the frontend caches the last API response. Always tell the user to **refresh the page** (pull-down on mobile) after any bot restart or config change. The dashboard auto-refreshes every 15 seconds via `setInterval(loadAll, 15000)` but the initial load may be stale.
- **Overtrading detection (Jun16 finding):** When `maxDailyTrades` is left at the default `99` (effectively unlimited) and the filter pass rate is high, the bot opens 20-30 positions in 24 hours. Observed: 25 trades in 1 day, 0W/19L on the worst day, 5W/20L overall. **The PnL is negative even with R:R 1:2.85** because WR is only 20%. **Mandatory cap:** `maxDailyTrades: 5-8` for sniper bots. Also: if `closed.length - 7 days ago` shows > 15 trades/day on average, the filter is too loose. Tighten `minOrganicScore`, `minHolders`, `minVolume24h`, `minBuyRatio` before going LIVE.
- **Cooldown too tight causes artificial re-entries (Jun16 finding):** `cooldownMs: 30000` (30s) means the bot can re-enter the same volatility regime every 30s. Combined with a 60-min `maxHoldMinutes`, that's 120 different positions per day if signals flood. **Rule:** `cooldownMs ≥ 180000` (3 min) for micro-cap sniping. The market needs time to settle between entries — fast re-entries are picking up noise, not signal.
- **Exit strategy triggers must match REAL token behavior (CRITICAL — Jun8/Jun16 lesson):** The default config values (break-even +10%, partial exit +25%, trailing +20%) are set for tokens that pump +30-50%. But Charon signals are micro-cap tokens that typically peak at +15-20%. With the old defaults: break-even triggers at +10% and locks at +2%, then when price peaks at +18% and drops, it sells at +2% instead of the +10% trailing would have caught. **Partial exit at +25% NEVER triggers** because peaks are ~+18%. **Trailing at +20% NEVER triggers** for the same reason. **ALWAYS audit config against observed data before going LIVE.** Run DRY RUN for 1-2 days, collect peak data, then set triggers BELOW the typical peak. Rule of thumb: trailing trigger should be ~60-70% of observed average peak. If average peak is +18%, set trailing trigger to +12%. **Jun16 worst case observed in production:** break-even trigger 3% + lockAt 1% + trailing trigger 5% + drop 3% + maxHold 60min → tokens pumped to +15-20%, break-even triggered at +3% locked at +1%, then dumped, sold at -2% to -9% (stolen upside). Break-even lock of +1% is THE single most destructive config value — tokens that should net +10% get sold at -3%.
- **Jupiter API v1 migration (CRITICAL — Jun 2026):** The old `api.jup.ag/quote` endpoint returns 404. Jupiter moved to `api.jup.ag/swap/v1/quote` and `api.jup.ag/swap/v1/swap`. The old `quote-api.jup.ag/v6/swap` also fails. **Additionally, the price API (`/price/v2`) returns 404.** Use quote-based price calculation as fallback: `0.001 SOL → tokens → price per token = lamports / tokens / 1e9`. If building a new bot or updating an old one, ALL Jupiter URLs must use the `/swap/v1/` prefix. Test with: `curl -s 'https://api.jup.ag/swap/v1/quote?inputMint=So11111111111111111111111111111111111111112&outputMint=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v&amount=1000000&slippageBps=500'` — should return `outAmount` field.
- **Jupiter swap returns `swapTransaction` NOT `txid`:** The old code assumed Jupiter returns `txid` directly. WRONG. Jupiter returns `swapTransaction` (base64-encoded VersionedTransaction) that must be: (1) deserialized with `VersionedTransaction.deserialize()`, (2) signed with `keypair`, (3) sent via `sendRawTransaction()`, (4) confirmed via `confirmTransaction()`. Without these steps, no actual on-chain transaction happens. The bot will appear to "buy" but nothing executes.
- **ANTI-CHASE FILTER (CRITICAL — Jun 16 2026 lesson):** Default `minPriceChange5m: -3` is NOT enough. With 61% of Charon signals having 5m momentum between 0 and +5%, the bot happily buys tokens already pumping — and becomes exit liquidity when early buyers dump. The 5m momentum field is a LAGGING indicator; by the time it shows positive, the pump is mid-stage. **Fix:** add `maxPriceChange5m: 3` to reject entries where 5m momentum is already > +3%. Combined with `minPriceChange5m: -8` (allow slight pullback / mean-reversion), this cuts losing entries dramatically. Validated: when ALL 8 losing trades had 5m +4% to +22% at entry, adding `maxPriceChange5m: 3` would have rejected 100% of them. The filter must include both bounds to work.
- **DATA-DRIVEN FILTER CALIBRATION (CRITICAL — workflow):** Stop guessing filter thresholds. The right workflow when losses cluster:
  1. `curl -s https://api.thecharon.xyz/api/signals -H "x-api-key: ..." > /tmp/charon-snapshot.json` (cache 100 signals)
  2. Run distribution analysis on `trending.stats5m.priceChange`, `ageMs`, `trending.organicScore`, `trending.stats24h.numNetBuyers`, `graduated.devHoldingsPercent`, `graduated.sniperCount`, etc. (bucket counts, percentile cuts)
  3. Set filter thresholds based on actual data: e.g. if 61% of signals have 5m < +5%, `maxPriceChange5m: 3` is the natural anti-chase. If 35% are 15-60m old, `maxAgeMinutes: 180` is the natural fresh window.
  4. Test with `node -e "import('./modules/token-filter.js').then(({filterSignals}) => filterSignals(...))"` — measure pass rate. Target 1-5% (10-30 trades/day on 100 signals/refresh × ~14 refreshes/hour). 0% = too strict; 30%+ = too loose.
  5. Document thresholds with `_comment` field in config.json so user can read/tune.
  6. See `references/data-driven-filter-calibration.md` for the full workflow with template.
- **daily-pnl.json format (BUG — Jun 16 2026):** The pnl-tracker.js `saveDailySnapshot()` reads `data.days.findIndex(d => d.date === pnl.date)`. If `data.days` is undefined (because file is `{}` after a manual reset), the cycle crashes with `Cannot read properties of undefined (reading 'findIndex')`. **Always reset daily-pnl.json as `{"days": []}`** — never `{}`, never `null`, never a bare array. Symptom: bot opens position, then `[MAIN] ERROR: Cycle error: Cannot read properties of undefined (reading 'findIndex')` — and the next cycle also fails until file is fixed.
- **PnL record mismatch with partial sells (BUG — Jun 16 2026, known):** `closePosition()` computes `pnlPct = (exitSol - entrySol) / entrySol` but `exitReason` shows `STOP LOSS -16.9%` (the actual pnlPct at exit time). These two values diverge when TP levels fired before SL — e.g. JOE: peak +34.3%, TP1 hit (sold 30% at +20%), then SL fired at -16.9% on remaining 70%, final pnlPct = -43% (combined TP1 profit + SL loss on remainder). The recorded pnlPct is the COMBINED exit value, not the SL-trigger pnlPct. Not a bug per se, but downstream consumers (Telegram alerts, dashboard) display this inconsistently. Workaround: parse `exitReason` for the trigger pct when displaying, or compute per-leg PnL separately. Track as a known issue until position-manager is refactored.
- **TP LADDER + TRAILING COMBO (WIN PATTERN — Jun 16 2026):** The TP ladder `[20/30, 40/35, 70/35]` + trailing +15% drop -10% combo WORKS for moonshots. Example: p (entry 5m +1.0%, organic 67, buyRatio 5.1) → peak +329.5% → TP1 sold 30% at +20%, TP2 sold 35% at +40%, TP3 sold 35% at +70%, then trailing sold remaining 5% on -12.1% drop from peak → final +139.91% / +0.14 SOL. Without TP ladder, single TP at +30% would have sold 100% and missed the 4x. Without trailing, the last 5% would have ridden back to entry and locked in less. **Both are needed.**
- **BUT: TP ladder 30/35/35 leaves 70% vulnerable to dump (CRITICAL — Jun 16 2026):** After TP1 fires at +20% (sells 30%), the remaining 70% has NO safety net if price dumps 30-50% before TP2. Observed: JOE peak +34.3% but closed -43% (TP1 profit wiped by remaining 70% SL hit). **Tighter TP1 (40% at +15%) OR more aggressive trailing (drop -7% from peak) reduces this risk.** Rule of thumb for micro-cap meme entries: TP1 should sell at least 40% on first +15-20% trigger, not 30%.
- **MAX AGE WINDOW IS A KEY LEVER:** Too tight (60-90 min) = 0 trades (pass rate 0%); too loose (12h) = catches post-pump dumps (losers from 1-6h age). Sweet spot empirically 120-180 minutes for current Charon signal distribution. If pass rate is 0% and most rejections are "too old", relax `maxAgeMinutes`. If pass rate > 10% and most losers are >2h old, tighten.
- **RESET & ACTIVATE PATTERN (workflow — Jun 16 2026):** When Hexa says "aktifkan" / "reset limit" / bot stuck on daily limit, the clean reset is:
  1. Backup: `cp data/positions.json data/positions-archive-DATE-full.json`
  2. Archive closed positions (don't lose PnL history)
  3. Reset positions.json: `open=[], closed=[]`
  4. Reset daily-pnl.json: `{"days": []}` (NOT `{}`)
  5. Reset sim-balance.json to initial_sol, archive history
  6. **Restart bot** (kill old PID, start fresh) — old process holds in-memory state (traded set, last buy time) and will keep reporting stale daily limit even after file reset. Just clearing files is not enough; must restart.
  7. Verify next cycle opens position (not just "Daily trade limit reached").
- **Filter test before deploying new config:** Always run a node one-liner against a fresh `/tmp/charon-snapshot.json` to measure pass rate BEFORE restarting the bot. `node -e "import('./modules/token-filter.js').then(({filterSignals}) => { const d=JSON.parse(require('fs').readFileSync('/tmp/charon-snapshot.json')); const r=filterSignals(d.signals, JSON.parse(require('fs').readFileSync('config.json')), []); console.log('Pass:', r.qualifying.length, '/', d.signals.length); if (r.qualifying[0]) console.log('Top:', r.qualifying[0].symbol, 'score', r.qualifying[0].qualityScore); })"` — if pass rate is 0%, loosen; if 30%+, tighten.
- **Phantom position DOUBLE GUARD (Jun 2026 — CRITICAL):** Phantom positions (entryPrice=0) appear when Jupiter quote fails AND `sig.priceUsd` is missing. Old code fallback: `outAmount = quote ? quote.outAmount : (sig.priceUsd > 0 ? solAmount/sig.priceUsd : solAmount * 1e9)` — this last branch creates a bogus 2e8 token count with `price = solAmount/outAmount ≈ 1e-9`. Bot thinks it bought something but it's garbage. **Fix at TWO layers:** (1) In `jupiter-executor.js buyToken`, REJECT (return success:false) if both quote AND sig.priceUsd are missing/invalid; (2) In `position-manager.js openPosition`, return null if `buyResult.price <= 0 || amountIn <= 0 || amountOut <= 0`. The double guard is belt-and-suspenders — first guard prevents creation, second guard prevents persistence if first is bypassed. Then in `index.js`, check `if (!pos)` and `return` (NOT `continue` — that's illegal outside a for loop).
- **Logger.js is console-only (Jun 2026):** The built-in `logger.js` only does `console.log()` — there is NO file output. When the bot is started with `nohup ... > /tmp/bot.log 2>&1 &`, log lines are captured via stdout/stderr redirect, but Node.js stdout buffering can delay writes. New `cycle()` output may not appear in the log file for 1-2 cycles even though `data/positions.json` IS being updated. **Symptom:** "Bot seems stuck, no new log lines, but `positions.json` mtime is fresh." **Fix:** Either (a) write a custom logger that `fs.appendFileSync`s per line, (b) force flush via `process.stdout.write` + `process.stdout.cork/uncork`, or (c) don't rely on log file — monitor `data/positions.json` mtime + `data/simulated-balance.json` instead. This is environmental, not a bug — the bot IS working, the log is just buffered.
- **Daily trade limit reset pattern (Jun 2026):** When the bot hits `maxDailyTrades` and user wants to reset without losing history, **DO NOT** clear `data/positions.json["closed"]` directly. Instead, archive today's trades: (1) split `closed` array into `closed_today` and `closed_other` by `closedAt.startsWith(today)`, (2) write `closed_today` to `data/positions-archive-YYYY-MM-DD.json` with date/count/totalPnlSol metadata, (3) keep only `closed_other` in `data/positions.json`, (4) drop today's entry from `data/daily-pnl.json`. This preserves the loss history (so the user can see what happened) while resetting the counter. Bot auto-picks up at next cycle. The archived JSON is what the user wants to see in Telegram reports — "moved N closed-today trades to archive-X.json, total PnL: -X.XX SOL".
- **Anti-chase momentum filter is THE WIN (Jun 2026):** Across 100 Charon signals, 61% had 5m momentum in -5% to +5% (the "neutral zone"). The v2 filter (minOrganic 30, minBuyRatio 0.85) let through 36/100 — too loose. ALL 8 losing trades had positive 5m momentum (+4% to +22%) at entry, meaning the bot entered AFTER the early pump and was exit liquidity when it dumped. The fix: add `maxPriceChange5m: 3` (reject if 5m > +3%). Combined with TP ladder exit (20/30, 40/35, 70/35), this captured a +139.91% winner on token "p" (peak +329.5%, all 3 TP levels hit, trailing exit on remaining 5%). The pattern: don't chase, let the runner come to you via TP ladder.
- **TP ladder > single TP (Jun 2026):** A single take profit at +25% or +30% misses runners that go to 4x+. The TP ladder pattern (`takeProfitLevels: [{triggerPct:20,sellPct:30},{triggerPct:40,sellPct:35},{triggerPct:70,sellPct:35}]`) splits the position across three profit levels, locking gains at each. The remaining 5-10% rides with trailing. Backtested on token "p" (Jun 16 2026): single TP at +30% would have captured +0.030 SOL. TP ladder + trailing captured +0.140 SOL — a 4.7x improvement on the same token. The pattern is already implemented in `position-manager.js checkExits` (see `tpLevelsHit`, `tpSoldTotal`, `originalTokenAmount` fields) — just configure the levels in config.json.
- **Data-driven filter tuning workflow (Jun 2026):** When a filter is producing consistent losses, do NOT just tweak numbers by feel. Run a 5-step analysis: (1) `curl https://api.thecharon.xyz/api/signals` with the API key and snapshot to `/tmp/charon-snapshot.json`, (2) bucket the 100 signals by each filter dimension (5m momentum, age, organic, buyRatio, etc.) and show distribution, (3) run the new filter logic against the snapshot using `node -e "import('./modules/token-filter.js').then(...)"`, (4) check the qualifying tokens — do they match the profile you want? (5) tune until pass rate is 1-5% AND the qualifying tokens look like real winners. The `node -e` invocation pattern lets you test filter changes against real data WITHOUT restarting the bot. See `references/filter-v3-data-driven.md` for the full 100-signal analysis.
- **Never put private keys in config.json:** Private keys go in `.env` ONLY. Config files get logged, displayed in dashboards, and shared. `.env` is gitignored and never exposed. Pattern: `.env` has `WALLET_PRIVATE_KEY=base58...`, code loads it at startup via manual parser (no dotenv needed).
- **bs58 v5 import shape (GOTCHA — 3rd-party Solana bots, Jun 2026):** Different bs58 versions have different default export shapes:
  - v4 (`bs58@^4.0.0`): `const bs58 = require('bs58'); bs58.encode(...)` works directly. Some old code also uses `import bs58 from "bs58"`.
  - v5 (`bs58@^5.0.0`, ESM-first): `const bs58 = require('bs58'); bs58.encode(...)` works (default export points to the object). But `const bs58 = require('bs58').default;` is `undefined` and crashes with `Cannot read properties of undefined (reading 'encode')`.
  - Always `console.log(typeof bs58.encode)` after require to verify. If a bot fails with "Cannot read properties of undefined" right after auth, suspect bs58 version mismatch.
  - Symptom in owntown-farming-bot v24.0: `❌ Auth failed: Cannot read properties of undefined (reading 'decode')` → bs58 v5 + wrong import.
- **Solana keypair JSON format mismatch (GOTCHA — deploying 3rd-party Solana bots, Jun 2026):** Different tools expect different formats for the same private key:
  - **Solana CLI** (`solana-keygen new`): JSON array of 64 numbers: `[37, 248, 211, 214, ...]`
  - **Most 3rd-party bots (owntown, etc.)**: JSON object with `private_key` field: `{"private_key": "m2tRz8i1Gm..."}` (base58 of 64 bytes)
  - **Some Phantom exports**: JSON array of 64 numbers
  - Conversion recipe: read array → `new Uint8Array(arr)` → `bs58.encode(bytes)` → wrap in `{private_key: b58}`. See template below.
  - Symptom of mismatch: bot reads wallet, gets `undefined.private_key` or wrong-length secret, then auth signature fails with `Expected String` or returns wrong pubkey.
- **Hardcoded wallet/player ID in 3rd-party bot repos (GOTCHA, Jun 2026):** Many Solana game/DeFi bots on GitHub have `const WALLET_ADDR = '...'; const MY_PLAYER_ID = '...';` hardcoded for the original author. Before deploying, refactor to env vars:
  - Replace `const WALLET_ADDR = '5zkF...'` with `const WALLET_ADDR = process.env.WALLET_ADDRESS || '';`
  - Replace `const WALLET_FILE = '/root/.hermes/...'` with `const WALLET_FILE = process.env.WALLET_KEYPAIR_FILE || '/home/ubuntu/.hermes/...';` (note: `/root/` paths break on non-root VPS — Hye-Jin runs as `ubuntu`)
  - Replace `const MY_PLAYER_ID = '39ebfc6a-...'` with `const MY_PLAYER_ID = process.env.MY_PLAYER_ID || '';` (set after first auth when player is auto-registered)
  - Add FATAL validation block AFTER `log()` function is defined (otherwise ReferenceError on init — `log()` called before declaration):
    ```js
    if (!WALLET_ADDR || !fs.existsSync(WALLET_FILE)) {
      log('FATAL: WALLET_ADDRESS or wallet keypair file missing!');
      process.exit(1);
    }
    ```
  - Add inline `.env` loader at the top so the user doesn't need `dotenv` package:
    ```js
    try { fs.readFileSync('.env', 'utf-8').split('\n').forEach(line => {
      const m = line.match(/^([A-Z_]+)=(.*)$/);
      if (m && !process.env[m[1]]) process.env[m[1]] = m[2].trim();
    }); } catch {}
    ```
  - **Token-entry-fee pattern:** Many Solana game bots require holding a minimum amount of their own token (e.g., 5000 OTWN to enter "Player Mode") before the auth returns success. Test auth FIRST with curl/node-direct before troubleshooting signature/wallet issues — the error message will name the token and required amount. Example: `{"error":"INSUFFICIENT_OTWN","message":"Hold at least 5000 $OTWN to enter Player Mode","balance":0,"required":5000}` → wallet signature WORKED, but the wallet doesn't hold the entry token.
- **Watch + auto-swap pattern for token-gated bots (Jun 2026):** When a bot refuses to start until wallet holds N tokens, build a self-contained watcher that:
  1. Polls the wallet's SOL + token balance every 30s via Helius RPC
  2. When SOL ≥ 0.01 AND tokens < required → auto-swap via Jupiter `/swap/v1/swap` (sign with wallet's keypair, send via Helius RPC)
  3. When tokens ≥ required → `pm2 start <bot> --name <bot>`
  4. Reserves 0.005 SOL for gas before swap
  5. Logs to `/tmp/<bot>-auto.log`
  6. Pattern: `pm2 start <watch-script> --name <bot>-watcher` runs in background
  7. Alternative: user can skip auto-swap by sending the required token directly to the wallet (e.g., transfer 5000 OTWN tokens via Phantom). Watcher detects either path.
  8. Full templates: `templates/solana-bot-watcher.sh` (bash loop) + `templates/solana-bot-autoswap.js` (Jupiter swap).
- **PM2 + Node.js module cache trap (Jun 2026):** Editing a JS source file does NOT reload it in a running PM2 Node.js process. The process has the OLD code in memory. `pm2 restart <app>` sends SIGTERM, Node exits gracefully — but if the old process holds the port or there's a hung module import, the new process may not bind correctly.
  - **Hard-kill pattern when restart doesn't pick up changes:**
    ```bash
    pkill -9 -f "node.*server.js" 2>&1   # SIGKILL all matching processes
    sleep 3
    pm2 delete <app> 2>/dev/null
    pm2 start server.js --name <app>
    sleep 5
    lsof -i :PORT | grep LISTEN          # verify new PID is listening
    ```
  - **Test direct vs API diagnostic:** If API returns wrong data but running the underlying script directly returns correct data, the bug is in the Node.js side (cache, args, old module) — hard-kill and restart. If both return wrong data, the bug is in the script itself.
  - **Cache poisoning compound effect:** Many bots (anime scrapers, game bots) cache empty/failed results. Hard-kill alone doesn't clear the cache file. Always `rm -f <cache-path>/*.json` AND hard-kill AND restart before re-testing.
- **LIVE mode balance guard:** Every cycle, check `getSolBalance()` against `minBalanceSol`. If below, pause 24h (not just skip cycle — prevent retry loops). Also check `balance < deployAmountSol + 0.01` before attempting buy (deploy + gas buffer). Without this, bot tries to buy → sendRawTransaction fails with insufficient lamports → wastes cycles.
- **Charon API has 18 fields per signal, not 13 (Jun8):** The documented fields above are the BASIC ones. The actual API returns `trending` (with `organicScore`, `buys/sells`, `stats5m.priceChange`, `stats24h.numNetBuyers`, `liquidityChange`, `holderChange`), `graduated` (with `devHoldingsPercent`, `sniperCount`, `topHoldersPercent`), `volume5m`, and `feeClaim`. These fields are CRITICAL for quality filtering. Without them, the filter is basically random — holders and mcap alone don't predict price movement. See `references/charon-api-fields.md` and `references/advanced-token-filter.md`.
- **Token filter v2 (7-layer) dramatically improves win rate:** Basic filter had 50% pass rate (25/50 signals). Advanced filter with organic score, buy ratio, momentum, dev holdings, and sniper count drops to 2% pass rate (1/50). The one that passes is genuinely high quality — e.g., Teletubby: organic 74, buyRatio 3.3x, 5m +11.6%, 1039 net buyers. See `references/advanced-token-filter.md` for full scoring formula.
- **Token dedup persistence (FIXED Jun9):** The `_traded` Set in `token-filter.js` was in-memory only — lost on bot restart, causing the same tokens to be sniped repeatedly (e.g., LIFE sniped 3x, GO 2x). **Fix:** Persist to `data/traded.json` on disk. On startup, load from file. On `markTraded()`, save to file. Use `path.resolve("data", "traded.json")` (NOT `__dirname` — ES module gotcha). See code in `modules/token-filter.js` lines 18-45.
- **ES module `__dirname` not available (Jun9):** The charon-sniper project uses `"type": "module"` in package.json. `__dirname` is NOT defined in ES module scope. Using it throws `ReferenceError: __dirname is not defined in ES module scope`. **Fix:** Either (a) use `import { fileURLToPath } from "url"; const __filename = fileURLToPath(import.meta.url); const __dirname = path.dirname(__filename);` or (b) simpler: use `path.resolve("relative/path")` which resolves from CWD. Option (b) is preferred for files relative to project root.
- **Cloudflare quick tunnel for dashboard access (Jun9):** `cloudflared tunnel --url http://localhost:PORT --no-autoupdate` creates a public URL (e.g., `https://random-words.trycloudflare.com`). No account needed. Tunnel runs in background. URL changes every restart. For 9Router dashboard: `cloudflared tunnel --url http://localhost:20128`.
- **LIVE mode infrastructure checklist:** (1) Create `.env` with `WALLET_PRIVATE_KEY` (base58) + `HELIUS_API_KEY`, (2) `initWallet()` at startup using `Keypair.fromSecretKey(bs58.decode(key))`, (3) `Connection` with `commitment: "confirmed"` + `confirmTransactionInitialTimeout: 30000`, (4) Balance check at startup AND every cycle, (5) 3x retry on `sendRawTransaction` with 1s delay, (6) `skipPreflight: true` for faster execution, (7) Confirm timeout = warning, not failure (tx may still succeed).

## Deploying 3rd-Party Solana Bots (Jun 2026 pattern)

When cloning a Solana bot from GitHub (e.g., Owntown farming bot, other game/DeFi bots) for the user:

1. **Refactor hardcoded config to env vars** (see "Hardcoded wallet/player ID" pitfall above)
2. **Convert wallet keypair to bot's expected format** — most 3rd-party bots expect `{private_key: "base58"}` not the Solana CLI array. Use `templates/solana-keypair-convert.js`
3. **Test auth FIRST** with direct `node bot.js` to surface the wallet/token issues before assuming bug
4. **If token-gated** (entry fee like 5000 OTWN), build a watcher that auto-swaps SOL → required token before bot starts. See `templates/solana-bot-watcher.sh` + `templates/solana-bot-autoswap.js`
5. **Hard-kill PM2 + clear cache + restart** for any code change to take effect (see "PM2 + Node.js module cache trap" above)
6. **Monitor:** `pm2 logs <bot> --lines 50 --nostream` for first 5 minutes to catch auth/startup issues

## Related Files (added Jun 2026 for 3rd-party bot deployment)

### Templates
- `templates/solana-bot-watcher.sh` — Bash watcher: poll wallet → auto-swap SOL to required token via autoswap.js → start bot via PM2. Use for any token-gated Solana bot deployment.
- `templates/solana-bot-autoswap.js` — Jupiter v1 swap helper (SOL→token), uses same Helius RPC + keypair pattern. Called by watcher.
- `templates/solana-keypair-convert.js` — Convert Solana CLI keypair `[64 bytes]` to bot-format `{private_key: "base58..."}`. Use when deploying any 3rd-party Solana bot that expects the object format.

### References
- `references/web3-game-economy-probe.md` — 18-layer systematic probe for Web3 game economies (on-chain token analysis, server endpoint discovery, JWT brute, admin endpoint bypass, dev social leak hunt, DEX buy paths). Battle-tested on Owntown.fun Jun 14 2026. Use when user needs a token that's locked behind a server-side balance check and asks "cari cara lain" / "hacker gak selemah itu".
- `references/phantom-position-guard.md` — **Jun16 fix for the DRY_RUN phantom-position bug.** Complete before/after code for `jupiter-executor.js`, `position-manager.js`, `index.js`. Use when bot shows "Max positions reached" with no real open positions, or when `data/positions.json` has entries with `entryPrice=0` / `solInvested=None` / `tokenAmount` in billions. Supersedes the Jun9 partial fix in `references/broken-position-fix.md`.

### Scripts
- `scripts/clean-phantom-positions.py` — Statically re-runnable cleanup: scans `data/positions.json` for phantoms (entryPrice=0, solInvested=None, tokenAmount=0), auto-backs up, removes phantoms, reports counts. Use after any bot crash or when migrating configs. Always run before restarting the bot.
