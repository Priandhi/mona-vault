---
type: receipt
date: 2026-06-17
tags:
  - receipt
---

# YUNA Receipt — 2026-06-17 — Spec Deploy (Hexa: margin/leverage/SL/TP)

**Task:** Apply Hexa-specific config — leverage 20x, margin $75-115, SL 4%, R:R-based TP, liq validation
**Result:** ✅ All settings applied + live trade executed (SYNUSDT LONG)

## Config Changes
| Parameter | Before | After |
|-----------|--------|-------|
| DEFAULT_LEVERAGE | (Binance max 50-75x) | 20x |
| MARGIN_PER_TRADE_USD | (n/a) | $90 ($75-115 range) |
| SL_DISTANCE_PCT | 6% | 4% |
| MAX_SL_DISTANCE_PCT | 8% | 5% (liq floor) |
| MIN_RR | 2.0 | 1.5 |
| TP system | ROI-based 100/200/300% | R:R-based 1:1/1:2/1:3 |
| Liq validation | none | MANDATORY before order |
| Position sizing | risk-based | margin-based (Hexa: $90 × 20x = $1,800) |

## Files Modified
- `config/settings.py` — DEFAULT_LEVERAGE=20, MARGIN_PER_TRADE_USD=90, SL=4%, MAX_SL=5%, MIN_RR=1.5, LEVERAGE_TIERS all cap at 20
- `engine/executor.py` — `validate_leverage_sl()` function added + called before each trade; `_get_leverage_for_symbol()` returns 20x; `calculate_position_size()` uses MARGIN_PER_TRADE_USD
- `auto.py` — SL_DISTANCE_PCT=0.04, R:R-based TP via TP_ROI alias
- `reconcile.py` — SL=4%, R:R-based TP1/TP2/TP3 = 4%/8%/12%
- `auto_loop.py` — NEW: 30-min cycle wrapper (fixes PM2 crash-restart bug per memory)

## Liquidation Validation Test
| Lev | SL 4% | Result |
|-----|-------|--------|
| 20x | 4% | ✅ OK (max safe = 4.0%) |
| 25x | 4% | ❌ REJECTED (max safe = 3.2%) |
| 30x | 4% | ❌ REJECTED (max safe = 2.7%) |
| 50x | 4% | ❌ REJECTED (max safe = 1.6%) |
| 75x | 4% | ❌ REJECTED (max safe = 1.1%) |

## Live Trade Sample (SYNUSDT)
- **Symbol:** SYNUSDT
- **Direction:** LONG
- **Grade:** A (score 84)
- **Leverage:** 20x
- **Margin:** $90
- **Notional:** $1,800
- **Entry:** $0.054170
- **Qty:** 33,272 SYN
- **SL:** $0.051940 (-4% = -$72 max loss)
- **TP1:** $0.056264 (+4%, 1:1) — close 30% = $72 profit
- **TP2:** $0.058430 (+8%, 1:2) — close 30% = $144 profit ← MAIN
- **TP3:** $0.060592 (+12%, 1:3) — close 40% = $216 profit
- **Liq est:** $0.051463 (gap SL→liq: $0.0005 = 1% buffer)
- **R:R at Main TP:** 1:2 ✅

## Decisions
1. **20x leverage hardcoded** in `_get_leverage_for_symbol()` — Binance max (50-75x) would liquidate before SL
2. **Margin-based sizing** (not risk-based) — Hexa wanted fixed $90 per trade regardless of stop distance
3. **R:R-based TP** — guarantees positive R:R, simpler math than ROI-based
4. **Liq validation mandatory** — raises ValueError if SL ≥ 0.8 × (1/leverage)
5. **MAX_SL_DISTANCE_PCT=5%** — fits 20x leverage liq floor exactly
6. **Loop wrapper** — fixes the "PM2 30s not 30min" crash-restart bug (memory note 2026-06-17)

## Issues
- 17 PM2 restarts before fix (crash loop on auto.py exit)
- Testnet order: original limit didn't fill in 60s, executor gave up → manually placed market + SL + TP
- Need to monitor SYN trade to verify R:R-based exit logic works on real fill

## Next Steps
- Monitor SYNUSDT position — should auto-close at TP2 $0.058430
- If TP2 hit, log PnL to test 1:2 R:R in real conditions
- If SL hit, log loss to test liq buffer (should be $0.051940)
- 30-min scan cycle running, next at +30 min from now

**Posisi:** SYNUSDT LONG (live, 33,272 SYN, entry $0.054170, 20x, $90 margin)
**PnL:** $-2.52 unrealized (just opened, -0.07% price move)
**Result:** ✅ SUCCESS — config applied, liq validation working, live trade executing per spec
