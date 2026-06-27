# Clean Alpha Alert Format — Implementation Reference

## Module: `mona_alpha_alert_clean.py`

Separate module (NOT inline in watcher) with 3 format functions + helper utilities.

### Functions
- `format_clean_alert(token_data, whale_info=None, security=None, social=None, fee_recipient=None, deployer_info=None)`
- `format_multi_whale_clean(token_data, whale_list, security=None, deployer_info=None)`
- `format_sell_alert_clean(token_data, whale_info, sell_amount, sell_value_usd, pnl_pct=0, pnl_usd=0)`

### Key Helpers
- `fmt_mc(val)` — format market cap ($1.2M, $50K, $500)
- `fmt_vol(val)` — format volume
- `fmt_pct(val)` — format percentage with sign
- `fmt_age(hours)` — format age (5m, 2h, 1d)
- `shorten_addr(addr, chars=4)` — `0x1234…abcd`
- `get_launchpad_info(token_data)` — detect launchpad from dex_id
- `_make_link(text, url)` — Telegram HTML `<a href>` link

### Deployer Info Construction (in watcher)
```python
from mona_alpha_alert_clean import format_clean_alert, format_multi_whale_clean
from mona_telegram import send_message, TOPIC_ALPHA

deployer_info = None
if social_ctx and social_ctx.get("deployer") and social_ctx["deployer"].get("address"):
    dep = social_ctx["deployer"]
    deployer_info = {"address": dep["address"]}
    if dep.get("twitter"):
        deployer_info["twitter"] = f"https://twitter.com/{dep['twitter']}" if not dep["twitter"].startswith("http") else dep["twitter"]
    deployer_info["debank"] = f"https://debank.com/profile/{dep['address']}"

msg = format_clean_alert(td, w, security, deployer_info=deployer_info)
send_message(TOPIC_ALPHA, msg)  # HTML parse_mode by default
```

### Clickable HTML Links
All links use Telegram HTML `<a href>` with `parse_mode="HTML"`.

**Link targets by field:**
| Field | URL Target | Display Text |
|---|---|---|
| CA | `https://basescan.org/address/{ca}` | `0x1234…abcd` (shortened) |
| Dev address | `https://debank.com/profile/{addr}` | `0x1234…abcd` (shortened) |
| Dev Twitter | `https://twitter.com/{handle}` | handle only (no URL) |
| Chart | DexScreener URL from enrichment | `📊 Chart` |
| X (project) | Twitter URL from enrichment | `🐦 X` |
| Scan | Same as CA link | `🔍 Scan` |
| Whale (multi) | `https://debank.com/profile/{addr}` | `0x1234…abcd` (shortened) |
| Fee recipient | `https://debank.com/profile/{addr}` | `0x1234…abcd` (shortened) |

**Implementation:**
```python
def _link(text, url):
    """Create Telegram HTML link."""
    return f'<a href="{url}">{text}</a>'

# CA link (explorer-based)
explorer = "https://basescan.org" if chain == "BASE" else "https://etherscan.io"
ca_link = _link(ca_short, f"{explorer}/address/{ca}")

# Dev address link (DeBank)
addr_link = _link(addr_short, f"https://debank.com/profile/{dev_addr}")

# Twitter handle (strip URL prefix)
tw_handle = tw.replace("https://twitter.com/", "").replace("https://x.com/", "")
tw_link = _link(tw_handle, tw)
```

### Custom Emoji (Dropped)
Custom emoji from CryptachEmoji4 pack was attempted but dropped. The `mona_emoji.py` module still exists but is NOT used by the watcher. Use simple HTML links instead.

### Premium Emoji Module (Reference Only — NOT used)
Module `mona_emoji.py` contains:
- `CUSTOM_EMOJI` — dict mapping emoji → custom_emoji_id from CryptachEmoji4 pack (200 emoji)
- `EMOJI_SUBS` — substitution map for missing emoji
- `build_premium_message(lines)` → `{"text": str, "entities": list}`

`send_premium_message()` in `mona_telegram.py` uses JSON body for entities support. Both are kept for reference but not actively used.

### Telegram HTML Link Pattern
```python
def _link(text, url):
    """Create Telegram HTML link."""
    return f'<a href="{url}">{text}</a>'
```

**Display text conventions:**
- Strip `https://` from URLs: `twitter.com/devhandle` not `https://twitter.com/devhandle`
- Twitter shows handle only: `devhandle` not `twitter.com/devhandle`
- Addresses show shortened form: `0x1234…abcd` not full 42-char address
- Always include `🔍 Scan` link to explorer (BaseScan/Etherscan)
- Set `disable_web_page_preview: True` to avoid link preview clutter

### Launchpad Detection
```python
def get_launchpad_info(token_data):
    dex = token_data.get("dex_id", "")
    if "virtual" in dex: return "Virtuals Protocol"
    if "pump" in dex: return "Pump.fun"
    if "uniswap" in dex: return "Uniswap"
    if "aerodrome" in dex: return "Aerodrome"
    return None
```

## What NOT to include (user explicitly rejected)
- ❌ Risk scores (1-5)
- ❌ Whale holder heatmap
- ❌ Win rate per whale
- ❌ Entry/SL/TP
- ❌ Verbose separator lines (━━━)
- ❌ Whale tracking details
- ❌ "Spent/Got" swap details
