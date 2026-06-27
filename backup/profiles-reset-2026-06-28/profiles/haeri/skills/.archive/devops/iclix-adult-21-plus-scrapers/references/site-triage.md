# Adult Site Triage — Can We Scrape It?

Use this checklist when user asks to add a new adult content source. Decision happens BEFORE writing any code.

## Quick Probe (run all 4)

```bash
# 1. Health + response size
curl -sIL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -m 8 "$URL" 2>&1 | grep -E "^HTTP|content-length|server" | head -5

# 2. Cloudflare / anti-bot fingerprint
curl -sL -A "Mozilla/5.0" -m 8 "$URL" 2>&1 \
  | grep -iE "cf-ray|cloudflare|challenge|please-wait|verify you are human" | head -3

# 3. Paywall markers
curl -sL -A "Mozilla/5.0" -m 8 "$URL" 2>&1 \
  | grep -iE "join now|sign up|subscribe|premium|membership|trial" | head -5

# 4. Content accessibility (can we see a video URL?)
curl -sL -A "Mozilla/5.0" -m 8 "$URL" 2>&1 \
  | grep -oE 'https?://[^"]*\.(mp4|m3u8)[^"]*' | head -3
```

## Decision Tree

```
Site returns 200, no CF challenge, has <video> or JSON-LD on listing pages
  └─→ ✅ AGGREGATOR — proceed to integration

Site returns 200, but home page has "join / subscribe" prominently
  └─→ ❌ PREMIUM PAYWALL — decline politely, pivot to free alternatives

Site returns 200, has CF challenge / "verify you are human"
  └─→ ⚠️ CLOUDFLARE-PROTECTED — likely needs CF clearance cookies; not worth the fight
  └─→ Decline unless user has CF clearance solution already working

Site returns 403/401 even with browser UA
  └─→ ❌ HARD-BLOCKED — decline

Site returns 200, but no video URLs in HTML (JS-rendered)
  └─→ ⚠️ NEEDS PLAYWRIGHT — possible but heavy. Check if there's a hidden API first.
  └─→ Look for /api/ endpoints in network tab via browser inspection
```

## 200 OK ≠ Scrapeable (The Most Common Trap)

A site returning `HTTP/2 200` is **necessary but not sufficient**. The fastest way to detect JS-only sites:

```bash
# If this returns ZERO real URLs (not menu/nav/login), site is JS-rendered
curl -sL -A "Mozilla/5.0" -m 8 "$URL" \
  | grep -oE 'href="[^"]*"' \
  | grep -vE "css|js|png|jpg|ico|svg|woff|#|/$" \
  | head -20
```

If grep returns only nav/menu/login/signup links → site is a heavy SPA → needs Puppeteer.

### Concrete case: 4tube.com (2026-06-14)
- `curl -sI https://www.4tube.com` → **200 OK** ✓
- `robots.txt` exists, allows crawling
- `sitemap.xml` exists, but its child file `/sitemap/item-collection/list/newest/default.xml` contains ONLY category URLs (`/category/japanese`, `/category/asian`, …) — **never individual video pages**
- Initial HTML has zero video data — all loaded via React hydration
- All `/api/*` paths return 404; JS bundle is small (33KB) with no embedded URLs
- **Verdict**: Skip. Would need Puppeteer + reverse-engineering internal XHR. ~half-day cost for one site. Not worth it when Eporner/HQPorner expansion is faster ROI.
- **User pattern**: 4tube keeps coming up in "premium Indo / Asian" requests. When user names 4tube, the honest answer is "200 OK but JS-only SPA, no public API, would need headless browser."

### General "JS-only site" markers
- Response size `< 50KB` for a content site = likely SPA shell
- `__NEXT_DATA__`, `__NUXT__`, or `window.__INITIAL_STATE__` in HTML = SPA framework
- `app-*.js` or `chunk-*.js` filenames, main JS > 200KB = SPA
- HTML contains only nav/menu/footer links, no `<article>` or product cards
- Sitemap only lists categories, never individual content pages

