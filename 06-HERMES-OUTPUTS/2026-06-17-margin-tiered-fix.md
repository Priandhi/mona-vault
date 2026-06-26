---
type: receipt
date: 2026-06-17
tags:
  - receipt
---

Date     : 2026-06-17
Agent    : YUNA — The Strategist
Task     : Change margin to $75-$115 range (tiered by grade)
Posisi   : 0 active (4 open limit orders pending)
PnL      : $0
Result   :
  - Grade A (score ≥80) → $115 margin
  - Grade B (score 70-79) → $75 margin
  - Defaults: B = $75 (case-insensitive)
  - Implemented in:
    * config/settings.py: added MARGIN_BY_GRADE dict
    * engine/executor.py: _get_margin_per_trade(grade) + calculate_position_size(grade=) + execute_trade(grade=)
    * auto.py: pass best.grade to executor
  - Tested: A=$115, B=$75, lowercase A=$115, C=$75 (fallback), None=$75 ✓
  - PM2 restart: dozero-auto online, loading new code
Decisions:
  - Hexa feedback: $5 margin from post-mortem was too small for current testing
  - Mapped $75-$115 range to Grade B (low) and Grade A (high) respectively
  - Margin now grows with conviction — A-grade signals get 1.5x more capital
  - C/D grades not in dict (won't reach trade anyway, filtered at MINIMUM_TRADE_SCORE)
Issues:
  - PM2 restart warning "Process 7 not found" appears during waiting state but process comes back online (cosmetic)
  - 4 signalled + 196 strike-cooldown = no fresh pairs to scan right now
  - Need new signal to verify new margin in production
Next     :
  - Watch next 1-2 signals to confirm margin = $75 (B) or $115 (A) is applied
  - Update risk.py defaults? Currently still use $5 fallback but caller passes correct margin
  - Reconcile.py: only imports MAX_MARGIN_PER_TRADE (unused), no change needed
