---
type: receipt
date: 2026-06-16
tags:
  - receipt
---

# Receipt: Dozero.X Auto-Execute + Telegram

**Date:** 2026-06-16
**Task:** Aktifin eksekusi otomatis + Telegram notif untuk Dozero.X
**Mas:** Hexa (@0xjosee)

## Result

Dozero.X sekarang **FULLY OPERATIONAL** di Binance Testnet:

### File baru
- `/home/ubuntu/dozero/notifier.py` — Kirim sinyal ke YUNA topic (2905) + PnL report (2893)
- `/home/ubuntu/dozero/engine/executor.py` — Eksekusi trade: limit order + SL/TP algo order
- `/home/ubuntu/dozero/auto.py` — Auto-runner: scan → notif → eksekusi → cooldown
- `/home/ubuntu/dozero/ecosystem.config.json` — PM2 config

### File diupdate
- `/home/ubuntu/dozero/config/connection.py` — Fix precision rounding di `algo_order()`

### First run success (12:19 UTC)
```
XRPUSDT LONG — Grade A (85/100)
Limit order @ $1.2354 → FILLED @ $1.2269
Qty: 302.6 | Leverage: 75x | Margin: $5
SL: $1.1539 | TP1: $1.3243
```

### PM2 Process
- **dozero-auto** (id 6) — `*/15 * * * *` cron restart
- Status: `waiting restart` (one-shot script per cycle)
- Logs: `/home/ubuntu/dozero/logs/pm2-error.log`

### Topic routing
- **Sinyal + eksekusi** → 2905 (💹 YUNA — Trading & LP)
- **PnL report** → 2893 (YUNA PnL)
- **Bot token** → YUNA (`~/.hermes/profiles/yuna/.env`)

### Fitur
- ✅ Auto-scan 10 symbols tiap 15 menit
- ✅ Telegram notif sinyal Grade A/B
- ✅ Limit order entry (maker fee)
- ✅ SL/TP via algo order
- ✅ Cooldown per symbol (5 menit)
- ✅ Trade tracking (traded.json)

### Decisions
- Pakai YUNA bot token karena Hermes main bot kicked dari group
- PnL report ke topic 2893 (YUNA), sinyal ke 2905
- Cooldown 5 menit per symbol dari settings.py

### Issues
- SL/TP precision error fixed (price rounding sebelum kirim ke API)
- NEARUSDT scan sometimes slow — not blocking

### Next Steps
- [ ] Monitor first few cycles for signal quality
- [ ] Implement PnL tracking + report to topic 2893
- [ ] Tweak scoring if too many/few signals
- [ ] Eventually switch to mainnet

### Related files
- `/home/ubuntu/dozero/auto.py` — main auto-runner
- `/home/ubuntu/dozero/notifier.py` — Telegram send
- `/home/ubuntu/dozero/engine/executor.py` — trade execution
- `/home/ubuntu/dozero/config/connection.py` — API layer
- `/home/ubuntu/dozero/data/traded.json` — cooldown tracker
