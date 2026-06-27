# Charon Sniper — Config Structure Reference

## config.json — Complete Field Map

The config is a flat JSON object (NOT nested YAML). All keys are top-level or one level deep.

```json
{
  "mode": "DRY_RUN",
  "charon": {
    "apiUrl": "https://api.thecharon.xyz",
    "refreshIntervalMs": 30000,
    "maxSignals": 50,
    "apiKey": "bb1eba..."
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
    "breakEven": { "enabled": true, "triggerPct": 5, "lockAtPct": 2 },
    "partialExit": { "enabled": true, "triggerPct": 12, "sellPct": 35 }
  },
  "risk": {
    "minBalanceSol": 0.2,
    "maxDailyLossSol": 0.15,
    "emergencyStopLossPct": -30,
    "pauseAfterConsecutiveLosses": 2,
    "pauseDurationMinutes": 30
  },
  "filter": {
    "minHolders": 200,
    "minMcap": 20000,
    "maxMcap": 2000000,
    "minVolume24h": 20000,
    "minLiquidity": 5000,
    "maxAgeHours": 6,
    "requireBondingComplete": true,
    "requireAtLeast2Sources": true,
    "blockedSymbols": ["USDC", "USDT", "SOL", "WSOL", "MSOL"],
    "blockedMints": [],
    "minPriceChange5m": -3,
    "minVolume5m": 1000,
    "minVolAcceleration": 1.0,
    "minOrganicScore": 40,
    "maxDevHoldings": 15,
    "maxTopHolders": 40,
    "maxSnipers": 50,
    "minBuyRatio": 0.85,
    "minNetBuyers": 15,
    "minLiqRatio": 4,
    "minLiqChange": -15
  }
}
```

## Key Config Rules

1. filter is SINGULAR — code reads config.filter, NOT config.filters
2. maxPositions not maxOpenPositions — code reads config.trade.maxPositions
3. Charon API key in config.json — config.charon.apiKey (x-api-key header, NOT Bearer)
4. Private keys in .env ONLY — never in config.json
5. Config is re-read every cycle — changes take effect without restart

## Log Analysis Commands

```bash
pm2 logs charon-sniper --lines 20 --nostream
pm2 logs charon-sniper --err --lines 20 --nostream
cat data/traded.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Traded: {len(d)} tokens')"
cat data/positions.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Open: {len(d.get(\"open\",[]))}, Closed: {len(d.get(\"closed\",[]))}')"
```
