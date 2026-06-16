# 💹 YUNA — The Strategist
# Trading & LP Operations Board
> Last Update: 2026-06-16
> **Focus:** Improve Dozero.X WR di testnet selama 1 bulan
> **Exit criteria:** WR stabil >60% + max DD <10% → lanjut mainnet

## 📋 BACKLOG
- [ ] Setup WR daily tracker (cron → topic 2893)
- [ ] Setup losing trade analyzer (weekly deep-dive)
- [ ] Per-symbol blacklist (skip pairs WR < 30% setelah 5+ trades)
- [ ] Backtest filter baru di 7-day historical data
- [ ] Setup PnL tracker harian

## 🔄 IN PROGRESS
- [ ] **Dozero.X Risk Filter Overhaul** — Filter baru applied, monitoring WR harian
  - Target: WR > 55% Week 1, > 60% Week 2-4
  - Current: 48.1% (27 trades hari ini, mostly pre-filter)

## 👀 PENDING REVIEW
- [ ] **Dozero.X SMC Engine** — Kalibrasi threshold & backtest

## ✅ DONE
- [x] **Dozero.X SMC Bot** — Implementasi SMC trading engine ✅ (2026-06-15)
- [x] **Dozero.X Cron Jobs** — Scanner 15m + PnL report 4h ✅ (2026-06-15)
- [x] **Dozero.X Connection** — Testnet API + Binance mainnet API ✅ (2026-06-15)
- [x] **BANK/INX/AR Post-mortem** — Closed manually, identified SL/TP failure root cause ✅ (2026-06-16)
- [x] **Dozero.X Risk Filter Overhaul** — Settings + risk + executor rewritten ✅ (2026-06-16)

## 🎯 1-Month Testnet Plan

### Week 1 (Jun 16-22)
- Monitor WR dengan filter baru (margin $5, tier leverage, SL 2-8%, price ≥$0.05)
- Daily report: total trades, WR, PnL, top winners/losers
- Identify: pairs yang masih lolos filter tapi loss

### Week 2-3 (Jun 23 - Jul 6)
- Tighten filter kalau WR < 55%: naikkan MIN_SL_DISTANCE_PCT ke 3%, naikkan score threshold ke 80
- Per-symbol blacklist: pair dengan WR < 30% setelah 5+ trades
- Backtest filter baru di 7-day data, compare dengan old filter

### Week 4 (Jul 7-13)
- Final review: WR, max DD, sharpe ratio
- Decision gate:
  - ✅ WR > 60% + DD < 10% + 20+ trades → **LANJUT MAINNET** (request Hexa)
  - ⚠️ WR 50-60% → iterasi filter, extend 2 minggu
  - ❌ WR < 50% → fundamental strategy issue, pivot ke different approach

## 📊 Success Metrics
- **Min trades:** 30+ per minggu (statistical significance)
- **Win rate:** > 60%
- **Max drawdown:** < 10% dari balance
- **Avg win / avg loss:** > 1.5 (reward:risk)
- **Sharpe ratio:** > 1.0
