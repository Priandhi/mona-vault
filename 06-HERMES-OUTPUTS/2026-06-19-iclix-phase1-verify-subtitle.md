---
type: receipt
date: 2026-06-19
tags:
  - receipt
  - iclix
  - streaming
---

# Receipt: ICLIX Subtitle Auto-Generator + Phase 1 Verification
Date: 2026-06-19

## Task
1. Verify Phase 1 (Video Resolver + Subtitle + Cache) works end-to-end in browser
2. Build Whisper Tiny auto-subtitle generator
3. Fix bugs found during verification

## Result
✅ Phase 1 VERIFIED WORKING in browser:
- Video instant play via HLS.js (no iframe)
- Multi-source resolver with failover (VidLink primary)
- Auto-subtitle generator with Whisper Tiny (75MB)
- VTT cache system (2h TTL)
- Indonesian subtitle auto-enable

## Subtitle System Architecture
```
User clicks play → /api/resolve/:type/:id
  → VidLink scraper returns m3u8 + subtitle tracks
  → VideoPlayer checks: hasIndonesian? 
    → YES: use source subtitle
    → NO: fetch /api/generate-subtitle/:tmdb_id
      → ffmpeg extract audio (10 min limit, proxy URL)
      → Whisper tiny transcribe (auto-detect language)
      → Google Translate → Indonesian
      → Save VTT to /data/subtitles/tmdb_{id}_id.vtt
      → Return VTT content
  → VideoPlayer adds <track> element
  → onload → mode='showing'
```

## Files Created/Modified
- `/home/ubuntu/iclix/backend/services/subtitle-generator.py` — Python pipeline
- `/home/ubuntu/iclix/backend/server.js` — API endpoints (/api/generate-subtitle, /api/subtitle-file)
- `/home/ubuntu/iclix/frontend/src/components/VideoPlayer.jsx` — auto-trigger + track loading
- `/home/ubuntu/iclix/whisper-env/` — Python venv with faster-whisper
- `/home/ubuntu/iclix/backend/data/subtitles/` — VTT cache dir

## Issues Found & Fixed
1. **PATH issue**: Node execFile couldn't find `/usr/bin/env` in PM2 env → switched to `exec` with clean PATH
2. **ffmpeg 403**: Direct URL needed headers → use proxy URL (localhost:3000/api/stream)
3. **ffmpeg timeout**: Full movie (2h) timed out → limit to 10 min audio
4. **Auto-trigger condition**: Only triggered when `subtitles.length === 0` → changed to check `hasIndonesian`
5. **Track not added to video**: `setSubtitles` didn't create `<track>` elements → added useEffect
6. **VTT cues=0**: Browser didn't parse VTT → added onload listener + retry with cues check

## Verified Test
- The Matrix (TMDB 603): 49 segments, EN→ID translation
- Subtitle visible: "Morpheus, garisnya sudah dilacak. Saya tidak tahu caranya."
- CC IND button active
- Cached response: instant (0ms)

## Next Steps
- Phase 3.6: Bug Fixes (rating 0.0, dedup, empty placeholders, carousel)
- Phase 3.3: Card Design Upgrade
- Phase 2: Content Database (500+ Drama Asia + 500+ Anime)
