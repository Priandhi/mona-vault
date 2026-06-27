# Calendar API Field Name Mismatch Fix

## Problem
Calendar shows "undefinedT 0W" instead of proper PnL data on dates with daily-pnl entries.

## Root Cause
`daily-pnl.json` uses different field names than what the calendar frontend expects:

**daily-pnl.json structure:**
```json
{
  "days": [{
    "date": "2026-06-08",
    "totalPnlSol": 0,      // ← frontend expects "pnlSol"
    "totalTrades": 0,       // ← frontend expects "trades"
    "wins": 0,
    "losses": 0,
    "winRate": 0
  }]
}
```

**Frontend expects:**
```
pnlSol, trades, wins, losses
```

In `server.js` line 123, the calendar endpoint merges daily data:
```javascript
// BUG: copies raw object with wrong field names
if (!byDate[d.date]) byDate[d.date] = d;
```

The `d` object has `totalPnlSol` (not `pnlSol`) and `totalTrades` (not `trades`).
When frontend reads `dayData.pnlSol.toFixed(2)`, it gets `undefined.toFixed(2)` → error or "undefined" display.
When frontend reads `dayData.trades`, it gets `undefined` → shows "undefinedT".

## Fix
Replace the raw merge with explicit field mapping:

```javascript
// Add daily PnL data
for (const d of daily.days) {
  if (!byDate[d.date]) {
    byDate[d.date] = {
      date: d.date,
      pnlSol: d.totalPnlSol || d.pnlSol || 0,
      trades: d.totalTrades || d.trades || 0,
      wins: d.wins || 0,
      losses: d.losses || 0,
      tokens: d.tokens || [],
    };
  }
}
```

## Verification
```bash
# Before fix
curl -s http://localhost:3458/api/calendar | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['calendar'][0])"
# Shows: pnlSol: None, trades: None

# After fix
curl -s http://localhost:3458/api/calendar | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['calendar'][0])"
# Shows: pnlSol: 0, trades: 0
```

## Files Modified
- `server.js` — calendar endpoint, daily data merge logic
