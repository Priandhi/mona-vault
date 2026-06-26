---
type: receipt
date: 2026-06-15
tags:
  - receipt
---

# 2026-06-15 — Live TV 5 Channel Nasional Legal

## Task
Replace broken YouTube/HLS channels for 5 Indonesian national TV (SCTV/Global TV/Indosiar/RCTI/ANTV) with legal official sources.

## Result
- SCTV + Indosiar → https://www.vidio.com/live/{id}/embed (XFO: ALLOWALL)
- RCTI + Global TV → https://www.rctiplus.com/tv/{slug} (no XFO)
- ANTV → https://www.vidio.com/search?q=antv (external — no public embed exists)
- Live confirmed via browser test: RCTI shows actual live broadcast, SCTV/Indosiar show "LANJUTKAN MENONTON" gate (1-click play, Vidio age/login wall)

## Decisions
- Vidio embed chosen for SCTV/Indosiar (Emtek group, legal)
- RCTI+ official site chosen for RCTI/Global TV (MNC group, no XFO)
- ANTV: NO public embed exists. Vidio doesn't carry it, antv.com is parked (302→jeffgreenfield), RCTI+ doesn't have it. Used Vidio search page as fallback.
- Added `type: 'iframe'` to LiveTV player for direct URL embeds
- Added `official` badge to each card showing legal source
- Added `external` flag for ANTV — shows "Buka di Vidio" redirect

## Issues
- Initial wrong approach: used YouTube channel IDs (user called out)
- ANTV has NO legal public stream — official site parked, not on Vidio, not on RCTI+
- RCTI+ embed shows "login for live chat" message (non-blocking, video plays)

## Next Steps
- Monitor if Vidio or RCTI+ add ANTV support later
- Consider adding "external player mode" for other national channels as they appear
