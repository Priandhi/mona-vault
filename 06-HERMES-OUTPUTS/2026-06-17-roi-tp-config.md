---
type: receipt
date: 2026-06-17
tags:
  - receipt
---

Date     : 2026-06-17
Agent    : YUNA — The Strategist
Task     : Change TP to ROI-based (100%/200%/300% of margin)
Posisi   : 0 active (1 open limit: LUMIA)
PnL      : $0
Result   : 
  - TP_ROI = [1.0, 2.0, 3.0] in settings.py (100%/200%/300% of margin)
  - TP placement: actual_entry × (1 + TP_ROI[i] / leverage)
  - Main TP placed at 200% ROI (TP_ROI[1]) — single order, close_position=True
  - TP1/TP3 levels logged for visibility (testnet has 1-stop-order limit per post-mortem)
  - Files modified: config/settings.py, engine/executor.py, auto.py
Decisions:
  - Hexa: "TP1 100% ROI, TP2 200% ROI, TP3 300% ROI" — leverage-aware
  - Kept post-mortem design: 1 SL + 1 Main TP only (testnet max 1 algo order per symbol)
  - Main TP = TP2 (200% ROI) as conservative target
  - ROI-based math: profit = price_move% × leverage × margin, so 100% ROI = price_move = 1/leverage
  - Test matrix:
    * $100 @ 75x: TP1=1.33%, TP2=2.67%, TP3=4.00% (profits $100/$200/$300)
    * $100 @ 15x: TP1=6.67%, TP2=13.33%, TP3=20% (profits $100/$200/$300)
    * LDO $0.29 @ 15x: TP1=$0.3093, TP2=$0.3287, TP3=$0.3480
Issues:
  - PM2 cron still firing every 6 min (not 30 min) — still need to fix later
  - 3 separate TP orders not placed (testnet 1-order limit) — only TP2 is real
  - LUMIA limit still open with old TP (was placed at 12% / 200% ROI under old config)
Next     :
  - Watch next signal to see new TP levels in log (info message)
  - Consider raising Main TP to TP3 (300%) for more aggressive exit — Hexa to decide
  - Cron timing fix pending — separate issue
