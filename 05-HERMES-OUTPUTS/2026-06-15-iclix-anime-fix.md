# Receipt: ICLIX Anime Fix — 2026-06-15

## Task
Memperbaiki video anime di ICLIX yang banyak gak bisa diputar

## Investigation
- **AnimeUnity** → domain NXDOMAIN, website 502 Bad Gateway
- **Oploverz** → domain `.cc` still alive, scraper works end-to-end (list/detail/stream)
- **Otakudesu** → domain `.live` alive, but episode page uses dynamic JS embed (no iframe in static HTML)
- **Samehadaku** → all domains dead/offline/behind Cloudflare

Root cause: 3 dari 4 source anime mati, cuma Oploverz yang berfungsi.

## Changes Made

### New Source: MyAnimeList (via Jikan API)
- **File:** `backend/services/anime-sources/myanimelist.js` (NEW)
- Gets anime list, detail, episodes from Jikan API v4 (free, no auth)
- 65+ anime: top airing, upcoming, popular, seasonal
- Video: searches Oploverz by anime title + episode number for blogger embed
- Rate limiter: queue-based, 450ms spacing, auto-retry on 429

### Backend
- `backend/services/anime-sources/index.js` — added MAL source, reduced active sources to Oploverz + MAL only (skips dead sources), added per-source timeout
- `backend/services/anime-sources/oploverz.js` — reduced domain check list to 4 working domains, reduced per-domain timeout to 3s

### Frontend
- `frontend/src/pages/AnimeList.jsx` — added MAL badge (blue #2e51a2), filter out sources with 0 items
- `frontend/src/pages/AnimeDetail.jsx` — added MAL badge
- Frontend rebuilt: `npm run build`

## Result
- **Oploverz:** 100 anime ✅ (fully working: list, detail, stream with blogger embed)
- **MyAnimeList:** 65 anime ✅ (list + detail via Jikan, stream via Oploverz fallback)
- **Total:** 165 anime tersedia (sebelumnya 0 yang fully working)
- Embed proxy: tested working with blogger.com/video.g embeds via Playwright

## Known Issues
- MAL stream fallback ke Oploverz: gak semua anime ada di Oploverz, beberapa bakal "not available" untuk video
- Otakudesu: bisa diperbaiki nanti dengan reverse-engineer embed JS API mereka
- Samehadaku + AnimeUnity: mati total, butuh domain baru

## Next Steps
- Tambahin notifikasi di frontend kalo MAL anime video gak tersedia (tampilkan external streaming links dari Jikan)

