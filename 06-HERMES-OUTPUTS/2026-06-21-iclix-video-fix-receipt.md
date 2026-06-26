---
type: receipt
date: 2026-06-21
tags:
  - receipt
  - iclix
  - streaming
---

# Video Player Critical Fix — 2026-06-21

## Task
**Mas interrupt:** Semua video tidak bisa diputar + buka tab iklan di semua content (anime/film/series/drama). Cron dilanjut nanti.

## Root Causes Ditemukan

### 🐛 Bug #1: Iframe tidak ada sandbox → popup ads
- `VideoPlayer.jsx` iframe TIDAK punya atribut `sandbox`
- 12 iframe sources tanpa sandbox → situs embed (terutama `rivestream.live`) bisa:
  - Buka popup window baru (iklan tab)
  - Navigate parent window (tab hijack)
- **Fix**: Tambah `sandbox="allow-scripts allow-same-origin allow-forms allow-presentation allow-autoplay"` + `referrerPolicy="no-referrer-when-downgrade"`
- `allow-popups` SENGAJA TIDAK di-include (block popup ads)
- `allow-top-navigation` SENGAJA TIDAK di-include (block tab hijack)

### 🐛 Bug #2: rivestream.live = ad network
- `rivestream.live` 302 redirect ke `effectivegatecpm.com` (ad network!)
- File `backend/server.js` line 372, 376, 385, 389 — 4 occurrences di iframe chain
- **Fix**: Hapus semua 4 occurrences dari TV chain + movie chain
- Chain sekarang 11 sources (turun dari 12)

## Verification
- ✅ Frontend built successfully (`✓ built in 8.95s`)
- ✅ iclix-api restarted (PID 933461)
- ✅ `pm2 restart iclix-api` → online 96.3MB
- ✅ Browser test: `https://iclix.web.id/movie/1084244`
  - Iframe load: vidlink.pro → vidsrcme.ru → vidsrc.to (auto-fallback)
  - Sandbox attribute confirmed live: `allow-scripts allow-same-origin allow-forms allow-presentation allow-autoplay`
  - Click-to-play overlay "Play (No Ads)" tampil (cross-origin iframe autoplay policy)
  - **Tidak ada popup tab iklan** (sandbox block)
- ✅ Backend chain verified: 11 sources, no rivestream

## Files Modified
- `/home/ubuntu/iclix/frontend/src/components/VideoPlayer.jsx` — added sandbox + referrerPolicy
- `/home/ubuntu/iclix/backend/server.js` — removed rivestream.live (4 occurrences)

## Decisions
- Pakai sandbox pattern sama persis dengan AnimeDetail.jsx (SANDBOX_BLOCK_ADS)
- Tidak pakai `allow-popups` atau `allow-top-navigation` (block iklan)
- Hapus rivestream dari chain sebagai defense-in-depth (sandbox sudah cukup, tapi cleaner)

## Issues (non-critical, separate tasks)
- ⚠️ `/api/content/movies` returns 0 results (content DB kosong — berbeda masalah dengan video)
- ⚠️ Auto-fallback 8s per source = 88s max untuk 11 sources — agak lama tapi works
- ⚠️ VidLink embed butuh ~3-5s untuk load (Next.js SPA) — kompetisi dengan 8s timeout

## Next Steps
1. Lanjut cron config update (yang sempet di-pause)
2. Investigate /api/content/movies=0 (content DB issue, bukan video)
3. (Optional) Optimize auto-fallback: vidlink.pro lebih lama (15s) karena prioritas Indo subs
