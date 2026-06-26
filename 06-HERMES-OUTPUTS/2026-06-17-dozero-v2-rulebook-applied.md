---
type: receipt
date: 2026-06-17
tags:
  - receipt
---

# YUNA Receipt — 2026-06-17 16:38 — DOZERO.X v2 Rulebook Applied

**Task:** Apply DOZERO.X v2 Complete Rulebook (SMC + Order Flow integration)
**Result:** Config layer + grading + breakeven + format applied. Engine rewrite deferred.

## Applied Changes

### config/settings.py (BAB 11.1 + 9.2 + 10.3)
- MAX_RISK_PCT = 0.02 (2% balance per trade = $86)
- DAILY_LOSS_LIMIT_R = 3 (stop if -3R/day)
- MAX_DRAWDOWN_PCT = 0.15
- CONFLUENCE_GRADING (ELITE/GOOD/WEAK/FAIL)
- CONFLUENCE_CHECKLIST_LONG/SHORT (9 items each)
- TIMEFRAMES (1d/4h/1h/15m)

### engine/scoring.py
- V2ConfluenceEngine class with evaluate() method
- 3/3 tests pass (WEAK notrade, ELITE trade, WAJIB fail)

### engine/executor.py (BAB 13.1 + 13.2)
- on_tp1_filled() — breakeven SL after TP1
- trail_sl() — structure-based trailing

### notifier.py (BAB 15.2)
- send_v2_signal() — new format with Alasan breakdown

## Pre-existing Matches
DEFAULT_LEVERAGE=20x, MARGIN=$90, SL=4%, TP R:R 1:2:3, MIN_RR=1.5,
validate_leverage_sl(), margin-based sizing

## Deferred (Engine Rewrite)
FVG, BOS/CHOCH, IDM, displacement, absorption, CVD divergence,
Premium/Discount Fib, OI delta, funding filter, BAB 16 architecture

## Live Status
- PM2 dozero-auto: online, 30-min cycle
- Active: SYNUSDT LONG + CROSSUSDT LONG (pending)
- V2 confluence: tested ✅

**Result:** Config layer 100% applied
