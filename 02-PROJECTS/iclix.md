# ICLIX Project

> **Status:** Active development (2026-06-15)
> **Stack:** Vite + React (frontend) / Node.js Express (backend) / TMDB (en-US)
> **URL:** Cloudflared tunnel (Tencent SG blocks all inbound ports)
> **Brand:** Red `#e50914` on black `#000`

## What it is
Netflix-style streaming platform. Movies, TV Series, Anime, Drama Asia, Live TV.

## Key Features
- Movies/TV detail pages with TMDB data
- Anime aggregation (multiple sources via Playwright scrapers)
- Live TV: 27 HLS channels (Indonesia) + FolaPlay real-time sports
- 21+ sub-project (multi-source adult scraper)
- Anti-ads HLS player (custom)

## Tech Notes
- Frontend: `/home/ubuntu/iclix/frontend/`
- Backend: `/home/ubuntu/iclix/backend/`
- PM2: `iclix-api` runs the backend
- Cache: `backend/services/cache/`, `backend/cache/` (note: 2 cache dirs)
- Embed proxy: `backend/services/embed-proxy.js` (Playwright-based, generic)
- Streaming sources: `backend/services/streaming-sources/`

## Live TV Section (2026-06-15)
**Backed by 2 sources:**
1. **FolaPlay** (`folaplay.com`) — real-time live sports. Frontend fetches `/api/streaming/list/folaplay` and displays 4 live matches + highlights. **Click opens modal with iframe loading folaplay via `/api/proxy/reverse/<url>` reverse proxy** — user can interact with folaplay's full Vue SPA inside iclix (solve captcha, browse matches, watch player).
2. **Local HLS** — 24 static Indonesian TV channels (Trans7, Trans TV, MetroTV, etc) + 3 sports (beIN, TVRI). HLS.js in modal.

## Kanban
- [x] Add FolaPlay + MaxStream TV to ICLIX — 2026-06-15
- [x] Live TV frontend integration with FolaPlay — 2026-06-15
- [x] Embed FolaPlay IN-ICLIX via reverse proxy (no more new tab) — 2026-06-15
- [ ] Fix folaplay highlight image extraction (lazy-load not captured in headless) — TBD
- [ ] Build m3u8 extractor for in-modal HLS player — TBD
- [ ] Add more live sources (Vidio free, RCTI+, etc) — TBD

## Receipts
- `05-HERMES-OUTPUTS/2026-06-15-mona-iclix-folaplay-maxstream.md` — backend scrapers
- `05-HERMES-OUTPUTS/2026-06-15-mona-iclix-livetv-frontend.md` — frontend integration
