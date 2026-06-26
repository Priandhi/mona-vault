---
type: receipt
date: 2026-06-16
tags:
  - receipt
---

Date     : 2026-06-16
Agent    : YUNA — The Strategist
Task     : Cek posisi futures YUNA (/pnl) + fix bugs yg muncul
Posisi   : 0 active (testnet)
PnL      : uPnL $0.00 (no positions)
Result   : 
  - Balance: $4,272.42 USDT (available)
  - Total wallet: $4,272.42
  - Active positions: 0
  - PnL sent to Telegram thread 2905 ✅
Decisions:
  - Bug 1: `BinanceConnection.get_balance()` returns float 4272.42, but `agent_data.py:get_yuna()` did `bal.get('availableBalance', 0)` → AttributeError → except → balance=0
    - Fix: `data['balance'] = round(float(bal) if bal else 0, 2)` (treat as float)
  - Bug 2: `Path.home()` in YUNA profile $HOME = /home/ubuntu/.hermes/profiles/yuna/home/ → wrong key path
    - Workaround: prefix `HOME=/home/ubuntu` when running dozero scripts
  - Bug 3 (earlier): soft-stop cron file path nested due to ~ expansion — already fixed earlier this turn
Issues:
  - All 3 bugs rooted in YUNA profile's $HOME = nested path. Long-term fix: either use absolute paths in dozero scripts OR set HOME explicitly in YUNA gateway.
Next     :
  - Confirm Dozero scanner (`*/30`) resumes with proper SL/TP
  - Watch next 1-2 soft-stop cron ticks to ensure no recurrence
  - Consider adding HOME=/home/ubuntu prefix to all dozero script calls from YUNA profile
