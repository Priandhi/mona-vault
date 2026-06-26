# ICLIX Subtitle Auto-Generator — DONE

**Date:** 2026-06-18
**Task:** Build subtitle auto-generator like IDLIX

## Results

### Subtitle System (FULLY WORKING)
- VidLink embed already has 11 subtitle tracks including Indonesian
- Subtitle source: cc.boopigcdn.com (WebVTT format)
- Languages: Indonesian, English, Arabic, German, French, Malay, Spanish, Thai, Turkish, Portuguese, Chinese

### Changes Made
1. **scraper.js** — Extract subtitle track `<track>` elements from VidLink Playwright scrape
2. **scraper.js** — Store subtitles in cache entry + resolve output
3. **server.js** — `/api/play` and `/api/resolve` return `subtitles` array
4. **multi-source-resolver.js** — Cache includes subtitles
5. **VideoPlayer.jsx** — Load subtitle tracks as `<track>` elements, auto-enable Indonesian, CC button with language selector

### Bug Fixes
- Double-proxy bug: `/api/resolve` was wrapping already-proxied m3u8 URLs
- Cache stale: Reduced TTL from 6h to 2h
- Scraper resolve missing subtitles: `scrapePlaywright` resolve didn't include `subtitles` field

### How It Works
1. User clicks play
2. VideoPlayer calls `/api/resolve` or `/api/play`
3. Scraper runs VidLink Playwright, extracts m3u8 + subtitle tracks
4. Response includes `subtitles: [{label, srclang, src}]`
5. VideoPlayer creates `<track>` elements for each subtitle
6. Indonesian subtitle auto-enabled by default
7. CC button allows switching languages or turning off

### Verified
- Beyond Evil (TMDB 116612) — 11 subtitle tracks, Indonesian "Bukan apa-apa." visible
- Alas Roban (TMDB 1497348) — confirmed working
