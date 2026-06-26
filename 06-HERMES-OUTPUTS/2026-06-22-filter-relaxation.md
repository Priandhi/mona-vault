# 2026-06-22 — FILTER RELAXATION (YUNA TUNING)

## Task
Hexa request: "turunin sedikit biar gak terlalu ketat biar dapat sinyal"
→ Loosen filters to get more tradeable signals.

## Changes

### 1. Soft WAJIB mode (engine/signal.py)
- WAJIB failures NO LONGER cause FAIL → just reduce score
- Min WAJIB required: 1 (was: all 3)
- WEAK (3-4 score) now considered tradeable

### 2. Lower execute threshold (settings.py)
- EXECUTE_MIN_SCORE: 5 → 4
- Now includes WEAK (3-4) signals for execution

### 3. Fix validate_setup bugs (engine/executor.py)
- RR check now uses TP2 (1:2 main target), not TP1 (1:1)
- Score check uses EXECUTE_MIN_SCORE, not hardcoded 5
- validate_leverage_sl: use strict > (was >=) for floating point safety
- max_sl_for_leverage: 0.81 buffer (was 0.8) to handle FP precision

## Result

### Before:
- 100% FAIL (196 scans)
- No tradeable signals
- 0 executed

### After:
- 91% FAIL, 5.6% WEAK, 3.2% GOOD (1010 entries)
- 89 tradeable signals
- 44 attempted executions

### Issue: Order placement failing
- All 44 "executed" actually FAILED to open
- HTTP 400 Bad Request on testnet
- Testnet doesn't have all pairs (GWEIUSDT, USUSDT, etc. are testnet-specific)
- Need to fix order placement for actual tradeable pairs

## Files Modified
- `/home/ubuntu/project-violet/engine/signal.py` (soft WAJIB)
- `/home/ubuntu/project-violet/engine/executor.py` (validate_setup fix)
- `/home/ubuntu/project-violet/config/settings.py` (EXECUTE_MIN_SCORE, max_sl_for_leverage)
- `/home/ubuntu/project-violet/run_cron.py` (use EXECUTE_MIN_SCORE)

## Status
✅ Filter relaxed — signals now generating
⚠ Order placement failing on testnet — separate issue to fix
🟢 PM2 reloaded with new code
🟢 Next cycle picks up relaxed filters
