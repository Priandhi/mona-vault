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
- [ ] Monitor 24-48 jam: WR improvement + phantom prevention

## ✅ DONE
- [x] Charon position + PnL snapshot — 2026-06-16
- [x] Charon fix: config retune + phantom guard + cleanup — 2026-06-16
  - jupiter-executor.js: reject buy if no quote+no price
  - position-manager.js: openPosition() guard against phantom
  - index.js: handle openPosition null return
  - config.json: BE 3%→15% / 1%→5%, trail 5%→12% / 3%→8%, maxHold 60→120m, deploy 0.2→0.1, maxPos 5→3, maxTrades 99→8, maxLoss 1.0→0.05
  - Phantom positions cleaned (3→0)
  - Bot restarted (new PID 2048420)
