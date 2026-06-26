---
type: receipt
date: 2026-06-14
tags:
  - receipt
  - iclix
  - streaming
---

# 2026-06-14 — ICLIX Video Playback Fix

## Result
4/4 anime sources working. ALL go through `/api/proxy/embed` (server-side rendered HTML).
Frontend iframe loads our backend URL → no CORS → video plays with user's IP.

## Final approach
**Stop trying to extract videoUrl.** Blogger/YouTube's videoplayback URL is IP-bound.
Even if we extract it, the user's browser can't use it (different IP).

**Instead**: Backend Playwright loads the embed page, returns rendered HTML
to user's browser iframe. Browser sees our backend (same-origin), plays video
using USER's IP via blogger's JS.

## Changes
- `backend/services/embed-proxy.js` — server-side Playwright renderer
- `backend/server.js` — `/api/proxy/embed` returns HTML with `X-Frame-Options: ALLOWALL`
- `frontend/src/pages/AnimeDetail.jsx` — always uses `/api/proxy/embed?url=...`
- `frontend/src/pages/Movie.jsx` — same
- Removed: extract-video.js, proxy/video endpoint (didn't help)

## Known limitations
- First load takes ~12s (Playwright render) — accept for now
- Some embeds (e.g. samehadaku CF-blocked) fall back to episode page directly
- AnimeUnity could be faster (direct mp4 available) but using proxy for consistency

## Next
- User tests in browser
- If specific anime fails, debug that source
