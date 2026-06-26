---
type: receipt
date: 2026-06-17
tags:
  - receipt
---

Date     : 2026-06-17
Agent    : YUNA — The Strategist
Task     : Change leverage to Binance max (override tier cap)
Posisi   : 1 active (LDO LONG 3882 @ 0.2889, 15x locked from entry)
PnL      : +$6.93 (LDO)
Result   : 
  - _get_leverage_for_symbol() now returns self.conn.get_max_leverage(symbol) directly
  - LEVERAGE_TIERS dict kept in settings.py for reference but not applied
  - Added LEVERAGE_USE_TIER_CAP = False flag (set True to re-enable tiers)
  - Test: all price tiers return 75x (Binance testnet max) ✓
  - PM2 restart loaded new code
Decisions:
  - Hexa override: "gas max" — wants max leverage across all pairs
  - Removed tier-cap logic, kept SL min 2% + margin tiered $75/$115 as risk buffer
  - Existing LDO position (15x) keeps its entry leverage — leverage is per-position
Issues:
  - LDO already filled at 15x — won't auto-rebalance
  - For new trades (LUMIA, SYN if filled, or future signals), leverage = binance_max
  - Testnet max varies by symbol: 75x for most, 50x for some, 25x for others
Next     :
  - Watch LUMIA + SYN limit orders — when they fill, they'll use max leverage
  - 1 liquidation risk: high leverage + dust token = tight buffer. Soft-stop cron still monitors uPnL < -5%
  - If WR drops below target, consider re-enabling tier cap (set LEVERAGE_USE_TIER_CAP=True)
