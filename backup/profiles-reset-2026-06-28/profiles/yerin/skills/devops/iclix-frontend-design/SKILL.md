---
name: iclix-frontend-design
description: Build and modify ICLIX frontend pages using the established dark/red/gold design system. Covers page structure, color tokens, component patterns, brand rules (logo treatments, social media order), and the deploy-build-restart cycle.
---

# ICLIX Frontend Design System

ICLIX is a dark-themed Indonesian streaming platform (React + Vite, single `index.css`). This skill is the source of truth for the visual language and page-building patterns. Every new page should follow these conventions.

## Brand rules (non-negotiable)

User has explicitly corrected these. Don't "unify" or "improve" them without asking.

- **Navbar logo** (`/public/logo.svg`): "ICLIX" all **RED** (`#e50914`). Single color, glossy 3D effect with white shine gradient + dark red stroke. Don't introduce yellow in the SVG.
- **Side menu logo** (text in `Navbar.jsx`): "IC" **YELLOW** gradient (`#ffd700`→`#ffaa00`) + "LIX" **RED** (`#e50914`). Classes: `.ic-yellow` and `.lix-red`. "BY HEXA" is white.
- **Hero brand text**: ICLIX = pure `#e50914` red, BY HEXA = pure white.
- **Page background**: exactly `#000`. Not `#0a0a0a`, not `#111` — `#000`.
- **Auth buttons in side menu**: both red-themed (Masuk = red-tinted bg, Daftar = solid red gradient with shadow).

## Color palette

| Token | Hex | Use |
|---|---|---|
| `--red` | `#e50914` | Primary brand, buttons, icons, highlights |
| `--red-dark` | `#5a0003` | SVG stroke depth |
| `--gold` | `#f5c518` | Premium/VIP accents, section titles |
| `--gold-bright` | `#ffd700` | Side menu "IC" gradient start |
| `--gold-warm` | `#ffaa00` | Side menu "IC" gradient end |
| `--bg-black` | `#000` | Page background |
| `--bg-card` | `#0a0a0a` | Card/panel background |
| `--border-subtle` | `#1a1a1a` | Card borders |
| `--border-hover` | `#2a2a2a` | Card hover borders |
| `--text-primary` | `#fff` | Headings |
| `--text-secondary` | `#b8b8b8` | Body text |
| `--text-muted` | `#888` | Captions |
| `--green` | `#22c55e` | Success/check icons |
| `--red-bright` | `#ef4444` / `#ff3344` | Error/cross icons |

## Typography

- Logo: `'Arial Black', sans-serif`, weight 900, letter-spacing 1-3px
- Hero H1: 44px, weight 800, letter-spacing -1.5px
- Section H2: 22px, weight 800
- Section H3: 16px, weight 700
- Body: 15px, line-height 1.7
- Use Lucide React icons for all UI icons (NOT emoji in code, though emoji is fine inside content text)

## Page structure pattern (`.info-page` family)

Used for About, Terms, Privacy, FAQ. Use this template for any new content/legal/info page:

```jsx
<div className="info-page">
  <div className="info-hero">
    <div className="info-hero-bg" />
    <div className="info-hero-content">
      <div className="info-hero-icon"><LucideIcon size={36} color="#e50914" /></div>
      <h1>Title <span className="info-highlight">Accent</span></h1>
      <p>One-line subtitle, max 60 chars, casual Indonesian.</p>
    </div>
  </div>
  <div className="info-section">
    {/* info-meta optional timestamp */}
    <div className="info-block">
      <h2>Section title</h2>
      <p>Body paragraph.</p>
      <ul className="info-list">
        <li><Icon /> <span>Item with icon</span></li>
      </ul>
    </div>
  </div>
</div>
```

### Available building blocks

