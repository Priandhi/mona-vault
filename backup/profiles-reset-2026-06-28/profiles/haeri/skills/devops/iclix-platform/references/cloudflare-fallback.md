# Cloudflare Anti-Bot Fallback Strategy for Anime Scrapers

## The Problem
Many anime sites (Samehadaku, others) use Cloudflare Turnstile / Bot Fight Mode on `admin-ajax.php`. The HTML page loads fine for Playwright (headless Chromium with `--disable-blink-features=AutomationControlled` and a `navigator.webdriver` override), but the AJAX endpoint returns **403** with the "Just a moment..." challenge page.

Symptoms:
- `page.goto('https://site.com/episode')` → loads, content visible
- `page.click('#play-button')` → click registers, no errors
- Network tab: POST to `/wp-admin/admin-ajax.php` → 403
- `<iframe>` never appears in the player

## Why It Happens
Cloudflare issues a JavaScript challenge that requires:
1. A non-headless browser fingerprint
2. Specific TLS/HTTP/2 settings
3. Cookie state from a successful challenge

Headless Chromium can sometimes pass page-level challenges but not AJAX-level ones. The site works in your real browser (Chrome with logged-in cookies) but not in Playwright.

## The Fallback (Production-Safe)
When stream extraction fails, **return the episode page URL as the embed URL**. The ICLIX user's browser passes the CF challenge naturally, sees the real play button, and clicks it.

```js
// Inside get_stream(), after the AJAX + iframe extraction:
if (embed) {
    return { embedUrl: embed, method: 'blogger' };  // Clean, no CF
}
// Fallback: return episode page, let user's browser handle CF
return {
    embedUrl: ep_url,
    method: 'episode_page',
    note: 'CF-blocked in headless, user browser will pass'
};
```

Frontend labels the embed differently:
```jsx
{method === 'episode_page' && (
    <p className="embed-note">⚠️ Player will load on samehadaku — click play when ready</p>
)}
```

## Better Solutions (When You Need Them)
1. **CloakBrowser** — patched Chromium that passes most anti-bot. See `browser/browser-agent` skill. Requires install.
2. **FlareSolverr** — self-hosted CF solver, exposes HTTP API. Run as Docker sidecar.
3. **Cookie injection** — solve CF manually once in a real browser, export `cf_clearance` cookie, inject into Playwright context. Cookies last ~30 days.
4. **Residential proxy** — Bright Data, Smartproxy. CF is more lenient on residential IPs.

## Detecting CF-Block Programmatically
```js
const isCfChallenge = (body) => body.includes('Just a moment...') ||
    body.includes('cf-chl-bypass') || body.includes('cf_clearance');
```

## Real Example (Samehadaku, June 2026)
- Headless Playwright → AJAX 403
- `embed: null` after click
- Fallback: return `https://v2.samehadaku.how/{slug}-episode-{N}/`
- User opens ICLIX → iframe loads samehadaku → CF passes (real browser) → user clicks play → blogger iframe loads → video plays

Acceptable trade-off: user does 1 extra click vs broken player. For 90% of anime, blogger iframe is the actual video source so the user experience is the same as if the API had extracted it server-side.

## When NOT to Use This Fallback
- Site has hard Cloudflare on the main page (not just AJAX) — iframe also won't load
- Site requires login for the episode
- Site actively blocks iframe embedding (`X-Frame-Options: DENY`)
- Episode URL is short-lived (e.g., signed token in path)
