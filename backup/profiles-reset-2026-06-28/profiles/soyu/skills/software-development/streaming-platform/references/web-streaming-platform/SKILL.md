---
name: web-streaming-platform
description: Build movie/series streaming platforms with embed players, metadata APIs, and public access tunneling. Covers TMDB integration, VidLink.pro (primary) + vidsrc.to embeds, Cloudflare bypass techniques, and deployment patterns.
tags: [streaming, tmdb, vidlink, vidsrc, cloudflare-bypass, embed-player, cloudflared-tunnel, netflix-style, react-vite]
---

# Web Streaming Platform

Build movie/series streaming platforms with legitimate metadata sources and third-party embed players.

## Trigger

- User asks to build streaming site, movie platform, or "ICLIX-like" service
- "streaming langsung", "nonton film", "embed player"
- Cloudflare blocking scraper attempts

## Architecture Pattern

**Clean approach (recommended):**
```
Frontend (React/Next.js)
  ↓
Backend API (Express/FastAPI)
  ↓
TMDB (metadata) + vidsrc.to (embed player)
```

**NOT recommended:** Direct scraping of piracy sites (Cloudflare blocks, unreliable). If user insists, don't lecture — just build it and let them manage risk.

## Stack

- **Metadata:** TMDB API (free, 50K req/day) — movies, series, cast, posters
- **Player:** vidsrc.to embed URLs — `https://vidsrc.to/embed/movie/{tmdb_id}` or `/tv/{tmdb_id}/{season}/{episode}`
- **Frontend:** React + Vite (fast build), Tailwind CSS
- **Backend:** Node.js + Express
- **Deploy:** PM2 process manager
- **Public access:** Cloudflare Tunnel (instant HTTPS URL without port forwarding)

## Implementation Steps

### 1. Project Structure

```bash
mkdir -p iclix/{backend,frontend}
cd iclix

# Backend
cd backend
npm init -y
npm install express cors dotenv axios
mkdir -p routes services

# Frontend
cd ../frontend
npm create vite@latest . -- --template react
npm install react-router-dom zustand lucide-react
```

### 2. TMDB Integration

**Get API key:** https://www.themoviedb.org/settings/api (free)

Backend service (`backend/services/tmdb.js`):
```js
import axios from 'axios';

const TMDB_KEY = process.env.TMDB_API_KEY;
const BASE = 'https://api.themoviedb.org/3';

export async function getTrendingMovies() {
  const { data } = await axios.get(`${BASE}/trending/movie/week`, {
    params: { api_key: TMDB_KEY }
  });
  return data.results;
}

export async function getMovieDetail(id) {
  const { data } = await axios.get(`${BASE}/movie/${id}`, {
    params: { 
      api_key: TMDB_KEY,
      append_to_response: 'videos,credits'
    }
  });
  return data;
}
```

### 3. Embed Player Integration

**Multiple sources with fallback** — single source breaks often. Always provide 2-3 alternatives:

