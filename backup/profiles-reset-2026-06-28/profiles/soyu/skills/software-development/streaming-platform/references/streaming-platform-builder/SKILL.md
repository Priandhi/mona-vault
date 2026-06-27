---
name: streaming-platform-builder
description: Build streaming/media platform web apps with TMDB data, video embeds, mobile-first UI. Covers React+Express stack, embed source selection, Indonesian UI patterns, Netflix-style layouts.
triggers:
  - streaming platform
  - movie site
  - watch movies online
  - TMDB integration
  - video embed
  - film streaming
  - nonton film
---

# Streaming Platform Builder

Build full-stack streaming/media platforms using TMDB API for metadata and third-party embed sources for video playback.

## Stack

- **Frontend**: React 18 + Vite + React Router v6
- **Backend**: Node.js + Express (ES modules)
- **Data**: TMDB API (free, requires API key from themoviedb.org)
- **Video**: Third-party embed sources (see `references/embed-testing-2026-06.md` for comprehensive test results)
- **Deploy**: PM2 + Cloudflare Tunnel for instant public access

## Critical: Mobile-First Design

This user accesses primarily from iPhone. ALL design decisions must prioritize mobile:

- **Buttons**: Full-width stacked on mobile, minimum 44px tap target
- **Navbar**: Hamburger menu with full-screen sidebar overlay on mobile
- **Cards**: 140px width on mobile, 180px on desktop
- **Hero buttons**: Stack vertically on mobile with full width
- **Search**: Hidden on mobile navbar, accessible via icon tap → full-width overlay
- **No hover-dependent interactions** on mobile

## Embed Sources (Tested & Ranked)

**Testing methodology** (always run before adding a new source):
```bash
# 1. Check HTTP status
curl -s -o /dev/null -w '%{http_code}' -L --max-time 10 'https://source.com/movie/550'

# 2. Verify iframe/video content
curl -s -L --max-time 10 'https://source.com/movie/550' | grep -ci 'iframe\|video\|player'
```

**⚠️ CRITICAL: Don't claim "done" until you've VALIDATED actual content, not just HTTP status.** User explicitly corrected: "mending lu tes dan cek dulu sebelum bilang done 🫠 soal nya gak bisa semua." HTTP 200 can return HTML error pages, binary garbage, or empty shells. Always inspect the response body.

**Recommended multi-server strategy**: Provide 5-7 servers for movies, 5 for TV. User expects resilience — "gaboleh menyerah kita punya banyak cara buat bypass."

### Movie Embeds (Tested 2026-06)

| Source | URL Pattern | Status | iframe | Notes |
|--------|------------|--------|--------|-------|
| VidLink.pro | `https://vidlink.pro/movie/{tmdb_id}` | ✅ 200 | 1 | ⭐ Primary — cleanest, minimal ads |
| AutoEmbed | `https://autoembed.co/movie/tmdb/{tmdb_id}` | ✅ 200 | 4 | Multi-iframe chain |
| VidSrc.to | `https://vidsrc.to/embed/movie/{tmdb_id}` | ✅ 200 | 3 | Reliable fallback |
| Flicky.host | `https://flicky.host/embed/movie/{tmdb_id}` | ✅ 200 | 4 | Good alternative |
| VidCloud9 | `https://vidcloud9.com/embed/movie/{tmdb_id}` | ✅ 200 | 0 | Works but no iframe detected |
| 111Movies | `https://111movies.com/movie/{tmdb_id}` | ✅ 200 | 1 | Basic embed |
| VidSrc.in | `https://vidsrc.in/embed/movie/{tmdb_id}` | ✅ 200 | 2 | Alternative to .to |
| PrimeWire | `https://primewire.to/movie/{tmdb_id}` | ✅ 200 | ? | Untested for iframe |

### TV Series Embeds (Tested 2026-06)

| Source | URL Pattern | Status | Notes |
|--------|------------|--------|-------|
| VidLink.pro | `https://vidlink.pro/tv/{tmdb_id}/{season}/{episode}` | ✅ 200 | Primary |
| VidSrc.to | `https://vidsrc.to/embed/tv/{tmdb_id}/{season}/{episode}` | ✅ 200 | Good fallback |
| Flicky.host | `https://flicky.host/embed/tv/{tmdb_id}/{season}/{episode}` | ✅ 200 | Reliable |
| VidCloud9 | `https://vidcloud9.com/embed/tv/{tmdb_id}/{season}/{episode}` | ✅ 200 | Works |
| VidSrc.in | `https://vidsrc.in/embed/tv/{tmdb_id}/{season}/{episode}` | ✅ 200 | Alternative |

**Always provide:**
1. 5-7 server buttons in a horizontal row above the player
2. Active state styling (red background) for selected server
3. "Open in New Tab" fallback link (critical for mobile Safari iframe issues)
4. Server switching without page reload (React state toggle)
5. **Auto-fallback timer** — see Embed Auto-Fallback Pattern below

### Embed Auto-Fallback Pattern (timer-based)

**Problem**: Even with 5-7 server buttons, user has to manually click through each one when embed sources fail silently. Most users don't realize a server has failed — they just see a black iframe. Result: "banyak film gak bisa diputar".

**Solution**: When user clicks play, start a 10s timer. If iframe hasn't fired `onLoad` by then, auto-cycle to the next server. Visual hint shows which server is active + countdown feel.

```jsx
const EMBED_SOURCES = [
  { name: 'Server 1 (VidLink)', url: (id) => `https://vidlink.pro/movie/${id}`, priority: 1 },
  { name: 'Server 2 (AutoEmbed)', url: (id) => `https://autoembed.co/movie/tmdb/${id}`, priority: 1 },
  { name: 'Server 3 (VidSrc)', url: (id) => `https://vidsrc.to/embed/movie/${id}`, priority: 1 },
  { name: 'Server 4 (Flicky)', url: (id) => `https://flicky.host/embed/movie/${id}`, priority: 2 },
  { name: 'Server 5 (111Movies)', url: (id) => `https://111movies.com/movie/${id}`, priority: 1 },
  { name: 'Server 6 (VidSrc.in)', url: (id) => `https://vidsrc.in/embed/movie/${id}`, priority: 2 },
  { name: 'Server 7 (Movie4k)', url: (id) => `https://movie4kto.net/embed/${id}`, priority: 2 },
  // ... add more as discovered
]

