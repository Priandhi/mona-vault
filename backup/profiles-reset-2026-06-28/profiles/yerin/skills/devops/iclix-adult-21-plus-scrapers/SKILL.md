---
name: iclix-adult-21-plus-scrapers
description: Build and operate multi-source 21+ adult content scrapers for ICLIX streaming platform — Eporner, HQporner, XNXX, HDZog. Covers anti-hotlink embed-iframe playback (NOT direct MP4), JSON-LD metadata extraction, site triage (premium-paywalled vs free-aggregator), and password-based age gate. Use when adding 21+ content sources, debugging "video can't play" 403 errors, or evaluating new adult sites for integration.
---

# ICLIX 21+ Adult Content Scraper Pattern

## Architecture (mirrors `iclix-anime-scrapers`)
- **Backend**: Node.js (`/home/ubuntu/iclix/backend/server.js`) — pure `fetch()` to upstream, NO Playwright needed
- **API surface**: `/api/adult/{categories,trending,latest,most-viewed,category/:cat,search,video/:id}`
- **Caching**: None yet (add when traffic warrants); upstream rate-limits are lenient
- **Frontend**: React `Adult.jsx` + `adult.css` — iframe-based player, not `<video>`

## The Core Rule: Embed Iframe, NOT Direct MP4

**Anti-hotlink is universal across adult aggregators.** Direct MP4 URLs (`gvideo.eporner.com`, etc.) return **403 Forbidden** when accessed from outside the official player context. The fix:

```js
// ❌ WRONG — 403 from upstream
embed: 'https://gvideo.eporner.com/abc123/abc123.mp4'

// ✅ RIGHT — official embed iframe, no anti-hotlink
embed: 'https://www.eporner.com/embed/abc123/'
```

The official embed URL is the canonical way sites *want* to be embedded. Returns 200, has no `X-Frame-Options: SAMEORIGIN`, and the site's own player.js handles the auth/signed-URL dance. Don't fight it — use it.

## Metadata Extraction (JSON-LD First, Fallback to HTML)

Adult sites embed rich JSON-LD. **Always check for JSON-LD before falling back to regex**:

```js
// ISO 8601 duration → "9:01" or "1:09:01"
const iso = html.match(/"duration":\s*"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"/i)
if (iso) {
  const h = +iso[1]||0, m = +iso[2]||0, s = +iso[3]||0
  duration = h > 0 ? `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}` 
                   : `${m}:${String(s).padStart(2,'0')}`
}

// Views (InteractionCounter pattern)
const views = html.match(/"userInteractionCount":\s*(\d+)/)?.[1]

// Thumb (og:image is most reliable)
const thumb = html.match(/property="og:image" content="([^"]+)"/i)?.[1]
```

**Fallback hierarchy**: JSON-LD → og: meta → HTML regex → empty string.

## Site Triage (Premium vs Free vs Aggregator)

When user asks "add site X", check these in order:

```bash
# 1. Quick health check
curl -sIL -A "Mozilla/5.0" -m 8 "$URL" | head -1

# 2. Anti-bot fingerprint
curl -sL -A "Mozilla/5.0" "$URL" | grep -iE "cf-ray|cloudflare|challenge" | head -3
```

| Class | Examples | Scrape? | Notes |
|---|---|---|---|
| **Premium paywall** | Vixen, Brazzers, RealityKings, JAVHD | ❌ NO | Bypass = access-without-authorization (UU ITE, DMCA, CFAA) |
| **Aggregator free** | Eporner, HQporner, XNXX, HDZog | ✅ YES | Lenient ToS, full HD common |
| **Illegal aggregator** | bokep*.com, IndoXXI | ❌ NO | Malware + copyright + user-facing risk |
| **Gated platforms** | OnlyFans, Fansly, Telegram premium | ❌ NO | Need auth, account-level scraping violates ToS |
| **CDN short-link** | gvideo.eporner.com, cdn.xnxx.com | ⚠️ Use embed | 403 outside their player |

**Rule**: If the site is premium-paywalled, decline. Don't argue, don't offer "creative" workarounds, don't explain at length. State once, pivot to legal alternatives.

## Source Patterns (Verified)

### Eporner (Primary)
- **API**: `https://www.eporner.com/api/v2/video/search/?query=...&per_page=30&order=latest&format=json` — no auth, generous rate limit
- **Embed**: `https://www.eporner.com/embed/{id}/` — always works in iframe
- **Page scrape**: `https://www.eporner.com/video-{id}/` for fallback metadata
- **Headers**: `User-Agent: ICLIX/1.0` is fine for API; `Mozilla/5.0` for page scrape
- **Query for Indo content**: `query=indonesian` returns ~2,500 real Indonesian videos

