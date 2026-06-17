# YUNA Receipt — 2026-06-17 — Audit + Fix (Hexa feedback: "ngawur")

**Task:** Audit settings, identify why trading felt random, fix
**Result:** ✅ 5 stale limit orders cancelled, MIN_SCORE raised 70→80, scan lists cleared, audit + fix applied

## Hexa's Feedback
"settingan mu gimana yuna kok trading nya ngawur gitu"
= "What's your settings, why is trading so random"

## Audit Findings (5 issues)

### Issue 1: 5 stale limit orders piling up
```
CLANKERUSDT @ $15.77 (CLANKER placed 7 min ago, never filled)
LUMIAUSDT @ $0.0944
CROSSUSDT @ $0.0981
AIAUSDT @ $0.0561
COMPUSDT @ $17.62
```
**Root cause:** No clean-up logic. Bot placed them, walked away, never cancelled.
**Fix:** All 5 cancelled ✅

### Issue 2: MINIMUM_TRADE_SCORE = 70 too permissive
**Problem:** B-grade (70-79) signals have low win rate. Bot was filling many weak signals.
**Fix:** Raised to 80 (A-grade only) ✅

### Issue 3: 100% LONG bias (35 LONG, 0 SHORT)
**Root cause:** Scanner DOES try both LONG+SHORT (line 310 of core.py), but bull market = LONG always scores higher.
**Status:** Working as designed, but bias is real. Add SHORT counter-bias filter in next iteration.

### Issue 4: signalled.json + no_signal.json clogged
**Problem:** 6 signalled + 240 no_signal entries. Bot was skipping re-scans.
**Fix:** Both cleared. Fresh cycle now.

### Issue 5: Bot missed XPL +24% pump
**Root cause:** Scanner only checks OB/FVG/IDM — not momentum. Pure momentum plays (volatility breakout) are missed.
**Status:** Deferred — needs separate scanner logic.

## Current Settings (post-fix)

```python
DEFAULT_LEVERAGE  = 20x
MARGIN_PER_TRADE  = $90
SL_DISTANCE_PCT   = 4% (range 2-5%)
MIN_RR            = 1.5
MIN_PRICE_USD     = $0.05
MIN_VOLUME_USDT   = $2,000,000
MINIMUM_TRADE_SCORE = 80   ← WAS 70
TIMEFRAMES        = 1d/4h/1h/15m
DAILY_LOSS_LIMIT_R= 3R
v2 Confluence     = ELITE(7-9) / GOOD(5-6) / WEAK(3-4) / FAIL(<3)
```

## Active Positions (after restart)
- 🟢 LQTYUSDT LONG @ $0.2174 — 8,253 qty, 20x, +$14.03 (+0.78%)
- 🟢 NEARUSDT LONG @ $2.3399 — 761 qty, 20x, +$3.91 (+0.22%)

## What Changes Now
- Bot only takes A-grade signals (score ≥80)
- All stale limit orders gone
- Fresh scan cycle running
- 30-min cycle: scan → grade A only → execute

**Posisi:** 2 LONG (LQTY +$14, NEAR +$3.91)
**PnL:** +$17.94 unrealized
**Result:** Audit complete, 5 limit orders cancelled, MIN_SCORE tightened to 80
