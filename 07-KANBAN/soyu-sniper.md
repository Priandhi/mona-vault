# 🎯 SOYU — The Phantom
# Sniper & Alpha Operations Board
> Last Update: 2026-06-16 (Charon PnL report sent to Hexa)

## 📋 BACKLOG
- [ ] Scan token launch minggu ini
- [ ] Setup alpha signal filter
- [ ] Konfigurasi entry/exit parameter
- [ ] Buat watchlist token prioritas
- [ ] Setup alert launch notifikasi
- [ ] Cross-agent: Terima token intel dari YUNA & HAERI
- [ ] **[DONE 2026-06-16]** Charon: 7-layer filter implementation (current basic filter = 20% WR)
- [ ] **[DONE 2026-06-16]** Charon: retune break-even (3%→15%, 1%→5%) + trailing (5%→12%, 3%→8%)
- [ ] **[DONE 2026-06-16]** Charon: cleanup 3 phantom positions (PARQ, 01, AICAST)

## 🔄 IN PROGRESS
- [ ] **Multi-Agent Comms** — Terima instruksi dari MONA & agent lain via inbox

## 👀 PENDING REVIEW
- [ ] Monitor FREDDY + JOE (next 60-90m) — verify v3 filter works
- [ ] If market stays rough, accept 1 trade/day with quality filter

## ✅ DONE
- [x] Charon position + PnL snapshot — 2026-06-16
- [x] Charon fix v1: config retune + phantom guard + cleanup — 2026-06-16
- [x] Charon fix v3: DATA-DRIVEN filter overhaul — 2026-06-16
  - token-filter.js: anti-chase (max 5m +3%), age window (10-120m), maxOrganic 90
  - config.json: 14 filter values retuned, TP ladder [20/30, 40/35, 70/35], trailing +15%/-10%
  - deploy 0.05, maxPos 2, maxTrades 5, maxLoss 0.03, pause after 2 losses
  - **p trade WIN +139.91% / +0.14 SOL** (first winner with new config!)
  - Bot restarted PID 2322233
