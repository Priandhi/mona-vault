---
type: kanban
tags:
  - kanban
---

# 💹 YUNA — The Strategist
# Trading & LP Operations Board
> Last Update: 2026-06-22 11:20 CST
> **Focus:** PROJECT VIOLET v2 — Smart Money + Order Flow (REPLACED Dozero.X Jun 21)
> **Exit criteria:** WR stabil >60% + max DD <10% → lanjut mainnet

## 📋 BACKLOG
- [ ] Setup WR daily tracker PV (cron → topic 2893)
- [ ] Setup losing trade analyzer (weekly deep-dive)
- [ ] Per-symbol blacklist (skip pairs WR < 30% setelah 5+ trades)
- [ ] Backtest PV di 7-day historical data
- [ ] Fix OI history API noise (engine/data.py: testnet endpoint returns empty)
- [ ] Update settings.py BALANCE kalau modal berubah significantly

## 🔄 IN PROGRESS
- **PROJECT VIOLET v2** — DEPLOYED Jun 22 14:30 ✅
  - PM2 cron_restart firing every 15 min
  - Cycle 1: 14:29:20, Cycle 2: 14:30:00 (verified)
  - No signals yet (sideways market, BTC/ETH both 0/9 FAIL)
  - Baseline WR: 0/0 (awaiting first trade)

## 👀 PENDING REVIEW
- (none)

## ✅ DONE
- [x] **Dozero.X → PROJECT VIOLET transition** — Hexa pivot Jun 22 ✅
  - Dozero archived ke `/home/ubuntu/dozero-backup-20260621_214538/`
  - PV v2 found di `/home/ubuntu/project-violet/` (built Jun 21 21:50-22:24)
  - Skill `project-violet-engine` di default profile
  - See: 2026-06-22-dozero-to-violet-transition.md
- [x] **PROJECT VIOLET v2 DEPLOY** — Hexa option B (step-by-step) Jun 22 ✅
  - Step 1: BALANCE 4300 → 4043.49 (API actual)
  - Step 2: ecosystem.config.json (PM2, cron_restart, autorestart=false)
  - Step 3: cron job yuna-violet-scan (wrapper script, 15-min interval)
  - Step 4: test BTCUSDT/ETHUSDT analyze (0/9 FAIL, sideways — correct skip)
  - Step 5: PM2 started, cron_restart firing 14:30/14:45/15:00/...
  - See: 2026-06-22-project-violet-deploy.md
- [x] **TUNING MODE ACTIVATED** — Hexa "testnet = tuning ground" Jun 22 ✅
  - SCAN_MODE "curated" → "volume" (50 pairs by $10M+ volume)
  - Scan interval 15min → 5min (more data points)
  - Log ALL signals/results ke signals.jsonl (for tuning analysis)
  - Tuning report: daily 23:00 UTC auto + on-demand /tuning
  - 196 scans in 1h, 100% FAIL (sideways market)
  - See: 2026-06-22-tuning-mode-report.md
- [x] **Dozero.X** full history (legacy, archived):
  - SMC Bot implementation, Cron Jobs, Connection ✅ (2026-06-15)
  - BANK/INX/AR Post-mortem ✅ (2026-06-16)
  - Risk Filter Overhaul ✅ (2026-06-16)
  - SL/TP Fix (-$65.92 realized) ✅ (2026-06-16)
  - PnL Script Bug Fix ✅ (2026-06-16)
  - Scanner Self-Deadlock Fix ✅ (2026-06-17)
  - Proxy Support + 50ms Throttle ✅ (2026-06-18)

## 🎯 PROJECT VIOLET v2 Spec

### Risk Config (Scalable)
- BALANCE: $4,300 (config, actual API: $4,043.60)
- Leverage: 20x
- Margin/trade: 2.1% balance ($90 @ $4300)
- SL: 4% (WAJIB validate_leverage_sl)
- TP: R:R 1:1 (30%) → 1:2 (30%, main) → 1:3 (40%, runner)
- Min RR: 1.5
- Max Risk: 2% balance
- Daily Loss Limit: -3R
- Max Drawdown: 15% → evaluasi

### Confluence Scoring
| Score | Grade | Action |
|---|---|---|
| 7-9 | ELITE | Execute — full confidence |
| 5-6 | GOOD | Execute — std size |
| 3-4 | WEAK | NO TRADE |
| <3 | FAIL | NO TRADE (no override) |

### Default Symbols
- BTCUSDT, ETHUSDT

### MTF Alignment
- Daily → H4 → H1 → M15

## 📊 Success Metrics
- **Min trades:** 30+ per minggu
- **Win rate:** > 60%
- **Max drawdown:** < 10% dari balance
- **Avg win / avg loss:** > 1.5 (R:R)
- **Sharpe ratio:** > 1.0
