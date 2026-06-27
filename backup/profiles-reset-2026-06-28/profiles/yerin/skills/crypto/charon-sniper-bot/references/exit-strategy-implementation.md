# Exit Strategy Implementation — Break-Even & Partial Exit

## Problem
Config fields `exit.breakEven.*` and `exit.partialExit.*` exist in config.json but the exit checker in `position-manager.js` does NOT implement them. These configs are silently ignored.

## Solution — Add to `checkExits()` in `position-manager.js`

Insert AFTER stop loss check (condition 2) and BEFORE take profit check (condition 5):

```javascript
// 3. Break-even: move SL to lock small profit
if (config.exit.breakEven?.enabled && !pos.breakEvenLocked) {
  if (pnlPct >= config.exit.breakEven.triggerPct) {
    pos.breakEvenLocked = true;
    pos.lockedPct = config.exit.breakEven.lockAtPct;
    log("pos", `🔒 ${pos.symbol} BREAK-EVEN LOCKED at +${config.exit.breakEven.lockAtPct}%`);
  }
}
// If break-even locked, treat as SL at locked level
if (pos.breakEvenLocked && pnlPct <= (pos.lockedPct || 0)) {
  exits.push({ pos, reason: `BREAK-EVEN LOCK ${pnlPct.toFixed(1)}%` });
  continue;
}

// 4. Partial exit: sell portion at trigger, keep rest for trailing
if (config.exit.partialExit?.enabled && !pos.partialExited && !pos.partialExitTriggered) {
  if (pnlPct >= config.exit.partialExit.triggerPct) {
    const partialSellPct = config.exit.partialExit.sellPct || 50;
    const partialAmount = Math.floor(pos.tokenAmount * (partialSellPct / 100));
    if (partialAmount > 0) {
      log("pos", `🎯 ${pos.symbol} PARTIAL EXIT ${partialSellPct}% at +${pnlPct.toFixed(1)}%`);
      try {
        const partialResult = await sellToken(pos.mint, partialAmount, config);
        if (partialResult.success) {
          pos.partialExited = true;
          pos.partialExitPct = partialSellPct;
          pos.partialExitSol = partialResult.amountOut || 0;
          pos.partialExitPrice = partialResult.price || 0;
          pos.tokenAmount -= partialAmount;
          log("pos", `✅ ${pos.symbol} sold ${partialSellPct}% → ${pos.partialExitSol} SOL`);
          partialExits++;
        }
      } catch (e) {
        log("pos", `⚠️ Partial exit failed for ${pos.symbol}: ${e.message}`);
      }
      pos.partialExitTriggered = true; // Don't try again even if failed
    }
  }
}
```

## Required: Track `partialExits` counter

Add at top of `checkExits()`:
```javascript
let partialExits = 0;
```

Use in the save logic (see position-persistence-fix.md).

## Exit Priority Order
1. Max hold time (no price needed)
2. Emergency SL
3. Normal SL
4. Break-even lock
5. Partial exit
6. Take profit (only if trailing disabled)
7. Trailing stop
