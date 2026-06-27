# Eporner API Reference (for ICLIX 21+ module)

Source: `https://www.eporner.com/api/v2/`
No auth, no key, no rate limit observed in production (ICLIX ran it 24/7 without 429s).

## Base URL
```
https://www.eporner.com/api/v2/
```

## Common Query Params
- `per_page` — int, max ~30 reliable (higher sometimes returns 500)
- `page` — int, 1-indexed
- `order` — `newest` | `top-weekly` | `top-monthly` | `top-yearly` | `most-viewed` | `top-rated` | `longest`
- `thumbsize` — `small` | `medium` | `big` | `large`
- `output` — MUST be `json` (default is XML)
- `gay` — `0` | `1` (include gay category)
- `lq` — `0` | `1` (include low-quality)

## Endpoints (all return `{count, total_count, videos: [...]}` shape)

### List videos
```
GET /video/?per_page=30&page=1&order=top-weekly&thumbsize=big&output=json
```

### Search
```
GET /video/?search=keyword&order=newest&per_page=30&output=json
```
Note: `search` param goes on the same `/video/` endpoint, no separate `/search/`.

### By category
```
GET /video/?category=<cat_id>&order=newest&per_page=30&output=json
```
Get category IDs from `/categories/` endpoint or hardcode (see below).

### Categories list
```
GET /categories/?output=json
```
Returns array of `{id, title, cat, url}`. Title is human-readable ("Amateur"), `cat` is URL slug.

### Single video by ID
```
GET /video/<id>/?output=json
```
OR `GET /video/?id=<id>` — both work. Returns full metadata + the `videos` array of MP4 qualities.

## Video Object Schema
```json
{
  "id": "thgkLBVAbZw",
  "title": "Beautiful 18yo Colombian Slut Pounds Her Ass Out With A BBC Dildo",
  "keywords": "BBC, Colombian, Slut, Ass, Dildo, 18yo",
  "views": 142388,
  "rate": "92%",
  "url": "https://www.eporner.com/video/thgkLBVAbZw/...",
  "added": "2 weeks ago",
  "length_sec": 1889,
  "length_min": "31:29",
  "thumb": "https://img010.eporner.com/thumbs/.../480/...jpg",
  "thumbs": ["https://img...jpg", ...],
  "category": "Anal",
  "pornstars": [],
  "videos": [
    {"src": "https://gvideo.eporner.com/.../720_6000.mp4", "res": "720p", "bitrate": "6000"},
    {"src": "https://gvideo.eporner.com/.../480_1500.mp4", "res": "480p", "bitrate": "1500"}
  ]
}
```

## Categories (37, hardcoded for ICLIX sidebar)
`amateur, anal, asian, babe, bbc, bdsm, big-ass, big-dick, big-tits, blonde, blowjob, brunette, creampie, cumshot, double-penetration, ebony, european, facial, fetish, french, gangbang, gay, german, handjob, hentai, interracial, japanese, latina, lesbian, masturbation, milf, orgy, pov, public, rough-sex, shemale, solo, squirt, stockings, teen, threesome, toys, uniform, vintage, voyeur, webcam`

## Critical pitfalls
- **CDN `gvideo.eporner.com/...mp4` is anti-hotlink — 403 from outside the embed player, regardless of Referer/Origin headers.** The previous "Referer required" advice is outdated; even with the right `Referer: https://www.eporner.com/` and `User-Agent: Mozilla/5.0`, the CDN still returns 403 from any non-Eporner origin (browser, backend proxy, or curl). The `videos[]` array in the API also points to the same blocked CDN. **Don't try to "save" by using direct MP4 — use the official embed iframe instead.** (See variant section in SKILL.md.)
- **Embed iframe is the only working path:** `https://www.eporner.com/embed/{id}/` returns 200 with no `X-Frame-Options` and a permissive CSP. Render it as `<iframe src={embed}>` — Eporner's player.js handles the actual video streaming and auth.
- **For single-video metadata**, the API's `/video/{id}/` works but is rate-limited; **scraping the main page or embed page** is more reliable (see Metadata scraper section below).
- **per_page > 30 is unreliable.** Returns 500 sometimes. Stick to 30.
- **No `Authorization` header.** Sending one returns 401 instantly. Header-less curl is the right baseline.
- **60-90s warmup on cold cache.** First request after CDN eviction takes a minute. After that, ~1-3s.
- **`gay` param defaults to 0.** Set to 1 to include gay content in results (was needed for full category coverage).
- **`thumbsize=big` is the sweet spot** — `large` is 3x bandwidth for barely better quality, `small` looks pixelated.
- **`length_sec` vs `length_min`.** Use `length_sec` for sorting/filtering, `length_min` for display. (Note: when scraping pages instead of API, duration is in ISO 8601 `"PT0H9M1S"` — see scraper below.)

