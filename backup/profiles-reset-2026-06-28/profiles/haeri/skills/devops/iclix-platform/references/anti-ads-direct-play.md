> **Source**: migrated from `iclix-anti-ads-direct-play` (consolidated June 2026). Original archived.

# ICLIX Direct Play — Anti-Iklan Mode

## Why
Free iframe embeds (VidLink, VidSrc, etc.) all serve ads inside the iframe: popups, redirects, click-hijacking, pre-roll video ads. Cannot block ads inside an iframe from outside.

## Solution
1. **Backend scraper** `services/scraper.js` uses Playwright to load `https://vidlink.pro/movie/{id}` in headless Chromium, intercepts network requests, captures m3u8 URL + actual referer (`megacloud.live` not `vidlink.pro`).
2. **Backend stream proxy** `/api/stream` in `server.js` fetches m3u8 from upstream `storm.vodvidl.site`, adds CORS headers (`Access-Control-Allow-Origin: *`), rewrites segment URLs using `new URL(line, baseUrl).href` to go through proxy too.
3. **Frontend HLS player** uses `hls.js` to play m3u8 in `<video>` element. No iframe = no iframe ads.

## Critical Pitfalls
- **Referer must be `https://megacloud.live/`** for m3u8 to be served by upstream. Capture this from `response.request.headers.referer` in Playwright, not from the embed URL.
- **URL rewriting**: Use `new URL(line, base).href` not string concatenation. Query strings in master URL (auth/host) cause double-encoding if you do `url.substring(0, lastIndexOf('/')+1)`.
- **Cache for 6 hours** to avoid re-scraping same film every click. Cache key = `${type}:${tmdb_id}`. Path: `/home/ubuntu/iclix/cache/scraped_streams.json`.
- **Sandbox iframe still kept** as fallback (`playMode === 'iframe'`) for when scraper fails. Use `sandbox="allow-scripts allow-forms allow-presentation allow-fullescreen"` — NO `allow-same-origin` (prevents `top.location` redirect), NO `allow-popups` (blocks `window.open`).

## YouTube Trailer Anti-Ad Trick
Don't embed YouTube iframe directly — it auto-loads and shows doubleclick ads + can redirect on click. Instead:
1. Show `<img src="https://img.youtube.com/vi/{key}/hqdefault.jpg">` thumbnail
2. On click → load `<iframe src="https://www.youtube-nocookie.com/embed/{key}?rel=0&modestbranding=1">` 
3. `youtube-nocookie.com` is YouTube's privacy mode: no personalized ads, no tracking, no ad-based redirects
4. `?rel=0&modestbranding=1` further reduces branding/related videos

## Verification
```python
# Headless Chromium test
async with async_playwright() as p:
    page = await ctx.new_page()
    ad_requests = []
    ad_domains = ['doubleclick','googlesyndication','adnxs','outbrain','taboola']
    page.on('request', lambda r: ad_requests.append(r.url) if any(d in r.url for d in ad_domains) else None)
    await page.goto(iclix_url + '/movie/550')
    await page.click('text=Tonton Sekarang')
    await page.wait_for_timeout(20000)
    # Expect: 0 ad requests, 0 out-of-domain navigations, video playing (readyState=4)
```

## API
- `GET /api/play/{type}/{id}` — scrapes m3u8, returns `{m3u8: '/api/stream?url=...', direct, source, referer, fromCache}`
- `GET /api/stream?url=...&referer=...` — CORS proxy for m3u8 + segments

## Files
- `/home/ubuntu/iclix/backend/services/scraper.js` — Playwright scraper
- `/home/ubuntu/iclix/backend/server.js` — routes `/api/play/:type/:id` + `/api/stream`
- `/home/ubuntu/iclix/frontend/src/pages/MovieDetail.jsx` — playMode toggle, hls.js player
- `/home/ubuntu/iclix/cache/scraped_streams.json` — 6h cache

