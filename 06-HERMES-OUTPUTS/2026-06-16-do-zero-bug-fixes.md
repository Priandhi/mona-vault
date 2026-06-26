---
type: receipt
date: 2026-06-16
tags:
  - receipt
---

# Receipt: Dozero.X Bug Fixes — 2026-06-16

## Task
Fix Dozero.X auto-trading system: double entry, missing SL/TP, TP not showing in dashboard

## Changes Made

### 1. Double Entry Guard
- **File:** `auto.py` (line 277-294)
- Sebelum entry, cek Binance positions. Kalo udah ada posisi open → skip + notif "⛔ SKIPPED"
- **File:** `executor.py` (line 97-107) — safety net kedua

### 2. SL/TP Recalculation
- **File:** `executor.py` (line 178-196)
- Setelah limit order terisi, ambil **fill price real** dari Binance
- Recalculate SL/TP pake percentage distance dari sinyal, tapi berdasarkan fill price
- Auto-widen SL kalo error -2021 ("would immediately trigger")

### 3. Main TP (Dashboard Visible)
- **File:** `executor.py` (line 320-336) — place `close_position=True` at TP3
- **File:** `reconcile.py` (line 103-118) — sama untuk existing positions
- **File:** `auto.py` `_reconcile_sltp()` — reconciliation auto

### 4. TP1/TP2/TP3 All Levels
- **File:** `executor.py` (line 256-318) — TP1 30%, TP2 30%, TP3 40%
- Sebelumnya cuma TP1 (30%) yang kepasang, TP2/TP3 gak pernah

### 5. Reconciliation System
- **File:** `reconcile.py` **BARU** — script for existing positions
- **`auto.py`** — `_reconcile_sltp()` dijalankan tiap cycle scan
- Memperbaiki SL/TP yang missing karena error sebelumnya

### 6. Support Methods
- **File:** `connection.py` — added `get_tick_size()` method

### 7. Closed Positions
- ADAUSDT ✅ CLOSED (was -$2.61)
- XRPUSDT ✅ CLOSED (was -$1.69)

## Active Positions (all green)
- PUMPBTCUSDT: +$10.10
- XLMUSDT: +$105.62 (double entry, still profitable)
- JASMYUSDT: +$3.46

## Notes
- Testnet doesn't support GET /fapi/v1/algoOrder/openOrder (404)
- Error -4130 means SL/TP already exists (not failure)
- Error -2021 = would immediately trigger → auto-widen 1.5x
- All numeric params for algo orders MUST be strings
- PM2: dozero-auto cron */30
