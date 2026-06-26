# ICLIX Video Resolver — Research & Bahan

> Tanggal: 2026-06-18
> Status: Research Phase
> Tujuan: Clone jeniusplay.com untuk ICLIX instant play

---

## 1. IDLIX Architecture (VERIFIED)

### Stack:
- **WordPress + DooPlay Theme** — streaming site theme
- **jeniusplay.com** — video resolver (embed URL → m3u8)
- **TMDB** — metadata (poster, deskripsi, rating)

### Content Import:
```javascript
// Import film pakai IMDB ID
action: 'dbmovies_insert_tmdb'
ptmdb: 'tt0338188'  // IMDB ID

// Import TV show pakai TMDB ID
action: 'dbmovies_insert_tmdb'
ptmdb: '1399'  // TMDB ID

// Generate season & episode
action: 'dbmovies_generate_te'
tmdb: tmdbId
type: 'seasons' / 'episodes'
```

### Video Playback Flow:
```
User klik play
↓
wp-admin/admin-ajax.php (doo_player_ajax)
↓
Embed URL (encrypted CryptoJS AES)
↓
jeniusplay.com/player/index.php?data={hash}&do=getVideo
↓
POST: hash={embed_url}&r={referer}
↓
Response: { videoSource: "https://cdn.../video.mp4" }
↓
Convert ke .m3u8 → HLS.js play
```

### Source:
- https://github.com/sandrocods/IdlixDownloader
- File: src/idlixHelper.py, src/CryptoJsAesHelper.py

---

## 2. VidSrc Chain Scraper (TANPA BROWSER!)

### Chain:
```
vidsrc.to/embed/{type}/{id}
    ↓
vsembed.ru/embed/{type}/{id}/  (extract rcp hash)
    ↓
cloudnestra.com/rcp/{hash}     (extract prorcp hash)
    ↓
cloudnestra.com/prorcp/{hash}  (extract m3u8 URLs)
    ↓
master.m3u8 → HLS.js PLAY! ⚡
```

### Cara Kerja:
1. **Step 1:** GET vidsrc.to/embed/movie/{id} → extract vsembed.ru iframe URL
2. **Step 2:** GET vsembed.ru → extract `data-hash` attributes (rcp hashes)
3. **Step 3:** GET cloudnestra.com/rcp/{hash} → extract prorcp hash dari JS
4. **Step 4:** GET cloudnestra.com/prorcp/{hash} → extract m3u8 URLs dari player
5. **Step 5:** Resolve CDN vars {v1}..{v5} dari obfuscated JS

### CDN Variables Resolution:
- cloudnestra.com inject obfuscated JS via `document.write`
- JS filename = hash.js (e.g., f59d610a61063c7ef3ccdc1fd40d2ae6.js)
- Run di Node.js VM sandbox → extract CDN hostnames
- Hostnames: neonhorizonworkshops.com, cloudnestra.com, dll

### Hasil (bukti):
```
Movie: tt9263550
✅ 5 m3u8 URLs ditemukan!
→ https://tmstr5.neonhorizonworkshops.com/.../master.m3u8
→ https://tmstr5.cloudnestra.com/.../master.m3u8
```

### Source:
- https://github.com/MaheshSharan/vidsrc
- File: scraper.py, extract_cdn_vars.js

---

## 3. Vidoy CDN Resolver

### Cara Kerja:
1. GET halaman video Vidoy
2. Extract video_id dari `<script>var id = "...";</script>`
3. GET embed endpoint: `https://{host}/embed.php?id={video_id}&bucket=temporary`
4. Extract dari embed HTML:
   - Title: `<title>...</title>`
   - Poster: `poster="..."`
   - CDN URL: `<source src="...">`

### Source:
- https://github.com/RozhakDev/VidoyCdnResolver

---

## 4. DooPlay WordPress Theme

### Fitur Built-in:
- Import dari TMDB/IMDB (auto-fetch metadata)
- Player system (encrypted embed URLs)
- Season/Episode management
- SEO optimized

### Import Script:
- Movies: CSV dengan IMDB IDs → `dbmovies_insert_tmdb`
- TV Shows: CSV dengan TMDB IDs → `dbmovies_insert_tmdb` + `dbmovies_generate_te`

