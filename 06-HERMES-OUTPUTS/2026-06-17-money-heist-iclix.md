---
type: receipt
date: 2026-06-17
tags:
  - receipt
  - iclix
  - streaming
---

# Receipt — Money Heist di ICLIX
**Date:** 2026-06-17
**Task:** Verifikasi ketersediaan Money Heist Spanish + Korea full episode di ICLIX

## Result
✅ **Money Heist (Spanish)** — TMDB 71446
- 3 Seasons, 41 Episode
- ALL episodes streaming via Vidlink (tested S1E1, S1E9, S2E1, S2E8, S3E1, S3E10)
- URL: `/tv/71446`

✅ **Money Heist: Korea — Joint Economic Area** — TMDB 112836
- 1 Season, 12 Episode
- ALL episodes streaming via Vidlink (tested S1E1, S1E6, S1E12)
- URL: `/tv/112836`

## Test Method
- Scraper API endpoint `/api/play/tv/{id}?season={s}&episode={e}` returns m3u8 from Vidlink
- Frontend Series.jsx renders with season selector + iframe player
- No additional scraper/config changes needed — both series already work with existing embed sources

## Notes
- Spanish version: 3 seasons in TMDB (S1=15eps parts 1-2, S2=16eps parts 3-4, S3=10eps part 5)
- Korean version: 1 season, 12 episodes
- Both use Vidlink embed source (via backend scraper)
- Spin-off "Berlin" (TMDB 146176) also available if user is interested