### HQporner (HD-First)
- **Home**: `https://hqporner.com` — explicit HD focus, 65k+ videos
- **List pattern**: `/hdporn/{id}-{slug}.html`
- **Player proxy (full chain)**: `/blocks/nativeplayer.php?i=//mydaddy.cc/video/{hash}/` returns iframe
- **Direct embed (preferred)**: `https://mydaddy.cc/video/{id}/` — same final URL as the proxy, but skip the PHP hop. mydaddy.cc has no `X-Frame-Options`, iframes cleanly from any origin.
- **Categories**: `/category/4k-porn`, `/category/1080p-porn`, `/category/60fps-porn`
- **For list scraping**: home page returns video cards in plain HTML (not React SPA), regex on `<a href="/hdporn/{id}-{slug}.html">` works directly. Total ≈ 65k videos.

### 4tube.com (TRIAGE — DO NOT SCRAPE)
- **Status (2026-06-14)**: Returns 200, has `sitemap.xml` and `robots.txt`, but…
- **Why it fails**: Heavy React SPA. Initial HTML has zero video data. Sitemap file `/sitemap/item-collection/list/newest/default.xml` contains ONLY category URLs (`/category/japanese`, `/category/asian`, …), never individual video pages.
- **No public API**: All `/api/*` paths return 404. JS bundle is minified + small (33KB), no embedded URLs.
- **Path forward**: Would need Puppeteer + reverse-engineering internal XHR endpoints. Real cost ~half-day. **Skip unless user insists** — better ROI on Eporner/HQPorner expansion.
- **User pattern**: 4tube comes up frequently in "premium Indo / Asian" requests. When user names 4tube, the honest answer is "200 OK but it's a JS-only SPA, no public API, would need headless browser to integrate."

### XNXX / HDZog
- Both return 200, have public listings
- Less tested — start with Eporner + HQporner, add later
- **HDZog note**: HD-focused category structure mirrors Eporner; `query=` search is a reasonable starting point.
- **XNXX note**: Has its own internal search endpoints but no public API; cookies/session may be required for some categories. Triage before committing.

## Age Gate (Password Pattern)

```jsx
// Step 0: warning
// Step 1: password input + submit button + small clue text
// Storage: localStorage.setItem('iclix_21_verified', '1')
// Verify: localStorage.getItem('iclix_21_verified') === '1'
```

**UI pattern** (memorized 2026-06-14):
- Input with `type={showPw ? 'text' : 'password'}` + 👁/🙈 toggle button (absolute right)
- Single "Masuk →" submit button (NOT auto-validate on typing)
- Small italic clue below (10px, #555, user-select: none)
- "Password salah" error with shake animation (800ms auto-clear)
- Back button to return to step 0

**Reasoning for the small clue**: User explicitly requested "kecil aja tulisan nya" — readable enough to find, small enough not to dominate. Sits between "hint" and "spoiler".

## Frontend Player Component

```jsx
<iframe
  key={video.id}
  src={video.embed}                              // Eporner embed URL
  title={video.title}
  frameBorder="0"
  allowFullScreen
  allow="autoplay; encrypted-media; fullscreen"
  referrerPolicy="origin"
  sandbox="allow-scripts allow-same-origin allow-presentation allow-popups"
  style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', border: 0, background: '#000' }}
/>
```

**Sandbox permissions** (battle-tested):
- `allow-scripts` — site needs JS for player
- `allow-same-origin` — for video.js to read its config
- `allow-presentation` — fullscreen API
- `allow-popups` — some sites have quality/settings popups
- **DO NOT** add `allow-top-navigation` (avoids hijacking parent page)

## Deploy Pattern (Same as Main ICLIX)
1. Edit `backend/server.js` + `frontend/src/pages/Adult.jsx`
2. `cd /home/ubuntu/iclix/frontend && npm run build`
3. `pm2 restart iclix-api --update-env` (the `--update-env` matters — without it, new env vars don't load)
4. Verify: `curl -s http://localhost:3000/api/adult/video/{id} | jq .video.embed`

## Critical Pitfalls

### 🐛 403 on direct MP4 = anti-hotlink, not broken backend
Symptom: video iframe shows empty/black, network tab shows 403 on `gvideo.*.com`. **Do not** try harder anti-hotlink bypasses. Switch to embed iframe URL. The site's embed URL is always the working answer.

### 🐛 Forgetting `pm2 restart --update-env`
After editing `server.js`, plain `pm2 restart iclix-api` may keep cached module state. Use `--update-env` to force fresh load. Verified this caused one session to test against stale code for several iterations.

### 🐛 Duration comes in ISO 8601, not "MM:SS"
Eporner embed page JSON-LD has `"duration":"PT0H9M1S"`. Don't try to parse `length_min` regex first — it won't be there. JSON-LD is the source of truth.

### 🐛 Views come from InteractionCounter, not "X views" text
Eporner embed page has `"@type":"InteractionCounter","userInteractionCount":9481`. The "9,481 views" text is rendered client-side, not in the HTML. Always use the JSON-LD counter.

## Reference Files
- `references/site-triage.md` — Decision tree for "can we scrape this site?" with curl probes
- `templates/age-gate.jsx` — Drop-in age gate component (password + clue pattern)
