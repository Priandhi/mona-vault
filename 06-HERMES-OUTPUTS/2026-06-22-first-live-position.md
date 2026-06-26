---
type: receipt
date: 2026-06-22
tags:
  - receipt
---

# 2026-06-22 — FIRST LIVE POSITION (LABUSDT LONG)

## Task
Hexa: "cek posisi" → verify Binance testnet state after first LIMIT entry fill.

## Result — POSITION LIVE

```
LABUSDT  LONG  amt=113.5
  Entry:   $14.9500 (LIMIT filled)
  Mark:    $14.9470
  PnL:     -$0.34 (-0.02% of margin)
  Lev:     20x
  Notional: $1,696.82
  Balance: $3,942.74

SL/TP algos (all status=NEW, awaiting trigger):
  SL    @ $14.36   STOP_MARKET    qty=113.5
  TP1   @ $15.55   TAKE_PROFIT    qty= 34.0  (30%)
  TP2   @ $16.15   TAKE_PROFIT    qty= 34.0  (30%)
  TP3   @ $16.75   TAKE_PROFIT    qty= 45.4  (40%)

Open orders: 0 (entry filled, all SL/TP via algo API)
```

## Trade Lifecycle
1. **16:02:26** — Signal generated (LABUSDT LONG, GOOD 6/9)
2. **16:02:26** — LIMIT entry placed @ $14.95 (orderId 494799223)
3. **16:02:26** — SL/TP algos placed (algoId 1000000113395244-250)
4. **~16:05** — Price retraced from $14.97 to $14.95 → LIMIT filled
5. **NOW** — Position live, SL/TP algos activated (will trigger on price levels)

## Validation
- LIMIT entry: worked (no slippage, filled at intended price)
- Algo SL/TP: dormant before entry, now armed (will trigger on price action)
- Position management: 20x lev, 2.1% margin per trade per settings
- Risk: -$66.96 max loss, Reward: +$204.30 at TP3 (1:3 RR)

## Files
- Position verification: `/home/ubuntu/project-violet/scripts/check_positions.py`
- Algo verification: `/home/ubuntu/project-violet/scripts/verify_lab_algos.py`

## Next
- Cron continues every 5 min — only pings when new LIMIT entry placed
- LABUSDT SL/TP auto-manage from algo
- JSONL log captures fills → tuning data accumulates
- When TP1 hits: SL moves to breakeven (planned but not auto yet)
- When SL/TP hits: position closes, PnL locked