## Known Failure Modes (2026-06)
- **No m3u8 found in network requests** (`scrapeM3u8` returns `{error: 'no m3u8 found'}`): vidlink.pro doesn't have that TMDB ID embedded. About 5-10% of movies fail this way. Examples: TMDB 155 (Dark Knight Rises 2012), 568332 (Tenet).
- **First-click latency 10-15s**: Playwright launch + page load + 5s wait for video. Cold cache. After 6h cache TTL, re-scrapes.
- **Signed auth tokens expire**: m3u8 URLs contain `auth=...&host=...` signed tokens that last ~hours. If a user clicks a movie that was scraped days ago, the URL may 403. Fix: keep cache TTL ≤ 6h (current setting is correct).
- **Frontend error UX is poor**: when scrape fails, user sees "❌ {error}" with a hint to switch to Iframe mode, but no auto-fallback. Consider adding: if direct play errors with `no m3u8 found`, auto-switch to iframe mode after 3s and show a toast.

## Auto-Fallback Pattern (TODO if user complains)
In `MovieDetail.jsx`, when `hlsError` contains 'no m3u8', set `setPlayMode('iframe')` and show a banner. Most users don't notice the swap; the 10 iframe servers cover the gap.

## Test
```bash
curl -s "http://127.0.0.1:3000/api/play/movie/550"  # Fight Club
# Returns: {m3u8, direct, referer, fromCache}
# First call ~5-15s (scrape), subsequent <0.5s (cache)
```

---

## Variant: Eporner Embed Iframe (21+ adult content)

For the `/21plus/*` adult section, Eporner's official **API** (`/api/v2/video/`) is great for listing/categories/search/metadata, but the actual MP4 CDN (`gvideo.eporner.com/...mp4`) is **anti-hotlink protected and not viable** for direct `<video src>` play. Even with the correct `Referer: https://www.eporner.com/` header, the CDN returns 403 from any non-Eporner origin (browser or backend proxy).

**Working approach: use Eporner's official embed iframe.** It's the only path that just works without auth tricks.

### Why iframe is the only viable option for Eporner
- `https://gvideo.eporner.com/{id}/{id}.mp4` → **403** (anti-hotlink, no way around from outside the player)
- The `videos[]` array in the API has quality-suffixed URLs (e.g. `...720_6000.mp4`) — same 403 problem
- Eporner's player.js handles hash/session auth that we can't replicate
- Embed iframe `https://www.eporner.com/embed/{id}/` returns 200 with no `X-Frame-Options` — designed to be iframed
- No CSP conflicts (only `upgrade-insecure-requests` on embed page)

### Backend pattern (`/api/adult/*`)
The **list endpoints** (trending/latest/most-viewed/category/search) use the Eporner API as before — that works fine. Only the single-video endpoint changes:

