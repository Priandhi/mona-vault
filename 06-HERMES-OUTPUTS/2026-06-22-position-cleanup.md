---
type: receipt
date: 2026-06-22
tags:
  - receipt
---

# 2026-06-22 — POSITION CLEANUP (LABUSDT)

## Task
Hexa: "cek posisi" → verify state.

## Discovered Issue
Cron fired multiple times → added 2nd LIMIT entry on same symbol → 8 algos (duplicate SL/TP).

Root cause: dedup only checked for PENDING LIMIT entries. Once filled, new entries could be placed (pyramiding).

## Cleanup Actions

1. **Cancel duplicate SLs** (qty=113.5 batch + qty=114.0 batch, both STOP_MARKET)
   - cancel_algo() was returning False due to type mismatch (`code` returned as STRING "200", not int)
   - Fix: accept both `(200, "200")`

2. **Cancel 3 OLD TP algos** ($15.55, $16.15, $16.75 triggers)
   - NEW TPs ($15.48, $16.08, $16.67) hit first and close position
   - OLD TPs would never fire (no position left)

3. **Re-add SL** @ $14.26 (4% below averaged entry $14.8537)
   - algoId 1000000113471281
   - qty 114.0 (matches position)

4. **Fix dedup in run_cron.py**:
   - Skip if existing position same direction (no pyramiding)
   - Skip if existing position opposite direction (no reversal)
   - Skip if pending SL/TP algos exist (active setup)

## Final State

```
LABUSDT  LONG  amt=114.0
  Entry:   $14.8537
  Mark:    $15.0760
  PnL:     +$25.34 (+0.6% balance)
  Notional: $1,718.66

Algos (4 — clean):
  SL    @ $14.26   qty=114.0
  TP1   @ $15.48   qty= 34.2 (30%)
  TP2   @ $16.08   qty= 34.2 (30%)
  TP3   @ $16.67   qty= 45.6 (40%)
```

## Risk Profile
- To SL:  -$93.20 (-2.3% balance)
- To TP1: +$48.90 (+1.2% balance)
- To TP2: +$121.80 (+3.1% balance)
- To TP3: +$180.92 (+4.6% balance)
- 1:0.52 / 1:1.31 / 1:1.94 actual RR (TP1 closer than ideal)

## Files Modified
- `/home/ubuntu/project-violet/engine/binance_executor.py` (cancel_algo type fix)
- `/home/ubuntu/project-violet/run_cron.py` (dedup: existing position + active algos check)

## Cleanup Scripts Created
- `scripts/cleanup_duplicate_algos.py`
- `scripts/cleanup_old_tps.py`
- `scripts/re_add_sl.py`

## Next
- Position protected by single SL/TP set
- Cron dedup prevents future pyramiding
- Monitor LABUSDT until SL or TP triggered
- JSONL log captures outcome for tuning