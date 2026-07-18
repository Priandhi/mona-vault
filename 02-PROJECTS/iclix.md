---
type: project
status: settled
priority: high
tags:
  - project
  - iclix
  - streaming
---
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

## IDLIX Design Reference (2026-06-18)
- Full design specs saved to: `04-RESOURCES/iclix-idlix-design-reference.md`
- Hero banner: Full HD backdrop, trailer, metadata, action buttons, production logos
- Episode list: 2-column grid, thumbnail overlays, season selector, sort controls
- Style specs: Colors, typography, spacing, border-radius
- Layout diagrams: Hero banner + Episode grid
- Implementation checklist: 4 phases (Hero, Episodes, Cards, Polish)

## UI/UX Audit (2026-06-18)
- Full audit saved to: `04-RESOURCES/iclix-ui-ux-audit-2026-06-18.md`
- P1 bugs: rating 0.0, content duplikat, placeholder kosong
- P2 design: text kecil, carousel arrows, app "SOON", section headers
- P3 features: personalisasi, continue watching, hover preview, trailer auto-play, sub indo badge, watchlist button

## Video Resolver Research (2026-06-18)
- Full research saved to: `04-RESOURCES/iclix-video-resolver-research.md`
- VidSrc chain scraper: vidsrc.to → vsembed.ru → cloudnestra.com → m3u8
- Pure HTTP request, no browser needed
- Sources: NetMirror (Netflix), video-api (all platforms), IDLIX downloader reference

## Kanban
- [x] Add FolaPlay + MaxStream TV to ICLIX — 2026-06-15
- [x] Live TV frontend integration with FolaPlay — 2026-06-15
- [x] Embed FolaPlay IN-ICLIX via reverse proxy (no more new tab) — 2026-06-15
- [x] ICLIX UI/UX overhaul (P1+P2+P3) — SETTLED (user dropped)
- [x] Integrate VidSrc chain scraper — SETTLED (user dropped)
- [x] Fix folaplay highlight image extraction — SETTLED (user dropped)
- [x] Build m3u8 extractor — SETTLED (user dropped)
- [x] Add more live sources — SETTLED (user dropped)

## Receipts
- `06-HERMES-OUTPUTS/2026-06-15-mona-iclix-folaplay-maxstream.md` — backend scrapers
- `06-HERMES-OUTPUTS/2026-06-15-mona-iclix-livetv-frontend.md` — frontend integration
- `04-RESOURCES/iclix-ui-ux-audit-2026-06-18.md` — UI/UX audit
- `04-RESOURCES/iclix-video-resolver-research.md` — Video resolver research
