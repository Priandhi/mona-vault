# 2026-06-22 — LIMIT ENTRY + ALGO SL/TP (YUNA FIX)

## Task
Hexa follow-up: "jangan juga gini jir maksudnya kalau 1 symbol sinyal lolos scan entry atau limit order"
→ Switch from MARKET order to LIMIT entry. Place SL/TP via algo API.

## Bug Fixed
**Root cause**: All 44 "executed" signals failed with HTTP 400 `-1111: Precision is over the maximum defined for this asset.`
- BTCUSDT stepSize = 0.0001 (4 decimals)
- Code was `round(qty, 6)` → 6 decimals → reject

## Changes

### 1. Precision-aware qty rounding (`engine/binance_executor.py`)
- New `_get_symbol_info()` — fetches stepSize/minQty from exchangeInfo
- New `_round_qty()` — floors qty to stepSize boundary
- `place_order()` auto-rounds qty to stepSize + price to 2 decimals

### 2. Algo API for SL/TP (`engine/binance_executor.py`)
- New `place_algo_sl()` / `place_algo_tp()` via `/fapi/v1/algoOrder`
- `algoType=CONDITIONAL`, `type=STOP_MARKET`/`TAKE_PROFIT_MARKET`
- `workingType=MARK_PRICE`, `reduceOnly=true`
- **Works without existing position** (algoStatus=NEW, dormant until trigger)
- Endpoint discovery: `/fapi/v1/algoOrder` POST (testnet confirmed)

### 3. LIMIT entry (`engine/binance_executor.py`)
- New `place_limit_entry()` — LIMIT order at entry_price, GTC
- `time_in_force` param added to `place_order()`

### 4. Auto-execute flow rewrite (`run_cron.py`)
- Place LIMIT entry at entry_price (waits for fill)
- Place SL via algo API (dormant until entry fills)
- Place TP1/TP2/TP3 (30/30/40%) via algo API
- If price never reaches entry → orders stay dormant, no fill, no loss
- Dedup: skip if pending LIMIT entry already exists for symbol

### 5. Telegram spam fix (`run_cron.py`)
- BEFORE: ALL signals_found → telegram spam
- AFTER: only send if "LIMIT ENTRY PLACED" in exec_report
- Cycle: scan 50 → 1 signal passes filter → 1 LIMIT placed → 1 telegram

### 6. WAJIB tuning (`config/settings.py`)
- MIN_WAJIB_REQUIRED: 1 → 2 (Hexa "jangan terlalu rendah")

## Result — REAL TRADE WORKING

```
=== OPEN ORDERS (LABUSDT) ===
  LIMIT BUY qty=113.5 @ $14.95 status=NEW ✅

=== OPEN ALGOS (LABUSDT) ===
  TAKE_PROFIT_MARKET SELL qty=45.4 @ trigger=$16.75 status=NEW ✅
  TAKE_PROFIT_MARKET SELL qty=34.0 @ trigger=$16.15 status=NEW ✅
  TAKE_PROFIT_MARKET SELL qty=34.0 @ trigger=$15.55 status=NEW ✅
  STOP_MARKET SELL qty=113.5 @ trigger=$14.36 status=NEW ✅

=== POSITION (LABUSDT) ===
  No position (LIMIT entry belum fill)

=== BALANCE ===
  $3941.77 (margin reserved $84.91 untuk LIMIT BUY)
```

**Signal**: LABUSDT LONG, score 6/9, GOOD, Confidence MEDIUM
**Current price**: $14.9690 (0.10% above entry $14.9540)
**Status**: LIMIT entry waiting — bakal fill kalau retrace 0.1%

## Files Modified
- `/home/ubuntu/project-violet/engine/binance_executor.py` (+95 lines: _round_qty, _get_symbol_info, place_limit_entry, place_algo_sl/tp, cancel_*, error body capture)
- `/home/ubuntu/project-violet/run_cron.py` (auto_execute rewrite, telegram dedup)
- `/home/ubuntu/project-violet/config/settings.py` (MIN_WAJIB 1→2)
- `/home/ubuntu/project-violet/scripts/cleanup_spam.py` (new: clean leftover orders)
- `/home/ubuntu/project-violet/scripts/verify_lab.py` (new: verify state)

## Issues
- `openInterestHist` API returning empty body on testnet (non-fatal, signals still work)
- `marginType: -4046 "No need to change margin type"` — handled, returns True silently

## Next Steps
- Wait for price action on LABUSDT — entry will fill if price retraces to $14.95
- Cron will continue every 5 min, only pinging when LIMIT ENTRY PLACED
- Monitor fills + SL/TP triggers → tuning data accumulates