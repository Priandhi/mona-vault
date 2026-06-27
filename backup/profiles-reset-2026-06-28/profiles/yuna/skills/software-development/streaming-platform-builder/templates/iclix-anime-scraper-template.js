/**
 * ANIME SCRAPER TEMPLATE — Copy & customize for new sources
 * Based on battle-tested AnimeUnity / Oploverz / Otakudesu / Samehadaku pattern
 *
 * GOTCHAS EMBEDDED (read comments before editing):
 * 1. JS template literal → Python: double ALL backslashes
 * 2. Use Playwright DOM API, NOT regex (modern sites use CSS background-image)
 * 3. Use Jikan API for cover fallback (AniList gets 429-blocked)
 * 4. Keep the final `print(json.dumps(...))` — it's the only signal back to Node
 * 5. Sandbox all embed URLs in iframe (anti-ad)
 */

import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CACHE_FILE = path.join(__dirname, '../cache/NEW_SOURCE.json');
const CACHE_TTL = 4 * 60 * 60 * 1000;  // 4 hours

const ENTRY = 'https://example.com';  // ← CHANGE: home URL

function loadCache() { try { return JSON.parse(fs.readFileSync(CACHE_FILE, 'utf-8')); } catch { return {}; } }
function saveCache(c) { try { fs.mkdirSync(path.dirname(CACHE_FILE), { recursive: true }); fs.writeFileSync(CACHE_FILE, JSON.stringify(c, null, 2)); } catch {} }

function runPython(script, args = []) {
  return new Promise((resolve, reject) => {
    const scriptPath = '/tmp/NEW_SOURCE_scrape.py';
    fs.writeFileSync(scriptPath, script);
    const proc = spawn('/tmp/pw-venv/bin/python', [scriptPath, ...args], { timeout: 180000 });
    let stdout = '', stderr = '';
    proc.stdout.on('data', d => stdout += d);
    proc.stderr.on('data', d => stderr += d);
    proc.on('close', code => code === 0 ? resolve(stdout) : reject(new Error(`exit ${code}: ${stderr.slice(0,200)}`)));
  });
}

