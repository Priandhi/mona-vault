# Charon Sniper Bot — Build Reference

## Files Created (June 2026)

### Backend: server.js
Express server on port 3456 with:
- `GET /api/signals` — live Charon signals (50 limit)
- `GET /api/trades` — today's trades
- `GET /api/pnl` — PnL summary (total, win rate, best/worst, avg win/loss, risk/reward)
- `GET /api/snapshots` — historical PnL snapshots for charting
- `GET /api/health` — status check

Trade generation: every 3 minutes, fetch signals → filter → simulate PnL → record.
Simulation uses quality score (holders, volume, mcap, liquidity, sources, trending) to determine win probability (40-85%).

### Frontend: public/index.html
Dark theme trading terminal style. Colors:
- Background: `#121826` (page), `#1a1f2e` (cards)
- Positive: `#00e5a0` (cyan/teal)
- Negative: `#ff4040` (red)
- Text: `#ffffff` (values), `#8a91a6` (labels)
- Font: Inter, weights 400/600/700/800

Layout: Header → Hero PnL Card → 4-col metrics grid → 2-col metrics grid → Progress bar + Risk/Reward → Trades table → Live signals → Footer

Auto-refresh: 30 seconds via `setInterval`.

### Config: config.json
Three main sections:
1. `filter` — token quality thresholds
2. `trade` — execution parameters (amount, slippage, priority fee)
3. `exit` — TP/SL/trailing/partial exit rules
4. `risk` — daily limits, emergency stops, pause rules

### PM2: ecosystem.config.cjs
Environment: CHARON_API_KEY in env block.

## Key Design Decisions

1. **DRY RUN first** — simulate trades before risking real money
2. **Quality score** — weighted scoring system for token selection
3. **Partial exits** — sell 50% at +40%, let rest ride with trailing
4. **Break-even stop** — move SL to entry after +15% gain
5. **Daily loss limit** — stop trading if daily loss exceeds threshold
6. **Consecutive loss pause** — pause after 3 losses in a row
