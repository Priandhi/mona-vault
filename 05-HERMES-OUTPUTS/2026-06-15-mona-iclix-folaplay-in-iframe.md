---
date: 2026-06-15
agent: MONA
task: ICLIX Live TV — embed FolaPlay IN-ICLIX via reverse proxy
---

# ICLIX Live TV — FolaPlay In-Iframe via Reverse Proxy

## Goal (user request)
"kok lu lasih link sih folaplay nya gua mintanya langsung lihat di iclix" — FolaPlay harusnya bisa dilihat LANGSUNG di dalam iclix, bukan di new tab.

## Result: ✅ FolaPlay loaded inside iclix modal

User clicks FolaPlay match card → modal opens → iframe loads full live folaplay.com (with all interactions working) → user can solve captcha, click match, watch player — all without leaving iclix.

## What I Built

### Backend: `/api/proxy/reverse/<encoded-url>` 
A path-based universal reverse proxy (different from existing `/api/proxy/embed` which was static-HTML capture).

**How it works:**
1. Browser requests `/api/proxy/reverse/<encoded-folaplay-url>`
2. Server fetches the real folaplay.com with spoofed headers (Referer, Origin, UA)
3. **Strips restrictive headers**: X-Frame-Options, CSP, COOP, CORP
4. For HTML responses, **injects**:
   - `<base href="...">` pointing to proxy root
   - Rewrites all `src`/`href`/`action` attributes to absolute proxy URLs (so relative resolution works — base href alone is unreliable when path contains encoded slashes)
   - **API rewriter script** that intercepts `fetch()` and `XMLHttpRequest.open()` and rewrites any URL pointing to `folaplay.com`/`app.folaplay.com`/`cms-static.folaplay.com` to go through the proxy
   - WebSocket interceptor (in case folaplay uses WS)
5. For binary/CSS/JS — passes through transparently
6. **Whitelist security**: only folaplay.com / app.folaplay.com / cms-static.folaplay.com allowed

**Why path-based not query-based**:
First attempt used `/api/proxy/reverse?url=...` with `<base href="...?url=...">`. Browser truncated the query string when resolving relative URLs → asset requests went to `/api/proxy/static/foo.js` (no `?url=`) and got 400'd. Path-based encoding (`/api/proxy/reverse/<encoded-url>`) doesn't have this issue.

### Frontend: `LiveTV.jsx` FolaplayCard reverted
- Click handler: back to `onPlay(card)` (not `window.open`)
- `embedUrl` now uses reverse proxy path: `/api/proxy/reverse/<encoded>`
- iframe gets `onLoad={() => setLoading(false)}` so spinner disappears as soon as folaplay loads
- Loading message updated: "Memuat FolaPlay... Selesaikan slide captcha lalu klik 'WATCH NOW' untuk mulai nonton"
- External link button in modal header kept as fallback (opens folaplay in new tab if user prefers)

## Discovery: Why FolaPlay Needed Reverse Proxy

Earlier attempts failed:
1. **Static HTML capture** (`/api/proxy/embed`): Playwright loaded folaplay, captured `page.content()` after 10s click loop. Returned HTML snapshot. But Vue SPA didn't have time to fully render → no player in iframe.
2. **In-app extraction**: Tried to extract m3u8 URL from folaplay's HLS.js bundle. Response from `LiveChannel` API is encrypted (base64) — decryption key in another encrypted response, and the actual decrypt function is hidden inside the minified app.js bundle. Slide-captcha blocks the player from loading.
3. **Window.open** (the rejected approach): User leaves iclix to watch.

**Reverse proxy is the only path that works** — user's browser runs the full Vue SPA inside our iframe. They solve captcha, browse, watch — all in iclix.

## Test Results

```
=== Backend proxy ===
GET /api/proxy/reverse/https%3A%2F%2Ffolaplay.com%2F%23%2Fhome
→ 200 OK, 1.9KB HTML
→ base tag + API rewriter script injected
→ all assets served with correct content-types (JS, CSS)

=== Frontend flow ===
1. User on /live-tv
2. Click "Spanyol vs Tanjung Verde" FolaPlay card
3. Modal opens with title "Spanyol vs Tanjung Verde"
4. iframe loads: /api/proxy/reverse/https%3A%2F%2Ffolaplay.com%2F%23%2Fhome
5. After ~15s: folaplay fully loaded inside iframe
   - Title: "Folaplay"
   - 4 match cards visible (.match-card)
   - hash: #/home?Id=4540 (auto-loaded first match)
   - Logo + player area rendered
   - User can interact (solve captcha, click matches)
```

## Decisions
1. **Path-based URL** instead of query string — browser drops query when resolving relative URLs
2. **API rewriter JS injected** — folaplay's JS bundle hardcodes `https://app.folaplay.com` so we need to intercept fetch/XHR
3. **Whitelist security** — only folaplay domains allowed (no open proxy)
4. **Kept external link button** in modal — fallback if user prefers new tab
5. **Loading spinner hides on iframe onLoad** — so user sees folaplay UI ASAP, not our spinner

## Issues
- **Slide captcha** still requires user to solve manually (drag the slider). folaplay's goCaptcha blocks the player.
- **Login dialog** might appear after captcha if user isn't authenticated (some content might require login).
- **No persistent session** — each iframe load is a fresh session. If user logs into folaplay in the iframe, they have to re-login on next visit (no cookies shared back to iclix).
- **HLS streaming m3u8 URLs** — if folaplay's HLS player tries to load m3u8 from a CDN that's not in the whitelist, it might fail. Currently cms-static.folaplay.com is whitelisted, but if the actual stream CDN is different (e.g., cloudfront), we'd need to add it.

## Next Steps
- [ ] Check what CDN folaplay's HLS uses (e.g., cloudfront, akamai) — add to whitelist
- [ ] Consider cookie forwarding (let user persist folaplay login across visits)
- [ ] Make FolaPlayCard show "click to watch" hint prominently so user knows iframe will load
- [ ] Add "open in folaplay.com" as a button INSIDE the iframe wrapper (currently only as fallback icon)
