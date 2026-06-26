---
type: receipt
date: 2026-06-16
tags:
  - receipt
  - iclix
  - streaming
---

# Receipt: ICLIX New Embed Sources — 2026-06-16

**Task:** Cari embed sources baru yang lebih bagus & reliable untuk ICLIX streaming.

## Testing Methodology
Tested 40+ embed source URLs against movie TMDB 1339713 (Obsession) and TV series TMDB 200709 (Weak Hero).

## Current Sources Status
| Source | Movie | TV Series | Notes |
|--------|-------|-----------|-------|
| VidLink.pro | ✅ 200 (55KB) | ✅ 200 (17KB) | Primary source, uses JWPlayer |
| Vidsrc.to | ✅ 200 (2.5KB) | ❌ | Wraps vsembed.ru (same provider) |
| vsembed.ru | ✅ 200 (58KB) | ❌ | Direct player with HLS |
| Vidsrc.in | ✅ 200 (1.2KB) | ❌ | Small stub page |

## New Sources Found & Added
| Source | Movie | TV Series | Status |
|--------|-------|-----------|--------|
| **multiembed.cc** | ✅ 200 (46KB) | ✅ 200 (16KB) | **BARU — Full player with server switching** |
| **vidsrc.pm** | ✅ 200 (71KB) | ✅ tested | **BARU — Wraps nextgencloudfabric.com** |

## Files Modified

### 1. `/backend/services/scraper.js`
- **Added 2 new embed sources** to EMBED_SOURCES:
  - `multiembed` → `https://multiembed.cc/embed/movie/{id}` / TV: `.../embed/tv/{id}/1/1`
  - `vidsrc-pm` → `https://vidsrc.pm/embed/{type}/{id}`
- **Increased Playwright timeout** from 10s → 15s per source

### 2. `/backend/server.js`
- **Added 3 new sources** to TV series `/api/series/:id/stream` route:
  - MultiEmbed, Vidsrc PM, Vidsrc.in (as iframe fallbacks)

### 3. `/frontend/src/pages/MovieDetail.jsx`
- **Expanded EMBED_SOURCES from 10 → 12 servers:**
  - Added Server 5 (MultiEmbed)
  - Added Server 6 (Vidsrc PM)
  - Added Server 11 (MultiEmbed V2)
  - Reordered: MultiEmbed & Vidsrc PM prioritized above Rivestream
  - Removed: Vidsrc.in V2 (dead), vsembed V2 (redundant)

## Verification
- ✅ Frontend build succeeded
- ✅ Backend restart succeeded
- ✅ Fresh scrape test: VidLink returned m3u8 for Obsession
- ✅ Multiembed.cc returns full page for both movies & TV

## Recommendations
- Cache TTL of 6 hours is reasonable (VidLink auth tokens expire)
- If TV series still fail, consider adding a queue-based background scraper that pre-caches popular content