### Source:
- https://github.com/Kuriel23/dooplay_imports

---

## 5. CDN Hostnames (Known)

### Video CDNs:
- tmstr5.neonhorizonworkshops.com
- tmstr5.cloudnestra.com
- megacloud.live
- vod3.ironwallnet.com
- storm.vodvidl.site

### Embed Sources:
- vidsrc.to
- vsembed.ru
- cloudnestra.com
- jeniusplay.com

---

## 6. Netflix/HBO/Disney+/Apple TV+ Content

### Pertanyaan: Dari mana IDLIX dapet konten premium?

### Kemungkinan Sumber:
1. **Embed sources sudah punya** — vidsrc.to, vsembed.ru dll sudah punya SEMUA konten termasuk originals
2. **Content aggregator API** — layanan yang bulk provide m3u8 links
3. **Torrent → Encode → CDN** — download, re-encode, host sendiri

### Yang perlu di-research:
- [ ] Cek apakah vidsrc.to punya Netflix Originals (Stranger Things, dll)
- [ ] Cek apakah vsembed.ru punya HBO content (Game of Thrones, dll)
- [ ] Cek apakah cloudnestra.com punya Disney+ content
- [ ] Cari content aggregator APIs (GitHub, Telegram, darkweb)
- [ ] Cek apakah ada layanan m3u8 provider yang bisa di-pake

### Testing URLs:
```
Netflix Original: Stranger Things (TMDB: 66732)
HBO: Game of Thrones (TMDB: 1399)
Disney+: The Mandalorian (TMDB: 82856)
Apple TV+: Ted Lasso (TMDB: 97546)
```

---

## 7. Rencana Build

### Phase 1: Video Resolver (clone jeniusplay.com)
- [ ] Build vidsrc chain scraper (pure HTTP, no browser)
- [ ] Build API endpoint: POST /api/resolve → m3u8 URL
- [ ] Cache system (6 jam TTL)
- [ ] CDN vars resolver (Node.js VM sandbox)

### Phase 2: Content Database
- [ ] SQLite database untuk konten
- [ ] Metadata dari TMDB API
- [ ] m3u8 URL storage + expiry tracking

### Phase 3: Admin Panel
- [ ] Tambah konten (TMDB ID → auto-import)
- [ ] Bulk import (CSV atau list TMDB IDs)
- [ ] Edit/delete konten

### Phase 4: HLS.js Player
- [ ] Ganti iframe dengan HTML5 video player
- [ ] HLS.js untuk m3u8 playback
- [ ] Subtitle Indonesia (SRT/VTT)
- [ ] Quality selector

### Phase 5: Auto-Refresh
- [ ] Cron job tiap 6 jam
- [ ] Cek m3u8 expired
- [ ] Re-resolve yang expired

---

## 8. Tools & Dependencies

### Backend:
- Node.js (Express)
- SQLite (better-sqlite3)
- node-fetch atau axios
- vm (Node.js built-in) untuk CDN vars

### Frontend:
- React + Vite
- hls.js untuk m3u8 playback
- video.js atau plyr (optional)

### TMDB API:
- API Key: 9e627fb78e0bf60cb5e464b28c36b321
- Base URL: https://api.themoviedb.org/3

---

## 9. Risiko & Mitigasi

### Risiko:
1. Embed sources down/blocked → Multiple fallback sources
2. m3u8 URLs expire cepat → Auto-refresh cron
3. Cloudflare protection → curl_cffi impersonate
4. Rate limiting → Delay between requests

### Mitigasi:
1. Support multiple embed sources (vidsrc, vsembed, dll)
2. Cache + auto-refresh setiap 6 jam
3. Pakai curl_cffi atau cloudscraper
4. Random delay 0.3-0.8 detik

---

## 10. Next Steps

1. ✅ Research & dokumentasi (DONE)
2. ⏳ Testing vidsrc chain (cek Netflix/HBO/Disney+ content)
3. ⏳ Build video resolver
4. ⏳ Build content database
5. ⏳ Build admin panel
6. ⏳ Build HLS.js player
7. ⏳ Deploy & test

---

> **Catatan:** Dokumentasi ini akan di-update seiring research berkembang.

---

## 11. Additional Resources Found