### Concrete case: javhd.com (premium paywall, 200 OK)
- `curl -sI https://javhd.com` → **200 OK** ✓ (so naïve probes think it's fine)
- But content is gated — the only accessible pages are `/en/join` and `/en/login`
- Tag pages like `/en/tags/indonesia` return 404
- The site IS reachable, but the content you want is behind a paywall
- **Verdict**: Premium. Don't try to scrape — that path leads to access-without-authorization.

## Site Classes (Verified)

### ✅ Scrape-friendly (free aggregators)
- **hqporner.com** — 200, no CF, HD-focused, mydaddy.cc proxy pattern
- **eporner.com** — 200, has public JSON API at `/api/v2/video/search/`
- **www.xnxx.com** — 200, large library
- **hdzog.com** — 200, HD-focused
- **xhamster.com** — 429 (rate-limited) but works with delay/header rotation

### ❌ Premium paywall (decline)
- **vixen.com** — 403, premium-only
- **brazzers.com** — paywalled
- **realitykings.com** — paywalled
- **naughtyamerica.com** — paywalled
- **javhd.com** — homepage 200 but content is paid, only signup/login accessible
- **mindgeek family** (Vixen, Brazzers, RealityKings, DigitalPlayground, etc.) — actively sue scrapers

### ❌ Illegal / risky (decline)
- **bokep*** (any Indo bokep aggregator) — illegal distribution, malware-laden
- **IndoXXI-style movie sites** — piracy, not adult
- **xnxx.com, pornhub.com** — legal but actively anti-scraping (CF + legal teams)

### ⚠️ Gated / personal (decline)
- **OnlyFans** — need user auth, account-level ToS
- **Fansly** — same
- **Telegram premium channels** — gated, requires joining with personal account
- **Cam platforms** (Chaturbate, Stripchat, etc.) — RTMP streams, not HTML

### ❌ Dead domains (verified 2026-06-14)
- **19mommy.com** — connection refused
- **18pole.com** — connection refused
- **jav321.tv** — connection refused
- These are not blocked, they don't exist anymore. Don't waste time retrying.

## Red Flags to Watch For

1. **"This site may be blocked in your country"** → likely illegal in origin country, decline
2. **Aggressive ad density** (popups, redirects, fake download buttons) → user-facing risk
3. **No HTTPS** → user-facing risk
4. **Domain registered < 1 year ago** → high churn, scraper breaks often
5. **Domain TLD .xxx, .porn, .adult** → varies wildly; some are legit (legal operators), some are scams
6. **No terms of service / privacy policy** → unaccountable operator, decline

## When to Ask the User

If after triage the answer is "borderline", ask one focused question:
- "This site returns 200 but looks like [premium paywall / gated community / X]. Want me to (A) try anyway with rate limits, (B) skip and use [alternative], (C) you have an account/credentials you can share?"

Don't ask permission to scrape *premium paywalls* — that's a hard line, not a choice.

## Indonesian-Language Sites (Special)

The user specifically asked for Indonesian content. Real check on 2026-06-14:

- **No major legal Indonesian premium adult site exists** that's scrape-friendly
- **The Indonesian content that's "rame" (popular) lives on international aggregators** under `query=indonesian` or `asian` category
- **Eporner Indonesian tag** = 2,482 real videos (best current source)
- **Premium Indo-targeted sites** that do exist are mostly individual creators on Telegram, OnlyFans, or local cam platforms — not scrapeable

When user asks for "premium Indonesian site", the honest answer is: doesn't exist in the legal-scrape-friendly quadrant. Pivot to:
- Eporner `query=indonesian` (2,482 videos)
- HQporner Indonesian search (TBD count)
- XNXX Indonesian tag (TBD count)

Frame as: "we'll surface Indonesian content as a top-level category across the sources we have" — that's a real product solution, not a workaround.