```js
// server.js — single video: return embed URL + scrape page for metadata
app.get('/api/adult/video/:id', async (req, res) => {
  const id = req.params.id
  const embedUrl = `https://www.eporner.com/embed/${id}/`
  const pageUrl  = `https://www.eporner.com/video-${id}/`
  const headers  = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' }

  let title = id, thumb = '', duration = '', views = 0, keywords = []
  // Try main page, fall back to embed page (one usually has full metadata)
  for (const url of [pageUrl, embedUrl]) {
    const r = await fetch(url, { headers, signal: AbortSignal.timeout(15000) })
    if (!r.ok) continue
    const html = await r.text()
    if (title === id) {
      const m = html.match(/<title>([^<]+)<\/title>/i)
      if (m) title = m[1].replace(/ - EPORNER$/, '').trim()
    }
    if (!thumb) {
      const m = html.match(/property="og:image" content="([^"]+)"/i)
        || html.match(/default_thumb[^}]+src":"([^"]+)"/)
        || html.match(/"thumbnailUrl":\s*"([^"]+)"/)
      if (m) thumb = m[1]
    }
    if (!duration) {
      // ISO 8601: "PT0H9M1S" → "9:01", or "PT1H2M3S" → "1:02:03"
      const iso = html.match(/"duration":\s*"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"/i)
      if (iso) {
        const h = +iso[1]||0, mn = +iso[2]||0, sc = +iso[3]||0
        duration = h > 0 ? `${h}:${String(mn).padStart(2,'0')}:${String(sc).padStart(2,'0')}`
                         : `${mn}:${String(sc).padStart(2,'0')}`
      } else {
        const m = html.match(/length_min["\s:=]+["']?(\d+:\d+)/i)
        if (m) duration = m[1]
      }
    }
    if (!views) {
      const m = html.match(/(\d[\d,]*)\s*views/i)
        || html.match(/"userInteractionCount":\s*(\d+)/)
      if (m) views = parseInt((m[1] || m[2]).replace(/,/g, ''))
    }
    if (keywords.length === 0) {
      const m = html.match(/keywords[^>]+content="([^"]+)"/i)
      if (m) keywords = m[1].split(',').map(s => s.trim()).filter(Boolean)
    }
    if (title && thumb && duration && views) break
  }

  res.json({ video: { id, title, thumb, duration, views, keywords,
    url: pageUrl, embed: embedUrl, pageUrl } })
})
```

### Frontend player pattern (iframe, not video)
```jsx
<iframe
  key={video.id}
  src={video.embed}                            // https://www.eporner.com/embed/{id}/
  title={video.title}
  frameBorder="0"
  allowFullScreen
  allow="autoplay; encrypted-media; fullscreen"
  referrerPolicy="origin"
  sandbox="allow-scripts allow-same-origin allow-presentation allow-popups"
  style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', border: 0, background: '#000' }}
/>
```

### Critical pitfall: don't try to "save" by using direct MP4
- Eporner's CDN (`gvideo.eporner.com`) is **not** a normal CDN. It checks Origin/Referer AND requires session cookies/hash that the embed player sets. Even with the right headers from curl, requests fail with 403.
- The `videos[]` array in the API response points to the same blocked CDN — they're not the answer.
- Some scraping tutorials show scraping `gvideo.eporner.com/${id}/${id}.mp4` — **outdated**, returns 403 now.
- **Just use the embed iframe.** It's the path Eporner actually supports for embedding.

### Age gate pattern (2-step)
```jsx
// localStorage gate — verify once per session, not per page
const ADULT_KEY = 'iclix_21_verified';
const [step, setStep] = useState(localStorage.getItem(ADULT_KEY) ? 'done' : 'warn');
if (step === 'warn') return <WarningScreen onContinue={() => setStep('verify')} />;
if (step === 'verify') return <PasswordGate onConfirm={...} />;
```
- Step 1: warning screen with explicit "Saya 21+ → Lanjut" button
- Step 2 (recommended): password input + explicit "Masuk →" submit button + small italic clue
- **Don't auto-validate-on-input** (type-the-phrase pattern) — breaks on paste/IME/exact-phrase-mismatch frustration. User explicitly prefers explicit submit.
- After verify → `localStorage` survives navigation within session
- Add menu link with 🔞 emoji + red badge so it's clearly marked

### Verification
```bash
# Backend returns embed URL (not gvideo)
curl -s "http://localhost:3000/api/adult/video/bgdAoGFOKTx" | jq '.video | {title, duration, views, embed}'
# → { "title": "German Girl Creamy", "duration": "9:01", "views": 9481, "embed": "https://www.eporner.com/embed/bgdAoGFOKTx/" }

# Browser
# 1. /21plus → warning → password "jokowi" + Masuk → unlock (localStorage)
# 2. Click video → player page → Eporner embed iframe loads (804x452)
# 3. Click play inside the iframe → Eporner's own player.js handles everything
# 4. Refresh → still unlocked (localStorage)
```

### Files
- `/home/ubuntu/iclix/backend/server.js` — `/api/adult/*` routes (list endpoints via API, single video via page scrape)
- `/home/ubuntu/iclix/frontend/src/pages/Adult.jsx` — all of: AgeGate, AdultHome, AdultCategory, AdultSearch, AdultPlayer (single file holds the whole 21+ module)
- `references/eporner-api.md` — full Eporner API reference + metadata scraper recipe
