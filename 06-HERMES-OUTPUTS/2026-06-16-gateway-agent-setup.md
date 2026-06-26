---
type: receipt
date: 2026-06-16
tags:
  - receipt
---

# Receipt: Gateway Agent Setup — June 16, 2026

## Task
Aktifkan Hermes gateway agents untuk 5 profile yang sudah ada (yuna, soyu, yerin, haeri, mona-bot) — ganti dari polling bot simplified ke Hermes gateway beneran.

## Result
**All 5 gateway agents 🟢 ONLINE** via systemd user services:

| Profile | Service | Topic | Bot |
|---------|---------|-------|-----|
| yuna | hermes-gateway-yuna.service | 2905 💹 YUNA | @YunaStrategistBot |
| soyu | hermes-gateway-soyu.service | 2906 🎯 SOYU | @SoyuPhantomBot |
| yerin | hermes-gateway-yerin.service | 2907 ⛏️ YERIN | @YerinGrinderBot |
| haeri | hermes-gateway-haeri.service | 2908 🍀 HAERI | @HaeriCollectorBot |
| mona-bot | hermes-gateway-mona-bot.service | 2909 🧠 MONA | @MonaOpsBot |

## Changes
- **Topic IDs updated**: 2476-2479 → 2905-2909 (current topic numbering)
- **Profile descriptions**: masing-masing agent dikasih identity sesuai peran (YUNA=trading, SOYU=sniper, YERIN=mining, HAERI=airdrop, MONA=koordinator)
- **Gateway installed**: systemd user services dengan linger enabled (survive logout/reboot)
- **Polling bots dihapus**: agent-yuna/soyu/yerin/haeri/mona PM2 processes deleted
- **Model**: tokenrouter/MiniMax-M3 via 9Router (localhost:20128)
- **Status**: ✅ All connected to Telegram via polling mode

## Key Decisions
- Gateway agents pake profile config yang sudah ada (bukan bikin dari nol)
- Systemd user services lebih reliable daripada PM2 untuk gateway
- Masing-masing agent isolated dengan memori, skills, dan config sendiri
- Format sinyal Dozero.X tetap pake PROJECT VIOLET branding

## Next Steps
- Monitor memory usage (5 gateway agents + 1 default = 6 Hermes processes)
- YERIN & HAERI masih fallback agent_data ke 'yuna' — perlu data sendiri nanti
