# Receipt: All Bot Polling Setup — June 16, 2026

## Task
Setup 5 Telegram polling bots (YUNA, SOYU, YERIN, HAERI, MONA) di PROJECT VIOLET group — bot bisa diajak chat AI di topic masing-masing.

## Result
**All 5 bots 🟢 ONLINE** via PM2, long polling (not webhook):

| PM2 ID | Name | Topic | Bot |
|--------|------|-------|-----|
| 15 | agent-yuna | 2905 💹 YUNA | @YunaStrategistBot |
| 11 | agent-soyu | 2906 🎯 SOYU | @SoyuPhantomBot |
| 12 | agent-yerin | 2907 ⛏️ YERIN | @YerinGrinderBot |
| 13 | agent-haeri | 2908 🍀 HAERI | @HaeriCollectorBot |
| 14 | agent-mona | 2909 🧠 MONA | @MonaOpsBot |

## Decisions
- **Polling > Webhook**: Webhook via cloudflared tunnel punya masalah routing token dan error 502. Polling works setelah semua bot jadi admin di group (bisa terima update dari forum topics).
- **Generic script**: Semua bot pake `agent_polling_bot.py` — parameter `--bot` menentukan config.
- **Topic isolation**: Masing-masing bot cuma respon di topic sendiri. MONA dulunya `all_topics=True` tapi user protes karena ikut-utan — diubah jadi `False`.
- **AI personality**: Per-bot system prompt — YUNA (trading), SOYU (sniper), YERIN (mining), HAERI (airdrop), MONA (command center/koordinator).
- **HTML safety**: AI response pake `<think>` tag — di-strip via regex, HTML entities di-escape, kirim dengan `parse_mode=None` untuk hindari HTTP 400.
- **Webhook handler di server.js**: Dibiarkan aja (gak dipake tapi gak ganggu).

## Issues
- `parse_mode: null` di JSON body Telegram return 400 — fix: omit field entirely when None.
- `<think>` tag dari Tokenrouter MiniMax-M3 bikin HTML parsing error — fix: strip + escape before send.
- Bot admin status critical untuk forum topic message delivery.

## Next Steps
- SOYU bisa diintegrasi dengan Charon sniper data (agent_data.py)
- YERIN & HAERI perlu agent_data masing-masing (masih fallback ke yuna)
- MONA bisa jadi command center penuh kalo di-allow all_topics lagi (tapi user prefer ga ikut campur)