export default function MovieDetail() {
  const [srcIdx, setSrcIdx] = useState(0)
  const [showPlayer, setShowPlayer] = useState(false)
  const [serverOk, setServerOk] = useState(true)
  const [autoFailed, setAutoFailed] = useState(false)

  // Auto-fallback: if iframe hasn't loaded in 10s, try next server
  useEffect(() => {
    if (!showPlayer) return
    setServerOk(true)
    setAutoFailed(false)
    const t = setTimeout(() => {
      setServerOk(prev => {
        if (!prev) {
          setSrcIdx(idx => {
            const next = (idx + 1) % EMBED_SOURCES.length
            setAutoFailed(true)
            return next
          })
          return true
        }
        return prev
      })
    }, 10000)
    return () => clearTimeout(t)
  }, [srcIdx, showPlayer, id])
```

**Critical iframe props** — `key` forces remount on server change, `onLoad` resets the timer:
```jsx
<iframe
  key={`${srcIdx}-${id}`}  // remount on server change
  src={EMBED_SOURCES[srcIdx].url(id)}
  allowFullScreen
  allow="autoplay;encrypted-media;fullscreen"
  referrerPolicy="origin"
  onLoad={() => { setServerOk(true); setAutoFailed(false); }}
  onError={() => { setServerOk(false); }}
/>
```

**Manual override buttons** for power users (left/right):
```jsx
<button onClick={()=>{if(srcIdx>0){setSrcIdx(srcIdx-1);setServerOk(true);}}}>← Server Sebelumnya</button>
<button onClick={()=>{if(srcIdx<EMBED_SOURCES.length-1){setSrcIdx(srcIdx+1);setServerOk(true);}}}>Server Berikutnya →</button>
```

**Why this works**: cross-origin iframes don't fire useful `onError` events (browser security). `onLoad` fires reliably when the iframe content loads OR fails. The 10s timer catches the "loads but video doesn't play" case. Don't try to detect playback state — just give up and try the next server.

**Honest fallback message**: When ALL servers fail, tell user the truth — "💡 Semua server pihak ketiga — kalo gak ada yang play, kemungkinan film ini emang belum tersedia di embed manapun."

## Design Handoff Workflow (wait for "gas")

**User rule (validated 2026-06-14):** when user shares a design image (footer mockup, side menu, page layout, anything), do NOT immediately implement. The flow is:

1. User shares image (often with: "tunggu aku kirim gambar dulu ya kalau udah kelar dan aku bilang gas baru di update di web nya")
2. Mona acknowledges + **saves design details to `~/mona-notes/iclix-<topic>-redesign-vN.md`** — full text breakdown: section names, copy text, icons, colors, layout.
3. If more images are expected, ask "tunggu gambar lain atau udah semua?" — don't assume.
4. After all images received, **wait for explicit "gas"**. Don't deploy or edit code until the word lands.
5. On "gas" → execute update on all mentioned pages (footer + side menu + whatever else in the same drop), build, deploy, verify with vision + page.evaluate.

**Why this exists:** User controls the cadence. Skipping the wait step and deploying before "gas" is treated as overreach ("gak ada perubahan mona😭...lu cuma tambah fitur di vip dan warna ICLIX 😭" — when partial changes looked like nothing changed). The wait is also a checkpoint — user often has 2-3 more images queued.

**Anti-pattern:** Treating "gas update web sekarang" as license to redesign the whole site. Update ONLY the components shown in the shared images. Other pages stay as-is unless user explicitly says "seluruh web".

## Footer v3 — 5-Section Premium Pattern (validated 2026-06-14)

User shipped a 2-image drop: footer design (5 sections) + side menu drawer. Both went live in one rebuild. Copy-paste-ready structure for similar streaming platform footers:

```jsx
<footer className="premium-footer">
  <div className="footer-glow" />  {/* red radial at very top */}
  <div className="footer-container">
    <div className="footer-section">
      <h3 className="footer-section-title">HUBUNGI KAMI</h3>
      <div className="contact-grid">
        <a href="https://t.me/oxjosee" className="contact-card" target="_blank" rel="noopener noreferrer">
          <div className="contact-icon-circle telegram"><Send size={22} /></div>
          <div className="contact-info">
            <div className="contact-label">TELEGRAM</div>
            <div className="contact-value">@oxjosee</div>
          </div>
          <div className="contact-arrow">›</div>
        </a>
        <a href="mailto:..." className="contact-card">
          <div className="contact-icon-circle email"><Mail size={22} /></div>
          <div className="contact-info">
            <div className="contact-label">EMAIL</div>
            <div className="contact-value">addr<br/>@gmail.com</div>
          </div>
          <div className="contact-arrow">›</div>
        </a>
      </div>
    </div>
    {/* Section 2: DOWNLOAD APLIKASI — same card grid, gold SOON badge */}
    {/* Section 3: IKUTI KAMI — 4 social circles (Instagram/TikTok/Twitter/YouTube) */}
    {/* Section 4: LEGAL & INFO — 4 list rows with gold icon + arrow */}
    {/* Section 5: ICLIX Brand Banner — 3D red play triangle + tagline */}
  </div>
  <div className="footer-copyright">© 2026 ICLIX by Hexa</div>
</footer>
```

**CSS essentials** (gold accent + dark cards + soft borders):
```css
.premium-footer { background:#000; margin-top:4rem; overflow:hidden; position:relative; }
.footer-glow { position:absolute; top:0; left:0; right:0; height:1px; background:linear-gradient(90deg,transparent,#e50914,transparent); }
.footer-section { margin-bottom:48px; }
.footer-section-title { text-align:center; color:#fbbf24; font-size:18px; font-weight:800; letter-spacing:3px; margin-bottom:24px; }
.contact-card { display:flex; align-items:center; gap:14px; padding:16px 18px; background:rgba(20,20,20,0.7); border:1px solid rgba(255,255,255,0.06); border-radius:14px; transition:all .3s; position:relative; }
.contact-card:hover { border-color:rgba(229,9,20,0.3); transform:translateY(-2px); }
.contact-icon-circle { width:44px; height:44px; border-radius:50%; display:flex; align-items:center; justify-content:center; flex-shrink:0; box-shadow:0 4px 12px rgba(0,0,0,0.4); }
.contact-icon-circle.telegram { background:linear-gradient(135deg,#29b6f6,#0288d1); }
.contact-icon-circle.email { background:linear-gradient(135deg,#ef4444,#b91c1c); }
.contact-info { flex:1; min-width:0; }
.contact-label { color:#fff; font-size:13px; font-weight:800; letter-spacing:1px; }
.contact-value { color:#d2d2d2; font-size:13px; word-break:break-all; }
.contact-arrow { color:#666; font-size:24px; margin-left:auto; }
.soon-badge { position:absolute; top:6px; right:6px; background:linear-gradient(135deg,#fbbf24,#f59e0b); color:#000; font-size:9px; font-weight:800; padding:3px 6px; border-radius:4px; letter-spacing:0.5px; }
.social-circle { width:50px; height:50px; border-radius:50%; display:flex; align-items:center; justify-content:center; }
.social-circle.instagram { background:linear-gradient(135deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888); }
.legal-item { display:flex; align-items:center; gap:14px; padding:14px 18px; background:rgba(20,20,20,0.7); border:1px solid rgba(255,255,255,0.06); border-radius:12px; }
.legal-icon-wrap { width:36px; height:36px; border-radius:10px; background:linear-gradient(135deg,#fbbf24,#f59e0b); color:#000; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.iclix-brand-banner { position:relative; padding:48px 4%; margin-top:32px; background:linear-gradient(180deg,transparent,rgba(229,9,20,0.1)); overflow:hidden; }
```

**Pitfall — DON'T use complex multi-color SVG paths for brand icons** (e.g. raw Telegram paper-plane with 4 colored paths, raw Google Play logo). Use Lucide's `Send`/`Mail` for simple icons. Complex paths with `fill="white"` can render as solid white blobs when the path includes a filled background shape.

## Side Menu Drawer v3 Pattern (validated 2026-06-14)

Mobile-first drawer with split-color logo, auth buttons row, and 10-item vertical nav. Key rules: drawer is hidden by default (`transform:translateX(-100%)`), slides in on hamburger click, has dark backdrop overlay, body scroll lock when open.

**Logo variant in drawer (DIFFERENT from navbar):**
- "ICL" = gold gradient (gold/amber, NOT red)
- "IX" = red solid (#e50914)
- "BY HEXA" = gold below

**Required structure** (works for any streaming platform):
```jsx
<aside className={`side-menu ${isOpen ? 'open' : ''}`}>
  <div className="side-menu-head">
    <span className="side-menu-logo"><span style={{color:'#fbbf24'}}>ICL</span><span style={{color:'#e50914'}}>IX</span></span>
    <button onClick={close} className="side-menu-close"><X size={22} /></button>
  </div>
  <div className="side-menu-auth">
    <button className="auth-btn masuk"><LogIn size={16} />Masuk</button>
    <button className="auth-btn daftar"><UserPlus size={16} />Daftar</button>
  </div>
  <nav className="side-menu-list">
    {MENU.map(item => (
      <Link key={item.path} to={item.path} className={`side-menu-item ${pathname===item.path ? 'active' : ''}`} onClick={close}>
        <item.icon size={20} className="side-menu-icon" />
        <span className="side-menu-label">{item.label}</span>
        {pathname===item.path && <Check size={18} className="side-menu-check" />}
      </Link>
    ))}
  </nav>
  <div className="side-menu-glow" />  {/* red radial at very bottom */}
</aside>
<div className="side-menu-backdrop" onClick={close} />
```

**Active state (red glow + checkmark):**
```css
.side-menu-item.active { background:linear-gradient(90deg,rgba(229,9,20,0.2),transparent); border-left:3px solid #e50914; }
.side-menu-item.active .side-menu-icon { color:#e50914; filter:drop-shadow(0 0 8px rgba(229,9,20,0.5)); }
.side-menu-item.active .side-menu-label { color:#fff; font-weight:800; }
.side-menu-check { color:#fff; margin-left:auto; }
```

**Standard 10-item menu for Indonesian streaming platform:**
Beranda (Home) · Film (Movies) · Serial TV · Drama Asia · Live TV · Anime · Trending · VIP · Negara (Country) · Tahun (Year)

## Design Preview Workflow (HTML Mockup → Screenshot → Telegram)

**Use when:** user wants a "design preview", "mockup", "redesign concept", or "bikin desain mirip X" — typically before any code integration. The deliverable is a **self-contained HTML file + screenshots** the user can review on their phone, NOT a full React implementation. Faster turnaround, gets user approval before committing to a 50-file refactor.

**Why this exists:** Jumping straight to rewriting React components (`Home.jsx`, `MovieCard.jsx`, etc.) for a redesign is wasteful — user can't visualize the final result, gives feedback, and you rebuild. The preview workflow collapses this to: build → screenshot → 1 round of feedback → 1 round of integration.

### Recipe (validated 2026-06-13 on ICLIX Premium Redesign v2)

**1. Build self-contained HTML at `~/<project>-design-preview/index.html`**
- One file, all CSS embedded in `<style>`, fonts via Google Fonts CDN, no JS framework
- Use phone-mockup frames (375×812 + notch + status bar) to show mobile screens
- Render multiple "screens" side-by-side in a CSS grid (Home, Detail, Profile, Downloads, Features)
- Premium touches: glassmorphism, multi-layer text-shadow for 3D logos, radial red glows, gradient borders, hover-lift effects
- Total file size ~50-70KB is fine — keeps it shareable

**2. Serve via Python http.server in background**
```bash
mkdir -p ~/iclix-design-preview && cd ~/iclix-design-preview
# Use terminal(background=true) for the long-lived server
python3 -m http.server 8765
# Verify ready:
sleep 1 && curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8765/index.html  # expect 200
```

**3. Screenshot each component with Playwright Python (NEVER use `waitUntil: 'networkidle'`)**
- **CRITICAL pitfall:** `networkidle` hangs ~60s waiting for Google Fonts that never reach idle state. Use `domcontentloaded` + `wait_for_timeout(2500)` to let fonts settle.
- Use **element-level `locator.screenshot()`** (NOT full-page) for clean phone-frame crops without surrounding chrome
- See `templates/design-preview-screenshot.py` for the copy-paste-ready script

**4. Send screenshots via `send_message` with `MEDIA:` prefix, one per message with a caption** (NOT as an album — albums get reordered/squashed on Telegram mobile)

**5. End with a short summary + 3-4 next-step options** ("gas integrate", "tambah X", "ubah Y", "beda lagi")

### Known-good Playwright venv (this environment)

```python
# /tmp/pw-venv has playwright + chromium drivers
# Chromium binary path:
CHROME = '/home/ubuntu/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome'
# Python interpreter:
PYTHON = '/tmp/pw-venv/bin/python3'
# Launch:
chromium.launch(executable_path=CHROME, args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
```

Other Chromium binaries available: `/home/ubuntu/.cache/puppeteer/chrome/linux-*/chrome-linux64/chrome`, `/home/ubuntu/.cache/cloakbrowser/chromium-*/chrome`.

### Design system quick reference (red-black cyber-thriller premium)

CSS variables that work across Netflix-style streaming UIs:
```css
:root {
  --bg: #000;            --bg-2: #0a0a0a;    --bg-3: #111;    --bg-4: #181818;
  --red: #e50914;        --red-2: #ff1a25;   --red-3: #b00610;
  --red-glow: rgba(229,9,20,.5);
  --text: #fff;          --text-2: #d2d2d2;  --text-3: #8a8a8a; --text-4: #5a5a5a;
  --border: rgba(255,255,255,.08);
  --grad-red: linear-gradient(135deg,#ff2a3a 0%,#e50914 50%,#a00610 100%);
  --grad-radial: radial-gradient(ellipse at top,rgba(229,9,20,.15),transparent 60%);
}
```

3D brand logo (5-layer text-shadow + perspective + gradient text-fill + drop-shadow):
```css
.logo-3d {
  font-weight: 900; font-size: 72px; letter-spacing: -4px; line-height: 1;
  background: linear-gradient(180deg,#ff3b4d 0%,#ff1a25 25%,#e50914 55%,#b00610 85%,#7a0409 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  filter:
    drop-shadow(0 1px 0 rgba(255,107,122,.6))
    drop-shadow(0 2px 0 rgba(229,9,20,.5))
    drop-shadow(0 3px 0 rgba(196,7,15,.5))
    drop-shadow(0 4px 0 rgba(160,6,13,.45))
    drop-shadow(0 5px 0 rgba(122,4,9,.4))
    drop-shadow(0 6px 1px rgba(0,0,0,.4))
    drop-shadow(0 0 12px rgba(229,9,20,.5))
    drop-shadow(0 0 30px rgba(229,9,20,.3));
  transform: perspective(500px) rotateX(8deg);
}
```

Glassmorphism card (premium feature card pattern):
```css
.glass-card {
  background: linear-gradient(135deg,rgba(229,9,20,.15) 0%,rgba(160,6,16,.05) 100%);
  border: 1px solid rgba(229,9,20,.25);
  border-radius: 16px;
  position: relative; overflow: hidden;
  transition: all .3s;
}
.glass-card:hover {
  transform: translateY(-4px);
  border-color: rgba(229,9,20,.5);
  box-shadow: 0 16px 40px -10px rgba(229,9,20,.3);
}
.glass-card::before {
  content:''; position:absolute; top:-30px; right:-30px;
  width:120px; height:120px;
  background: radial-gradient(circle,var(--red-glow) 0%,transparent 70%);
  filter: blur(20px);
}
```

### Indonesian UI text for premium features (validated list)

When adding a "Semua Fitur Premium" section, use these 12 (covers Netflix-style + Indo context):
1. 4K Ultra HD — "Kualitas gambar tertinggi untuk pengalaman menonton sinematik"
2. Dolby Atmos — "Audio 3D surround yang menghidupkan setiap adegan"
3. Tanpa Iklan — "Tonton tanpa gangguan iklan, popup, atau banner sama sekali"
4. Unduh & Tonton — "Konten favorit bisa diunduh dan ditonton offline kapan saja"
5. Multi Device — "Nikmati di smartphone, tablet, laptop, dan smart TV sekaligus"
6. Profil Anak — "Konten khusus edukatif dan aman untuk anak-anak"
7. Rekomendasi AI — "Saran personal dari machine learning sesuai seleramu"
8. Kontrol Orang Tua — "Atur batasan konten dan rating dengan mudah"
9. Multi Subtitle — "Subtitle Indonesia, English, dan 20+ bahasa lainnya"
10. Watchlist — "Simpan film & series favorit untuk ditonton nanti"
11. Riwayat Tonton — "Lanjutkan dari menit terakhir yang kamu tinggalkan"
12. Update Harian — "Konten baru setiap hari, film & series original mingguan"

### Netflix-style Home page section patterns (validated 2026-06-13)

When updating a Home page to match the Netflix/Disney+ reference layout, the user-approved section recipe is:

**Order top-to-bottom (validated on ICLIX):**
1. **Hero carousel** (existing — top-rated content as backdrop slides)
2. **Lanjutkan Menonton** (Continue Watching) — horizontal cards 16:9 with progress bar at bottom, red time remaining label
3. **Pilihan Untukmu** with **AI badge** — small red `AI` pill next to title (`background: linear-gradient(135deg,#ff1a25,#a00610); box-shadow: 0 0 12px rgba(229,9,20,.4)`)
4. **Jelajahi Berdasarkan Genre** — circle icons (72×72) with emoji, name below, hover scales to 1.05 with red border glow
5. **Film Terbaru** + **Series Tayang** + **Asian Releases** (existing auto-discovery rows preserved)
6. **ICLIX Originals** — vertical poster cards (160×228, 2:3 ratio) with **ICLIX badge** at top-left (black background + red border + red text + glassmorphism `backdrop-filter: blur(8px)`), title + rating at bottom with dark gradient overlay
7. **Trending / Top Rated / TV Series** (existing rows preserved)
8. **Premium banner** at the END of the page — 56×56 crown icon in red gradient box, title + subtitle, "Upgrade" red button on the right, with `::before` radial glow positioned top-right for premium feel

**Section header pattern** (matches reference design):
```jsx
<div className="section-head">
  <h2 className="section-title">Pilihan Untukmu <span className="ai-badge">AI</span></h2>
  <Link to="/somewhere" className="section-see">Lihat Semua ›</Link>
</div>
```
```css
.section-head { display:flex; align-items:center; justify-content:space-between; padding:0 4%; margin-bottom:12px; }
.section-title { font-size:20px; font-weight:700; display:flex; align-items:center; gap:10px; }
.section-see { color:#999; font-size:13px; transition:color .2s; }
.section-see:hover { color:var(--red); }
.ai-badge { background:linear-gradient(135deg,#ff1a25,#a00610); padding:3px 8px; border-radius:4px; font-size:10px; font-weight:800; letter-spacing:1px; box-shadow:0 0 12px rgba(229,9,20,.4); color:#fff; }
```

**MovieRow `hideTitle` prop** (when section has its own header): pass `hideTitle` to suppress the internal `<h2>`:
```jsx
<MovieRow title="" items={topRated.slice(0, 10)} mediaType="movie" hideTitle />
```

**Lanjutkan Menonton card** (16:9 with progress):
```jsx
<Link to={path} className="cw-card">
  <div className="cw-card-img" style={{backgroundImage: `url(https://image.tmdb.org/t/p/w500${backdrop})`}} />
  <div className="cw-card-content">
    <div className="cw-card-title">{title}</div>
    <div className="cw-card-time">{time}</div>
  </div>
  <div className="cw-progress"><div className="cw-progress-fill" style={{width: `${progress}%`}} /></div>
</Link>
```
- Width 280px, aspect-ratio 16:9, border-radius 10px
- Progress bar at bottom: 3px tall, red gradient fill, 8px red glow
- Read history from `localStorage.getItem('iclix_history')` as JSON array

**Genre circle with emoji** (no Lucide icon — emoji looks better at small size for genre):
```jsx
const iconForGenre = (name) => {
  const n = (name||'').toLowerCase()
  if (n.includes('action')) return '💥'
  if (n.includes('sci') || n.includes('fant')) return '🚀'
  if (n.includes('thrill') || n.includes('mystery')) return '🔪'
  if (n.includes('romance')) return '💔'
  if (n.includes('comedy')) return '😄'
  if (n.includes('horror')) return '👻'
  if (n.includes('anim')) return '🎌'
  return '🎬'
}
```

**Premium banner** (full-width at page bottom):
```jsx
<Link to="/vip" className="premium-banner">
  <div className="premium-banner-inner">
    <div className="premium-banner-icon">👑</div>
    <div className="premium-banner-text">
      <div className="premium-banner-title">Upgrade ke Premium</div>
      <div className="premium-banner-sub">Nonton tanpa batas dengan kualitas 4K Dolby Atmos · Rp 5.000/bulan</div>
    </div>
    <div className="btn btn-primary">Upgrade</div>
  </div>
</Link>
```
```css
.premium-banner { margin:32px 4% 24px; padding:24px; border-radius:16px;
  background:linear-gradient(135deg,rgba(229,9,20,.15),rgba(160,6,16,.05));
  border:1px solid rgba(229,9,20,.3); position:relative; overflow:hidden; }
.premium-banner::before { content:''; position:absolute; top:-50%; right:-20%;
  width:240px; height:240px; background:radial-gradient(circle,rgba(229,9,20,.5) 0%,transparent 70%);
  filter:blur(40px); }
```

**Pitfall when adding new sections to existing Home.jsx:** The `MovieRow` component renders its own `<h2 className="section-title">` even when you pass `title=""`. Always update `MovieRow.jsx` to support `hideTitle` prop, OR pass `title=""` and accept the empty heading (looks broken). The home-content wrapper needs `background:#000` set explicitly, otherwise the existing semi-transparent overlays leak through.

### Pitfalls

- **Don't integrate React until user approves the preview.** Always present screenshots first, get explicit "gas" before touching production code.
- **Don't use `waitUntil: 'networkidle'`** for pages loading Google Fonts — use `domcontentloaded` + explicit timeout. Costs 60s otherwise.
- **Don't send screenshots as a Telegram album** — they get reordered/squashed. Send one per `send_message` call with its own caption.
- **Don't use Tailwind for the preview** — the goal is a portable single file. Embedded CSS only.
- **Don't claim "all 6 screens look good" without running vision_analyze on each** — the screenshot might have rendered elements off-screen or with broken CSS.
- **Don't partial-update after a full redesign request** — when user says "update like this image", update ALL major pages (Home, Detail, Profile, Downloads), not just the most visible one. User reads "no changes" if 80% of the app is still old. See section 0 above.
- **Don't gradient-color the ICLIX word in the logo** — user wants PURE solid red (#e50914), not a red gradient (light to dark). BY HEXA must be PURE white, not gray. See section 1 above.

## Auto-Discovery Cron Pattern (Daily Latest Content Sync)

**User request (2026-06-13)**: "Untuk setiap film apakah kamu gak bisa mencari update episode terbaru terus langsung otomatis kamu tambah kan?" — automatically discover new movies/episodes and surface them on the platform.

**Auto-discovery cron pattern** (see `templates/sync_latest.py.template` for full reusable script):
1. Daily cron at 9 AM WIB (cron `0 2 * * *` UTC, since WIB = UTC+7) runs a Python sync script
2. Script fetches 4 TMDB sources and dedupes against a `state.json` of seen IDs
3. Writes results to `cache/latest.json` (cumulative, never shrinks — only adds new)
4. Sends Telegram notification on new IDs (only when delta > 0)
5. Frontend Home page renders 3 new MovieRows from `/api/latest`: "🆕 Film Terbaru", "🌏 Asian Releases", "📺 Series Tayang Sekarang"
6. Manual refresh via `POST /api/latest/refresh` (executes the sync script on demand)

**Sources polled**:
```python
# 1. Movies in theaters now (region ID) + upcoming (next 30 days)
tmdb('/movie/now_playing', {'region': 'ID', 'page': 1})
tmdb('/movie/upcoming', {'region': 'ID', 'page': 1})

# 2. TV on the air (currently airing, new episodes weekly)
tmdb('/tv/on_the_air', {'page': 1})

# 3. Asian releases (last 60 days, sorted by release date desc)
#    Filter by with_original_language, requires minimum vote count
for lang in ['ko', 'zh', 'ja', 'th']:
    tmdb('/discover/movie', {
        'with_original_language': lang,
        'sort_by': 'primary_release_date.desc',
        'primary_release_date.lte': today,
        'primary_release_date.gte': (today - 60d),
        'vote_count.gte': 5,
        'page': 1,
    })
```

**Sync script template** (`scripts/sync_latest.py`):
```python
import json, os, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

TMDB_KEY = os.environ.get('TMDB_API_KEY', '')
CACHE = Path('/home/ubuntu/<project>/cache')
STATE_FILE = CACHE / 'state.json'
LATEST_FILE = CACHE / 'latest.json'
WIB = timezone(timedelta(hours=8))

def tmdb(path, params=None):
    base = 'https://api.themoviedb.org/3'
    q = dict(params or {})
    q['api_key'] = TMDB_KEY
    q['language'] = 'en-US'
    url = f"{base}{path}?{urlencode(q)}"
    return json.loads(urlopen(Request(url, headers={'User-Agent': 'ICLIX-Sync/1.0'}), timeout=20).read())

def load_state():  # {'seen_movie_ids': [], 'seen_tv_ids': [], 'last_sync': ''}
    if STATE_FILE.exists(): return json.loads(STATE_FILE.read_text())
    return {'seen_movie_ids': [], 'seen_tv_ids': [], 'last_sync': ''}

def load_latest():  # {'movies': [...], 'tv': [...], 'asian_releases': [...], 'updated': ''}
    if LATEST_FILE.exists(): return json.loads(LATEST_FILE.read_text())
    return {'movies': [], 'tv': [], 'asian_releases': [], 'updated': ''}

# Fetch, dedup, save. Track new IDs and send TG on delta > 0.
# ... (full script pattern, see ICLIX/scripts/sync_latest.py for complete implementation)
```

**Cron install**:
```bash
# 9 AM WIB = 2 AM UTC
( crontab -l 2>/dev/null | grep -v sync_latest ; \
  echo "0 2 * * * /usr/bin/python3 /home/ubuntu/<project>/scripts/sync_latest.py >> /home/ubuntu/<project>/cache/sync.log 2>&1" \
) | crontab -
```

**Backend route** (ES modules — see pitfall #24):
```javascript
import fs from 'fs';
import { exec } from 'child_process';

app.get('/api/latest', async (req, res) => {
  try {
    const latestPath = path.join(__dirname, '../cache/latest.json');
    if (!fs.existsSync(latestPath)) {
      return res.json({ movies: [], tv: [], asian_releases: [], updated: null });
    }
    const data = JSON.parse(fs.readFileSync(latestPath, 'utf-8'));
    res.json(data);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.post('/api/latest/refresh', async (req, res) => {
  exec('python3 /home/ubuntu/<project>/scripts/sync_latest.py', { timeout: 60000 }, (err, stdout, stderr) => {
    if (err) return res.status(500).json({ error: err.message, stderr });
    res.json({ ok: true, output: stdout });
  });
});
```

**Frontend Home integration** (3 new sections, pinned to top):
```jsx
const [latestMovies, setLatestMovies] = useState([])
const [latestTV, setLatestTV] = useState([])
const [latestAsian, setLatestAsian] = useState([])
const [latestUpdated, setLatestUpdated] = useState(null)

// In useEffect: also fetch('/api/latest') and store

// In render (before other rows):
{latestMovies.length > 0 && (
  <MovieRow
    title={`🆕 Film Terbaru${latestUpdated ? ' • Update ' + formatUpdated(latestUpdated) + ' WIB' : ''}`}
    items={latestMovies.map(m => ({...m, media_type: 'movie'}))}
    mediaType="movie"
    highlight="latest"  // adds gold border + "AUTO-UPDATED DAILY" badge
  />
)}
{latestAsian.length > 0 && <MovieRow title="🌏 Asian Releases (Korea/China/Japan/Thailand)" items={...} />}
{latestTV.length > 0 && <MovieRow title="📺 Series Tayang Sekarang (Episode Baru Setiap Minggu)" items={...} />}
```

**Telegram notification on new IDs** (only when delta > 0, prevents spam):
```python
total_new = len(new_movies) + len(new_tv) + len(new_asian)
if total_new > 0:
    lines = [f"🆕 <b>ICLIX — {total_new} konten baru ditemukan</b>\n"]
    # ... format by category
    tg_send("\n".join(lines))
```

**Why this is a cron job, not a webhook**: TMDB doesn't push webhooks. The catalog updates multiple times per day but daily polling is enough for "latest" UX. If you need sub-day freshness, switch to every 6 hours: `0 */6 * * *`.

## Subtitle Overlay System (for Iframe Embed Players)

**User request (2026-06-13):** "Tambahkan subtitle di semua video" — add subtitle support across all videos. **Hard constraint:** video plays inside an embed iframe (cross-origin), so you **cannot access `video.currentTime`** from outside. This rules out automatic sync via `<track>` + native `textTracks`. You need a **manual-sync overlay**.

**Architecture** (validated on ICLIX 2026-06-13):
1. **Parser** — accepts `.srt` and `.vtt` (both full `HH:MM:SS,mmm` and short `MM:SS.mmm` formats). Manual block split + dual regex. Full code in `templates/subtitle-parser.js`.
2. **Search link aggregation** — Cloudflare blocks server-side scraping of Subscene, OpenSubtitles, Yifysubtitles, SubsSaber, SubHD (all 403 from VPS IPs). Provide 5 search URLs that auto-prefill the movie title. User downloads the file locally, then uploads to ICLIX.
3. **Custom overlay div** — `<div className="subtitle-overlay">` positioned absolute over the iframe. White text + black text-shadow + translucent background. `pointer-events: none` so it doesn't block iframe interaction.
4. **Manual sync controls** — `⏸ Pause` / `▶ Lanjutkan` / `⟲ Reset` / `🙈 Hide`. Offset buttons `±1s` / `±5s`. User aligns manually: pause embed → click `▶ Lanjutkan` when embed starts playing → adjust offset until subtitles match.
5. **File upload** — `FileReader.readAsText()` on `.srt`/`.vtt` (max 2MB). State: `subtitleCues: []`, `manualTime: 0`, `subtitleOffset: 0`, `isSyncRunning: false`.

**Search link template** (build URLs server-side, send to frontend):
```js
const movieTitle = movie?.title || movie?.name || ''
const movieYear = (movie?.release_date || movie?.first_air_date || '').slice(0, 4)
const subSearchLinks = [
  { name: 'Subscene', url: `https://subscene.com/subtitles/searchbytitle?query=${encodeURIComponent(movieTitle)}` },
  { name: 'OpenSubtitles', url: `https://www.opensubtitles.com/en/search/all/${encodeURIComponent(movieTitle + ' ' + movieYear)}` },
  { name: 'Yifysubtitles', url: `https://yifysubtitles.com/search?q=${encodeURIComponent(movieTitle)}` },
  { name: 'SubsSaber', url: `https://subssaber.com/?s=${encodeURIComponent(movieTitle)}` },
  { name: 'SubHD (Chinese)', url: `https://subhd.tv/search/${encodeURIComponent(movieTitle)}` },
]
```

**Current cue derivation** (driven by `setInterval` ticking every 100ms when sync is running):
```jsx
useEffect(() => {
  if (!isSyncRunning) return
  const tick = setInterval(() => setManualTime(prev => prev + 0.1), 100)
  return () => clearInterval(tick)
}, [isSyncRunning])

const currentCue = (() => {
  if (!subtitleCues.length || !isSyncRunning) return null
  const t = manualTime + subtitleOffset
  return subtitleCues.find(c => t >= c.start && t <= c.end) || null
})()
```

**Overlay CSS** (gold-standard, copy-paste ready):
```css
.subtitle-overlay {
  position: absolute; left: 0; right: 0; bottom: 24px; text-align: center;
  pointer-events: none; z-index: 10; padding: 0 20px;
}
.subtitle-overlay {
  display: inline-block; color: #fff; font-size: 22px; font-weight: 600;
  line-height: 1.3; background: rgba(0,0,0,0.5);
  padding: 6px 16px; border-radius: 6px; max-width: 90%;
  white-space: pre-wrap;
  text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000,
               0 0 4px rgba(0,0,0,0.9), 0 2px 8px rgba(0,0,0,0.8);
}
```

**Honest user disclosure pattern:** When user asks for a feature that's architecturally hard with iframes, tell them the constraint upfront and offer the manual-sync workaround. Don't pretend you can do automatic sync that you can't.

**To upgrade to fully-automatic sync:** Switch from iframe embeds to a custom HLS.js player. That requires: (1) extracting the actual `.m3u8` URL from the embed source via internal API, (2) replacing `<iframe>` with `<video>` + `hls.js`, (3) using native HTML5 `<track>` with the subtitle file. Multi-day refactor — not for a quick feature add. Document manual-sync as the pragmatic interim.

## TMDB Data Shape: Full-URL vs Raw-Path Field Convention

**Problem (encountered 2026-06-13):** When `/api/latest` (auto-discovery cache) returns items, it serializes them as `{ poster: 'https://image.tmdb.org/t/p/w500/abc.jpg' }` (full URL, pre-built by the sync script). But the rest of the platform's TMDB-direct routes return `{ poster_path: '/abc.jpg' }` (raw path). Components like `MovieCard` and `Hero` only knew about `poster_path` / `backdrop_path`, so the new section rendered **blank grey placeholders** instead of posters.

**Fix pattern** — components must accept BOTH shapes:
```jsx
// MovieCard
const poster = item.poster || (item.poster_path ? `https://image.tmdb.org/t/p/w500${item.poster_path}` : null)
const backdrop = item.backdrop || (item.backdrop_path ? `https://image.tmdb.org/t/p/original${item.backdrop_path}` : null)

// Hero (similar pattern for backdrop)
const backdrop = item.backdrop || (item.backdrop_path ? `https://image.tmdb.org/t/p/original${item.backdrop_path}` : null)
```

**Alternative (preferred for new code):** Normalize at the API boundary. Pick one shape (recommend raw-path + base URL constant in the consumer) and serialize everything through the same backend transformer.

**`<img>` defensive onError** (always include — some TMDB image URLs return 404 over time):
```jsx
<img src={poster} alt={title} loading="lazy"
  onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }} />
<div className="card-placeholder" style={{display: poster ? 'none' : 'flex'}}>
  <Film size={32} />
  <small>{title}</small>
</div>
```

## Featured/Pinned Content Pattern (Gold Border + Badge)

**User request (2026-06-13)**: "nanti kamu sematkan di atas" — pin a specific item to the top of a list with visual emphasis (used for World Cup streaming beIN SPORTS XTRA at top of Live TV).

**Recipe** (works for any list: Live TV channels, Movies row, etc.):
1. Add `featured: true` flag to the item
2. MovieRow component accepts `highlight="latest"` prop → adds `section-latest` CSS class
3. Channel card accepts conditional `channel-card-featured` class
4. CSS: gold gradient border + glow pulse animation

**CSS** (`.section-latest` + `.channel-card-featured`):
```css
.section-latest {
  background: linear-gradient(180deg, rgba(245,158,11,0.08) 0%, rgba(245,158,11,0.02) 100%);
  border-top: 2px solid rgba(245,158,11,0.4);
  border-bottom: 2px solid rgba(245,158,11,0.4);
  padding: 24px 0;
  margin: 20px 0;
  position: relative;
}
.section-latest::before {
  content: '🆕 AUTO-UPDATED DAILY';
  position: absolute; top: -10px; left: 4%;
  background: linear-gradient(135deg,#f59e0b,#ef4444);
  color: white; font-size: 10px; font-weight: 800; letter-spacing: 1px;
  padding: 3px 10px; border-radius: 12px;
  box-shadow: 0 2px 8px rgba(245,158,11,0.4);
}
.section-latest .section-title { color: #f59e0b; }

.channel-card-featured {
  background: linear-gradient(135deg, rgba(245,158,11,0.05) 0%, rgba(239,68,68,0.05) 100%);
  border: 2px solid rgba(245,158,11,0.5);
  box-shadow: 0 0 20px rgba(245,158,11,0.15);
  transform: scale(1.02);
}
.channel-card-featured:hover {
  border-color: rgba(245,158,11,0.8);
  box-shadow: 0 0 32px rgba(245,158,11,0.4);
  transform: scale(1.04);
}
.featured-badge {
  position: absolute; top: 10px; left: 10px;
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
  color: white; padding: 4px 10px; border-radius: 12px;
  font-size: 11px; font-weight: 800; letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(245,158,11,0.4);
  animation: featuredGlow 2.5s infinite;
}
@keyframes featuredGlow {
  0%, 100% { box-shadow: 0 2px 8px rgba(245,158,11,0.4); }
  50% { box-shadow: 0 4px 16px rgba(245,158,11,0.7); }
}
```

**JSX** (LiveTV example):
```jsx
const TV_CHANNELS = [
  { id: 0, name: '⚽ beIN SPORTS XTRA - World Cup 2026', logo: '...', stream: '/api/proxy?url=...', category: 'sports', featured: true },
  { id: 0.5, name: '⚽ TVRI Sport HD', logo: '...', stream: '/api/proxy?url=...', category: 'sports' },
  // ... rest
]

<div className={`channel-card ${channel.featured ? 'channel-card-featured' : ''}`}>
  ...
  {channel.featured && <span className="featured-badge">🔥 FEATURED</span>}
  ...
</div>
```

**Why gold + glow + scale**: Gold reads as "premium/special" in any culture, glow draws the eye without being aggressive, and `scale(1.02)` makes it slightly larger than peers without breaking grid alignment. The pulsing animation (`featuredGlow` 2.5s) is subtle but signals "look here first."

## Native Alphabet Sort (K-Drama, C-Drama Browsing)

**Solution**: Add language filter + native title sort to Movies page:

```jsx
const [lang, setLang] = useState('')  // TMDB original_language ISO code

useEffect(() => {
  const params = new URLSearchParams({ page, sort_by: sort })
  if (genre) params.set('with_genres', genre)
  if (lang) params.set('with_original_language', lang)  // ko, zh, ja, id, etc.
  fetch(`/api/discover/movie?${params}`)...
}, [genre, lang, sort, page])

<select value={lang} onChange={e=>{setLang(e.target.value);setPage(1)}}>
  <option value="">🌍 Semua Bahasa</option>
  <option value="ko">🇰🇷 Korea</option>
  <option value="zh">🇨🇳 China</option>
  <option value="ja">🇯🇵 Jepang</option>
  <option value="id">🇮🇩 Indonesia</option>
  <option value="hi">🇮🇳 India</option>
  <option value="th">🇹🇭 Thailand</option>
</select>

<select value={sort} onChange={...}>
  <option value="popularity.desc">🔥 Most Popular</option>
  <option value="original_title.asc">🔤 A–Z (Original Title)</option>  {/* Korean/Chinese alphabet */}
  <option value="original_title.desc">🔤 Z–A (Original Title)</option>
  <option value="title.asc">🔤 A–Z (English Title)</option>
  {/* ... */}
</select>
```

**Difference between `with_origin_country` vs `with_original_language`**:
- `with_origin_country=KR` — production country (Korean-produced films, includes US-Korea co-productions)
- `with_original_language=ko` — original language (films originally in Korean, even if produced elsewhere)
- For "K-Drama page" use `with_origin_country=KR` (typical user intent)
- For "All Korean-language films including foreign-produced" use `with_original_language=ko`

## MovieCard: Display English/Romanized Title (NOT native script)

**⚠️ USER CORRECTION (2026-06-13):** Initial version of this skill recommended showing `original_title` (native script like 鬼滅の刃/한글/中文) for non-English films. **User rejected this explicitly**: "Untuk Judul Film Maksudnya Bukan kayak gini bukan sesuai bahasa negaranya Tapi Judul film nya Kimatsu No Yaiba" — the user wants the romanized/English version of the title, not the native script. Sort A-Z by `original_title.asc` is FINE (it sorts by romanized form correctly when set to en-US), but the **displayed** title must be English/romanized.

**Problem**: TMDB's default `language` parameter (often `id-ID` for Indonesian sites) returns Indonesian-translated titles when available. For films WITHOUT an Indonesian translation, TMDB falls back to the **original script** (e.g., 鬼滅の刃 for Demon Slayer). User sees Japanese/Korean/Chinese characters they don't read.

**Solution**: 
1. Set TMDB `language=en-US` in the backend tmdb() wrapper (NOT `id-ID`). This returns English titles for everything that has a translation, with the romanized original (Kimetsu no Yaiba) embedded for anime/Asian films.
2. MovieCard displays `item.title` (English/romanized) as the main title.
3. Show `item.original_title` ONLY as a `title=` tooltip on hover (so users who want to see the native script can hover). Do NOT show it as visible subtitle.
4. Add country flag badge (🇰🇷🇨🇳🇯🇵) so user knows the film is non-English at a glance.

```jsx
// In MovieCard component
// Use English title (TMDB returns localized title when language=en-US requested).
const title = item.title || item.name || ''
const langFlag = {ko:'🇰🇷',zh:'🇨🇳',ja:'🇯🇵',id:'🇮🇩',en:'🇺🇸',hi:'🇮🇳',th:'🇹🇭',es:'🇪🇸',fr:'🇫🇷'}[item.original_language] || ''

// In JSX
<div className="card-title" title={item.original_title || title}>{title}</div>  {/* hover shows native script */}
{langFlag && <span className="card-lang-badge" title={`Original: ${item.original_language?.toUpperCase()}`}>{langFlag}</span>}
```

**Backend tmdb.js change**:
```javascript
// WRONG (causes native script fallback for films without ID translation):
url.searchParams.set('language', 'id-ID');

// RIGHT (returns English/romanized for all films with translation):
url.searchParams.set('language', 'en-US');
```

**Why this works**: For popular films, TMDB has English translations:
- Demon Slayer: Kimetsu no Yaiba Infinity Castle (not 劇場版「鬼滅の刃」無限城編)
- JUJUTSU KAISEN: Execution (not 劇場版 呪術廻戦...)
- Spirited Away (not 千と千尋の神隠し)
- Your Name. (not 君の名は。)

**Sort A-Z by `original_title.asc` still works correctly** because TMDB sorts by the original-language key — but the user sees the English title in the card while the sort uses the original-language sort key.

## TMDB API Patterns

```javascript
// Base fetch wrapper
const API_KEY = process.env.TMDB_API_KEY;
const BASE = 'https://api.themoviedb.org/3';

async function tmdb(path, params = {}) {
  const url = new URL(`${BASE}${path}`);
  url.searchParams.set('api_key', API_KEY);
  url.searchParams.set('language', 'id-ID'); // Indonesian locale
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`TMDB ${res.status}`);
  return res.json();
}
```

**Key endpoints:**
- `/trending/{type}/day` — trending content
- `/movie/{id}?append_to_response=videos,credits,similar,recommendations` — full movie details
- `/tv/{id}?append_to_response=videos,credits,similar,recommendations` — full TV details
- `/discover/movie?with_genres=X&with_origin_country=XX&sort_by=popularity.desc` — filtered discovery
- `/discover/tv?with_genres=X&with_origin_country=XX&sort_by=popularity.desc` — filtered TV discovery
- `/search/multi?query=X` — search across movies + TV
- `/genre/movie/list` and `/genre/tv/list` — genre lists

**Asia Content Discovery** (for K-Drama, C-Drama, Anime, Thai Drama pages):
```javascript
// K-Drama
/discover/tv?with_origin_country=KR&with_genres=18&sort_by=popularity.desc&page=1

// C-Drama
/discover/tv?with_origin_country=CN&with_genres=18&sort_by=popularity.desc&page=1

// Anime (Japan + Animation genre)
/discover/tv?with_origin_country=JP&with_genres=16&sort_by=popularity.desc&page=1

// Thai Drama
/discover/tv?with_origin_country=TH&with_genres=18&sort_by=popularity.desc&page=1

// Korean Movies
/discover/movie?with_origin_country=KR&sort_by=popularity.desc&page=1

// Japanese Movies
/discover/movie?with_origin_country=JP&sort_by=popularity.desc&page=1
```

**Country codes**: KR (Korea), CN (China), JP (Japan), TH (Thailand), US (USA), ID (Indonesia)
**Genre IDs**: 18 (Drama), 16 (Animation), 28 (Action), 35 (Comedy), 10749 (Romance)

**Image URLs:**
- Poster: `https://image.tmdb.org/t/p/w500{poster_path}`
- Backdrop: `https://image.tmdb.org/t/p/original{backdrop_path}`
- Cast: `https://image.tmdb.org/t/p/w200{profile_path}`

## Indonesian UI Conventions

User prefers Indonesian language for UI elements:
- Home → **Beranda**
- Movies → **Film**
- TV Series → **Serial TV**
- Drama Asia → **Drama Asia** (dedicated page for K-Drama, C-Drama, Anime, Thai, JP/KR movies) — use `<Globe2>` icon
- Trending → **Lagi Tren Sekarang**
- Search placeholder → "Cari film, serial TV..."
- Genre, Country (Negara), Year (Tahun)
- Login → **Masuk**
- Register → **Daftar**
- Watch Now → **Tonton Sekarang**
- Play button → **▶ Tonton Sekarang** (not just icon, include text)

## Navigation Pattern (IDLIX-Style)

Mobile sidebar with:
- Auth buttons (Masuk/Daftar) at top
- Menu items with **Lucide React SVG icons** (NOT text emojis — see Icons section below)
- Active state: red text + dark gray background + checkmark
- Genre tags as pills at bottom
- Full-screen overlay backdrop

Desktop: horizontal nav links in navbar

## Icons: Lucide React (NOT Text Emojis)

Use `lucide-react` SVG icons throughout. Text emojis (🔥🎬📺👑 etc.) render differently per platform and look unprofessional.

```bash
npm install lucide-react
```

**Icon mapping (common replacements):**
| Text Emoji | Lucide Icon | Usage |
|-----------|-------------|-------|
| 🔍 | `<Search size={18} />` | Search button |
| 👤 | `<User size={18} />` | Account/profile |
| 🌏 | `<Globe2 size={16} />` | Drama Asia nav |
| 📡 | `<Tv size={16} />` | Live TV nav |
| 👑 | `<Crown size={16} />` | VIP badge/nav |
| 🏠 | `<Home size={18} />` | Sidebar home |
| 🎬 | `<Film size={18} />` | Movies, player |
| 📺 | `<Tv size={18} />` | TV Series |
| 🔥 | `<Flame size={18} />` | Trending |
| 📅 | `<Calendar size={18} />` | Year filter |
| ⭐ | `<Star size={14} fill="#fbbf24" color="#fbbf24" />` | Rating (filled yellow) |
| ▶ | `<Play size={16} fill="white" />` | Play button |
| ℹ | `<Info size={16} />` | More info |
| 🎭 | `<Clapperboard size={18} />` | Cast/genre |
| 🚪 | `<LogIn size={16} />` / `<LogOut size={16} />` | Auth |
| 👤+ | `<UserPlus size={16} />` | Register |
| ✅/❌ | `<Check size={14} color="#4ade80" />` / `<X size={14} color="#666" />` | Feature lists |

**Usage pattern — inline with text:**
```jsx
<Link to="/live-tv"><Tv size={16} style={{marginRight:4,verticalAlign:'text-bottom'}} />Live TV</Link>
```

**Usage pattern — standalone button:**
```jsx
<button className="nav-icon-btn"><Search size={18} /></button>
```

**Usage pattern — page title:**
```jsx
<h1 className="grid-title"><Film size={28} color="#e50914" style={{marginRight:8,verticalAlign:'text-bottom'}} />Movies</h1>
```

**Exception:** Country flags (🇰🇷🇯🇵🇨🇳 etc.) are fine as text — Lucide has no flag icons.

## UI Style Preferences

- **Logo**: Clean text-based, NOT icon-heavy (user rejected play-button icon as "kepencet youtube")
- **Colors**: Dark (#0a0a0a bg), Red accent (#e50914), White text
- **Buttons**: Rounded (8px), shadow on primary, hover scale effect
- **Cards**: Dark background, subtle hover zoom, rating badge in yellow
- **Hero**: Auto-rotating, backdrop image, gradient overlay

## Premium UI Redesign — User Preferences (validated 2026-06-13)

**⚠️ Critical user corrections when doing premium redesigns.** When user says "buatin desain mirip X tapi lebih premium", do NOT default to maximum visual complexity. The user has 5 strong opinions learned from rejecting earlier attempts:

### 0. Scope: when user shows a reference image, update the WHOLE design — not 1-2 pages
**User frustration (2026-06-13):** *"gak ada perubahan mona😭 masih bagus ini banget 😭😭🫠 Lu cuma tambah fitur di vip dan warna ICLIX 😭"* — after updating only the VIP page and logo, the rest of the app was unchanged, so the user felt nothing had changed.

**Lesson:** When user shares a reference design image and asks to "perbarui seperti ini" / "update like this", they expect **every major page** to be updated to match the reference — Home, Detail (Movie/TV/Anime), Profile, Downloads, etc. NOT just the most visible one (VIP) + logo.

**Pre-flight checklist before declaring a redesign done:**
1. Identify all major pages in the app (Home, [Movie/TV/Anime]Detail, Profile, Downloads, VIP, etc.)
2. For each page, check which sections from the reference are present
3. If a page is missing 1+ reference sections, add them
4. Verify the deployed site actually shows the changes (don't claim "done" before checking with `vision_analyze` on the live URL)

**Workflow rule:** Build preview → screenshot → user approves → update ALL pages that need it → build → deploy → verify each page. NOT build preview → user approves → update only one page → declare done.

### 1. Logo: minimalist + slightly thicker, NOT crazy 3D
**REJECTED approach** (5-layer text-shadow + perspective rotateX + multi-stop gradient + drop-shadow filter) — user: *"Tulisan ICLIX nya jelek banget😭"*

**CORRECT approach v3 (validated 2026-06-13, user approved):** text-based logo with PURE red base + thick dark-red stroke + offset dark-red shadow layer for 3D depth + top highlight. "BY HEXA" preserved below as bold PURE WHITE.

**Critical color rules (user explicit):** ICLIX = MERAH banget (very red, #e50914 solid), BY HEXA = PUTIH banget (very white, #ffffff solid). NOT gradient ICLIX, NOT gray BY HEXA.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 65" fill="none">
  <defs>
    <linearGradient id="redShine" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.4"/>
      <stop offset="40%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <!-- ICLIX: deep red base + thick dark stroke for outline thickness -->
  <text x="2" y="42" font-family="'Arial Black', 'Helvetica Neue', sans-serif"
        font-weight="900" font-size="46" letter-spacing="3"
        fill="#e50914" stroke="#5a0003" stroke-width="2.2"
        stroke-linejoin="round" paint-order="stroke fill">ICLIX</text>
  <!-- 3D depth: offset shadow layer (down-right) -->
  <text x="3" y="43" font-family="'Arial Black', 'Helvetica Neue', sans-serif"
        font-weight="900" font-size="46" letter-spacing="3"
        fill="#5a0003" opacity="0.5">ICLIX</text>
  <text x="2" y="42" font-family="'Arial Black', 'Helvetica Neue', sans-serif"
        font-weight="900" font-size="46" letter-spacing="3"
        fill="#e50914" stroke="#5a0003" stroke-width="2.2"
        stroke-linejoin="round" paint-order="stroke fill">ICLIX</text>
  <!-- top highlight for glossy 3D feel -->
  <text x="2" y="42" font-family="'Arial Black', 'Helvetica Neue', sans-serif"
        font-weight="900" font-size="46" letter-spacing="3"
        fill="url(#redShine)">ICLIX</text>
  <!-- BY HEXA: pure white, bold -->
  <text x="3" y="58" font-family="'Arial', sans-serif"
        font-weight="700" font-size="11" letter-spacing="5"
        fill="#ffffff">BY HEXA</text>
</svg>
```

**3D technique stack** (combine for the "slightly thicker + 3D" look):
- `stroke="#5a0003"` (very dark red, almost black) at `stroke-width="2.2"` — adds visible thickness without breaking letter shapes
- `paint-order="stroke fill"` — stroke renders BEHIND fill, so the outline shows around the letter edges
- Second `<text>` at `x+1, y+1` with `fill="#5a0003" opacity="0.5"` — offset shadow layer creates true depth perception
- Top highlight via `url(#redShine)` (white-to-transparent vertical gradient) — subtle gloss effect

**v2 recipe (NOT v3) had a gradient red ICLIX** — user wanted solid red. v3 uses solid `#e50914`.

### 2. Pure `#000000` black everywhere — never `#0a0a0a`
**User**: *"untuk warna hitam jangan nanggung" 100% hitam banget ya*

**Pitfall**: When user says "black", they mean `#000000`. Default dark mode `#0a0a0a` / `#111` / `#1a1a1a` (used as page backgrounds) all read as "not committed to black". Audit ALL of these in your CSS:
- `body` background
- `:root` `--bg` variable
- `.page-wrap`, `.showcase-header`, container backgrounds
- Section backgrounds that aren't intentionally tinted
- Footer / loading-screen backgrounds

```css
/* WRONG (too gray) */
:root { --bg: #0a0a0a; }
body { background: var(--bg); }

/* RIGHT (committed to black) */
:root { --bg: #000; }
body { background: #000; }
```

The user will check with `vision_analyze` or just by looking — even a slightly gray background reads as "not black enough". Use `#000` literally, not `var(--bg)` if there's any chance it could resolve to a non-zero value. Surface/card backgrounds (`#0a0a0a`, `#181818`) are still fine — only the PAGE/MAIN backgrounds need to be pure `#000`.

### 3. Feature cards: horizontal "di samping" layout, NOT vertical icon-on-top
**User**: *"untuk tombol fitur bagus di samping kayak sekarang"*

**REJECTED**: vertical card with icon on top, title centered, description centered below (typical icon-card grid).

**CORRECT** (validated on ICLIX VIP page, user approved): horizontal card with icon container on the LEFT, title+description stacked on the RIGHT. Looks like a settings-list row, not a feature-grid cell.

```css
/* WRONG (rejected by user) */
.perk-card { text-align: center; }
.perk-icon { display: block; margin: 0 auto 12px; font-size: 40px; }

/* RIGHT (validated) */
.perk-card {
  display: flex; align-items: flex-start; gap: 16px;
  text-align: left; padding: 20px;
  background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 14px;
  position: relative; overflow: hidden;
}
.perk-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(135deg,#ff2a3a,#e50914,#a00610);
  opacity: 0.6; transition: opacity 0.3s;
}
.perk-card:hover { border-color: rgba(229,9,20,0.4); transform: translateY(-2px); }
.perk-icon {
  width: 48px; height: 48px; border-radius: 12px; flex-shrink: 0;
  background: linear-gradient(135deg,#ff2a3a,#e50914,#a00610);
  display: flex; align-items: center; justify-content: center;
  color: #fff; box-shadow: 0 4px 16px rgba(229,9,20,0.18);
}
.perk-body { flex: 1; min-width: 0; padding-top: 2px; }
.perk-card h3 { font-size: 15px; margin-bottom: 5px; font-weight: 800; }
.perk-card p { font-size: 12px; color: #999; line-height: 1.5; }
```

```jsx
{/* React JSX pattern */}
<div className="perk-card">
  <div className="perk-icon">{iconComponent}</div>
  <div className="perk-body">
    <h3>{title}</h3>
    <p>{desc}</p>
  </div>
</div>
```

### 4. Feature preservation: APPEND, never REPLACE
**User**: *"fitur sekarang jangan di hapus cukup di tambah yang belum ada aja"*

When adding features (e.g., growing from 6 perks to 12 perks), keep the original 6 in their slot and add the new 6 alongside. Never remove, even if a feature is duplicated or feels redundant. The user will check that all 12 (or however many existed + however many new) are present after the update. The grid will resize itself; do not consolidate.

**Pre-flight checklist before any feature work**:
1. List current features in the component
2. List new features user wants added
3. Confirm set is union (current ∪ new), not just (new) — and never (current − X + new)

## ICLIX-Specific Deploy Workflow (Vite + Express + PM2 + CF Tunnel)

ICLIX backend (`backend/server.js`) serves the built frontend directly:
```javascript
app.use(express.static(path.join(__dirname, '../frontend/dist')));
```

So the deploy cycle is just rebuild + restart, no need to copy files anywhere:

```bash
# 1. Rebuild frontend (Vite outputs to frontend/dist/)
cd /home/ubuntu/iclix/frontend && npm run build

# 2. Restart backend PM2 process — it picks up the new dist/ via express.static
pm2 restart iclix-api

# 3. Verify (no need to restart tunnel — it just proxies the backend)
curl -s -o /dev/null -w "API: %{http_code}\n" https://<tunnel-url>/api/health
curl -s -o /dev/null -w "Frontend: %{http_code}\n" https://<tunnel-url>/
curl -s -o /dev/null -w "Logo: %{http_code} (%{size_download} bytes)\n" https://<tunnel-url>/logo.svg
```

**Vite auto-copies `public/*` → `dist/*` on build.** Just drop a new `public/logo.svg` and `npm run build` — it's served at `/logo.svg` immediately after the backend restart picks up the new dist.

**Common sequence bug**: User says "gas update di web" → you edit `src/` files and forget `npm run build` → backend still serves OLD `dist/`. The new code never reaches the user. Always run `build` BEFORE `pm2 restart` — the restart only takes effect on the new files.

**File size check confirms the new build landed**: `curl -s https://<url>/logo.svg | wc -c` should return the byte count of the NEW file, not the old. If it matches the old, you didn't rebuild.

## Backend API Routes (Complete)

The frontend calls many TMDB endpoints. The backend MUST proxy ALL of them. **Common bug: frontend loads but shows no content because API routes return 404/HTML (catch-all SPA route).**

**Complete route list for Express backend:**

```javascript
// Trending
app.get('/api/trending/:type/:period', ...) // /trending/all/day, /trending/movie/day
app.get('/api/trending', ...)               // fallback to /trending/all/day

// Movies
app.get('/api/movie/popular', ...)
app.get('/api/movie/top_rated', ...)
app.get('/api/movie/upcoming', ...)
app.get('/api/movie/:id', ...)              // append_to_response=credits,videos,similar,recommendations

// TV
app.get('/api/tv/popular', ...)
app.get('/api/tv/top_rated', ...)
app.get('/api/tv/:id', ...)                 // append_to_response=credits,videos,similar,recommendations

// Genres
app.get('/api/genre/movie/list', ...)
app.get('/api/genre/tv/list', ...)

// Discover (with query params: with_genres, with_origin_country, sort_by, page, year)
app.get('/api/discover/movie', ...)
app.get('/api/discover/tv', ...)

// Search (query param: q)
app.get('/api/search', ...)                 // maps to /search/multi

// Live TV proxy
app.get('/api/proxy', ...)                  // see references/hls-proxy-implementation.md

// SPA catch-all (MUST BE LAST)
app.get('*', ...)
```

**All routes use the same tmdb() wrapper:**
```javascript
const data = await tmdb('/movie/popular', { page: req.query.page || 1 });
res.json(data);
```

**For routes with append_to_response:**
```javascript
const data = await tmdb(`/movie/${req.params.id}`, { 
  append_to_response: 'credits,videos,similar,recommendations' 
});
```

**For discover routes, pass req.query directly:**
```javascript
const data = await tmdb('/discover/movie', req.query);
```

**Verification — test all routes after build:**
```bash
for ep in /api/trending/all/day /api/movie/popular /api/tv/popular /api/genre/movie/list "/api/discover/movie?with_origin_country=KR" "/api/search?q=avengers"; do
  result=$(curl -s "http://localhost:3000$ep" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('results',d.get('genres',[]))))")
  echo "$ep: $result items"
done
```

## Footer Patterns

**Use React Router `<Link>` for internal navigation** — NOT `<a href="/path">` which causes full page reload and loses all React state:

```jsx
import { Link } from 'react-router-dom'

// ✅ Correct
<li><Link to="/movies">Film</Link></li>

// ❌ Wrong — causes full page reload
<li><a href="/movies">Film</a></li>
```

**External links (Telegram, email, TMDB) keep `<a href>` with target="_blank".**

**"Coming Soon" pattern for unready features:**
```jsx
<span className="download-btn" style={{opacity:0.5,pointerEvents:'none',position:'relative'}}>
  {/* button content */}
  <span style={{position:'absolute',top:-8,right:-8,background:'#e50914',color:'#fff',
    fontSize:9,padding:'2px 6px',borderRadius:4,fontWeight:700}}>SOON</span>
</span>
```

## Project Structure

```
project/
├── backend/
│   ├── server.js          # Express server, API routes, static serving
│   ├── services/tmdb.js   # TMDB API wrapper
│   └── .env               # TMDB_API_KEY
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Router setup
│   │   ├── components/    # Navbar, Footer, Hero, MovieRow, MovieCard
│   │   ├── pages/         # Home, Movies, TVSeries, MovieDetail, TVDetail, etc.
│   │   └── index.css      # All styles (no Tailwind)
│   ├── index.html
│   └── vite.config.js
└── package.json
```

## Deployment

```bash
# Build frontend
cd frontend && npx vite build

# Start/restart with PM2
pm2 start backend/server.js --name app-name --interpreter node
pm2 restart app-name

# Cloudflare Tunnel (instant public URL)
cloudflared tunnel --url http://localhost:3000
```

## Drama Asia Feature

Dedicated page with 6 tabs for Asian content discovery:
- **🇰🇷 K-Drama** — Korean dramas (origin=KR, genre=18)
- **🇨🇳 C-Drama** — Chinese dramas (origin=CN, genre=18)
- **🇯🇵 Anime** — Japanese animation (origin=JP, genre=16)
- **🇹🇭 Thai Drama** — Thai dramas (origin=TH, genre=18)
- **🇯🇵 Film Jepang** — Japanese movies (origin=JP, type=movie)
- **🇰🇷 Film Korea** — Korean movies (origin=KR, type=movie)

**Implementation pattern:**
```jsx
const ASIA_TABS = [
  { id: 'kdrama', label: '🇰🇷 K-Drama', genreId: 18, country: 'KR', type: 'tv' },
  { id: 'cdrama', label: '🇨🇳 C-Drama', genreId: 18, country: 'CN', type: 'tv' },
  { id: 'anime', label: '🇯🇵 Anime', genreId: 16, country: 'JP', type: 'tv' },
  { id: 'thai', label: '🇹🇭 Thai Drama', genreId: 18, country: 'TH', type: 'tv' },
  { id: 'jmovie', label: '🇯🇵 Film Jepang', genreId: '', country: 'JP', type: 'movie' },
  { id: 'kmovie', label: '🇰🇷 Film Korea', genreId: '', country: 'KR', type: 'movie' },
]
```

Add prominent navigation link: **🌏 Drama Asia** in navbar and sidebar.

## Live TV Feature

Add Live TV page with free M3U8 streams for Indonesian + international channels. Use HTML5 `<video>` element.

**Channel categories:**
- 🇮🇩 TV Lokal (Trans7, TransTV, MetroTV, tvOne, BeritaSatu, BTV, GarudaTV, MBG TV, Indonesiana, Bandung TV, Banten TV, BRTV, Caruban TV, Padang TV, Batam TV, Biznet channels)
- 📰 Berita (DW News, TRT World)
- ⚽ Olahraga (Red Bull TV)

**Implementation:**\n```jsx\n// Channel data — all streams MUST go through proxy\nconst TV_CHANNELS = [\n  { id: 1, name: 'Trans7', logo: '...', stream: '/api/proxy?url=' + encodeURIComponent('https://video.detik.com/trans7/smil:trans7.smil/index.m3u8'), category: 'hiburan' },\n  { id: 2, name: 'Trans TV', logo: '...', stream: '/api/proxy?url=' + encodeURIComponent('https://video.detik.com/transtv/smil:transtv.smil/index.m3u8'), category: 'hiburan' },\n  // ... see references/hls-proxy-implementation.md for full list\n]\n\n// Player: HLS.js in modal popup (NOT simple <video src> — CORS will block!)\n// See references/hls-proxy-implementation.md for complete component code\n```\n\n**M3U8 sources:** Search GitHub for `iptv m3u indonesia`, `free iptv streams`. Best source: `https://iptv-org.github.io/iptv/countries/id.m3u` for Indonesia specifically, and `https://iptv-org.github.io/iptv/index.m3u` (2.4MB, ~24k lines, 100k+ channels) for the **full global catalog**. See `references/iptv-m3u8-tested-2026-06.md` for Indonesian content-validated test results, and the section below for global catalog scan + sports discovery.

**World Cup / Sports discovery method (verified 2026-06-13 for piala dunia 2026):**
1. Download the FULL iptv-org catalog: `curl -sS -o /tmp/iptv.m3u https://iptv-org.github.io/iptv/index.m3u` (~65ms, 2.4MB)
2. Grep for keywords: `fifa`, `world cup`, `piala dunia`, `beIN`, `Fox Sport`, `ESPN`, `RCTI`, `SCTV`, `TVRI Sport`, `SPOTV` — extract name+URL pairs
3. Validate each URL with the validation script above (HTTP 200 + content contains `#EXTM3U`/`#EXT-X`)
4. **For Asian sports rights specifically**, prioritize: beIN Sports (free worldwide, official World Cup 2026 broadcaster for US), SPOTV (Korean sports network), TVRI Sport (Indonesian free-to-air)
5. Pick the one with most `m3u8` variants (multi-bitrate = smooth adaptive playback) + free + official

**Working free streams verified for piala dunia 2026**:
| Channel | Resolution | URL |
|---|---|---|
| **beIN SPORTS XTRA** (EN) | 1080p, 7 variants | `https://bein-xtra-bein.amagi.tv/playlist.m3u8` |
| beIN Sports XTRA en Español | 1080p, 4 variants | `https://dc1644a9jazgj.cloudfront.net/beIN_Sports_Xtra_Espanol.m3u8` |
| SPOTV Indonesia | 720p | `http://primestreams.tv:826/live/mookie22/49aV7nBsK4/119515.m3u8` |
| SPOTV 2 Indonesia | 1080p | `http://primestreams.tv:826/live/mookie22/49aV7nBsK4/119516.m3u8` |
| TVRI Sport HD (free-to-air ID) | 720p, 5 variants | `https://ott-balancer.tvri.go.id/live/eds/SportHD/hls/SportHD.m3u8` |
| Fox Sports 1 US | 1280p | `http://cdn12.henico.net:8080/live/gsctv/index.m3u8` (geo-blocked outside US) |

**Caveat**: `primestreams.tv` and `cdn12.henico.net` are third-party grabbers that can die without notice. beIN SPORTS XTRA (Amagi CDN) is the most reliable for World Cup 2026 — it's an **official** free stream, not a re-stream.

**Discovery strategy**: Always do a full scan of the iptv-org catalog before targeted tests. You'll find hidden gems (Trans7/TransTV via detik.com CDN, GarudaTV, MBG TV, Padang TV, Batam TV) that weren't in your initial shortlist. Don't test one-by-one — grep keywords first, batch test all candidates.

**⚠️ CRITICAL FINDINGS:**
- **Trans7 and TransTV work** via `video.detik.com` CDN — these are major commercial channels! Always include these first.
- **detik.com CDN is a gold mine** — check for other detik-owned properties.
- **RCTI, SCTV, Indosiar** etc. require DRM/auth/geo-blocking — NOT embeddable. Don't waste time.
- **Always validate M3U8 response body** contains `#EXTM3U` or `#EXT-X` — HTTP 200 alone is not sufficient.
- Sources change frequently — build "Report broken stream" button → Telegram contact.

**HLS.js for browsers without native HLS:**\n```bash\nnpm install hls.js\n```\n\n### HLS Proxy — CRITICAL for Live TV to Actually Work\n\nM3U8 streams from Indonesian CDNs (detik.com, medcom.id, biznetvideo.net, etc.) have **CORS headers that block browser-side playback**. You MUST proxy all HLS requests through the backend. But naive proxying breaks because HLS manifests contain **relative URLs** for variant playlists and .ts segments.\n\n**The problem:**\n1. Backend proxies the master manifest → browser gets it via `/api/proxy?url=...`\n2. HLS.js parses the manifest, finds relative URLs like `chunklist_w123_b744100_sleng.m3u8`\n3. HLS.js resolves them relative to the *page URL* (not the original stream URL) → requests go to wrong path\n4. Video never loads, no error visible in console\n\n**The fix — manifest URL rewriting in the proxy:**\n\n```javascript\n// Backend proxy route — MUST rewrite URLs in manifest responses\napp.get('/api/proxy', async (req, res) => {\n  const url = req.query.url;\n  if (!url) return res.status(400).json({ error: 'Missing url param' });\n  \n  const protocol = url.startsWith('https') ? https : http;\n  const parsedUrl = new URL(url);\n  const domain = parsedUrl.hostname;\n  const baseUrl = url.substring(0, url.lastIndexOf('/') + 1);\n  \n  const options = {\n    headers: {\n      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',\n      'Referer': `https://${domain}/`,\n      'Origin': `https://${domain}`\n    },\n    timeout: 10000,\n  };\n  \n  const request = protocol.get(url, options, (stream) => {\n    const contentType = stream.headers['content-type'] || '';\n    const isManifest = contentType.includes('mpegurl') || \n                       contentType.includes('m3u8') || \n                       url.endsWith('.m3u8');\n    \n    if (isManifest) {\n      // Read manifest, rewrite relative URLs to absolute proxied URLs\n      let body = '';\n      stream.on('data', chunk => body += chunk.toString());\n      stream.on('end', () => {\n        const rewritten = body.split('\\n').map(line => {\n          const trimmed = line.trim();\n          if (!trimmed || trimmed.startsWith('#')) return line; // Tags pass through\n          \n          // It's a URL — resolve to absolute, then proxy it\n          let absoluteUrl;\n          if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {\n            absoluteUrl = trimmed;\n          } else {\n            absoluteUrl = baseUrl + trimmed; // Relative → absolute\n          }\n          return `/api/proxy?url=${encodeURIComponent(absoluteUrl)}`;\n        }).join('\\n');\n        \n        res.setHeader('Content-Type', 'application/vnd.apple.mpegurl');\n        res.setHeader('Access-Control-Allow-Origin', '*');\n        res.setHeader('Cache-Control', 'no-cache');\n        res.send(rewritten);\n      });\n    } else {\n      // Not a manifest — pipe through directly (.ts segments, etc.)\n      res.setHeader('Content-Type', contentType || 'video/mp2t');\n      res.setHeader('Access-Control-Allow-Origin', '*');\n      res.setHeader('Cache-Control', 'public, max-age=5');\n      stream.pipe(res);\n    }\n  });\n  \n  request.on('error', (e) => res.status(500).json({ error: e.message }));\n  request.on('timeout', () => { request.destroy(); res.status(504).json({ error: 'Timeout' }); });\n});\n```\n\n**Why this works:**\n1. Master manifest gets rewritten: `chunklist_w123.m3u8` → `/api/proxy?url=https%3A%2F%2Fexample.com%2Fchunklist_w123.m3u8`\n2. HLS.js requests the chunklist through the proxy\n3. Chunklist ALSO gets rewritten: `segment_001.ts` → `/api/proxy?url=https%3A%2F%2Fexample.com%2Fsegment_001.ts`\n4. Segment requests go through proxy → gets actual video data\n5. All 3 levels (master → variant → segments) flow through the same proxy endpoint\n\n**Frontend HLS.js setup (no special config needed):**\n```jsx\nconst hls = new Hls({\n  enableWorker: true,\n  lowLatencyMode: true,\n  backBufferLength: 90,\n  maxBufferLength: 30,\n});\nhls.loadSource('/api/proxy?url=' + encodeURIComponent(streamUrl));\nhls.attachMedia(video);\n```\n\n**Always add loading/error states:**\n- Show spinner while HLS manifest loads\n- Show error message if stream fails (with \"try another channel\" hint)\n- Add `FRAG_LOADED` event listener to clear loading state\n- Network errors: retry with `hls.startLoad()` after 2s delay\n- Media errors: recover with `hls.recoverMediaError()`\n\n**Testing the proxy end-to-end:**\n```bash\n# 1. Test manifest rewriting\ncurl -sL "http://localhost:3000/api/proxy?url=https%3A%2F%2Fvideo.detik.com%2Ftrans7%2Fsmil%3Atrans7.smil%2Findex.m3u8" | head -5\n# Should show: /api/proxy?url=... (rewritten URLs, NOT raw relative paths)\n\n# 2. Test chunklist (second level)\ncurl -sL "http://localhost:3000/api/proxy?url=<chunklist_url_from_step_1>" | head -5\n# Should show: /api/proxy?url=... (rewritten .ts segment URLs)\n\n# 3. Test in browser with HLS.js — click channel, verify video plays\n# 4. Check browser console for CORS or network errors\n```\n\n**Navbar link:** `Live TV` (with `<Tv>` Lucide icon) in desktop nav + sidebar menu.

## Premium Footer Pattern

4-column responsive footer with gradient effects, contact cards, and download buttons:

```
[Brand + Language] [Navigation] [Contact + Download] [Legal/TMDB]
```

**Features:**
- Contact cards: Telegram (link) + Email (mailto) with SVG icons, hover glow effects
- Download buttons: Google Play + App Store (placeholder)
- Language selector: 🇮🇩/🇺🇸 toggle (localStorage)
- TMDB attribution: Required by API terms
- Bottom bar: disclaimer + copyright with heartbeat ♥ animation (use HTML entity, not emoji)
- Responsive: 4 cols → 2 cols → 1 col
- Gradient background (dark → subtle red), glow animation on top

## Legal/Info Pages Bundle (Tentang Kami, S&K, Privasi, FAQ)

**When:** User wants to add About / Terms / Privacy / FAQ pages — common for any streaming platform that wants to feel legit and provide contact/support info. Routes typically: `/about`, `/terms`, `/privacy`, `/faq`. Footer links to all four.

**Validated copy-paste-ready structure** (Indonesian streaming platform context, ICLIX June 2026). Each page follows the same skeleton — info-hero + info-section with info-blocks:

```jsx
// Page wrapper (used by all 4 pages)
<div className="info-page">
  <div className="info-hero">
    <div className="info-hero-bg" />
    <div className="info-hero-content">
      <div className="info-hero-icon"><Info size={36} color="#e50914" /></div>
      <h1>Tentang <span className="info-highlight">ICLIX</span></h1>
      <p>Platform streaming lokal...</p>
    </div>
  </div>
  <div className="info-section">
    <div className="info-meta">Terakhir diperbarui: 14 Juni 2026</div>
    <div className="info-block">
      <h2>1. Section Title</h2>
      <p>Body text...</p>
      <ul className="info-list">
        <li><CheckCircle size={16} color="#22c55e" /> <span>List item with green check</span></li>
      </ul>
    </div>
  </div>
</div>
```

**FAQ pattern** — accordion with 5 categories, all collapsible. State: `const [openIdx, setOpenIdx] = useState(null)`. Click toggles, only one open at a time. Add `data` array of `{category, items: [{q, a}]}` and map.

**CSS class names** (drop into `index.css`, mobile-responsive included):
```css
.info-page { padding-top:68px; min-height:100vh; background:#000; }
.info-hero { position:relative; padding:80px 4% 60px; text-align:center; overflow:hidden;
  background:linear-gradient(135deg,#0a0a0a 0%,#1a0500 50%,#0a0a0a 100%); }
.info-hero-bg { position:absolute; inset:0; background:radial-gradient(ellipse at center,rgba(229,9,20,.15) 0%,transparent 70%); }
.info-hero-content { position:relative; z-index:2; }
.info-hero-icon { display:inline-flex; align-items:center; justify-content:center;
  width:64px; height:64px; border-radius:50%; background:rgba(229,9,20,.12);
  border:1px solid rgba(229,9,20,.3); margin-bottom:20px; }
.info-hero h1 { font-size:44px; font-weight:800; margin-bottom:14px; letter-spacing:-1.5px; }
.info-highlight { background:linear-gradient(135deg,#f5c518,#e50914);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.info-section { max-width:820px; margin:0 auto; padding:50px 4% 80px; }
.info-meta { text-align:center; color:#666; font-size:13px; margin-bottom:30px;
  padding:8px 16px; background:rgba(229,9,20,.06); border:1px solid rgba(229,9,20,.15);
  border-radius:8px; }
.info-block { background:#0a0a0a; border:1px solid #1a1a1a; border-radius:16px;
  padding:32px; margin-bottom:20px; }
.info-block h2 { font-size:22px; font-weight:800; color:#fff; margin-bottom:14px;
  display:flex; align-items:center; }
.info-block p { color:#b8b8b8; line-height:1.7; font-size:15px; margin-bottom:12px; }
.info-list { list-style:none; padding:0; margin:14px 0 0; display:flex; flex-direction:column; gap:12px; }
.info-list li { display:flex; align-items:flex-start; gap:10px; color:#b8b8b8; line-height:1.6; }
.faq-item-page { background:#000; border:1px solid #1a1a1a; border-radius:12px;
  margin-bottom:10px; overflow:hidden; }
.faq-item-page.open { border-color:#e50914; }
.faq-q { width:100%; display:flex; align-items:center; justify-content:space-between;
  padding:16px 20px; background:transparent; border:none; color:#fff; font-size:15px;
  font-weight:600; text-align:left; cursor:pointer; }
.faq-chev { transition:transform .25s; }
.faq-item-page.open .faq-chev { transform:rotate(180deg); color:#e50914; }
.faq-a { padding:0 20px 18px; color:#b8b8b8; line-height:1.7; font-size:14px;
  border-top:1px solid #1a1a1a; padding-top:14px; }
/* Mobile */
@media (max-width: 640px) {
  .info-hero h1 { font-size:32px; }
  .info-block { padding:22px; }
}
```

**Indonesian content templates** — write in casual Indonesian, use Lucide icons (Info, FileText, Shield, HelpCircle, Check, X). Keep paragraphs under 4 lines, use bullet lists for skimmability. FAQ categories for streaming: Umum, Nonton & Streaming, Akun & VIP, Download & Device, Konten & Request.

**Routes** (App.jsx):
```jsx
<Route path="/about" element={<About />} />
<Route path="/terms" element={<Terms />} />
<Route path="/privacy" element={<Privacy />} />
<Route path="/faq" element={<FAQ />} />
```

**Footer link pattern** (use React Router `<Link>`, not `<a href>`):
```jsx
<Link to="/about" className="legal-item">
  <div className="legal-icon-wrap"><Info size={16} /></div>
  <span className="legal-label">Tentang Kami</span>
  <span className="contact-arrow">›</span>
</Link>
```

**Why this set:** Required by Indonesian UU ITE (transparency about data collection, content rights, terms of use), provides legitimate contact info, reduces trust issues with users, and gives SEO content. User accepted a 4-page bundle shipped in one rebuild.

## Pitfalls

1. **Don't use Tailwind** — user's previous setup had PostCSS config issues. Plain CSS is simpler and works.
2. **Don't use placeholder logos** — user is very particular about branding. Text-based logo is safest.
3. **Always test video embed** — curl the embed URL to verify it returns 200 before showing to user.
4. **Mobile Safari iframe issues** — always provide "Open in New Tab" fallback.
5. **TMDB images may fail** — add dark gradient background to card images as fallback.
6. **Vite build may hang** — run with `background=true` and `notify_on_complete=true`.
7. **PM2 env loading** — use `--update-env` flag when restarting after .env changes.
8. **Player not showing after episode click** — verify `showPlayer` state is being set to `true` in onClick handler. For TV series, clicking an episode card should: `setEpisode(ep); setShowPlayer(true);`
9. **Black iframe on load** — this is normal, embed sources take 2-5 seconds to load video. Don't panic and rebuild — wait for the embed to fully load.
10. **Multi-server strategy is mandatory** — user expects "gaboleh menyerah kita punya banyak cara buat bypass" (never give up, we have many ways to bypass). Always provide 5-7 fallback servers so if one fails, user can switch immediately.
11. **Cloudflare Tunnel caching** — After rebuild + restart, the CF tunnel URL still serves OLD cached content. Even new browser won't help. **Fix:** Kill old tunnel process, start new one (generates new URL). If user says "still looks the same" after rebuild → restart tunnel immediately, don't ask them to hard refresh.
12. **Don't over-explain** — this user gets frustrated with long explanations, disclaimers, or asking for confirmation. Just execute and report results. "gas" = do it now. **Exception:** When user says "jelaskan dulu jangan di kerjain" (explain first, don't execute), they want to see the plan/options BEFORE implementation. Present choices clearly, wait for their pick, then execute.
13. **Live TV M3U8 streams are fragile** — they go down without notice. Always provide "Report broken stream" button linking to Telegram contact. Don't promise 100% uptime.
14. **M3U8 stream validation — HTTP 200 is NOT enough.** A stream returning HTTP 200 might contain an HTML error page, binary garbage, or DRM-protected content that won't play in `<video>`. **Always validate the response body contains actual HLS headers:**
    ```bash
    response=$(curl -s -L --max-time 8 "$url" | head -5)
    if echo "$response" | grep -q "#EXTM3U\|#EXT-X"; then
      echo "VALID HLS"
    else
      echo "INVALID - response: $(echo $response | head -c 100)"
    fi
    ```
    User frustration signal: claiming "all streams work" based on HTTP status alone, then user reports none play. **Validate content before reporting results.**
15. **User workflow preference: TEST BEFORE CLAIMING DONE.** When user says "tes dulu sebelum bilang done" or "belum bisa semua" — they mean you must exercise/validate every deliverable end-to-end before reporting success. This applies to streams, API endpoints, page rendering, everything. Don't just build and assume it works.
16. **User preference: Explain first for complex decisions.** When user says "jelaskan dulu jangan di kerjain" (explain first, don't execute), present the options/plan BEFORE implementing. This is especially important for features with multiple approaches (e.g., Live TV sources, bypass methods). Show what's possible, let them choose, then execute.
17. **User frustration: "agent teman gua udah banyak yang bisa bypass apapun"** — This means the user compares your capabilities to other agents that can bypass anything. When you say "this can't be done," the user sees it as a skill deficiency, not a technical limitation. NEVER say "can't be done" or give up. Instead: try every possible approach (different URLs, headers, referrers, CDNs), exhaust all options from iptv-org list, then report what worked vs. what didn't. The user wants to see you TRY HARD, not give up early.
18. **IPTV discovery strategy: don't test one by one, scan the whole list.** Fetch the full iptv-org M3U file, extract ALL URLs, then batch test them. You'll find hidden gems (Trans7 via detik.com CDN, GarudaTV, MBG TV, Indonesiana, Padang TV, Batam TV) that weren't in your initial list. Always do a full scan, not just targeted tests.\n19. **Naive HLS proxy DOES NOT WORK.** Simply piping the manifest through a backend proxy breaks HLS.js because manifests contain relative URLs (`chunklist_w123.m3u8`, `segment_001.ts`). HLS.js resolves these against the wrong base URL. You MUST rewrite manifest URLs to absolute proxied URLs. See `references/hls-proxy-implementation.md` for the complete working implementation. This is the #1 reason Live TV "loads but shows nothing" — the manifest arrives but segments can't be fetched.\n20. **Don't claim Live TV works until video actually renders in browser.** Test end-to-end: click channel → verify video plays with actual content (not black screen). Use `browser_vision()` to confirm the video frame shows real broadcast content (logos, commercials, live footage). curl testing the proxy is necessary but NOT sufficient — HLS.js rendering is the final gate.
21. **Frontend loads but shows no content = missing backend API routes.** If the page renders (navbar, footer visible) but no movie rows/hero appear, the backend is missing TMDB proxy routes. The frontend fetches from `/api/trending/all/day`, `/api/movie/popular`, etc. — if these aren't defined in Express, the catch-all SPA route returns HTML for them, and `response.json()` fails silently. **Always add ALL API routes before the catch-all.** Test each route with curl to verify it returns JSON, not HTML.
22. **Footer links must use React Router `<Link>`.** Using `<a href="/path">` in a SPA causes full page reload, losing all React state and re-fetching everything. The user may not notice but it's poor UX. Always use `<Link to="/path">` from react-router-dom for internal navigation.
23. **Install `lucide-react` before using it.** It's NOT included by default. Run `npm install lucide-react` in the frontend directory. Build will fail with "Rollup failed to resolve import" if missing.
24. **ES modules (`"type": "module"` in package.json) — NO `require()`.** When adding a new backend route that uses Node built-ins (`fs`, `child_process`, etc.) or any CommonJS-only library, use ES module syntax: `import fs from 'fs';` `import { exec } from 'child_process';`. The error `"require is not defined"` is the symptom — fix by adding proper imports at the top of `server.js`. **Do not** import them inline inside route handlers either; always hoist to module top.
25. **Cloudflared processes spawned by PM2 are owned by `root`, not the user running PM2.** When restoring tunnel infra (`pm2 start tunnel-ecosystem.config.js`), the `cloudflared` child processes inherit from PM2's launch context (root, since PM2 was started with sudo/systemd). Killing orphaned tunnels requires `sudo kill -9 <pid>`, plain `kill` returns "Operation not permitted". This is a real pitfall when debugging "PM2 says tunnel online but no URL" — the process may be a zombie that needs `sudo` to reap.
26. **For auto-discovery of new content, daily cron + state-dedupe is the right pattern.** TMDB doesn't push webhooks. The catalog updates multiple times per day but daily polling (or every 6h if sub-day freshness needed) is sufficient for "latest" UX. Always dedup against a `state.json` of seen IDs — without dedup the user gets TG notification spam on every cron tick. Use cumulative `latest.json` (only adds, never shrinks) for the frontend cache.
27. **Cloudflare Managed Challenge ≠ Turnstile widget — YesCaptcha has NO task for the former.** If you hit a Cloudflare gate on `login.kimchi.dev/cdn-cgi/challenge-platform/...` (URL pattern: `/cdn-cgi/challenge-platform/h/g/orchestrate/chl_page/`), this is a **Cloudflare Managed Challenge** — fully behavioral, runs JavaScript that observes mouse/touch/cookie/fingerprint/timing. It does NOT expose a `data-sitekey` in the DOM, so YesCaptcha's `TurnstileTask` cannot solve it (TurnstileTask requires a sitekey + proxy). YesCaptcha task types available (verified 2026-06-13): `TurnstileTask` (proxy-required, needs sitekey), `HCaptchaTask` (proxy-required, needs sitekey), `ImageToTextTask` (image OCR). NO `AntiCloudflareTask`, NO `CloudflareChallenge` task. Conclusion: Managed Challenge with YesCaptcha alone is a dead end. Real options: (1) user manually runs login on local browser, (2) CapSolver (has `AntiCloudflareTask` — different provider, costs $), (3) FlareSolverr real-browser service. Don't waste credits on `TurnstileTask` for Managed Challenge URLs.
28. **MovieCard / Hero must accept BOTH `poster` (full URL) and `poster_path` (raw TMDB path) shapes.** When adding a new API endpoint (like `/api/latest` from auto-discovery sync) that pre-builds full image URLs, the consumer components silently render blank placeholders if they only check `item.poster_path`. Always normalize in the component: `const poster = item.poster || (item.poster_path ? \`https://image.tmdb.org/t/p/w500${item.poster_path}\` : null)`. Same for `backdrop` vs `backdrop_path` in Hero. Better long-term: pick one shape and serialize through a single backend transformer.
29. **JavaScript typo trap: `endswith` is Python, `endsWith` is JavaScript.** When copy-pasting code patterns across languages, watch the case-sensitive string method names. `String.prototype.endswith` does NOT exist in JavaScript — only `endsWith` (capital W). Using the wrong one throws `TypeError: ... .endswith is not a function` at runtime. Other common cross-language traps: `len()` → `length`, `range()` → `Array.from()`, `dict.items()` → `Object.entries()`. When in doubt, type it out fresh in the target language.
30. **New page = new mobile review, even if you "know" the mobile rules.** When adding a new page (e.g. `/anime` alongside existing `/movies`), don't assume inline styles that worked elsewhere work here. The user will screenshot the broken mobile view and say "tampilan nya jelek belum support mobile" — that means **the page was tested on desktop only**. Specific anti-patterns that break on iPhone: (1) `padding: '20px 40px'` on the outer container — kills usable width, just use 16-20px horizontal. (2) `gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))'` — 180px minimum forces tiny 2-col grid on phone; use `minmax(120px, 1fr)` or switch to 2-col fixed on `<768px`. (3) Fixed font-size 28px for H1 — wraps badly on phone, use `clamp(20px, 5vw, 28px)`. (4) Multi-line filter button row without `flexWrap: 'wrap'` — overflows horizontally. **Always** add a mobile-only branch via CSS `@media (max-width: 768px)` or React responsive check. Quick mobile test: Chrome DevTools toggle device toolbar, iPhone 12 Pro viewport (390×844), or just resize browser to 375px width.
31. **Global layout components = page-level imports break the layout.** When `App.jsx` renders `<Navbar />` and `<Footer />` outside `<Routes>`, EVERY page already has them globally. Importing them again inside individual pages (e.g., `AnimeList.jsx` had its own `<Navbar />` AND `<Footer />`) produces duplicates the user sees as "footer dobel 3x" or "navbar muncul 2x". **Symptoms:** `document.querySelectorAll('footer').length` returns >1; user pastes the footer text content multiple times in a screenshot. **Fix pattern:** Always search the file for `<Navbar` and `<Footer` BEFORE adding new pages. If found, REMOVE the local import + usage. Global layout = page is just `<div className="page">{pageContent}</div>`. Add to project checklist when creating new pages: "1. Did I import Navbar/Footer? 2. Does App.jsx already have them globally? 3. If yes to both — remove local imports."
32. **JSX closing-tag typos are build-time errors, easy to miss in long strings.** When the same word opens/closes adjacent JSX (e.g., `<h1>Title <span>word</h1>` missing `</span>`), the build fails with "Unexpected closing h1 tag does not match opening span tag" — but only on the exact line, not the obvious-looking one. Watch for this when you have a self-closing element pattern mixed with nested spans. Always re-read the open/close tags in the exact order they appear, top-to-bottom, when you have mixed inline elements.
