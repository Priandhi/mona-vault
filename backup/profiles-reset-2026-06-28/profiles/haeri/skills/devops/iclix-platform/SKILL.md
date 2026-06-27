---
name: iclix-platform
description: "ICLIX streaming platform — Indonesian dark/red/gold streaming site with React+Vite frontend, Node.js backend, Playwright-based content scrapers (anime, 21+, anti-ads HLS), and TMDB metadata. Class-level umbrella covering the design system, content sources, scraping patterns, anti-ads playback, and deploy-build-restart cycle. Trigger when user mentions ICLIX, asks to add a content source, modify the ICLIX UI, debug the anti-ads player, or run any ICLIX-specific operation."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [iclix, streaming, react, vite, node, scraper, playwright, tmdb, anime, adult, anti-ads, hls]
    replaces: [iclix-anime-scrapers, iclix-adult-21-plus-scrapers, iclix-frontend-design, iclix-anti-ads-direct-play]
---

# ICLIX Platform

ICLIX is a dark-themed Indonesian streaming platform — React + Vite frontend, Node.js backend, Playwright-based scrapers, TMDB metadata. This umbrella loads the right reference based on what aspect of ICLIX the user touches.

## Loading the right reference

| Task | Reference |
|---|---|
| Build/modify a page (color tokens, components, brand) | `references/frontend-design.md` |
| Add a new anime source (Jikan/AniList + JS-rendered) | `references/anime-scrapers.md` |
| Add a new 21+ source (Eporner/HQporner/XNXX/HDZog) | `references/adult-scrapers.md` |
| Anti-ads HLS player / direct m3u8 playback | `references/anti-ads-direct-play.md` |
| Deploy-build-restart cycle for ICLIX | `references/deploy-cycle.md` |

## Architecture (one-page summary)

```
ICLIX Platform
├── Frontend (React 18 + Vite, single index.css)
│   ├── Dark/red/gold design system (see references/frontend-design.md)
│   └── Pages: home, browse, detail, watch, search
├── Backend (Node.js, /home/ubuntu/iclix/backend/services/)
│   ├── anime-sources/     (AnimeUnity, Oploverz, Otakudesu, Samehadaku)
│   ├── adult-sources/     (Eporner, HQporner, XNXX, HDZog)
│   ├── scraper.js         (Anti-ads direct-play via Playwright)
│   └── tmdb/              (TMDB metadata proxy)
└── Scrapers (Python via /tmp/pw-venv, spawned by Node)
    └── One Python script per source (JS-rendered site fallback)
```

## §1. Frontend Design System (was `iclix-frontend-design`)

Brand rules are non-negotiable. User has explicitly corrected violations.

- **Colors**: Dark backgrounds (`bg-zinc-950`), red accents (`text-red-500`, `bg-red-600/40`), gold highlights (`text-yellow-400`)
- **Typography**: Sans-serif, weights 400/500/700. NO italic
- **Layout**: Mobile-first, max-w-7xl containers, generous padding
- **Logo**: Always use `<Logo />` component — never inline SVG
- **Social order**: Telegram → WhatsApp → Instagram → TikTok → X (fixed)

For full rules, color tokens, and page templates: `references/frontend-design.md`

## §2. Anime Scrapers (was `iclix-anime-scrapers`)

Architecture mirrors the 21+ scrapers. Each source = one Python script invoked by Node.js spawn.

**Pattern:**
1. Node.js handler in `anime-sources/<name>.js` defines endpoint + scrape flow
2. JS template literal embeds Python scraper code
3. Spawn `/tmp/pw-venv/bin/python` with Playwright + Chromium
4. Return JSON `{videos: [{embed_url, quality, type}]}`
5. Frontend plays via `<iframe>` (blogger/vixcloud) or direct m3u8 (anti-ads path)

**Sources configured:** AnimeUnity, Oploverz, Otakudesu, Samehadaku
**Fallbacks:** Jikan API (AniList for metadata when site fails)

For site-specific selectors + Playwright patterns: `references/anime-scrapers.md`

## §3. 21+ Scrapers (was `iclix-adult-21-plus-scrapers`)

Same pattern as anime, different sources + age gate.

**Sources:** Eporner, HQporner, XNXX, HDZog
**Key differences:**
- Anti-hotlink embed-iframe playback (NOT direct MP4) — sites serve m3u8 via signed URLs
- JSON-LD metadata extraction from result pages
- Site triage: premium-paywalled vs free-aggregator (only integrate free)
- Age gate via `templates/age-gate.jsx`

For site-specific quirks: `references/adult-scrapers.md`

## §4. Anti-Ads Direct Play (was `iclix-anti-ads-direct-play`)

Problem: Free iframe embeds (VidLink, VidSrc) serve ads INSIDE the iframe — popups, redirects, click-hijacking, pre-roll. Can't block ads inside an iframe from outside.

**Solution:**
1. Backend `scraper.js` uses Playwright to load `https://vidlink.pro/movie/{id}` in headless Chromium
2. Intercepts network requests to capture the m3u8 manifest
3. Returns clean m3u8 URL (no ads) to frontend
4. Frontend plays via `<video>` element directly

For full Playwright flow + m3u8 handling: `references/anti-ads-direct-play.md`

## §5. Deploy-Build-Restart Cycle

```bash
# Frontend (React/Vite, served by backend)
cd /home/ubuntu/iclix/frontend
npm run build
# Backend serves the dist/ folder

# Backend (Node.js)
cd /home/ubuntu/iclix/backend
pm2 restart iclix-backend
# Verify
curl -s https://iclix.example.com/api/health
```

**PITFALL**: After any `index.css` change, hard-refresh (Ctrl+Shift+R) — Vite HMR can show stale CSS for new color tokens.

## Absorbed Skills (consolidated June 2026)

- `iclix-frontend-design` → §1 + `references/frontend-design.md`
- `iclix-anime-scrapers` → §2 + `references/anime-scrapers.md` + `scripts/verify-scraper.sh` + templates + references (string-raw-escape, js-template-literal-escape, cloudflare-fallback)
- `iclix-adult-21-plus-scrapers` → §3 + `references/adult-scrapers.md` + `templates/age-gate.jsx` + `references/site-triage.md`
- `iclix-anti-ads-direct-play` → §4 + `references/anti-ads-direct-play.md` + `references/eporner-api.md`

## Related skills (kept standalone)
- `streaming-platform-builder` (in `software-development/`) — General React+Express streaming platform builder (non-ICLIX). Substantial 92K-char skill.
- `web-streaming-platform` (in `software-development/`) — Web streaming with embed players + tunneling (28K-char).
