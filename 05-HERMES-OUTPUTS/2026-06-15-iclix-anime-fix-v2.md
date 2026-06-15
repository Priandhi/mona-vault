# Receipt: ICLIX Anime Section Fix
**Date:** 2026-06-15
**Task:** Fix ICLIX anime — video dead, anime gak lengkap, episode gak lengkap

## Result
✅ **Full pipeline berfungsi:**
- **AniNeko.to scraper** (scraper baru) — episode list + embed video dari anineko.to (Gogoanime successor)
- **AniList API** (GraphQL metadata) — ganti Jikan/MAL, no rate limit drama
- **Direct HLS streaming** — extract m3u8 dari vibeplayer.site, play via HLS.js + proxy
- **Embed proxy** — Playwright fallback buat video yang ga punya direct m3u8
- **Auto-source switching** — AniList → AniNeko search by title, merged results

## Stats
| Before | After |
|--------|-------|
| 165 anime (dead embeds) | **214 anime** |
| Video expired | **64+ anime HLS HD** (360p/720p/1080p) |
| BLEACH partial | **366 episodes** |
| Oploverz 18s Playwright | **2-3s HTTP direct** |

## Files Changed
- `backend/services/anime-sources/anineko.js` — **NEW** (AniNeko.to scraper)
- `backend/services/anime-sources/anilist.js` — **NEW** (AniList GraphQL)
- `backend/services/anime-sources/index.js` — Rewritten (merged sources, title matching)
- `backend/server.js` — Detail route: auto-search AniNeko by title
- `frontend/src/pages/AnimeList.jsx` — Badges: AL (AniList), NK (AniNeko)
- `frontend/src/pages/AnimeDetail.jsx` — Native HLS.js, source routing, first-ep autoplay

## Decisions
- **Ganti Oploverz/MAL** → AniNeko.to + AniList karena embed Oploverz expired semua
- **Direct HLS > Playwright proxy** — ekstrak m3u8 dari vibeplayer, skip Playwright buat anime
- **Title-based matching** — fuzzy match AniList → AniNeko by title (60% threshold)

## Issues Found & Fixed
1. "invalid AniList ID: undefined" — missing `url` field in merged items (FIXED)
2. Video player empty/iframe — switched to native HLS.js with proxied m3u8 (FIXED)

## Next Steps
- Cari lebih banyak video source & episode terbaru
- Perbaiki desain web
