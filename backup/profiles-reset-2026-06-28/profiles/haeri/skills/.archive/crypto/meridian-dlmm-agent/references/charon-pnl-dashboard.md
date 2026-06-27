# Charon PnL Dashboard — Web-Based Sniper Bot Tracker

Built June 2026. Express.js + vanilla HTML/CSS/JS. Dark theme matching trading terminal aesthetic.

## Architecture

```
charon-dashboard/
├── server.js              Express backend (port 3456)
├── public/index.html      Frontend (single file, embedded CSS/JS)
├── data/trades.json       Trade history (auto-generated from signals)
├── data/daily-pnl.json    Aggregated daily PnL
├── ecosystem.config.cjs   PM2 config
└── package.json           express + cors
```

## Backend API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/signals` | Live Charon signals (top 50) |
| `GET /api/trades` | Today's trades |
| `GET /api/pnl` | PnL summary (total, win rate, best/worst, avg, risk/reward) |
| `GET /api/daily` | Historical daily PnL |
| `GET /api/health` | Health check |

## Charon API Integration

```
Endpoint: https://api.thecharon.xyz/api/signals
Auth: x-api-key header (NOT Bearer — returns 401)
Cache: 3-minute TTL to avoid hammering
```

Signal fields used:
- `symbol`, `mint` — token identification
- `holders`, `marketCapUsd`, `volume24h`, `liquidityUsd` — quality metrics
- `ageMs`, `bondingComplete` — maturity
- `sourceCount`, `trending` — social proof
- `priceUsd` — current price (used for PnL calculation)

## Trade Generation (Demo Mode)

Since Meridian runs DRY RUN, trades are simulated from Charon signals:
1. Filter signals: `bondingComplete && holders > 100 && volume24h > 5000`
2. Take top 5 qualifying signals
3. Simulate PnL based on signal quality score: `holders/1000 + volume24h/100000`
4. Quality > 1: random +10% to +70%. Quality < 1: random -15% to +25%.
5. Calculate SOL PnL: `pnlPct/100 * 0.1` (deploy amount)

**For LIVE integration:** Replace demo generation with actual position data from Meridian's `state.json` or Meteora portfolio API.

## Frontend Design

Dark theme palette:
- Background: `#121826` (page), `#1a1f2e` (cards)
- Positive: `#00e5a0` (cyan/green)
- Negative: `#ff4040` (red)
- Text: `#ffffff` (values), `#8a91a6` (labels)
- Font: Inter (Google Fonts), weights 400/600/700/800

Layout sections:
1. Header: title + date badge + status badge (PROFIT/LOSS)
2. Hero card: total PnL (large centered value + percentage)
3. Metrics grid (4-col): total trades, win rate, best trade, worst trade
4. Metrics grid (2-col): avg win, avg loss
5. Bottom row: trade progress bar + risk/reward ratio
6. Trades table: today's individual trades
7. Live signals table: Charon signals with holders, mcap, volume, trending
8. Footer: strategy name + timestamp

Auto-refresh: 30-second interval via `setInterval`

## PM2 Deployment

```bash
cd ~/mona-workspace/charon-dashboard
pm2 start ecosystem.config.cjs
```

**PORT:** 3456 (configurable in server.js)

**Environment:** CHARON_API_KEY set in ecosystem.config.cjs env block.

## Telegram Notification Integration (Future)

Pattern for notifying on new trades:
```javascript
// In server.js, after adding a new trade:
if (trade.pnlPct > 0) {
  // Send win notification to topic 947
  await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: CHAT_ID,
      message_thread_id: 947,
      text: `💰 *${trade.symbol}* +${trade.pnlPct}% (+${trade.pnlSol} SOL)`,
      parse_mode: 'Markdown'
    })
  });
}
```

## Connecting to Real Meridian Data

To show actual Meridian positions instead of simulated trades:

1. Read `~/mona-workspace/meridian/state.json` for open positions
2. Read `~/mona-workspace/meridian/lessons.json` for closed positions
3. Merge with Charon signal data for enrichment
4. Calculate real PnL from entry/exit prices

```javascript
// In server.js:
import { readFile } from 'fs/promises';

async function getMeridianPositions() {
  const state = JSON.parse(await readFile(
    path.join(process.env.HOME, 'mona-workspace/meridian/state.json'), 'utf8'
  ));
  return state.positions || [];
}
```
