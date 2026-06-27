# Browser Automation + Telegram Bot Integration

Pattern for integrating CloakBrowser automation with a Telegram forum bot.

## Architecture

```
Telegram Topic (user command)
    ↓
Bot Handler (sync context)
    ↓
Browser Commands Module (detects browser commands)
    ↓
run_async() wrapper (sync → async bridge)
    ↓
CloakBrowser (async Playwright)
    ↓
Screenshot → send to Telegram topic
```

## Key Pattern: Sync → Async Bridge

Telegram bot handlers are sync (long-polling). CloakBrowser is async (Playwright). Bridge:

```python
def run_async(coro):
    """Run async function in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        else:
            return asyncio.run(coro)
    except RuntimeError:
        return asyncio.run(coro)
```

## Command → Topic Mapping

| Commands | Topic | Handler |
|----------|-------|---------|
| `twitter follow/like/rt/reply/bookmark` | 💎 Alpha | `handle_twitter_command()` |
| `dapp connect [url]` | ⭐️ NFT Mint | `handle_dapp_command()` |
| `browse [url]`, `click [target]`, `isi [selector] [value]` | 📣 Airdrop | `handle_airdrop_browser_command()` |

## Integration Steps

1. Create `mona_browser.py` — Core engine with `TwitterAutomation`, `DappAutomation`, `AirdropAutomation` classes
2. Create `mona_browser_commands.py` — Bot command handlers with `is_twitter_command()`, `handle_twitter_command()`, etc.
3. In bot handlers, add delegation at the top:

```python
def handle_alpha(text, user):
    # Check for Twitter commands first
    from mona_browser_commands import is_twitter_command, handle_twitter_command
    if is_twitter_command(text):
        handle_twitter_command(text, user)
        return
    # ... rest of alpha handler
```

4. Add to smart router's `detect_intent()`:

```python
if text_lower.startswith('twitter ') or text_lower in ('/twitter', 'twitter help'):
    return TOPIC_ALPHA
```

## Screenshot Management

Screenshots go to `~/.hermes/screenshots/`. Naming: `{context}_{action}_{timestamp}.png`

```python
from mona_browser import ScreenshotManager

# List recent
screenshots = ScreenshotManager.list_screenshots(limit=10)

# Send to Telegram
path = os.path.join(SCREENSHOTS_DIR, screenshots[0])
send_message(TOPIC_ALPHA, f"📸 Screenshot:\nMEDIA:{path}")

# Cleanup old (>7 days)
deleted = ScreenshotManager.cleanup(days=7)
```

## Pitfalls

- **CloakBrowser must use `python3.12`** — System python3 is 3.11 with PEP 668 lock.
- **DISPLAY=:99 must be set** — Xvfb must be running.
- **MetaMask v13 needs `cloaking=False`** — Stealth patches conflict with MetaMask's SPA renderer.
- **Twitter SPA needs `wait_until='commit'`** — Not `'load'` (never fires reliably).
- **Async context issues** — Don't call `asyncio.run()` inside an already-running event loop. Use the `run_async()` wrapper.
- **Screenshots are local files** — Use `MEDIA:/absolute/path` to send via Telegram, not URLs.
