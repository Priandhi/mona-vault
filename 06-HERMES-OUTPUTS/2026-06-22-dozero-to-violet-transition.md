---
type: receipt
date: 2026-06-22
tags:
  - receipt
---

# 2026-06-22 — DOZERO→PROJECT VIOLET TRANSITION (YUNA)

## Task
Hexa said "udah pake engine dan skill baru" — pivot dari Dozero.X ke PROJECT VIOLET v2.

## What Hexa Means
- **Dozero.X is DEPRECATED** (folder archived ke `dozero-backup-20260621_214538/` Jun 21 21:45)
- **PROJECT VIOLET v2** = new engine, built Jun 21 21:50-22:24 di `/home/ubuntu/project-violet/`
- Skill `project-violet-engine` ada di `/home/ubuntu/.hermes/skills/crypto/` (default profile, NOT yuna)

## Findings

### PROJECT VIOLET v2 — current state
- ✅ Engine built (engine/{data, smc, orderflow, signal, executor, binance_executor, utils}.py)
- ✅ Telegram formatter (Bab 15.2 format)
- ✅ run.py manual entry: `python3 run.py --scan` atau `--analyze --symbol BTCUSDT`
- ✅ run_cron.py untuk cron mode (silent unless signal)
- ✅ Rulebook v2 PDF di docs/
- ✅ Testnet keys di `~/.hermes/profiles/yuna/.env`
- ❌ NOT in PM2 (cuma charon-bot + meridian running)
- ❌ NO cron job (soft-stop cron paused Jun 21 14:12)
- ❌ Empty data/ dan logs/ folders — NEVER run yet

### YUNA spec PV v2 (settings.py)
- BALANCE $4300, 20x lev, 2.1% margin ($90/trade)
- SL 4%, TP R:R [1:1/30%, 1:2/30% main, 1:3/40% runner]
- MIN_RR 1.5, MAX_RISK 2% bal, DAILY_LOSS -3R
- Scoring: 7-9 ELITE / 5-6 GOOD / 3-4 WEAK / <3 FAIL (NO TRADE)
- WAJIB validate_leverage_sl
- Default symbols: BTCUSDT, ETHUSDT

### PM2 current list
- charon-bot (SOYU) — online 14h, 1 restart
- meridian (LP) — online 14h, 6 restarts
- iclix-api — online
- pm2-logrotate — online

### Balance check
- Last known: $4,043.60 testnet (no positions, no orders)
- PV setting: BALANCE = 4300.0 (hardcoded — need update ke actual)

## Decisions
- Dozero folder DIARSIPKAN, jangan disentuh lagi (per Hexa)
- YUNA primary engine = PROJECT VIOLET v2
- PM2 entry UNTUK PV — BELUM DIBUAT (awaiting Hexa go)
- Cron UNTUK PV — BELUM DIBUAT (awaiting Hexa go)
- BALANCE di settings.py = 4300 (hardcoded, tidak ambil dari API balance)

## Issues
- PV never run → zero historical data, no baseline WR
- BALANCE hardcoded 4300 vs API balance 4043.60 — discrepancy
- PM2 dozero-auto hilang, belum ada PV entry
- charon + meridian masih jalan (bukan domain YUNA)

## Files Referenced
- `/home/ubuntu/project-violet/run.py` (main entry)
- `/home/ubuntu/project-violet/run_cron.py` (cron-friendly)
- `/home/ubuntu/project-violet/config/settings.py` (BALANCE, leverage, RR, dll)
- `/home/ubuntu/project-violet/engine/executor.py` (validate_leverage_sl)
- `/home/ubuntu/project-violet/telegram/formatter.py` (Bab 15.2)
- `/home/ubuntu/.hermes/skills/crypto/project-violet-engine/SKILL.md` (skill)

## Next Steps
1. **HEXA decide:** deploy PV cron + PM2 sekarang atau nanti?
2. Kalau gas:
   - Bikin `/home/ubuntu/project-violet/ecosystem.config.json` (PM2)
   - Setup cron job (refer to `run_cron.py`)
   - Update settings.py BALANCE ke $4,043.60 (API actual)
   - Test single run: `cd /home/ubuntu/project-violet && python3 run.py --analyze --symbol BTCUSDT`
3. Set initial baseline WR (30 trades minimum = ~1 minggu PV running)

## Status
✅ DONE — engine found, transition acknowledged, awaiting Hexa deploy signal