- **`.info-block`** — main card container, dark bg, subtle border, hover lightens border
- **`.info-block h2/h3`** — section titles (h2 with icon prefix, h3 for sub-sections)
- **`.info-list`** — vertical list with icon + text, gap 12px
- **`.info-grid`** — `grid-template-columns: repeat(auto-fill, minmax(220px, 1fr))` card grid
- **`.info-card`** — small card with title + description, hover lifts +2px and red border
- **`.info-contact-grid`** — same as info-grid but minmax 260px
- **`.info-contact-card`** — clickable card with icon + label + value (use for Telegram/Email)
- **`.info-cta`** — gradient-tinted variant for "contact us" blocks
- **`.faq-item-page`** — accordion item (button + collapsible body), red border when `.open`
- **`.info-meta`** — small timestamp/tag pill, inline-block, red-tinted bg

## Social media order (footer "IKUTI KAMI")

Fixed order — don't reorder: **Instagram → TikTok → X (Twitter) → YouTube**

Each gets a circular button with the platform's brand color and a thin yellow outer glow (Instagram, X, YouTube) or cyan glow (TikTok).

## How to add a new page

1. **Create** `src/pages/MyPage.jsx` using the `.info-page` template above (or a domain-specific page pattern like VIP.jsx for pricing pages)
2. **Import + add route** in `src/App.jsx`:
   ```jsx
   import MyPage from './pages/MyPage'
   // ...
   <Route path="/my-page" element={<MyPage />} />
   ```
3. **Add CSS** to `src/index.css` (single file, no CSS modules). Place near related page styles.
4. **Build + restart**:
   ```bash
   cd /home/ubuntu/iclix/frontend && npm run build
   pm2 restart iclix-api
   ```
   The API serves `dist/` as static assets. Cloudflare tunnel (cf-tunnel-iclix) proxies to localhost:3000. Tunnel URL stored in `/tmp/tunnel-watchdog/urls.json`.
5. **Verify** with browser: `https://prague-runner-cyber-volumes.trycloudflare.com/my-page`
   - Use `page.evaluate` + `getComputedStyle` for color checks (vision_analyze is inconsistent on small screenshots — per memory)

## Common pitfalls

- **Logo split** confusion: navbar SVG is ALL red, side menu text is SPLIT. Don't "fix" one to match the other.
- **JSX nesting**: every `<span>` and `<div>` must be properly closed. Watch for missing `</span>` after content with `info-highlight` class (caused a build failure once).
- **CSS placement**: the file is 1100+ lines. Use search_files to find existing patterns before adding new ones. Don't duplicate `.info-block` definitions.
- **Build path**: `npm run build` regenerates `dist/`, then `pm2 restart iclix-api` picks it up. Don't forget the restart — Vite dev mode isn't running in production.
- **PM2 deploy verification**: After `pm2 restart iclix-api`, the process sometimes keeps serving the OLD code if the Node module cache didn't pick up the file changes (rare but happens with large edits to `server.js`). Always verify with `curl http://localhost:3000/api/<changed-route>` before telling the user it's done. If the old response comes back, run `pm2 restart iclix-api --update-env` (the `--update-env` flag forces a full process reset). Then verify again.
- **Vision verification**: don't rely solely on `vision_analyze` for color/layout checks. Use `browser_console` with `getComputedStyle` for definitive answers. Small emoji (👁) inside input fields are often missed by vision on the first pass even when positioned correctly.
- **Indonesian tone**: user-facing copy is casual Indonesian (lo/gue/lo-gue style, mixed). Match that voice for any new content.
- **Avoid auto-validate-on-input for fragile flows.** User explicitly said "biar gak eror" when switching from "type SAYA 21 TAHUN OR LEBIH" auto-validate to explicit password + submit button. Auto-validating as the user types looks slick but breaks on paste/copy/IME, and the user has to know exact phrasing. Default to: input + explicit submit button + clear error state.
- **Re-check the AGE_KEY `localStorage` name** (`iclix_21_verified`) before changing the gate. The `useState` initializer reads from this key on mount; renaming the key forces a re-prompt for every existing user.

## Reference pages using this design

