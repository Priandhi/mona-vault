# Position Persistence Race Condition Fix

## Problem
`checkExits()` in `position-manager.js` has a race condition:
1. Loads positions at start: `const data = loadPositions()`
2. Processes exits → calls `closePosition()` → `savePositions()` (correct)
3. At END: calls `savePositions(data)` with OLD data → **overwrites all close changes**

Result: closed positions reappear as "open" on next restart.

## Fix
Replace the final `savePositions(data)` with:

```javascript
// Save updated peak data — reload to avoid overwriting closePosition changes
if (exits.length > 0 || partialExits > 0) {
  const freshData = loadPositions();
  // Copy peak data from in-memory positions to fresh data
  for (const pos of data.open) {
    const freshPos = freshData.open.find(p => p.id === pos.id);
    if (freshPos) {
      freshPos.peakPrice = pos.peakPrice;
      freshPos.peakPct = pos.peakPct;
      if (pos.breakEvenLocked) {
        freshPos.breakEvenLocked = pos.breakEvenLocked;
        freshPos.lockedPct = pos.lockedPct;
      }
    }
  }
  savePositions(freshData);
} else {
  // No exits, safe to save with peak updates
  savePositions(data);
}
```

## Verification
After fix, check positions file:
```bash
cat data/positions.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Open: {len(d[\"open\"])}, Closed: {len(d[\"closed\"])}')"
```
Should show correct counts matching bot logs.
