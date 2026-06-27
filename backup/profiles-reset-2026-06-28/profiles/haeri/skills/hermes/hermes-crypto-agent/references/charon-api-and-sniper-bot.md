# Charon API & Solana Sniper Bot Pattern

## Charon Signal Server (api.thecharon.xyz)

**Auth**: `x-api-key` header (NOT Bearer token)
**Base URL**: `https://api.thecharon.xyz`

### Endpoints
- `GET /api/signals` → `{ count, signals: [...] }`
- `GET /api/health` → health check

### Signal Object Fields
```json
{
  "symbol": "LIFE",
  "mint": "J8cXU1EF...",
  "holders": 1733,
  "marketCapUsd": 190637,
  "volume24h": 2248827,
  "volume5m": 9042,
  "liquidityUsd": 48950,
  "priceUsd": 0.000195,
  "ageMs": 54331516,
  "sourceCount": 4,
  "sources": [...],
  "bondingComplete": true,
  "trending": { "buys": 2232, "sells": 446, ... },
  "firstSeen": "2026-06-07T23:12:15Z",
  "lastSeen": "2026-06-08T14:16:55Z"
}
```

### Typical Stats (as of Jun 2026)
- ~80-95 signals per fetch
- ~50-60 pass basic quality filters (bonding + holders + mcap)
- Refresh: don't hammer — cache 30-60s minimum

## Sniper Bot Filter Thresholds (Charon signals)

Starting thresholds that work for small wallets (~0.36 SOL):

| Filter | Min | Max | Notes |
|--------|-----|-----|-------|
| holders | 150 | - | Below 150 = too early |
| mcap | $15K | $5M | Below $15K = dust, above $5M = late |
| volume24h | $10K | - | Minimum trading activity |
| liquidity | $3K | - | Minimum pool depth |
| ageMs | - | 72h | Older = less opportunity |
| bondingComplete | true | - | Must be bonded |
| minSources | 2 | - | Multi-source verification |

## Jupiter Integration for Buys/Sells

**⚠️ Jupiter API v1 (as of Jun 2026):** Old endpoints are DEAD (404).

**Quote API**: `GET https://api.jup.ag/swap/v1/quote?inputMint=SOL&outputMint=TOKEN&amount=LAMPORTS&slippageBps=500`
**Swap API**: `POST https://api.jup.ag/swap/v1/swap` with quote response
**Price API**: DEAD (404) — use quote-based fallback instead

### SOL Mint Address
`So11111111111111111111111111111111111111112`

### Quote-based Price Fallback (when price API is down)
```javascript
// Calculate price from quote: 0.001 SOL → tokens → price per token
const lamports = 1000000; // 0.001 SOL
const url = `https://api.jup.ag/swap/v1/quote?inputMint=SOL_MINT&outputMint=${mint}&amount=${lamports}&slippageBps=500`;
const data = await fetch(url).then(r => r.json());
const tokens = Number(data.outAmount);
const pricePerToken = lamports / tokens / 1e9; // in SOL
```

### Swap Execution Flow (LIVE)
1. Get quote from `/swap/v1/quote`
2. POST to `/swap/v1/swap` with `quoteResponse` + `userPublicKey`
3. Response returns `swapTransaction` (base64) — NOT `txid`!
4. Deserialize: `VersionedTransaction.deserialize(Buffer.from(base64, 'base64'))`
5. Sign with keypair: `tx.sign([keypair])`
6. Send: `connection.sendRawTransaction(Buffer.from(tx.serialize()))`
7. Confirm: `connection.confirmTransaction(txHash, 'confirmed')`

### DRY RUN Pattern
- Get real quote from Jupiter for realistic simulation
- Calculate token amount and entry price from quote
- Track simulated positions with entry/exit/PnL
- Use `getTokenPrice()` for real-time price checks

## Position Management Pattern

### Exit Conditions (check every cycle)
1. **Emergency SL**: -30% → immediate close
2. **Stop Loss**: -20% → close
3. **Take Profit**: +50% → close (if no trailing)
4. **Trailing Stop**: peak +25%, drop -10% → close
5. **Max Hold**: 4 hours → close regardless
6. **Break Even**: +15% → move SL to entry
7. **Partial Exit**: +40% → sell 50%, let rest ride

### Risk Management
- Max 3 concurrent positions
- Max 0.05 SOL daily loss → pause 1 hour
- 3 consecutive losses → pause 1 hour
- Min balance 0.15 SOL → stop all trading
- Cooldown 2 minutes between buys

## Dashboard Pattern (Express + Vanilla HTML)

Dark theme trading dashboard — reusable pattern:

### Backend (Express)
```
/api/pnl      → today's PnL stats
/api/trades   → today's closed trades
/api/positions → open positions
/api/config   → current config (sanitized)
/api/health   → health check
```

### Frontend
- Dark navy background (#0f1117)
- Cards with #161923 background
- Cyan (#00e5a0) for positive values
- Red (#ff4040) for negative values
- Purple (#8b5cf6) for accents
- Grid layout: 4-col metrics, 2-col secondary
- Auto-refresh every 15-30 seconds

### PM2 Ecosystem
```js
module.exports = {
  apps: [
    { name: "bot-name", script: "index.js", ... },
    { name: "bot-dashboard", script: "server.js", ... },
  ],
};
```

## PM2 Management for Multiple Bots

Pattern for running multiple crypto bots:
```
pm2 list                    → see all processes
pm2 logs bot-name --lines 10 → check logs
pm2 restart bot-name        → restart after config change
pm2 stop bot-name           → stop safely
pm2 delete bot-name         → remove from PM2
```

Port conflicts: always check `lsof -i :PORT` before starting a new dashboard.