- `src/pages/VIP.jsx` — pricing page (3 plans + perks grid + FAQ)
- `src/pages/LiveTV.jsx` — channel grid with category filters
- `src/pages/DramaAsia.jsx` — content row layout
- `src/pages/AnimeList.jsx` — filterable content grid
- `src/pages/About.jsx` — info-page template (About Us style)
- `src/pages/Terms.jsx` — info-page template (legal style with sections)
- `src/pages/Privacy.jsx` — info-page template (data policy style)
- `src/pages/FAQ.jsx` — info-page template with accordion (faq-item-page)

## Age gate / password gate pattern

Used for the `/21plus/*` adult section and any future restricted route (VIP-only preview, hidden admin area, etc.). Two-step flow: warning screen → password form. Verification is stored in `localStorage` so the user only sees the gate once per browser.

When to use: any page that needs an additional "are you really sure / do you know the password" wall beyond just a route. **Don't** use this for actual security — it's a soft gate, not auth. A determined user can bypass it with devtools.

### JSX template (replace `AgeGate` component in `src/pages/Adult.jsx`)

```jsx
const AGE_KEY = 'iclix_21_verified'  // rename per route if you have multiple gates

function AgeGate({ onVerified }) {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)         // 0: warning, 1: password
  const [pw, setPw] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [shake, setShake] = useState(false)
  const [err, setErr] = useState('')

  const submitPw = (e) => {
    e?.preventDefault()
    if (pw.trim().toLowerCase() === 'YOUR_PASSWORD') {
      localStorage.setItem(AGE_KEY, '1')
      onVerified()
    } else {
      setErr('Password salah, coba lagi.')
      setShake(true)
      setTimeout(() => { setShake(false); setErr('') }, 800)
      setPw('')
    }
  }

  // step 0: warning screen (unchanged from existing Adult.jsx — see file)
  // step 1: <form> with input + show/hide toggle + "Masuk →" button
  //         + .agegate-pw-clue with the trivia hint (small italic)
  //         + .agegate-pw-err for wrong-password feedback
  //         + "← Kembali" back button to return to step 0
}
```

The mounted `<Adult>` parent reads `localStorage` synchronously in `useState` initializer and only renders the gate when the value is not `'1'`.

### CSS classes (live in `src/styles/adult.css`)

| Class | Purpose |
|---|---|
| `.adult-agegate` | Fullscreen fixed overlay (radial-gradient bg + 2 glow blobs) |
| `.agegate-box` | Centered card, `max-width: 480px`, glassmorphism + red border |
| `.agegate-box.shake` | Triggered on wrong password; `shake` keyframe 500ms |
| `.agegate-title` | Gradient red text for the "21+ CONTENT" heading |
| `.agegate-buttons` | Flex row of 2 buttons in step 0 |
| `.agegate-btn` / `.agegate-btn-yes` / `.agegate-btn-no` | Button base + variants |
| `.agegate-pw-form` | Vertical flex, gap 12px — wraps input + submit |
| `.agegate-pw-wrap` | `position: relative` so the eye toggle can absolute-position |
| `.agegate-input` | Full-width input, red focus border, 16px font for non-zoom on iOS |
| `.agegate-pw-toggle` | Absolute-positioned eye emoji (👁 / 🙈) at `right: 8px; top: 50%` |
| `.agegate-pw-submit` | Reuses `.agegate-btn-yes` (red gradient), full width |
| `.agegate-pw-err` | Red-tinted error banner, shown on wrong password |
| `.agegate-pw-clue` | Trivia hint — **10px italic gray, low contrast on purpose** so it's a nudge, not a giveaway |
| `.agegate-btn-back` | "← Kembali" link, resets state and returns to step 0 |

### Trivia clue style

User explicitly wants clue text **small** ("kecil aja tulisan nya"). Don't make it prominent — it's a fun nudge, not the answer. Use:

```css
.agegate-pw-clue {
  margin-top: 14px; font-size: 10px; color: #555;
  letter-spacing: .5px; font-style: italic; text-align: center;
  user-select: none;
}
```

`user-select: none` is optional but discourages accidental highlight.

### Building a second gate (e.g. for VIP-only preview)

Use a different `AGE_KEY` constant — e.g. `iclix_vip_preview_verified`. Otherwise the same user instantly passes the new gate because they already cleared the first one.
