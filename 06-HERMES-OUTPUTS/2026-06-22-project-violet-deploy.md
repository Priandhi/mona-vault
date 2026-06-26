# 2026-06-22 — PROJECT VIOLET DEPLOY (YUNA)

## Task
Hexa approved option B (step-by-step deploy). Execute steps 1-5:
1. ✅ Update settings.py BALANCE
2. ✅ Bikin PM2 ecosystem config
3. ✅ Setup Hermes cron job
4. ✅ Test single run
5. ✅ Start PM2 process

## Result

### Step 1 — BALANCE sync
- `/home/ubuntu/project-violet/config/settings.py`
- `BALANCE = 4300.0` → `BALANCE = 4043.49` (API actual)
- Computed: margin $84.91, risk $80.87, range $70-108

### Step 2 — PM2 ecosystem
- `/home/ubuntu/project-violet/ecosystem.config.json`
- name: project-violet
- script: run_cron.py
- cron_restart: */15 * * * * (every 15 min)
- autorestart: false (cron_restart only, prevent 1-min autorestart loop)
- env: PROXY_URL="" slot ready
- logs: `/home/ubuntu/project-violet/logs/pm2-{out,error}.log`

### Step 3 — Hermes cron job
- Wrapper: `/home/ubuntu/.hermes/profiles/yuna/scripts/yuna_violet_cron.py` (chmod +x)
- Cron: `yuna-violet-scan` ID `483b2e0869ca`, schedule `*/15 * * * *`, no_agent, deliver origin

### Step 4 — Test runs
- BTCUSDT @ $64,172.70: 0/9 FAIL (sideways, premium) — no tradeable
- ETHUSDT @ $1,736.78: 0/9 FAIL (sideways, premium, bullish absorption) — no tradeable
- Engine behaves correctly: skip sideways markets, no fake signals

### Step 5 — PM2 deploy
- 14:29:20 first cycle (manual start)
- 14:30:00 second cycle (cron_restart fired) ✅
- 14:30:01 ETHUSDT analyzed
- Status: "stopped" between cycles (expected — autorestart=false, cron_restart fires it)
- Cron + PM2 working in tandem

## Decisions
- **autorestart: false** — prevent 60s autorestart loop (was happening with autorestart=true). Cron_restart handles the 15-min schedule.
- **Both PM2 + Hermes cron** — defense in depth:
  - PM2: log ke file, process management
  - Cron: signal → Telegram via origin delivery
  - If PM2 dies, cron still works (independent)
- **BALANCE hardcoded** at 4043.49 — sync sekali, must update kalau modal berubah significantly
- **OI history API error** — non-fatal, testnet OI hist endpoint sometimes returns empty. Engine continues with other signals.

## Issues
- ⚠ OI history endpoint (testnet) returns empty → ERROR log spam
  - Non-fatal, doesn't affect trade decisions
  - Future: suppress this specific error or fall back to current OI only
- ⚠ Script exits cleanly with status 0 — autorestart=false was the fix (was restarting every 60s before)
- ⚠ 2 OI errors per cycle (1 per symbol) — log noise

## Files Created/Modified
- `/home/ubuntu/project-violet/config/settings.py` (BALANCE)
- `/home/ubuntu/project-violet/ecosystem.config.json` (NEW)
- `/home/ubuntu/.hermes/profiles/yuna/scripts/yuna_violet_cron.py` (NEW, chmod +x)
- `/home/ubuntu/.hermes/profiles/yuna/cron/jobs.json` (added yuna-violet-scan)

## Operations
- Manual run: `cd /home/ubuntu/project-violet && python3 run.py --analyze --symbol BTCUSDT --testnet`
- PM2: `HOME=/home/ubuntu pm2 [start|stop|restart|logs] project-violet`
- Cron job: Hermes auto-fires every 15 min
- Logs: `tail -f /home/ubuntu/project-violet/logs/pm2-out.log`

## Next Steps
1. Monitor first signal (waiting for ELITE/GOOD setup)
2. Track WR baseline (target: >60%, current 0/0 = n/a)
3. If 24h no signal: lower threshold or add symbols
4. Future: fix OI history API noise

## Status
✅ DONE — PROJECT VIOLET v2 fully deployed, cycle 1+2 verified, awaiting signals
