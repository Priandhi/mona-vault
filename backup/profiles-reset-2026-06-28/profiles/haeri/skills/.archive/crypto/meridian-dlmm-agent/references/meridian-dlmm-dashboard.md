# Meridian DLMM Dashboard — DRY RUN Monitoring

Built June 2026. Express.js + vanilla HTML/CSS/JS. Dark theme with purple accents (Meridian brand).

## Architecture

```
meridian-dashboard/
├── server.js              Express backend (port 3457)
├── public/index.html      Frontend (single file, embedded CSS/JS)
├── data/                  (reserved for future use)
├── ecosystem.config.cjs   PM2 config
└── package.json           express + cors
```

## Backend API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/status` | PM2 status + active config from user-config.json |
| `GET /api/logs` | Parsed Meridian PM2 logs (cycles, screenings, deploys, rejects, errors) |
| `GET /api/config` | Current user-config.json values |
| `GET /api/wallet` | Wallet balance from Helius RPC |
| `GET /api/screening` | Screening analytics (cycles, Charon signals, bot drops, rejects) |
| `GET /api/candidates` | Parsed pool candidates from logs |
| `GET /api/health` | Health check |

## What It Tracks

### From PM2 Logs (meridian-out-0.log)
- **Screening cycles:** Start time, model, steps taken, deploys, rejects
- **Charon signals:** Total fetched, qualifying count, last fetch time
- **Bot filter drops:** Pool name, bot %, threshold
- **Safety blocks:** Reason for rejection
- **LLM errors:** Empty responses, max steps hits
- **Deploys:** DRY RUN or LIVE deploy attempts

### From Config (user-config.json)
All 21 active parameters displayed in a grid with color coding:
- Green: safe values (deploy < 0.15 SOL, SL -15%, TP +5%)
- Yellow: borderline (maxSteps < 8, temperature > 0.5)
- Red: aggressive values (SL < -20%)

### From Wallet (Helius RPC)
Real-time SOL balance + USD estimate.

## Frontend Design

Dark theme palette:
- Background: `#0f1117` (page), `#161923` (cards), `#1c2030` (table rows)
- Purple accent: `#8b5cf6` (Meridian brand)
- Cyan: `#00e5a0` (positive values)
- Red: `#ff4040` (negative/errors)
- Yellow: `#fbbf24` (warnings, DRY RUN badge)

Layout sections:
1. Header: MERIDIAN title (purple) + wallet badge + DRY RUN badge + PM2 status
2. Metrics row 1 (4-col): wallet, screening cycles, candidates found, deploys
3. Metrics row 2 (3-col): LLM model, empty responses, max steps hits
4. Charon signals: total, qualifying, last fetch time
5. Recent screening cycles table: timestamp, model, steps, deploys, rejects
6. Bot filter drops table: timestamp, pool, bot %, threshold
7. Active configuration grid: all 21 parameters with color coding
8. Rejected candidates table: timestamp, type (safety/llm_decision), reason
9. Footer: strategy + timestamp

Auto-refresh: 15-second interval.

## PM2 Deployment

```bash
cd ~/mona-workspace/meridian-dashboard
pm2 start ecosystem.config.cjs
```

**PORT:** 3457 (configurable in server.js)

## Key Findings from First Run

| Metric | Value | Notes |
|---|---|---|
| Screening cycles | 128 total, 81 completed | ~26 minutes of operation |
| Candidates found | 54 | From 128 cycles |
| DRY RUN deploys | 5 | Candidate pool passes filters |
| Charon signals | 89 total, 50 qualifying | 56% pass rate |
| Empty responses | 35 | MiMo blank responses — major issue |
| Max steps hits | 1 | Agent timeout |
| Bot filter drops | Bountywork-SOL (31%), GO-SOL (34.5%), Bountywork-USDC (31%) | Consistent rejections |

## MiMo Empty Response Problem

**CRITICAL FINDING:** MiMo returns empty responses in ~27% of screening cycles (35/128). This wastes API calls and screening time.

Root cause: MiMo model returns blank at higher step counts (steps 5-10). The agent retries each step, burning 60+ seconds per cycle.

Mitigations applied:
- `maxSteps: 10` (down from 15) — faster fail
- `temperature: 0.3` (up from 0.2) — fewer blank responses

If empty responses persist above 20%, consider:
1. Switching to a different model
2. Adding a fallback model for screening
3. Implementing step-level timeout (kill after 30s per step)

## Connecting to Real Meridian Data

The dashboard reads live from:
- PM2 stdout log (`/home/ubuntu/.pm2/logs/meridian-out-0.log`)
- `user-config.json` (config)
- Helius RPC (wallet balance)

For LIVE mode, add position tracking:
```javascript
// Read Meridian state
const state = JSON.parse(fs.readFileSync(
  '/home/ubuntu/mona-workspace/meridian/state.json', 'utf8'
));
// Read lessons
const lessons = JSON.parse(fs.readFileSync(
  '/home/ubuntu/mona-workspace/meridian/lessons.json', 'utf8'
));
```
