# 💹 YUNA — The Strategist
# Trading & LP Operations Board
> Last Update: 2026-06-16

## 📋 BACKLOG
- [ ] Deploy LP SOL-USDC range optimal (waiting wallet funding)
- [ ] Setup PnL tracker harian
- [ ] Konfigurasi notif OOR alert
- [ ] Review posisi futures aktif
- [ ] Laporan trading mingguan template
- [ ] Cross-agent: Kirim signal bagus ke SOYU buat sniper entry
- [ ] **Binance mainnet API key rotation** (401 — perlu Hexa action)

## 🔄 IN PROGRESS
- [ ] **Dozero.X Risk Filter Overhaul** — Filters applied, monitoring WR
  - ✅ Max margin $5 (was $100)
  - ✅ Leverage tiers (high 50x, mid 25x, low 15x)
  - ✅ Min SL 2% / Max 8%
  - ✅ Min price $0.05
  - ✅ Min volume $2M
  - ✅ 1 SL + 1 Main TP (was 5 orders)
  - ✅ Emergency close on SL fail
  - 📊 Waiting 2-3 days WR data

## 👀 PENDING REVIEW
- [ ] **Dozero.X SMC Engine** — Kalibrasi threshold & backtest
- [ ] **Multi-Agent Comms** — Terima instruksi dari MONA & agent lain via inbox

## ✅ DONE
- [x] **Dozero.X SMC Bot** — Implementasi SMC trading engine ✅ (2026-06-15)
- [x] **Dozero.X Cron Jobs** — Scanner 15m + PnL report 4h ✅ (2026-06-15)
- [x] **Dozero.X Connection** — Testnet API + Binance mainnet API ✅ (2026-06-15)
- [x] **BANK/INX/AR Post-mortem** — Closed manually, identified SL/TP failure root cause ✅ (2026-06-16)
- [x] **Dozero.X Risk Filter Overhaul** — Settings + risk + executor rewritten ✅ (2026-06-16)