### A. NetMirror Netflix Scraper
- **Repo:** https://github.com/AliHaSSan-13/Netflix-scrapper
- **Description:** Playwright-based scraper for NetMirror (net22.cc) - Netflix mirror
- **Method:** Capture m3u8 URLs via Playwright network interception
- **Use Case:** Netflix Originals content
- **Caveat:** Needs Playwright (browser-based)

### B. Free Movie Series DB API
- **Repo:** https://github.com/TelegramPlayground/Free-Movie-Series-DB-API
- **Stars:** 162
- **Description:** FREE UnOfficial Movie / Series Search API, without APIKeys
- **API URL:** https://imdb.iamidiotareyoutoo.com/docs/index.html
- **Use Case:** Movie metadata (no video URLs)
- **Caveat:** Metadata only, no streaming URLs

### C. video-api (HLS Streaming URLs)
- **Repo:** https://github.com/byteful/video-api
- **Description:** REST API that provides direct HLS streaming URLs from movie/show names
- **Method:** Scrapes fmovies.ps via Puppeteer + uBlock Origin
- **Endpoints:**
  - GET /movie?name={name}&player={true}
  - GET /show?name={name}&season={s}&episode={e}&player={true}
  - GET /search?query={title}
- **Use Case:** Get m3u8 URLs from movie names
- **Caveat:** Slow (webscraping), may break if fmovies.ps changes

### D. Vidoy CDN Resolver
- **Repo:** https://github.com/RozhakDev/VidoyCdnResolver
- **Description:** Resolve CDN and embed video URLs from Vidoy
- **Method:** Extract video ID -> fetch embed -> extract CDN URL
- **Use Case:** Resolve Vidoy embed URLs to CDN URLs

### E. M3U8 Telegram Bots
- **Repo:** https://github.com/alien5516788/M3U8DL
- **Description:** Telegram bot to download m3u8 video streams
- **Use Case:** Download m3u8 streams via Telegram

---

## 12. Content Sources Analysis

### Netflix Originals (Stranger Things, etc.)
- **Source 1:** NetMirror (net22.cc) - Netflix mirror site
- **Source 2:** vidsrc.to - Has Netflix content (need to verify)
- **Source 3:** fmovies.ps - Has Netflix content

### HBO Content (Game of Thrones, etc.)
- **Source 1:** vidsrc.to - Has HBO content (need to verify)
- **Source 2:** fmovies.ps - Has HBO content

### Disney+ Content (The Mandalorian, etc.)
- **Source 1:** vidsrc.to - Has Disney+ content (need to verify)
- **Source 2:** fmovies.ps - Has Disney+ content

### Apple TV+ Content (Ted Lasso, etc.)
- **Source 1:** vidsrc.to - Has Apple TV+ content (need to verify)
- **Source 2:** fmovies.ps - Has Apple TV+ content

---

## 13. Testing Plan

### Test 1: VidSrc Chain (HTTP only, no browser)
- Netflix Original: Stranger Things (TMDB: 66732)
- HBO: Game of Thrones (TMDB: 1399)
- Disney+: The Mandalorian (TMDB: 82856)
- Apple TV+: Ted Lasso (TMDB: 97546)

### Test 2: video-api (Puppeteer needed)
- Deploy video-api locally
- Test GET /movie?name=Stranger+Things
- Check if m3u8 URL is returned

---

## 14. Recommended Approach

### Combined Strategy:
1. Try VidSrc chain first (HTTP, fast)
2. If fails, try video-api (Puppeteer, slower)
3. If fails, try NetMirror (Playwright, heaviest)

---

## 15. Tools and Resources Collected

1. vidsrc chain scraper (HTTP, no browser) - PRIMARY
2. IDLIX downloader (architecture reference)
3. VidoyCdnResolver (pattern reference)
4. CryptoJsAes helper (encryption reference)
5. DooPlay import system (WordPress reference)
6. NetMirror Netflix scraper (Playwright fallback)
7. Free-Movie-Series-DB-API (metadata API)
8. video-api (HLS streaming URLs)
9. M3U8 Telegram bots (download reference)

---

> **Status:** Research COMPLETE. Ready to build.
> **Next:** Testing vidsrc chain for Netflix/HBO/Disney+ content.

