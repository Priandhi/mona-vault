# Browser Automation — Sprint 3 Integration

Built: June 2026. Integrates CloakBrowser with Mona's Telegram command center for Twitter, dApp, and airdrop website automation.

## Architecture

```
User command in topic → mona_bot.py router → mona_browser_commands.py → mona_browser.py → CloakBrowser → Screenshot → Reply
```

## Files

| File | Location | Purpose |
|------|----------|---------|
| `mona_browser.py` | `~/.hermes/scripts/` | Core engine: TwitterAutomation, DappAutomation, AirdropAutomation, ScreenshotManager |
| `mona_browser_commands.py` | `~/.hermes/scripts/` | Bot integration: command parsing, async execution, topic routing |
| `~/mona-workspace/skills/browser-agent/scripts/browser_engine.py` | Skills dir | CloakBrowser wrapper (BrowserAgent, BrowserConfig, StealthConfig, ExtensionSpec) |
| `~/.hermes/screenshots/` | Screenshots dir | All screenshots saved here with timestamp |

## CloakBrowser Import Pattern

```python
import sys, os
os.environ.setdefault('DISPLAY', ':99')
sys.path.insert(0, os.path.expanduser('~/mona-workspace/skills/browser-agent/scripts'))

from browser_engine import BrowserAgent, BrowserConfig, StealthConfig, ExtensionSpec
```

**CRITICAL:** CloakBrowser binary is installed for `python3.12`, not system `python3.11`. Always use `python3.12` for browser automation scripts.

## Topic Integration

### Twitter Commands → Topic 💎 Alpha (ID: 13)

```
twitter follow [username]     — Auto-follow user
twitter like [tweet_url]      — Auto-like tweet
twitter rt [tweet_url]        — Auto-retweet
twitter reply [url] [text]    — Auto-reply
twitter bookmark [tweet_url]  — Auto-bookmark
twitter cookies               — Show cookie status
twitter screenshot            — Latest screenshot
```

### dApp Commands → Topic ⭐️ NFT Mint (ID: 14)

```
dapp connect [url]            — Connect MetaMask to dApp
dapp screenshot               — Latest screenshot
```

### Airdrop Website Commands → Topic 📣 List Airdrop (ID: 11)

```
browse [url]                  — Open airdrop website
click [text/selector]         — Click button
isi [selector] [value]        — Fill form field
screenshot                    — Take screenshot
```

## MetaMask v13 Compatibility

**CRITICAL:** MetaMask v13 SPA doesn't render in CloakBrowser with stealth enabled. Use `cloaking=False`:

```python
cfg = BrowserConfig(
    headless=False,
    cloaking=False,  # ← REQUIRED for MetaMask v13
    extensions=[ExtensionSpec.from_webstore('nkbihfbeogaeaoehlefnkodbefgpgknn', name='MetaMask')],
)
```

**popup-init.html timeout fix:** MetaMask v13's `popup-init.html` never fires `load` event. Use route interception:

```python
ctx = b._context()
async def intercept(route):
    if 'popup-init' in route.request.url:
        await route.continue_(url=route.request.url.replace('popup-init.html', 'home.html'))
    else:
        await route.continue_()
await ctx.route('**/popup-init.html', intercept)
```

## Async Execution Pattern

Bot commands run in sync context but browser automation is async. Use this pattern:

```python
import asyncio, concurrent.futures

def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        else:
            return asyncio.run(coro)
    except RuntimeError:
        return asyncio.run(coro)

# Usage:
result = run_async(some_async_function())
```

## Screenshot Management

All screenshots saved to `~/.hermes/screenshots/` with pattern:
```
{type}_{action}_{timestamp}.png
```

Types: `twitter_`, `dapp_`, `airdrop_`

Cleanup old screenshots (>7 days):
```python
from mona_browser import ScreenshotManager
ScreenshotManager.cleanup(days=7)
```

## Pitfalls

- **DISPLAY=:99 required.** Xvfb must be running. Check: `ps aux | grep Xvfb`. Start: `Xvfb :99 -screen 0 1920x1080x24 &`
- **python3.12 for CloakBrowser.** System python3 is 3.11 — CloakBrowser binary installed for 3.12.
- **cloaking=True for airdrop sites.** Use stealth for sites that block headless. Use `cloaking=False` only for MetaMask/dApp interaction.
- **Twitter cookies not yet available.** User needs to provide `auth_token` + `ct0` from browser DevTools → Application → Cookies → x.com. Until then, Twitter commands will fail.
- **Async in sync context.** Bot handlers are sync. Browser automation is async. Use `run_async()` wrapper. Don't call `asyncio.run()` inside an already-running loop.
- **Long-running browser tasks block the bot.** Browser operations take 10-30 seconds. During this time, the bot can't process other messages. Consider threading or background execution for production use.
- **Screenshot files accumulate.** Set up a cron job or manual cleanup to delete screenshots older than 7 days.
