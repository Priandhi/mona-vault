# TP Ladder Strategy — Capturing Runners

## The Problem with Single Take Profit

A single TP at +25% or +30% works for choppy markets, but misses runners that go to 4x or higher. Once you sell at +30%, you don't participate in the rest of the pump.

**Example:** Token "p" peaked at +329.5%. Single TP at +30% would have captured ~+0.03 SOL. TP ladder + trailing captured +0.14 SOL — a 4.7x improvement on the same token.

## The TP Ladder Pattern

Instead of one TP, use a LADDER of three (or more) TPs, each selling a portion of the position at increasing profit levels. The remainder rides with trailing stop.

```json
"takeProfitLevels": [
  { "triggerPct": 20, "sellPct": 30 },
  { "triggerPct": 40, "sellPct": 35 },
  { "triggerPct": 70, "sellPct": 35 }
]
```

This sells 30% at +20%, 35% at +40%, 35% at +70% = 100% via TP ladder.

**For partial + trailing pattern** (recommended — keep small remainder riding):
```json
"takeProfitLevels": [
  { "triggerPct": 20, "sellPct": 25 },
  { "triggerPct": 40, "sellPct": 30 },
  { "triggerPct": 70, "sellPct": 30 }
],
"trailingEnabled": true,
"trailingTriggerPct": 15,
"trailingDropPct": 10
```

This sells 85% via ladder, remaining 15% rides with trailing.

## Case Study: token "p" (Jun 17 2026)

| Field | Value |
|---|---|
| Entry | 0.1 SOL @ $0.0000000000008 |
| Age at entry | 18 minutes (fresh) |
| 5m momentum | +1.0% (NEUTRAL — not chasing) |
| Organic | 67 |
| buyRatio | 5.1 |
| Holders | 326 |
| MCap | $62K |
| Peak | **+329.5% (4.3x)** |
| TP1 hit | +20% (30% sold) |
| TP2 hit | +40% (35% sold) |
| TP3 hit | +70% (30% sold) |
| Trailing exit | Peak +329.5%, dropped -12.1% (within -10% trigger) |
| **Final PnL** | **+139.91% / +0.14 SOL** |

The TP ladder hit all three levels. The remaining portion (after ladder sold ~95% of `originalTokenAmount`) rode with the trailing stop. When the price dropped 12.1% from peak, the trailing exit triggered and sold the rest at ~+278% of original entry.

**Final PnL: +139.91%** (averaged across TP1 +20%, TP2 +40%, TP3 +70%, trailing at ~+278%).

## Why This Works

1. **Locking gains incrementally** — each TP level converts unrealized profit to SOL in your wallet
2. **Riding the runner** — the remaining portion participates if the token keeps pumping
3. **Trailing captures the spike** — if the token peaks at 4x, trailing exits the remainder at a high price instead of waiting for a fixed TP that's never reached
4. **Asymmetric risk** — even if the token dumps after TP1, you've already locked 30% of the position at profit

## How to Configure the Ladder

The ladder should match the OBSERVED peak distribution for your token source. For Charon signals (micro-cap memecoins), observed peaks are:
- Median: +15% to +25%
- 75th percentile: +30% to +50%
- 95th percentile: +100% to +400% (rare runners)

So a ladder starting at +20% (covers the median) and going to +70% (catches most runners) is well-calibrated.

| Token Type | Suggested Ladder |
|---|---|
| Conservative (small wallet) | [15/30, 30/35, 50/35] |
| Balanced (Charon micro-caps) | [20/30, 40/35, 70/35] |
| Aggressive (let it ride) | [30/25, 60/30, 100/30] + trailing 5% drop |
| Runner hunters | [40/20, 80/30, 150/30] + trailing 8% drop |

## Implementation in position-manager.js

The TP ladder is already implemented in `position-manager.js checkExits()`. The relevant fields in each position:

- `tpLevelsHit` — array of trigger percentages already hit
- `tpSoldTotal` — total raw token amount sold via TP levels
- `originalTokenAmount` — initial token count (for percentage calculations)
- `tokenAmount` — current remaining tokens (decreases as TPs execute)

The exit checker priority order in v3:
1. Max hold time (90m default) — no price needed
2. Emergency SL (-25% to -30% default)
3. Normal SL (-12% default in v3)
4. Break-even lock (trigger +20% lock +8% in v3) — if enabled
5. **TP ladder levels** (20%, 40%, 70% with 30/35/35 sellPct) — sell portion
6. Trailing stop (trigger +15% drop -10%) — for remaining position

## Pitfalls

- **`tpSoldTotal` MUST be persisted across cycles (Jun 2026 CRITICAL):** The position file race condition fix (see SKILL.md pitfalls) must copy `tpSoldTotal` AND `tokenAmount` from in-memory position to fresh data, otherwise the next cycle re-sells from the original amount and you double-sell. The fix: in `position-manager.js checkExits`, after `closePosition()` calls `savePositions()`, reload positions and copy ALL mutable fields: `peakPrice, peakPct, breakEvenLocked, lockedPct, tpLevelsHit, tpSoldTotal, tokenAmount, partialExited, partialExitPct, partialExitSol, partialExitPrice, partialExitTriggered`.

- **Token decimals matter:** Charon signals can have 6, 9, or other decimals. The `tpSoldTotal` is in RAW token units, not human-readable. Don't try to display it in Telegram — just log "TP1 executed: X.XXXXXX SOL" (the SOL received, not the token count).

- **TP execution in DRY_RUN:** The DRY_RUN sell simulates SOL received as `amountToSell * currentPrice`. In LIVE mode, it's the actual Jupiter quote. The numbers can differ by slippage (5% default). Don't expect exact TP-level prices — expect ±5%.

- **Don't over-ladder:** 3 levels is enough. Adding 4+ levels with small sellPct each just makes the math complex and adds slippage cost. Stick to 3: lock initial gains, ride the middle, capture the runner.

## Rollback / Tuning

If TP ladder is producing too many small wins and missing the big runners:
- Move TP2 trigger down to +30% and TP3 to +50% — captures more of the distribution
- Lower trailing drop from -10% to -5% — tighter stop, captures more of the peak

If TP ladder is selling too early:
- Raise TP1 to +30% or +40% — wait for stronger confirmation
- Lower TP1 sellPct to 20% — keep more riding

The TP ladder is a lever you can tune based on observed outcomes. The [20/30, 40/35, 70/35] starting point is calibrated for Charon micro-caps, not memecoin launches on pump.fun (which have different distribution).
