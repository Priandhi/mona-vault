---
date: 2026-06-15
agent: MONA
task: Remove FolaPlay integration (user said "stopp ribet hapus folaplay semua")
---

# ICLIX — Remove FolaPlay Integration

## What user wanted
"stopp ribet hapus folaplay semua" — stop the folaplay rabbit hole, remove everything.

## What got removed

### Backend (`server.js`)
- `import * as StreamingSources from './services/streaming-sources/index.js'`
- `/api/streaming/sources` endpoint
- `/api/streaming/list/:source` endpoint
- `/api/streaming/list` endpoint
- `/api/proxy/reverse/*` (the entire reverse proxy block + `apiRewriteScript()` helper)
- Comment "===== Streaming (Live TV) sources =====" block

### Backend (filesystem)
- `backend/services/streaming-sources/folaplay.js` (scraper)
- `backend/services/streaming-sources/index.js` (aggregator)
- `backend/services/streaming-sources/maxstream.js` (honest stub)
- `backend/services/cache/folaplay.json` (cache)
- `backend/cache/folaplay.json` (cache, 2nd location)

### Frontend (`LiveTV.jsx`)
- `FolaplayCard` component
- FolaPlay section (live matches, highlights, special, extended)
- `useEffect` to fetch from `/api/streaming/list/folaplay` (3 min auto-refresh)
- `folaplay` state, `folaplayLoading`, `folaplayError`, `lastUpdated`
- Loading state for FolaPlay embed
- FolaPlay-specific CSS (`.channel-card-live`, `.live-iframe`, etc) — kept some, removed unused

## What stayed

### Live TV page
- 27 static HLS channels (beIN Sports World Cup 2026, beIN Español, TVRI Sport, Trans7, Trans TV, MetroTV, tvOne, BeritaSatu, BTV, Garuda TV, MBG, Indonesiana, Bandung TV, Banten TV, BRTV, Caruban TV, Padang TV, Batam TV, Balikpapan TV, Banjar TV, AFBTV, Al-Iman, Alwafa Tarim, Angel TV, Ashiil TV, Astha TV, Biznet Adventure)
- Category filter (Semua / Sports / Berita / Hiburan / Lokal / Agama)
- HLS.js modal player (tested: Trans7 readyState=4 = playing)
- All existing CSS + components

## Test results

```
=== LIVE TV PAGE ===
title: ICLIX - By Hexa
sections: ["Channel TV (HLS)"]                ← only 1 section, no FolaPlay
allCards: 27                                  ← all 27 local TV cards
liveCards: 0                                  ← no folaplay cards
noFolaplay: true                              ← no folaplay references
noFolaCard: true                              ← no .channel-card-live

=== TRANS7 MODAL ===
modal: true
title: "Trans7"
hasVideo: true
readyState: 4                                 ← HAVE_ENOUGH_DATA = playing
```

## Process
```
iclix-api  online  (PM2 #2, 72mb RAM)
node -c server.js  OK (no syntax errors)
```

## Receipts (chronological)
1. `2026-06-15-mona-iclix-folaplay-maxstream.md` — original backend scrapers
2. `2026-06-15-mona-iclix-livetv-frontend.md` — frontend with FolaPlay + new-tab
3. `2026-06-15-mona-iclix-folaplay-in-iframe.md` — in-iframe via reverse proxy
4. `2026-06-15-mona-iclix-remove-folaplay.md` — this one (removal)

Net: FolaPlay removed. Live TV page is back to its pre-FolaPlay state + 3 sports channels (beIN, TVRI Sport).
