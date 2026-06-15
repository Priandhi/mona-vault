---
date: 2026-06-15
agent: MONA
task: Add FolaPlay + MaxStream TV live sources to ICLIX
---

# ICLIX: Add Live TV Sources (FolaPlay + MaxStream TV)

## Goal
Extend ICLIX backend with live TV streaming sources. FolaPlay (folaplay.com) and MaxStream TV (Telkomsel).

## Result

**FolaPlay ✅** — fully working scraper
- `GET /api/streaming/list/folaplay` returns 4 live matches + highlights
- 4 live matches detected on test (Spanyol vs Tanjung Verde, Belgia vs Mesir, Arab Saudi vs Uruguay, Iran vs Selandia Baru)
- All have proper image URLs from `cms-static.folaplay.com`
- 2-min cache (live status changes fast)

**MaxStream TV ⚠️** — honest stub
- The official MAXStream at `maxstream.tv` is Telkomsel's commercial OTT
- Requires authenticated session + Widevine L1 DRM (hardware-level)
- No public unauthenticated API or scraper path exists
- Returned: `{error: "not_implemented", reason: "...", home: "https://maxstream.tv"}`
- This is the honest answer, not a fake "loading" state

## Architecture

Created new `streaming-sources/` folder mirroring `anime-sources/` pattern:

```
backend/services/streaming-sources/
├── index.js       # aggregator
├── folaplay.js    # Playwright-based scraper
└── maxstream.js   # honest stub
```

**FolaPlay scraper** (`folaplay.js`):
- Spawns Python Playwright subprocess (same pattern as animeunity.js)
- Loads `https://folaplay.com/#/home` with stealth UA + navigator.webdriver bypass
- Closes splash ad overlays
- Walks `<h2>` sections: "Pertandingan Langsung" → live, "Highlights" → highlights, "Extended" → extended, "Klip" → special
- For each section, finds cards inside `.horizontal-section` root (parent of `.section-header`)
- Extracts: title (`.movie-title`), image (`img[src|data-src]`), pageUrl (placeholder, no static URL — Vue routes internally)

**API endpoints added** in `server.js`:
```js
GET /api/streaming/sources           // list available streaming sources
GET /api/streaming/list/:source      // list matches from one source
GET /api/streaming/list              // aggregate from all sources
```

## What I Tried First (failed)

1. **Direct API calls** — folaplay's API is signature-protected (`qh=MD5(params + secret)`) + server-side encrypted responses. Without the correct client-side decryption, server returns garbage blob.
2. **JS click via browser** — works for non-overlay clicks, but `.splash-ad-mask` blocks Playwright clicks. Workaround: remove overlay via JS evaluate before scraping.
3. **First selector guess** (`.item`, `a[href*="play"]`) returned 0 results. Site uses Vue SPA with no anchors — clicks are bound via `@click` handler. Real cards use `.match-card` class.

## Discovery (interesting findings)

**Folaplay leaks their entire backend config** at `/static/config.js`:
```js
window.g = {
  api_url: 'https://app.folaplay.com/',
  base_url: 'https://app.folaplay.com/Web/H5/',
  WEB_ID: 'nqQ6SK0W',
  defaultLanguageId: 12,
  firebase: { projectId: 'ott-overseas', apiKey: 'AIzaSy...' },
  imageUrl: 'https://app.folaplay.com/public',
  // ...
}
```
API endpoints discovered via browser network panel:
- `LiveChannel?langID=12&qh=...&w=nqQ6SK0W` — main live channel list
- `view_temp_page_detail?pageid=...` — page-specific content
- `get_starting_view` — splash config
- All require `qh` signature (MD5 of params + secret) + server-side encryption

**Playwright approach is the right call** — bypasses signature/encryption by using a real browser context. The bundle's own decryption logic handles the response transparently.

## Decisions

1. **Stub for MaxStream** instead of fake-loading. Honest > pretend-working.
2. **Image extraction limited** — live matches get real `cms-static` URLs; highlights get placeholder SVGs (loading state never replaced in headless because images are lazy-loaded outside viewport). Could fix with scroll-to-element before scrape — defer to v2.
3. **Cache TTL = 2 min** — live status changes fast, but Playwright launches take ~10s so 2 min minimum.
4. **pageUrl = home placeholder** — Vue handles routing internally, no static URL per match. Frontend would need to use embed-proxy + Playwright to load full play page. (Not implemented yet — out of scope for this task.)

## Issues

- Highlights get placeholder SVG images (loading state). Fix: scroll cards into view before scraping, wait for `img.complete`.
- Frontend Live TV page NOT built yet. Backend returns data; UI is separate task.
- Click-to-play not implemented — would need additional Playwright flow to navigate to match page, capture m3u8 URL, return to embed-proxy.

## Test
```bash
curl http://localhost:3000/api/streaming/sources
# {"sources":[{"id":"folaplay","name":"FolaPlay","type":"live-sports"},{"id":"maxstream","name":"MaxStream TV","type":"live-tv-stub"}]}

curl http://localhost:3000/api/streaming/list/folaplay
# {"live": [{title: "Spanyol vs Tanjung Verde", image: "...", pageUrl: "..."}, ...], "highlights": [...], "fromCache": false}
```

## Next Steps
- [ ] Frontend: Live TV page (grid view of matches, click to play)
- [ ] Folaplay: extract real m3u8 URL from play page (use embed-proxy pattern)
- [ ] Folaplay: scroll cards into view so highlight images load
- [ ] Consider other Indonesian live TV aggregators as alternatives to MaxStream (RCTI+, Vidio free tier, Mivo TV, etc.)