Backend route (`backend/routes/movies.js`):
```js
router.get('/:id/stream', async (req, res) => {
  const { id } = req.params;
  const { source = 'auto' } = req.query;
  
  const sources = [
    { name: 'VidLink', url: `https://vidlink.pro/movie/${id}` },
    { name: 'AutoEmbed', url: `https://autoembed.co/movie/tmdb/${id}` },
    { name: 'VidSrc', url: `https://vidsrc.to/embed/movie/${id}` },
  ];
  
  // For series: autoembed.co/movie/tmdb/tv/{id}/{season}/{episode}
  //              vidsrc.to/embed/tv/{id}/{season}/{episode}
  
  if (source !== 'auto') {
    const found = sources.find(s => s.name.toLowerCase() === source.toLowerCase());
    if (found) return res.json({ success: true, data: { embedUrl: found.url, ...found, type: 'movie', sources } });
  }
  
  res.json({ success: true, data: { embedUrl: sources[0].url, ...sources[0], type: 'movie', sources } });
});
```

**Source reliability (tested 2026-06-12, expanded):**

**Movies (7 sources — always provide 5+ fallbacks):**
1. `vidlink.pro/movie/{tmdb_id}` — **BEST: Next.js player, minimal ads, fast** ⭐
2. `autoembed.co/movie/tmdb/{tmdb_id}` — reliable, works mobile
3. `vidsrc.to/embed/movie/{tmdb_id}` — good desktop, chains vsembed.ru
4. `flicky.host/embed/movie/{tmdb_id}` — good backup, fast load
5. `vidcloud9.com/embed/movie/{tmdb_id}` — works but sometimes empty shell
6. `111movies.com/movie/{tmdb_id}` — solid fallback
7. `vidsrc.in/embed/movie/{tmdb_id}` — alternative vidsrc network

**TV Series (5 sources):**
1. `vidlink.pro/tv/{tmdb_id}/{season}/{episode}` — primary
2. `vidsrc.to/embed/tv/{tmdb_id}/{season}/{episode}`
3. `flicky.host/embed/tv/{tmdb_id}/{season}/{episode}`
4. `vidcloud9.com/embed/tv/{tmdb_id}/{season}/{episode}`
5. `vidsrc.in/embed/tv/{tmdb_id}/{season}/{episode}`

**Add these for more redundancy (tested 2026-06-13):**
6. `movie4kto.net/embed/{tmdb_id}` — works for movies
7. `putlocker-website.com/embed/movie/{tmdb_id}` — works
8. `moviesjoy.to/embed/{tmdb_id}` — works (note: replace, not append, the test ID in template)

**Embed source auto-fallback pattern (CRITICAL UX fix):** Static "click a server" UX means most users never try the next server — they just see a black iframe and assume the movie is broken. Always add timer-based auto-fallback: 10s timeout after iframe mount → if `onLoad` hasn't fired, auto-cycle to next server. Manual left/right buttons for power users. State machine: `serverOk` flag, `key={srcIdx-id}` to force iframe remount. See full implementation in `streaming-platform-builder` skill → "Embed Auto-Fallback Pattern" section.

**Testing methodology:** Use curl to check HTTP status AND iframe content:
```bash
curl -s -o /dev/null -w '%{http_code}' -L --max-time 10 'https://vidlink.pro/movie/550'
curl -s -L --max-time 10 'https://vidlink.pro/movie/550' | grep -ci 'iframe\|video\|player'
```
Test with TMDB ID 550 (Fight Club) for movies, 93405 (Squid Game) for TV.

Frontend player with source switcher:
```jsx
const [activeSource, setActiveSource] = useState(0);
const currentEmbedUrl = stream?.sources?.[activeSource]?.url || stream?.embedUrl;

