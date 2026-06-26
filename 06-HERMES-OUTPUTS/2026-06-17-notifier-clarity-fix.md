---
type: receipt
date: 2026-06-17
tags:
  - receipt
---

Date     : 2026-06-17
Agent    : YUNA — The Strategist
Task     : Fix notifier to distinguish FILLED vs LIMIT PLACED
Posisi   : 0 active (5 open limit orders waiting for fill)
PnL      : $0
Result   : 
  - send_execution() now takes `filled` + `limit_price` params
  - Status text changed:
    * "✅ FILLED" when position is actually open
    * "⏳ LIMIT PLACED (waiting fill)" when order in book
    * "❌ FAILED" if order failed
  - Limit-only message includes "⚠️ Posisi BELUM terbuka — nunggu market nyentuh limit"
Decisions:
  - Hexa feedback: "✅ EXECUTED" too ambiguous — could mean filled or just placed
  - Source: Hexa thought SYNUSDT was an open position but it was just a limit order in the book
  - Fix: explicit distinction at notifier level + executor passes filled flag based on position state
  - Default filled=True for backward compat (filled = position open)
Issues:
  - Standalone Python test from YUNA profile session fails: "No YUNA bot token found" because _get_bot_token() uses Path.home() which expands to nested path under YUNA HOME
  - In production (PM2 process), HOME=/home/ubuntu, notif works fine — not a real bug
Next     :
  - Next signal will use new format
  - Watch for next 1-2 signals to confirm both filled/limit-placed paths display correctly
