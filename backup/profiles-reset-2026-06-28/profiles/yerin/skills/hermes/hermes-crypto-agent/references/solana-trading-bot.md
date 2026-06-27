# Solana Trading Bot Architecture — Pitfalls & Patterns

> Built from Charon Sniper Bot development (Jun 2026)

## Critical Pitfalls

### 1. Position Manager Race Condition
When `checkExits()` loads positions at start, then calls `closePosition()` (which also loads+saves), then saves again at end → the final save OVERWRITES the close.

**Fix:** After executing exits, reload positions from disk, merge in-memory state (peak, breakEven, partialExit), then save fresh data.

```js
// ❌ BAD: savePositions(data) at end overwrites closePosition changes
const data = loadPositions();
// ... process exits calling closePosition() ...
savePositions(data); // WRONG — stale data

// ✅ GOOD: reload after exits
if (exits.length > 0) {
  const freshData = loadPositions();
  // Copy in-memory state to fresh data
  for (const pos of data.open) {
    const freshPos = freshData.open.find(p => p.id === pos.id);
    if (freshPos) {
      freshPos.peakPrice = pos.peakPrice;
      freshPos.peakPct = pos.peakPct;
      // ... other fields ...
    }
  }
  savePositions(freshData);
} else {
  savePositions(data); // Safe when no exits
}
```

### 2. DRY RUN Sell Returns 0 SOL
When `getTokenPrice()` returns null (common for micro-caps), the DRY RUN sell calculates `solValue = 0`, causing -100% PnL and hitting daily loss limits.

**Fix:** Fallback to deploy amount estimate:
```js
if (solValue <= 0) {
  solValue = (config?.trade?.deployAmountSol || 0.04) * 0.85;
}
```

### 3. Config Key Naming Mismatches
Code reads `config.filter` (singular) but config file has `filters` (plural). Also `maxPositions` vs `maxOpenPositions`.

**Fix:** Always verify config key names match between code and JSON. Test with: `node -e "console.log(Object.keys(JSON.parse(fs.readFileSync('config.json'))))"`

### 4. Break-Even & Partial Exit Not Implemented
Config had `breakEven` and `partialExit` fields but the exit checker code only had: SL, TP, trailing. These features were "configured" but never running.

**Fix:** Implement in exit checker between SL check and TP check:
1. After SL check → check breakEven trigger → lock SL at higher level
2. After breakEven → check partialExit trigger → sell portion, mark triggered
3. After partialExit → check TP → check trailing

### 5. PM2 Restart Doesn't Reload .env
`pm2 restart` preserves the old process environment. `.env` changes won't take effect.

**Fix:** Use `pm2 delete <name> && pm2 start ecosystem.config.cjs --update-env`

### 6. `maxDailyTrades` Blocks Signal Fetching
Risk checks (including daily limit) run BEFORE signal fetch. If limit hit, filter never runs and no data is collected.

**Fix:** This is correct behavior for LIVE. For DRY RUN testing, temporarily set `maxDailyTrades: 99`.

## Architecture Pattern

```
index.js           Main loop (30s interval)
├── config.json    All settings (mode, trade, exit, risk, filter)
├── .env           Secrets (wallet key, API keys, RPC URL)
├── modules/
│   ├── charon-fetcher.js     Signal fetch + cache (30s TTL)
│   ├── token-filter.js       Multi-layer filter + quality scoring
│   ├── jupiter-executor.js   Buy/sell via Jupiter (DRY + LIVE)
│   │   ├── initWallet()      Load keypair from .env
│   │   ├── getQuote()        Jupiter /swap/v1/quote
│   │   ├── executeSwap()     Deserialize → sign → send → confirm
│   │   └── getTokenPrice()   Quote-based price estimation
│   ├── position-manager.js   Open/close positions, exit checker
│   ├── pnl-tracker.js        Daily PnL snapshots
│   ├── telegram-notifier.js  Buy/sell notifications
│   └── logger.js             Daily rotating logs
├── data/
│   ├── positions.json        { open: [...], closed: [...] }
│   └── daily-pnl.json        { days: [...] }
└── server.js                 Dashboard API + static frontend
```

## LIVE Mode Checklist

1. `.env` file with `WALLET_PRIVATE_KEY` (base58) and `HELIUS_API_KEY`
2. `config.json` with `"mode": "LIVE"`
3. Wallet initialized via `initWallet()` at startup
4. Balance check: `getSolBalance() >= minBalanceSol`
5. Jupiter `/swap/v1/swap` → `swapTransaction` (base64)
6. Deserialize → sign with keypair → sendRawTransaction → confirmTransaction
7. Balance recheck each cycle (safety: pause if < minBalance)