// Source selector buttons
{stream?.sources?.length > 1 && (
  <div className="flex gap-2">
    {stream.sources.map((src, i) => (
      <button key={src.name} onClick={() => setActiveSource(i)}
        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
          activeSource === i ? 'bg-[#e50914] text-white' : 'bg-white/5 text-gray-400'
        }`}>
        {src.name}
      </button>
    ))}
  </div>
)}

// Player iframe
<iframe src={currentEmbedUrl} className="w-full h-full"
  allowFullScreen allow="autoplay; fullscreen; picture-in-picture; encrypted-media" />
```

Frontend player (`frontend/src/pages/Movie.jsx`) — **mobile-safe version**:
```jsx
{stream?.embedUrl && (
  <div className="aspect-video w-full">
    <iframe
      src={stream.embedUrl}
      className="w-full h-full"
      allowFullScreen
      allow="autoplay; fullscreen; picture-in-picture; encrypted-media; gyroscope; accelerometer"
      referrerPolicy="no-referrer"
      frameBorder="0"
      sandbox="allow-scripts allow-same-origin allow-presentation allow-popups"
    />
  </div>
)}
```

**CRITICAL: Mobile Safari iframe fallback** — Always include "Open Player" button (opens embed URL in new tab) AND "Open in new tab" link below the player. Mobile Safari often blocks iframe video playback. The user must have a way to open the embed URL directly:

```jsx
// Action buttons — always show both
<a href={currentEmbedUrl} target="_blank" rel="noopener noreferrer"
  className="..."><ExternalLink size={16} /> Open Player</a>

// Below player
<a href={currentEmbedUrl} target="_blank" rel="noopener noreferrer"
  className="text-xs text-[#e50914]">↗ Open in new tab</a>
```

### 4. Public Access via Cloudflare Tunnel

**Problem:** VPS port 3000 blocked by cloud provider firewall.

**Solution:** Cloudflare Tunnel (instant public HTTPS URL, no port config needed).

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Start tunnel (temporary, for testing)
nohup cloudflared tunnel --url http://localhost:3000 > /tmp/tunnel.log 2>&1 &

# Extract public URL
sleep 5 && cat /tmp/tunnel.log | grep -oE "https://[a-z0-9-]+\.trycloudflare\.com"
```

Output example: `https://assign-peace-away-shows.trycloudflare.com`

**Permanent tunnel (named):** https://developers.cloudflare.com/cloudflare-one/connections/connect-apps

### 5. Deploy with PM2

```bash
cd backend
pm2 start npm --name iclix-api -- start
pm2 save
pm2 startup  # enable on boot
```

## Cloudflare Bypass (When Scraping is Required)

⚠️ **Prefer legitimate APIs over scraping.** Use this only when no API exists.

### Technique 1: cloudscraper (Python)

Solves basic Cloudflare challenges automatically.

```python
import cloudscraper

scraper = cloudscraper.create_scraper()
r = scraper.get('https://target-site.com/page')
print(r.text)
```

Replace all `requests.get()` with `scraper.get()`.

### Technique 2: curl_cffi (Advanced)

Mimics real browser TLS fingerprint.

```python
from curl_cffi import requests

r = requests.get('https://target-site.com', impersonate="chrome110")
print(r.text)
```

### Technique 3: Browser Automation

When JS challenge is complex, use real browser:
- Load `browser-agent` or `cloakbrowser-setup` skill
- Use Playwright/Puppeteer with stealth plugins

## Drama Asia Page

Standard feature for Indonesian streaming platforms — dedicated page for Korean, Chinese, Japanese, Thai content.

```jsx
// DramaAsia.jsx — filter by TMDB discover API with country + genre
const ASIA_TABS = [
  { id: 'kdrama', label: '🇰🇷 K-Drama', genreId: 18, country: 'KR', type: 'tv' },
  { id: 'cdrama', label: '🇨🇳 C-Drama', genreId: 18, country: 'CN', type: 'tv' },
  { id: 'anime', label: '🇯🇵 Anime', genreId: 16, country: 'JP', type: 'tv' },
  { id: 'thai', label: '🇹🇭 Thai Drama', genreId: 18, country: 'TH', type: 'tv' },
  { id: 'jmovie', label: '🇯🇵 Film Jepang', genreId: '', country: 'JP', type: 'movie' },
  { id: 'kmovie', label: '🇰🇷 Film Korea', genreId: '', country: 'KR', type: 'movie' },
]

// Backend endpoint
app.get('/api/discover/:type', async (req, res) => {
  const { type } = req.params
  const params = { api_key: TMDB_KEY, ...req.query, language: 'id-ID' }
  const { data } = await axios.get(`https://api.themoviedb.org/3/discover/${type}`, { params })
  res.json(data)
})
```

## Live TV Page (M3U8 Streams)

Free M3U8 streams for Indonesian + international channels. Use HTML5 `<video>` element with HLS.js or native support.

```jsx
// Channel data structure
const TV_CHANNELS = [
  { id: 1, name: 'RCTI', logo: '...', stream: 'https://...m3u8', category: 'lokal', status: 'live' },
  { id: 20, name: 'CNN', logo: '...', stream: 'https://...m3u8', category: 'news', status: 'live' },
  { id: 30, name: 'beIN Sports', logo: '...', stream: 'https://...m3u8', category: 'sports', status: 'live' },
]

// Categories: 'all', 'lokal', 'news', 'sports', 'music'
// Player: <video src={channel.stream} controls autoPlay playsInline />
// Modal player pattern: click card → fullscreen modal with video player
```

**M3U8 source discovery:** Use `https://iptv-org.github.io/iptv/countries/id.m3u` for Indonesian channels. See `references/iptv-m3u8-tested-2026-06.md` for tested working streams (last validated 2026-06-13) — most major Indonesian networks (RCTI, SCTV, Indosiar) are NOT freely available. Working: tvOne, BeritaSatu, BTV, Bandung TV, Banten TV, BRTV, Caruban TV, Biznet channels + international (DW, TRT World, Red Bull TV) + **sports: beIN SPORTS XTRA, SPOTV id, TVRI Sport HD**. Sources change frequently — build a "Report broken stream" button that sends to Telegram contact. Use `scripts/discover-and-validate-iptv.sh [keyword...]` to scan + validate streams from full iptv-org catalog in one shot.

**⚠️ CRITICAL: Validate M3U8 content before claiming streams work.** HTTP 200 is NOT enough — response body must contain `#EXTM3U` or `#EXT-X` headers. Use the validation script in the reference file. User explicitly corrected: "mending lu tes dan cek dulu sebelum bilang done 🫠 soal nya gak bisa semua." Real examples: CGTN returns HTTP 200 but body is `<!DOCTYPE html>`. LOFI Radio returns binary audio bytes. Both fail content validation despite HTTP 200. Real examples: CGTN returns HTTP 200 but body is `<!DOCTYPE html>`. LOFI Radio returns binary audio bytes. Both fail content validation despite HTTP 200.

**HLS.js for browsers that don't support native HLS:**
```bash
npm install hls.js
```
```jsx
import Hls from 'hls.js'
// In component: check Hls.isSupported(), attach to video element
```

### Sports Channels & Featured/Pinned Card Pattern

For major events (World Cup, Olympics, league finals), users want the broadcaster **immediately visible**, not buried in a category tab. Pattern (validated 2026-06-13 on ICLIX for Piala Dunia 2026):

**Data model** — add a `featured: true` flag and a dedicated `sports` category:
```jsx
const TV_CHANNELS = [
  // Pinned to top — most stable stream for the event
  { id: 0, name: '⚽ beIN SPORTS XTRA - World Cup 2026', logo: '...', 
    stream: '/api/proxy?url=https://bein-xtra-bein.amagi.tv/playlist.m3u8', 
    category: 'sports', featured: true },
  // Other sports channels in same category, sorted by id (ascending = top)
  { id: 0.5, name: '⚽ beIN Sports XTRA en Español', logo: '...', 
    stream: '/api/proxy?url=https://dc1644a9jazgj.cloudfront.net/beIN_Sports_Xtra_Espanol.m3u8', 
    category: 'sports' },
  // Rest of channels...
]
```

**Default category** — set initial filter to sports so event content is what user sees first:
```jsx
const [category, setCategory] = useState('sports')  // not 'all'
```

**Card rendering** with featured CSS class:
```jsx
<div className={`channel-card ${channel.featured ? 'channel-card-featured' : ''}`}>
  ...
  {channel.featured && <span className="featured-badge">🔥 FEATURED</span>}
  <button>{channel.featured ? 'Tonton 1080p' : 'Tonton'}</button>
</div>
```

**CSS** (gold border + glow + slight scale, copy-paste ready):
```css
.featured-badge {
  position: absolute; top: 10px; left: 10px;
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
  color: white; padding: 4px 10px; border-radius: 12px;
  font-size: 11px; font-weight: 800; letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.4);
  animation: featuredGlow 2.5s infinite;
}
@keyframes featuredGlow {
  0%, 100% { box-shadow: 0 2px 8px rgba(245, 158, 11, 0.4); }
  50% { box-shadow: 0 4px 16px rgba(245, 158, 11, 0.7); }
}
.channel-card-featured {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.05) 0%, rgba(239, 68, 68, 0.05) 100%);
  border: 2px solid rgba(245, 158, 11, 0.5);
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.15);
  transform: scale(1.02);
}
.channel-card-featured:hover {
  border-color: rgba(245, 158, 11, 0.8);
  box-shadow: 0 0 32px rgba(245, 158, 11, 0.4);
  transform: scale(1.04);
}
```

**Why pin beIN SPORTS XTRA over SPOTV/TvRI for World Cup:** beIN is the **official FIFA broadcaster** for the US market, hosted on Amagi CDN (Cloudflare), 7 adaptive bitrate variants (smooth 1080p). 3rd-party hosted streams (primestreams.tv, henico.net) have 50-70% uptime and die without notice. Always pin the official CDN-backed stream.

## Premium Footer Pattern

4-column responsive footer with gradient effects:

```
[Brand/Logo + Language Selector] [Navigation Links] [Contact Cards + Download Buttons] [Legal/TMDB]
```

- Contact cards: Telegram (link) + Email (mailto) with SVG icons, hover glow effects
- Download buttons: Google Play + App Store (placeholder, future)
- Language selector: 🇮🇩 Indonesia / 🇺🇸 English toggle (localStorage)
- TMDB attribution: Required by TMDB API terms — include logo + link
- Bottom bar: disclaimer + copyright with heartbeat animation on 💜
- Responsive: 4 cols desktop → 2 cols tablet → 1 col mobile

## Cloudflare Tunnel Caching Issue

**CRITICAL PITFALL:** When you rebuild frontend and restart backend, the Cloudflare tunnel URL still serves OLD cached content. Even opening a "new browser" won't help — the cache is at CF edge.

**Fix:** Kill old tunnel process, start new one (generates new URL):
```bash
# Find old tunnel PID
ps aux | grep cloudflared | grep -v grep
# Kill it
kill <PID>
# Start new tunnel
cloudflared tunnel --url http://localhost:3000 > /tmp/iclix-tunnel-new.log 2>&1 &
sleep 8 && grep "trycloudflare" /tmp/iclix-tunnel-new.log
```

**User frustration signal:** If user says "still looks the same" after rebuild → CF cache is the cause. Don't ask them to hard refresh — restart the tunnel immediately.

## Pitfalls

1. **Hardcoded scraper URLs go stale fast** — sites migrate domains, IPs change, SSL certs expire. Always parameterize base URL and add fallback logic.

2. **Cloudflare blocks increase over time** — simple `requests` fails immediately. Start with `cloudscraper`, escalate to `curl_cffi` or browser if blocked.

3. **IdlixAPI-style scrapers are 4 years old** — most GitHub scraping repos are outdated. Test before trusting.

4. **Port 3000 often blocked on cloud VPS** — don't assume public IP = accessible. Use Cloudflare Tunnel or Nginx on port 80.

5. **TMDB API key is free but rate-limited** — 50K requests/day. Cache responses (Flask-Caching, Redis) for production.

6. **vidsrc.to embed has no official docs** — format is reverse-engineered. Test before deploying. Backup: autoembed.co, embed.su, 2embed.org.

7. **Frontend build output must be served by backend** — `npm run build` generates `dist/`, backend serves it as static files. Don't run Vite dev server in production.

8. **PM2 process doesn't auto-restart after code changes** — run `pm2 restart <name>` after edits.

9. **Node.js 22+ ES modules: dotenv.config() runs AFTER static imports** — This is a CRITICAL pitfall. When you have:
   ```js
   import dotenv from 'dotenv';
   dotenv.config();                    // runs 2nd
   import moviesRouter from './routes/movies.js';  // imports tmdb.js which reads process.env.TMDB_API_KEY at module level — runs 1st!
   ```
   ES module static imports are hoisted and evaluated BEFORE any code in the module body. So `process.env.TMDB_API_KEY` is `undefined` when `tmdb.js` loads, even though `dotenv.config()` appears first in the file.

   **Fix:** Use Node.js native `--env-file` flag (Node 20+):
   ```bash
   node --env-file=.env server.js
   ```
   For PM2:
   ```bash
   pm2 start server.js --name iclix-api --node-args="--env-file=.env"
   ```
   This loads env vars BEFORE the process starts, so they're available at import time. No `dotenv` package needed.

10. **TMDB API key activation delay** — After creating a key at themoviedb.org, it may take 5-10 minutes to activate. Test directly with curl before debugging backend code:
    ```bash
    curl -s "https://api.themoviedb.org/3/trending/movie/week?api_key=YOUR_KEY" | head -c 200
    ```

11. **Cloudflare tunnel URL extraction** — When running `cloudflared tunnel` in background, stdout is silent. Write to file and grep:
    ```bash
    nohup cloudflared tunnel --url http://localhost:3000 > /tmp/tunnel.log 2>&1 &
    sleep 5 && cat /tmp/tunnel.log | grep -oE "https://[a-z0-9-]+\\.trycloudflare\\.com"
    ```
    Don't try to pipe background process output directly — it won't work with `terminal(background=true)`.

12. **Mobile iframe embed failures** — vidsrc.to may not load in mobile Safari (iOS). Always provide autoembed.co as primary or fallback. Test on actual mobile device before declaring success.

13. **TMDB series: fetch ALL seasons, not just season 1** — Don't hardcode `tmdb('/tv/${id}/season/1')`. Instead, loop through `series.seasons` and fetch each:
    ```js
    const seasonPromises = series.seasons
      .filter(s => s.season_number > 0)
      .map(s => tmdb(`/tv/${id}/season/${s.season_number}`).catch(() => null));
    const seasonData = await Promise.all(seasonPromises);
    ```
    This gives you episode data for all seasons. Filter out season_number 0 (specials).

14. **TMDB field name inconsistency** — Movies use `title`/`release_date`, series use `name`/`first_air_date`. Normalize to `title` and `release_date` in your backend mapping for frontend consistency.

15. **User hostility toward legal disclaimers** — When user explicitly says "stop lecturing" or "jangan nasehati", do NOT add legal warnings to architecture recommendations. State the technical approach, let user manage their own risk. Repeated disclaimers after being told to stop = trust damage.

16. **Vite PostCSS config leftover breaks build** — When rebuilding a frontend that previously used Tailwind CSS, a leftover `postcss.config.js` referencing `tailwindcss` will cause `vite build` to fail with `Cannot find module 'tailwindcss'`. **Fix:** Delete `postcss.config.js` and `tailwind.config.js` before building if Tailwind is no longer used:
    ```bash
    rm -f frontend/postcss.config.js frontend/tailwind.config.js
    ```

17. **`write_file` tool corrupts `process.env` strings** — The `write_file` tool may mangle `process.env.TMDB_API_KEY` (the dot gets corrupted or variable name truncated). **Fix:** Use `terminal` with heredoc to write files containing `process.env.*` references instead of write_file.

18. **TMDB language parameter for localized content** — Add `language=id-ID` to TMDB API calls for Indonesian synopses and titles. This is important for Indonesian audiences — they expect Bahasa Indonesia descriptions.

19. **Embed source testing methodology** — Don't just check HTTP status code. The response might be 200 but contain a Cloudflare challenge page or empty shell. Always `curl -s URL | head -50` to verify actual content contains iframe/player elements. Test with a known TMDB ID (550 = Fight Club) for consistency.

20. **M3U8/IPTV stream validation — HTTP 200 is NOT enough.** Same principle as #19 but for live TV streams. A stream returning HTTP 200 might be an HTML error page, binary audio data, or DRM-protected content. **Always validate HLS headers:**
    ```bash
    response=$(curl -s -L --max-time 8 "$url" | head -5)
    if echo "$response" | grep -q "#EXTM3U\|#EXT-X"; then
      echo "VALID HLS"
    else
      echo "NOT HLS: $(echo $response | head -c 80)"
    fi
    ```
    Real example: CGTN (`english.cctv.com`) returns HTTP 200 but the body is `<!DOCTYPE html>`. LOFI Radio returns binary audio bytes. Both fail content validation despite HTTP 200.

21. **User workflow preference: TEST BEFORE CLAIMING DONE.** When user says "tes dulu sebelum bilang done" or "belum bisa semua" — they mean exercise/validate every deliverable end-to-end before reporting success. Don't build and assume it works. Don't claim "all streams work" based on HTTP status alone. Validate content, test playback, verify rendering. This applies to streams, API endpoints, page rendering, everything.

20. **VidLink.pro chaining behavior** — VidLink.pro is a Next.js app that loads the actual player dynamically. It works great as an iframe embed but the content is client-side rendered, so `curl` only shows the loading skeleton. Test with actual browser, not just curl. URL pattern: `https://vidlink.pro/movie/{tmdb_id}` for movies, `https://vidlink.pro/tv/{tmdb_id}/{season}/{episode}` for series.

21. **Cross-origin m3u8 playback needs proxy** — When serving m3u8 from a streaming platform on a different origin (e.g. `tvri.go.id`, `amagi.tv`, Cloudfront), CORS will block the browser from fetching segments directly. The ICLIX `/api/proxy` pattern (Express route that fetches m3u8, rewrites all segment URLs to go through the same proxy, serves with `Content-Type: application/vnd.apple.mpegurl`) is required. Don't try to set `crossOrigin="anonymous"` on `<video>` and hope — manifest rewriting is the only reliable fix. See `backend/server.js` `/api/proxy` route for the full pattern (handles relative + absolute segment URLs).

22. **Use string IDs (not float) for React list keys with sort** — When using float IDs like `0.5` to "insert" items between integer IDs, React's key diff can cause re-mount issues on filter changes. Stick to integer IDs and rely on array order for pinning. If you must preserve sort order across data changes, use a separate `priority: number` field and sort on it.

## Authentication System (localStorage-Based)

When no backend auth server is available, implement localStorage-based auth:

```jsx
// AuthModal component pattern
const handleRegister = (e) => {
  e.preventDefault()
  // Validate required fields
  if (!form.username || !form.password) { setMsg('Username & password wajib!'); return }
  if (!form.email && !form.phone) { setMsg('Email atau telepon wajib!'); return }
  // Check duplicates
  const users = JSON.parse(localStorage.getItem('iclix_users') || '[]')
  if (users.find(u => u.username === form.username)) { setMsg('Username sudah dipakai!'); return }
  // Save
  const newUser = { ...form, id: Date.now(), vip: null }
  users.push(newUser)
  localStorage.setItem('iclix_users', JSON.stringify(users))
  localStorage.setItem('iclix_user', JSON.stringify(newUser))
}

const handleLogin = (e) => {
  e.preventDefault()
  const users = JSON.parse(localStorage.getItem('iclix_users') || '[]')
  const found = users.find(u =>
    (u.username === form.username || u.email === form.username || u.phone === form.username)
    && u.password === form.password
  )
  if (!found) { setMsg('Username/email/telepon atau password salah!'); return }
  localStorage.setItem('iclix_user', JSON.stringify(found))
}
```

**Login fields:** Username / Email / Telepon (single field, matches against all three)
**Register fields:** Username*, Email, No. Telepon, Password* (at least one contact method required)

## VIP Subscription System

Implement tiered VIP with localStorage persistence:

```jsx
// VIP plans (Indonesian pricing)
const PLANS = [
  { name: 'Basic', price: 'Gratis', features: ['SD 480p', 'Iklan', 'No download'] },
  { name: 'VIP', price: 'Rp 5.000/bln', features: ['HD 720p', 'Tanpa iklan', 'Download 5/bulan'] },
  { name: 'VIP Premium', price: 'Rp 10.000/bln', features: ['Full HD 1080p', 'Unlimited download', 'Akses awal'] },
]

// Subscribe handler
const handleSubscribe = (plan) => {
  const user = JSON.parse(localStorage.getItem('iclix_user') || 'null')
  if (!user) { alert('Silakan login terlebih dahulu!'); return }
  localStorage.setItem('iclix_vip', JSON.stringify({
    plan: plan.name,
    expires: Date.now() + 30 * 24 * 60 * 60 * 1000 // 30 days
  }))
}
```

**VIP badge on content:** Rating >= 8.0 gets 👑 VIP badge on cards.

**Indonesian payment methods (for future backend):**
- Transfer bank: BCA, BRI, Mandiri
- E-wallet: GoPay, OVO, DANA, ShopeePay
- QRIS universal

## User Preference: "Nothing Is Impossible"

This user explicitly pushes back on "can't do" responses. When user says:
> "gak ada yang gak bisa semua pasti bisa kita punya banyak cara kok"

**Do NOT say "this is impossible."** Instead:
1. Search for alternatives (different APIs, embed sources, scraping techniques)
2. Propose creative solutions (proxy, cache, third-party services)
3. If truly blocked, explain the technical constraint AND what IS possible
4. Never give up first — always try multiple approaches before reporting results

## Example: Full ICLIX Setup (v3 — 2026-06-12)

Complete working implementation with Netflix-style UI:
- TMDB metadata (language=id-ID for Indonesian) + VidLink.pro primary embed
- React frontend (Vite) + Express backend
- 3-source fallback: VidLink → AutoEmbed → VidSrc
- Cloudflare tunnel for public access
- PM2 deployment with `--env-file=.env`

**Features built:**
- Hero banner auto-rotate from trending content
- 6+ carousels (Trending, Popular, Top Rated, TV Popular, TV Top Rated, Coming Soon)
- Movies page with genre filter, sort, pagination (discover API)
- TV Series page with genre filter, sort, pagination
- Movie detail: poster, backdrop, cast, YouTube trailers, Watch Now with embed player
- TV detail: season selector, episode picker, Watch Episode with embed player
- Search page (multi-search API)
- Genre page (discover by genre)
- Navbar: logo "ICLIX" + "By Hexa" subtitle, nav links, genre dropdown, search bar
- Footer with TMDB attribution

**Key learnings from v3:**
- VidLink.pro outperforms all other embed sources — use as primary
- `language=id-ID` on TMDB gives Indonesian synopses (important for local audience)
- Separate discover endpoints for movies vs TV with genre/sort/page params
- Season/episode picker needs `season_number > 0` filter (skip specials)
- Backend must serve frontend `dist/` as static files + SPA fallback

## Reference Files

- `references/embed-sources.md` — Complete embed source testing results, URL patterns, and reliability data
- `references/iclix-vps-deployment.md` — ICLIX Mona-VPS-specific deployment quirks (Tencent Cloud security group, port 80 reserved, tunnel-url-watcher, localhost.run fallback)
- `templates/server.js` — Production-ready Express backend template with all TMDB endpoints

- `browser-agent` — when scraping requires full browser
- `crypto-data-scrapers` — similar API scraping patterns
- `devops` category — PM2, VPS deployment