// ⚠️ CRITICAL: In the template literal below, escape backslashes for Python:
//    JS `\\s` → Python file `\s` (regex whitespace)
//    JS `\\n` → Python file `\n` (newline)
//    JS `\\(` → Python file `\(` (literal paren)
const PY_SCRAPER = `
import asyncio, json, sys, re
from playwright.async_api import async_playwright

ENTRY = '${ENTRY}'  # Entry URL (Python string)

async def get_list():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=['--no-sandbox','--disable-dev-shm-usage'])
        c = await b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        page = await c.new_page()
        try:
            await page.goto(ENTRY, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)
            # USE DOM API — adjust selectors for your site
            items = await page.evaluate("""
() => {
  const items = [];
  // Example: iterate <a class="anime-card"> with <img> child
  for (const a of document.querySelectorAll('a.YOUR_CARD_CLASS')) {
    const m = a.href.match(/\\\\/YOUR_PATTERN\\\\/([\\\\w-]+)/);
    if (!m) continue;
    // Cover extraction: try <img>, then background-image
    let cover = '';
    for (const im of a.querySelectorAll('img')) {
      if (im.src && im.src.length > 10 && !im.src.startsWith('data:')) { cover = im.src; break; }
    }
    if (!cover) {
      for (const el of a.querySelectorAll('*')) {
        const bg = el.style && el.style.backgroundImage;
        if (bg) {
          const u = bg.match(/url\\\\(["\\\\']?(https?:[^"\\\\')]+)/);
          if (u) { cover = u[1]; break; }
        }
      }
    }
    const titleEl = a.querySelector('.title-class');
    items.push({slug: m[1], title: titleEl?.textContent?.trim() || m[1], cover, url: a.href});
  }
  return items;
}
""")
            await b.close()
        except Exception as e:
            print(json.dumps({'err': str(e), 'items': []}))
            return

        # OPTIONAL: enrich with Jikan covers (for sites without native covers)
        # Skip if your site already returns covers in items[]
        import urllib.parse as _up
        async def fetch_cover(session, title):
            try:
                url = 'https://api.jikan.moe/v4/anime?q=' + _up.quote(title) + '&limit=1'
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as r:
                    if r.status == 200:
                        d = await r.json()
                        data = d.get('data') or []
                        if data:
                            imgs = data[0].get('images', {}).get('jpg', {})
                            return imgs.get('large_image_url') or imgs.get('image_url') or ''
            except: pass
            return ''

        import aiohttp
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(items), 3):  # Batch 3, 1.5s delay = 60/min Jikan limit
                batch = items[i:i+3]
                results = await asyncio.gather(*[fetch_cover(session, it.get('title', '')) for it in batch], return_exceptions=True)
                for it, cv in zip(batch, results):
                    if isinstance(cv, str) and cv and not it.get('cover'):
                        it['cover'] = cv
                if i + 3 < len(items): await asyncio.sleep(1.5)

        print(json.dumps({'items': items[:100]}))


async def get_anime(anime_url, title):
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=['--no-sandbox','--disable-dev-shm-usage'])
        c = await b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        page = await c.new_page()
        try:
            await page.goto(anime_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)
            # Adjust to your site
            info = await page.evaluate("""
() => {
  const title = document.querySelector('h1')?.textContent?.trim() || '';
  const ogImg = document.querySelector('meta[property="og:image"]')?.content || '';
  const desc = document.querySelector('meta[property="og:description"]')?.content || '';
  // Extract episode list — adjust selector
  const epLinks = Array.from(document.querySelectorAll('a[href*="episode"]'));
  const episodes = epLinks.map(a => {
    const m = a.href.match(/episode-(\\\\d+)/);
    if (!m) return null;
    return {index: parseInt(m[1]), epId: m[1], url: a.href};
  }).filter(Boolean).sort((a, b) => a.index - b.index);
  return {title, cover: ogImg, description: desc.slice(0, 500), episodes};
}
""")
            await b.close()
            print(json.dumps(info))
        except Exception as e:
            print(json.dumps({'err': str(e)}))


async def get_stream(ep_url):
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=['--no-sandbox','--disable-dev-shm-usage'])
        c = await b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        page = await c.new_page()
        try:
            await page.goto(ep_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)
            # Common patterns: blogger embed, vixcloud embed, plain iframe
            embed = await page.evaluate("""
() => {
  const f = document.querySelector('iframe[src*="blogger.com/video.g"]');
  if (f) return f.src;
  const f2 = document.querySelector('iframe[src*="vixcloud"]');
  if (f2) return f2.src;
  const m = document.body.innerHTML.match(/(https?:\\\\/\\\\/[^"\\\\s<>&]+blogger[^"\\\\s<>&]+)/);
  if (m) return m[1].replace(/&amp;/g, '&');
  return null;
}
""")
            await b.close()
            if not embed:
                print(json.dumps({'err': 'no embed found'}))
                return
            print(json.dumps({'embedUrl': embed, 'epUrl': ep_url}))
        except Exception as e:
            print(json.dumps({'err': str(e)}))


async def main():
    mode = sys.argv[1]
    if mode == 'home': await get_list()
    elif mode == 'anime': await get_anime(sys.argv[2], sys.argv[3])
    elif mode == 'stream': await get_stream(sys.argv[2])

asyncio.run(main())
`;

// === EXPORTED FUNCTIONS (Node.js wrapper) ===
export async function getNewSourceList() {
  const cache = loadCache();
  if (cache._list && Date.now() - cache._list.scrapedAt < CACHE_TTL) {
    return { ...cache._list, fromCache: true };
  }
  try {
    const stdout = await runPython(PY_SCRAPER, ['home']);
    const result = JSON.parse(stdout.trim().split('\n').pop());
    const entry = { items: result.items, scrapedAt: Date.now() };
    cache._list = entry;
    saveCache(cache);
    return { ...entry, fromCache: false };
  } catch (e) { return { error: e.message, items: [] }; }
}

export async function getNewSourceAnime(animeUrl, title) {
  const cache = loadCache();
  const key = `anime:${animeUrl}`;
  if (cache[key] && Date.now() - cache[key].scrapedAt < CACHE_TTL) {
    return { ...cache[key], fromCache: true };
  }
  try {
    const stdout = await runPython(PY_SCRAPER, ['anime', animeUrl, title || '']);
    const result = JSON.parse(stdout.trim().split('\n').pop());
    cache[key] = { ...result, scrapedAt: Date.now() };
    saveCache(cache);
    return { ...result, fromCache: false };
  } catch (e) { return { error: e.message }; }
}

export async function getNewSourceStream(epUrl) {
  const cache = loadCache();
  const key = `stream:${epUrl}`;
  if (cache[key] && Date.now() - cache[key].scrapedAt < 30 * 60 * 1000) {
    return { ...cache[key], fromCache: true };
  }
  try {
    const stdout = await runPython(PY_SCRAPER, ['stream', epUrl]);
    const result = JSON.parse(stdout.trim().split('\n').pop());
    if (result.err) return { error: result.err };
    cache[key] = { ...result, scrapedAt: Date.now() };
    saveCache(cache);
    return { ...result, fromCache: false };
  } catch (e) { return { error: e.message }; }
}
