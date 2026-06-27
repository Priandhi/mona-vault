---
name: iclix-anime-scrapers
description: Build and operate multi-source anime scrapers for ICLIX streaming platform - AnimeUnity, Oploverz, Otakudesu, Samehadaku. Each source uses Playwright via Python (Node.js spawns Python script) for JS-rendered sites. Covers extracted via Jikan/AniList API fallback. Videos sandboxed in iframe (blogger/vixcloud embeds).
---

# ICLIX Anime Scraper Pattern

## Architecture
- **Backend**: Node.js (`/home/ubuntu/iclix/backend/services/anime-sources/`) with JS template literals containing Python scrapers
- **Run via spawn**: `spawn('/tmp/pw-venv/bin/python', [scriptPath, ...args])`
- **Cache**: 4hr TTL in `backend/services/cache/{source}.json`
- **Frontend**: React `AnimeList.jsx` + `AnimeDetail.jsx` with mobile-first CSS in `src/styles/anime.css`

## CRITICAL Pitfalls (Will Burn You If You Don't Read This First)

### 🐛 JS template literal → Python source escaping (recurring trap)
When `writeFileSync` writes a JS template literal to a `.py` file, the backslashes are interpreted ONCE by JS, then again by Python. So to get a Python regex escape like `\s` (matches whitespace) or a string literal like `'\n'` (newline) into the file, you need to **DOUBLE the backslash in the JS source**:
- JS `r'\\s'` (2 chars: `\` + `s`) → file has `\s` (2 chars) → Python regex sees `\s` ✓
- JS `'\\n'` (2 chars: `\` + `n`) → file has `\n` (2 chars) → Python string sees newline ✓
- JS `r'\s'` (1 char each, no escape) → file has actual newline from JS template processing → **Python syntax error**
- Same applies to `\\w`, `\\d`, `\\b`, `\\.` in regex; and `\\n`, `\\t`, `\\r` in string literals.
- **Mental rule:** count backslashes. If you want N backslashes in the Python source, write 2N in the JS template literal.

This bit me hard: wrote `r'background-image:\s*url\(["\']?...'` in JS template literal → Python file got `background-image:s*url(["']?...` (no backslash) → SyntaxError "unterminated string literal". Fix: use `\\s*` and `\\(` and `\\.` in JS source.

### 🐛 String.raw template = the CLEAN solution (skip the backslash math)
**Recommended for all NEW scrapers.** After burning 4+ hours debugging backslash traps, the cleanest fix is to make the JS template literal a raw template — backslashes pass through verbatim:

```js
// GOOD: backslashes pass through, just write Python normally
const PY_SCRAPER = String.raw`
    m = re.search(r'episode\s*(\d+)', text)
`;

// BAD: every Python escape needs doubling, error-prone
const PY_SCRAPER = `
    m = re.search(r'episode\\s*(\\d+)', text)  // \\d, \\s, etc.
`;
```

**Two exceptions with String.raw** — Python raw strings still hate escaped quotes inside character classes. Replace with hex escapes:
- `r'[^"\'<>]'` breaks because `\'` ends the raw string. Use `r'[^"\x27<>]'` instead.
- Same for `\"` → `\x22`. This was the actual root cause of the animeunity vixcloud regex breaking on `[^\"\\'<>\\s]*` — once converted to `String.raw`, the `\\` disappeared and the `\\'` (which was meant to be `\'`) became a literal `'` that closed the string.

**Migration cost:** existing working `\\d` style scrapers don't need migration. For new files, default to `String.raw`.

### 🐛 page.evaluate adds a SECOND backslash layer (Python triple-quoted → JS source → regex)
This is a deeper trap that hits when Python writes a JS file and Playwright passes it via `page.evaluate(jsBody)`. The browser's JS engine interprets the function body, processing backslash escapes AGAIN. So a regex like `r'episode-(\d+)(?!\d)'` written inside a Python triple-quoted string in a JS template literal has THREE backslash layers:
1. JS template literal (handled by `String.raw` or doubling)
2. Python triple-quoted string `"""..."""` (handles `\\` → `\`)
3. Browser's JS parser (handles `\\` → `\`, but `\d` in a string literal → just `d`!)

Verify empirically:
```bash
node -e "
const re = new RegExp('(\\d+)(?!\\d)');  // 1 backslash each
console.log(re.source);  // (d+)(?!d) — BROKEN, backslashes stripped
const re2 = new RegExp('(\\\\d+)(?!\\\\d)');  // 2 backslashes each
console.log(re2.source);  // (\\d+)(?!\d) — WORKS
"
```

**Hex-dump is the fastest debug tool** when backslashes don't match expectations:
```bash
sed -n '116p' /tmp/sh_scrape.py | xxd
```
If you see `5c 64 2b` (single backslash + d + +), the JS template literal stripped it. Need `5c 5c 64 2b` (double backslash) or fix the source.

### 🐛 patch tool "Found N matches" false positive
When a file is last read with `read_file` pagination (offset/limit), the `patch` tool may report "Found 2 matches" even though `grep -c` finds 1. This is because the cached view is partial. **Workarounds:**
1. `read_file` with no limit first to refresh cached view, then `patch` again
2. Use `sed -i` via terminal for one-liner replacements
3. Use a Python heredoc that does `str.replace(old, new, 1)` with full file context

### 🐛 Cache poisoning from empty result — the silent feedback loop
When the API runs a Python scraper that returns `{"episodes": []}` (e.g. due to CF rate limit, or a bug that's now fixed), `getAnime` saves that empty result to `services/cache/{source}.json`. Next call hits the cache and returns the SAME empty data — even after you fix the script. **`fromCache: false` doesn't mean the run was successful; it just means the cache was missing for that key.**
- **Always check `cache[key].episodes.length` after a fix**, not just the response.
- **Nuclear clear pattern when debugging:** `rm -f services/cache/*.json && pkill -9 -f "node.*server.js" && pm2 start server.js --name iclix-api` then re-test. If the same source still returns 0 with `fromCache: false`, the script itself is broken. If it now returns N>0, you were hitting the stale cache.

### 🐛 "Test direct vs API" diagnostic split — always do this FIRST
When a scraper returns wrong/empty data, the bug could be in:
- (a) The Python script — `re.compile`, regex, page.evaluate, etc.
- (b) The Node.js call — cache, args, JSON parsing, etc.

**Isolate in 2 minutes:**
1. `cat /tmp/{src}_scrape.py` — file the API just wrote
2. Run it directly: `/tmp/pw-venv/bin/python /tmp/{src}_scrape.py {mode} {url} {title}`
3. Compare output with API response.

If direct run returns correct data but API doesn't → bug is in Node.js side (cache, args, runPython call). If direct run also returns wrong data → bug is in the Python script.

**Bonus:** the `/tmp/{src}_scrape.py` is overwritten on every API call, so test it immediately after a failed call to capture the exact broken state.

### 🐛 Page-evaluate JS regex + nested HTML (episode link text)
Many modern anime sites wrap the link text in nested tags: `<a href="..."><p class="ep-title">Ep 1</p></a>` (otakudesu) or `<a href="..."><span>Episode 1</span></a>`. A naive `r'<a[^>]+href="..."[^>]*>([^<]+)</a>'` fails because `[^<]+` can't cross the `<p>` or `<span>`.
- **Pattern that works:** `r'<a[^>]+href="..."[^>]*>(?:<[^>]+>)?\s*([^<]+)'` — optional nested tag, then text.
- **For the full HTML, also handle trailing attributes:** `r'<a[^>]+href="..."[^>]*>(?:<[^>]+>)?[^<]*([^<]{2,})'` (require min 2 chars to skip empty content).
- Empirically verified: the text after the nested tag is the actual episode label ("Ep 1", "Episode 1", etc.).

### 🐛 URL with trailing suffix after episode number
Anime sites often append variants: `episode-12-end`, `episode-10-subtitle-indonesia`, `episode-1-ova`. A naive `r'-episode-(\d+)'` will match `12` from `episode-12-end` (wrong, that's 1, not 12). The fix:
- Use `r'-episode-(\d+)(?!\d)'` (negative lookahead for more digits) to anchor at the episode number.
- For the slug, use non-greedy `([^"]+?)-episode-(\d+)` so the slug captures only up to `-episode-`.
- For trailing variants, accept them in the URL: `r'href="(/episodes/([^"]+?)-episode-(\d+)[^"]*)"'` — the `[^"]*` after the number allows `-end-subtitle-indonesia` etc.

### 🐛 Episode title extraction by visiting each episode page (AnimeUnity)
AnimeUnity doesn't show episode titles on the list/detail page — they're only visible on the individual episode page. The scraper has to navigate to each episode to extract the `<h1>` or `.episode-title`:
```js
// Inside the loop that clicks each episode-item
const ep_title = await page.evaluate("""() => {
    const h1 = document.querySelector('h1, .episode-title, .title');
    return h1 ? h1.textContent.trim() : document.title;
}""");
```
Trade-off: this multiplies scraping time by N (one page visit per episode). For a 12-episode anime, expect 30-60s total. Worth it for user experience, but warn the user when adding new sources.

### 🐛 Cover for first episode also extracted in get_anime (Samehadaku pattern)
The detail page's first episode post contains the og:image — scrape it for the anime cover, don't rely on a separate Jikan API call (which is slower and may return wrong anime). Add a `cover` field to the response by visiting the first episode URL and reading `meta[property="og:image"]`.

### 🐛 Don't break the print statement when replacing code blocks
The `print(json.dumps({'items': ...}))` at the end of `get_list()` / `get_anime()` is the only signal back to Node.js. If you replace a code block and forget to include the print, the function returns silently and Node sees "Unexpected end of JSON input". Always preserve the final `print(...)` when refactoring.

### 🐛 Python dict syntax inside JS template literal `{key:val}` is NOT Python
When calling `page.evaluate("""...js...""", {someKey: someVar})` from inside a Python function, the dict argument to `page.evaluate` is a **Python** literal. JS object-shorthand `{key:val}` is invalid Python (`NameError: name 'key' is not defined`). Always use Python dict syntax `{'key': val}` so it serializes to a proper JS object via Playwright's JSON bridge.
- ✗ `page.evaluate("""(args) => args.animeUrl""", {animeUrl: anime_url})` → Python `NameError`
- ✓ `page.evaluate("""(args) => args.animeUrl""", {'animeUrl': anime_url})` → JS sees `{animeUrl: '...'}` ✓

### 🐛 JavaScript `||` leaked into Python heredoc
When editing a Python function inside a JS template literal, it's easy to accidentally write `value = title || info.title` (JS syntax). Python's `||` is a SyntaxError. Use `or` and method calls: `info['title'] = title or info.get('title') or 'Unknown'`.

### 🐛 jQuery `.click()` returns false if option already has 'on' class (Samehadaku)
The site uses `$(".east_player_option").click(function(){ if ($(this).hasClass("on")) return false; ... $.ajax({...}) })`. The first option is loaded with `class="on"` and clicking it does NOTHING — no AJAX fires. Always click option 2 (or a non-active option), or use a selector that excludes `.on`: `#player-option-1.east_player_option:not(.on)`.

### 🐛 Regex literal `/pattern/g` — trailing `g` is interpreted as flag, not part of pattern
When using a regex like `/(https?:\/\/...g)$/` in a JS template literal, the closing `/$/` is fine, but if the literal ends with `/g` right after, the JS parser sees `g` as the regex `g` flag and throws "Invalid regular expression flags" if the next char isn't a valid flag. **Fix:** use string operations (`indexOf`, `split`, `substring`) instead of regex when the match is for a known substring.

### 🐛 Cloudflare blocks headless admin-ajax.php — fall back to episode page iframe
Many anime sites (Samehadaku, others) use Cloudflare Turnstile/bot protection on `admin-ajax.php`. The page itself loads fine for headless browsers, but the AJAX returns 403. **Fallback strategy:** when stream extraction fails due to CF, return the **episode page URL** as the embed URL. The ICLIX user's real browser passes the CF challenge naturally and clicks play themselves. This is acceptable UX — better than a broken player. Mark it with `method: 'episode_page'` in the response so frontend can label it ("Watch on samehadaku" instead of "Direct play").

## Source Patterns

### AnimeUnity (Italian)
- Home: `https://www.animeunity.so` - 41 items
- **DOM structure**: "ULTIMI EPISODI" section uses `<a class="cover"><div class="image" style="background-image: url(...)\">` (CSS background, NOT `<img>`)
- **Fix**: Use Playwright DOM API, NOT regex. Iterate `.item` containers, find cover via `style.backgroundImage` or `<img>`
- Video: vixcloud.co embed (intercept network response for `token=...`)

### Samehadaku (Indonesian) - DOMAIN MIGRATION 2026-06
- **OLD (DEAD)**: `samehadaku.fun` → `tecnotemas.com` (both 403 now)
- **NEW**: `https://samehadaku.care` → JS redirect (4s countdown) → `https://v2.samehadaku.how`
- **Mirror-hunt shortcut**: the `care` page has `<a href="https://v2.samehadaku.how">` link — extract that instead of waiting for redirect
- List: `https://v2.samehadaku.how/daftar-anime-2/` (alphabetical, scrolls to load more)
- Anime: `https://v2.samehadaku.how/anime/{slug}/` — has og:image cover, episode list at root-level
- Episode URL pattern: `https://v2.samehadaku.how/{slug}-episode-{N}/` (root-level, NOT under `/anime/`)
- **Stream mechanism**: AJAX POST to `/wp-admin/admin-ajax.php` with `action=player_ajax, post={postId}, nume={1|2|3}, type=schtml`. Response HTML contains the blogger iframe.
- **Filter out duplicate posts**: URLs like `{slug}-episode-2khusus-duplikat-jangan-dipake-post/` exist — strip via negative regex lookbehind `(?!\d)` in episode number
- **Cover**: og:image from detail page (often from `v1.samehadaku.how` CDN). Fallback to Jikan API.
- **Video**: Blogger embed `https://www.blogger.com/video.g?token=...` (returned in AJAX response HTML)
- **CF-blocked fallback**: if AJAX returns 403 in headless, return the episode page URL as embed. User's browser handles CF + click.

### Oploverz (Indonesian, +18+) - EPISODE EXTRACTION FIX
- Home: `https://oploverz.cc/list-anime-terupdate/` (alts: .io, .click, .site, .co, .net)
- **List page has NO cover images** - just text search results
- **Cover fallback**: Jikan API (`https://api.jikan.moe/v4/anime?q=...&limit=1`) or AniList
- **Video**: Blogger embed `https://www.blogger.com/video.g?token=...` - extract from `<iframe>` or HTML match
- **🚨 ONE-POST-PER-EPISODE TRAP**: Oploverz stores each episode as a separate post. The search URL `?s=Title` returns ALL episodes for that anime as search results, but the old `get_anime` only grabbed the first post.
- **Fix**: scan search results page, extract ALL `<a href="https://oploverz.[domain]/[slug]/[epId]/">` links, dedupe by epId, sort by episode number from text ("Episode 4") or epId.
- **Regex pattern**: `r'href="(https?://oploverz\.[a-z.]+/[a-z0-9-]+/(\d+)/?)"[^>]*>([^<]+)'` — capture URL, epId, and anchor text
- **Skip batch links**: filter URLs containing `batch` (these are full-season downloads, not individual episodes)
- Example: search for "Aishiteru Game" returns 7+ episodes; was returning 1.

## Rate-Limit Strategy
- **AniList GraphQL** (`graphql.anilist.co`): 90 req/min, hard-blocks IP on 429. Use batch 3 + 1.5s delay. **AniList WILL block you if you hit it hard** — even with delays. Prefer Jikan for new sources.
- **Jikan** (`api.jikan.moe/v4/anime`): 60 req/min, lenient. Use batch 3 + 1.5s delay. Reliable.
- **NEVER** do 100 sequential requests (will timeout at 60s)
- **NEVER** do batch of 10+ parallel (429 flood)
- **Multi-source fallback**: Jikan → AniList → empty string. Use 1 retry max per source before giving up.

## Workflow: Iterate Fast, Don't Loop Slowly
- User gets frustrated ("gimana lama banget") when you test 10+ items serially, each taking 10-15s. **Always:**
  1. **Test ONE item end-to-end first** (list → detail → stream). Fix everything before scaling.
  2. **Then test 3-5 items in a small batch** to confirm generalization.
  3. **Only then** commit to a full benchmark — and warn the user it will take 5+ minutes.
- Each Playwright launch costs ~2-3s. If you're testing 30 items, expect 5-10 minutes minimum.
- **Use `time curl` to time individual requests** — if one takes 30s, something is wrong (infinite scroll, JS hang, CF challenge).
- **Run quick tests via heredoc + `node -e`** instead of restarting PM2 each time:
  ```bash
  cd /home/ubuntu/iclix/backend && node -e "
  import('./services/anime-sources/x.js').then(async m => {
    const r = await m.getXList();
    console.log('items:', r.items?.length, 'err:', r.error);
  });
  "
  ```
  This uses the FRESH code (no PM2 needed) and finishes in seconds.

## jQuery Click Pattern (Playwright)
Many anime sites (Samehadaku, Oploverz) bind click handlers via jQuery. `page.click()` works MOST of the time, but for jQuery-bound handlers use `page.evaluate("jQuery('#sel').trigger('click')")` for reliability:
```js
clicked = await page.evaluate("""() => {
    const opt = document.querySelector('#player-option-2');  // NOT option-1 (already 'on')
    if (opt) { jQuery(opt).trigger('click'); return opt.id; }
    return null;
}""")
```
**Why:** jQuery handlers run in a different event scope than Playwright's synthetic click. Direct `trigger('click')` invokes the same code path as a user click. Also avoids timing issues with `addEventListener` vs jQuery's `.on('click')` bindings.

## Mirror-Hunt Recipe (Finding New Anime Sources)
When a domain "goes down", don't give up. Test 10+ TLDs systematically:
```bash
for d in samehadaku.care samehadaku.run samehadaku.how samehadaku.lol samehadaku.online \
         samehadaku.website samehadaku.fun samehadaku.cc samehadaku.nu samehadaku.com \
         samehadaku.tv samehadaku.id; do
    status=$(curl -s -o /dev/null -w "%{http_code}" -m 5 -A "Mozilla/5.0" "https://$d/")
    if [ "$status" = "200" ] || [ "$status" = "301" ] || [ "$status" = "302" ]; then
        echo "✅ $d: $status"
    fi
done
```
Then use Playwright (real browser) to check the live content — many have anti-bot redirects that block curl but allow real Chromium.

## Scraping Template (Copy-Paste Pattern)
```python
const PY_SCRAPER = `
import asyncio, json, sys, re
from playwright.async_api import async_playwright

async def get_list():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=['--no-sandbox','--disable-dev-shm-usage'])
        c = await b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        page = await c.new_page()
        await page.goto(URL, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(5000)
        # USE DOM API, NOT REGEX
        cards = await page.evaluate("""
() => {
  const items = [];
  for (const CARD_SELECTOR of document.querySelectorAll('CARD_SELECTOR')) {
    const m = CARD_SELECTOR.href.match(/PATTERN/);
    if (!m) continue;
    // Extract cover from <img> or background-image
    let cover = '';
    for (const im of CARD_SELECTOR.querySelectorAll('img')) {
      if (im.src && im.src.length > 10 && !im.src.startsWith('data:')) { cover = im.src; break; }
    }
    if (!cover) {
      for (const el of CARD_SELECTOR.querySelectorAll('*')) {
        const bg = el.style?.backgroundImage;
        if (bg) { const u = bg.match(/url\\\\(["\\\\']?(https?:[^\"\\\\')]+)/); if (u) { cover = u[1]; break; } }
      }
    }
    items.push({url: CARD_SELECTOR.href, title: ..., cover});
  }
  return items;
}
""")
        await b.close()
        print(json.dumps({'items': cards}))  # CRITICAL: keep this print
```

## Mobile UI Pattern (ICLIX Lessons Learned)
- **NEVER use inline styles** like `padding: 20px 40px` in JSX — they don't adapt to mobile
- **Always extract to CSS classes** with media queries
- 3-breakpoint system: mobile (0-599px), tablet (600-1023), desktop (1024+)
- Grid: `repeat(auto-fill, minmax(120px, 1fr))` mobile → `180px` desktop
- **Touch targets**: min 40px height for buttons (44px iOS HIG recommendation)
- **Search bar**: collapsible on mobile (toggle button), always visible on desktop
- See `references/mobile-css-template.css` for the full template

## Iframe Sandbox (Anti-Ad)
```jsx
<iframe
  src={embedUrl}
  sandbox="allow-scripts allow-same-origin allow-forms allow-presentation"
  referrerPolicy="no-referrer"
  allow="autoplay;encrypted-media;fullscreen"
  allowFullScreen
/>
```
- Block popup, top-level navigation, new tabs
- DO NOT add `allow-popups` or `allow-top-navigation`

## Registration
Add new source in `backend/services/anime-sources/index.js`:
```js
import * as NewSource from './newsource.js';
const SOURCES = {
  ...
  newsource: { name: 'NewSource', module: NewSource, fn: { list: 'getNewSourceList', anime: 'getNewSourceAnime', stream: 'getNewSourceStream' }, type: 'regular' },
};
```

## Deploy Steps
1. Edit source file
2. `rm services/cache/{source}.json` (force refresh)
3. Test locally: `cd services/anime-sources && node --input-type=module -e "import { getXList } from './x.js'; const r = await getXList(); console.log(r.items?.length, (r.items||[]).filter(i=>i.cover).length)"`
4. `pm2 restart iclix-api`
5. Verify via tunnel: `curl -s -m 90 https://{tunnel}/api/anime/list`

## Total Stats (As of June 2026)
- 4 sources, 211 anime, 180 with covers (85%)
- AnimeUnity 41/41, Oploverz 100/72, Otakudesu 20/20, Samehadaku 50/47
- Up from original 3 sources / 163 anime / 0% covers

## Related Skills
- `iclix-anime-scraper` (older version) has a `references/cover-extraction-patterns.md` with battle-tested cover extractors — overlap noted, curator should consolidate.

## Reference Files
- `references/js-template-literal-escape.md` — The backslash trap that costs hours if you don't know it. Read FIRST when writing new scrapers.
- `references/string-raw-escape.md` — 🆕 The CLEAN solution: `String.raw\`...\`` skips the backslash math. Includes the page.evaluate 3rd-layer trap and hex-dump debug recipe.
- `references/cloudflare-fallback.md` — When admin-ajax.php is CF-blocked, the production-safe fallback pattern (return episode URL, user's browser handles CF).
- `templates/scraper-template.js` — Drop-in template with all 4 functions (list/anime/stream) wired up. Edit selectors, deploy.
- `templates/mobile-css-template.css` — Mobile-first CSS template (3 breakpoints, 120px/180px grids, touch targets). Use for any new ICLIX page.
- `scripts/verify-scraper.sh` — End-to-end verification (cache clear → local test → PM2 restart → tunnel API check).