## Frontend iframe pattern (current — use this)
```jsx
<iframe
  src={`https://www.eporner.com/embed/${video.id}/`}
  title={video.title}
  frameBorder="0"
  allowFullScreen
  allow="autoplay; encrypted-media; fullscreen"
  referrerPolicy="origin"
  sandbox="allow-scripts allow-same-origin allow-presentation allow-popups"
  style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', border: 0, background: '#000' }}
/>
```
- `referrerPolicy="origin"` is safe (we're not exposing the tunnel URL to Eporner in a way that matters)
- `sandbox="allow-scripts allow-same-origin allow-presentation allow-popups"` is required so the Eporner player can boot its video.js + click handlers. **Do NOT add `allow-popups-to-escape-sandbox`** — that lets it open popunders.
- Don't use the API's `videos[]` URLs even as fallback. They will all 403. The embed iframe is the single working path.

## Metadata scraper (for single-video endpoint)

The API endpoint `/api/v2/video/{id}/` works but is sometimes rate-limited and adds latency. For the ICLIX player, scraping the page directly is faster and more reliable. Two pages are useful: `https://www.eporner.com/video-{id}/` (full HTML) and `https://www.eporner.com/embed/{id}/` (lightweight, has the same JSON-LD).

```js
// Reusable scraper — used in /api/adult/video/:id
const headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' }

for (const url of [pageUrl, embedUrl]) {
  const r = await fetch(url, { headers, signal: AbortSignal.timeout(15000) })
  if (!r.ok) continue
  const html = await r.text()

  // Title — strip " - EPORNER" suffix
  const t = html.match(/<title>([^<]+)<\/title>/i)
  if (t && title === id) title = t[1].replace(/ - EPORNER$/, '').trim()

  // Thumb — og:image is most reliable
  const th = html.match(/property="og:image" content="([^"]+)"/i)
    || html.match(/default_thumb[^}]+src":"([^"]+)"/)
    || html.match(/"thumbnailUrl":\s*"([^"]+)"/)
  if (th && !thumb) thumb = th[1]

  // Duration — JSON-LD ISO 8601 "PT0H9M1S" → "9:01", with H/M/S optional
  const iso = html.match(/"duration":\s*"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"/i)
  if (iso && !duration) {
    const h = +iso[1]||0, mn = +iso[2]||0, sc = +iso[3]||0
    duration = h > 0 ? `${h}:${String(mn).padStart(2,'0')}:${String(sc).padStart(2,'0')}`
                     : `${mn}:${String(sc).padStart(2,'0')}`
  }

  // Views — JSON-LD userInteractionCount (most reliable)
  const v = html.match(/"userInteractionCount":\s*(\d+)/)
    || html.match(/(\d[\d,]*)\s*views/i)
  if (v && !views) views = parseInt((v[1] || v[2]).replace(/,/g, ''))

  // Keywords — meta tag
  const k = html.match(/keywords[^>]+content="([^"]+)"/i)
  if (k && keywords.length === 0) keywords = k[1].split(',').map(s => s.trim()).filter(Boolean)

  if (title && thumb && duration && views) break  // got everything, stop
}
```

**Why try both pages?** The main video page has full HTML/JSON-LD but is heavier. The embed page is lighter and usually has all the same JSON-LD. Sometimes one of them 404s for weird IDs — falling back to the other covers it.

## Backend proxy pattern (Node/Express)
```js
app.get('/api/adult/list', async (req, res) => {
  const params = new URLSearchParams({
    per_page: '30',
    page: req.query.page || '1',
    order: req.query.order || 'newest',
    thumbsize: 'big',
    output: 'json',
    gay: '1',
    ...(req.query.search ? { search: req.query.search } : {}),
    ...(req.query.category ? { category: req.query.category } : {}),
  });
  try {
    const r = await fetch(`https://www.eporner.com/api/v2/video/?${params}`);
    const data = await r.json();
    res.json(data);
  } catch (e) {
    res.status(502).json({ error: 'eporner_unavailable', detail: e.message });
  }
});
```

## Frontend `<video>` pattern
```jsx
<video
  src={videos[0].src}        // best quality
  controls autoPlay playsInline
  onError={(e) => {
    // fallback to 480p if 720p CDN miss
    e.currentTarget.src = videos[1]?.src;
  }}
  style={{ width: '100%', background: '#000' }}
/>
```

## When NOT to use Eporner
- If you need auth-gated content (Eporner is all anonymous)
- If you need real-time/newest releases within minutes (Eporner has 5-30min indexing delay)
- If you need specific performers' content with full bio (Eporner's pornstars field is often empty)
- If you need >720p reliably (some videos have 1080p but inconsistent)

## Alternatives tested
- **HQporner API** — exists but less reliable, fewer categories
- **Pornhub API** — public version deprecated, requires scraping iframe → use same anti-ads pattern as movies
- **xHamster embed** — has iframe ad redirects, same problem as VidLink
- **PornDig API** — auth required, paid
