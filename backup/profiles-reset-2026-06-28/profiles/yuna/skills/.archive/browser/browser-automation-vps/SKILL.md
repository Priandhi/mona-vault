---
name: browser-automation-vps
description: "Browser automation on headless VPS — CloakBrowser + Xvfb setup, stealth browsing, session persistence, scraping patterns. For Linux servers without display."
triggers:
  - "browser automation vps"
  - "headless browser"
  - "cloakbrowser"
  - "xvfb"
  - "scraping vps"
  - "stealth browser"
---

# Browser Automation on VPS

## Setup

### 1. Install CloakBrowser

```bash
# Install package
uv pip install cloakbrowser

# Install browser binary (~200MB)
python3.12 -m cloakbrowser install
# Installs to: ~/.cloakbrowser/chromium-<version>/chrome
```

### 2. Install Xvfb (virtual display)

```bash
apt-get install -y xvfb
```

### 3. Start Xvfb

```bash
# Run in background (permanent)
Xvfb :99 -screen 0 1920x1080x24 &

# Or use terminal background mode
terminal(background=true, command="Xvfb :99 -screen 0 1920x1080x24")
```

### 4. Set DISPLAY

```python
import os
os.environ['DISPLAY'] = ':99'
```

## Basic Usage

```python
import asyncio, os
os.environ['DISPLAY'] = ':99'

async def main():
    from browser_engine import BrowserAgent, BrowserConfig
    
    cfg = BrowserConfig(headless=False, cloaking=True)
    async with BrowserAgent(cfg) as b:
        await b.goto("https://example.com")
        title = await b.page.title()
        text = await b.page.query_selector("body")
        print(await text.text_content())

asyncio.run(main())
```

## CloakBrowser Config Options

```python
from browser_engine import BrowserConfig, StealthConfig

# Full stealth
stealth = StealthConfig(
    humanize=True,           # Human-like mouse/typing
    fingerprint_seed=42069,  # Consistent fingerprint
)

cfg = BrowserConfig(
    headless=False,     # False = needs Xvfb, True = headless
    cloaking=True,      # True = CloakBrowser (stealth), False = plain Playwright
    stealth=stealth,    # Stealth config
)
```

## PITFALL: cloaking=False requires Playwright

If you set `cloaking=False`, you need Playwright installed separately:
```bash
pip install playwright && playwright install chromium
```

With `cloaking=True`, CloakBrowser uses its own binary — no Playwright needed.

## Common Patterns

### Screenshot
```python
await b.page.screenshot(path="screenshot.png", full_page=True)
```

### Wait for element
```python
await b.page.wait_for_selector(".target-element", timeout=10000)
```

### Click + wait
```python
await b.page.click("button.submit")
await asyncio.sleep(1)  # Wait for action to complete
```

### Extract all links
```python
links = await b.page.query_selector_all("a[href]")
for link in links:
    href = await link.get_attribute("href")
    text = await link.text_content()
```

### Type with delay (human-like)
```python
await b.page.type("input.search", "query text", delay=50)
```

### Scroll
```python
await b.page.mouse.wheel(0, 500)  # Scroll down 500px
# Or to bottom:
await b.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
```

## Cloudflare Challenges

CloakBrowser's stealth mode helps but **does not guarantee bypassing Cloudflare**. For sites with heavy Cloudflare protection (like DEXScreener), prefer API-based approaches when available.

## API-First Alternatives

Many crypto data sites have free APIs that are faster and more reliable than scraping:

| Site | API | Endpoint |
|------|-----|----------|
| DEXScreener | Free | `api.dexscreener.com` |
| DeFiLlama | Free | `api.llama.fi` |
| CoinGecko | Free tier | `api.coingecko.com/api/v3` |
| Binance | Free | `fapi.binance.com` |

**Always check for API first.** Browser = last resort for sites without APIs.

## Session Persistence

```python
# Save cookies after session
cookies = await b.context.cookies()
import json
Path("cookies.json").write_text(json.dumps(cookies))

# Load cookies in next session
cookies = json.loads(Path("cookies.json").read_text())
await b.context.add_cookies(cookies)
```
