# MonaBrowser Wrapper — Reusable Browser Automation

## Overview

`mona_browser.py` is a reusable wrapper around CloakBrowser/Playwright for Mona's browser tasks. Located at `~/.hermes/scripts/mona_browser.py`.

## Features

- **Stealth mode** — CloakBrowser with fingerprint patches (fallback to plain Playwright)
- **Session persistence** — Cookies saved/loaded per profile
- **Rate limiting** — Configurable delay between requests (default 2s)
- **Screenshot capture** — Auto-saved to `~/.hermes/browser-data/screenshots/`
- **Telegram alerts** — Integrated `send_telegram_alert()`

## Usage

```python
import asyncio, os
os.environ['DISPLAY'] = ':99'
from mona_browser import MonaBrowser

async def main():
    async with MonaBrowser(profile="default", headless=True) as b:
        await b.goto("https://example.com")
        text = await b.get_text("body")
        screenshot = await b.screenshot("my_page")
        
        # Cookie persistence
        await b.save_cookies()
        await b.load_cookies()  # On next session
        
        # Form interaction
        await b.type_text("#search", "query")
        await b.click("#submit")
        
        # Data extraction
        links = await b.query_all("a[href]")
        title = await b.get_attribute("h1", "class")
        js_data = await b.evaluate("document.title")

asyncio.run(main())
```

## Directory Structure

```
~/.hermes/browser-data/
├── profiles/
│   └── default/
│       └── cookies.json      # Saved cookies per profile
├── screenshots/
│   └── my_page_20260607_193000.png
└── cache/
```

## Environment Setup

```bash
# Always set DISPLAY before any browser code
export DISPLAY=:99

# Xvfb must be running (daemon on :99)
pgrep -a Xvfb || Xvfb :99 -screen 0 1920x1080x24

# CloakBrowser binary (one-time install)
python3.12 -m cloakbrowser install

# Dependencies
uv pip install beautifulsoup4 lxml
```

## API Methods

| Method | Description |
|--------|-------------|
| `goto(url, wait_until)` | Navigate to URL |
| `click(selector)` | Click element |
| `type_text(selector, text)` | Fill input field |
| `wait_for(selector, timeout)` | Wait for element |
| `get_text(selector)` | Get text content |
| `get_attribute(selector, attr)` | Get attribute value |
| `query_all(selector)` | Get all matching elements [{text, href}] |
| `evaluate(js)` | Run JavaScript |
| `screenshot(name)` | Capture screenshot, return path |
| `scroll_down(pixels)` | Scroll page |
| `scroll_to_bottom()` | Scroll to bottom |
| `get_page_data()` | Get title + url + text + links |
| `save_cookies()` | Save cookies to profile |
| `load_cookies()` | Load cookies from profile |
| `send_alert(msg, topic)` | Send Telegram alert |

## Known Issues

- **MetaMask v13 SPA conflict**: Use `cloaking=False` in BrowserConfig
- **Xvfb must be running**: Check with `pgrep -a Xvfb`
- **python3.12 for CloakBrowser**: System python3 is 3.11 (Hermes venv)
- **Rate limiting**: Default 2s between requests to avoid bans
- **Headless mode**: Set `headless=True` for server use (no display needed)
