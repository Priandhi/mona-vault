# Clickable HTML Links in Telegram Alerts

## Core Helper
```python
def _link(text, url):
    """Create Telegram HTML link."""
    return f'<a href="{url}">{text}</a>'
```

## Link Targets by Field

| Field | URL Template | Display Text |
|---|---|---|
| Contract Address | `{explorer}/address/{ca}` | `0x1234…abcd` |
| Dev/Deployer | `https://debank.com/profile/{addr}` | `0x1234…abcd` |
| Dev Twitter | `https://twitter.com/{handle}` | handle only |
| Project Chart | DexScreener URL from enrichment | `📊 Chart` |
| Project X | Twitter URL from enrichment | `🐦 X` |
| Explorer Scan | `{explorer}/address/{ca}` | `🔍 Scan` |
| Whale address | `https://debank.com/profile/{addr}` | `0x1234…abcd` |
| Fee recipient | `https://debank.com/profile/{addr}` | `0x1234…abcd` |

## Explorer Selection
```python
explorer = "https://basescan.org" if chain == "BASE" else "https://etherscan.io"
```

## Display Text Conventions
- **Strip `https://`** from URL display: `twitter.com/devhandle` not `https://twitter.com/devhandle`
- **Twitter shows handle only**: `devhandle` not `twitter.com/devhandle` and not full URL
- **Addresses shortened**: `0x1234…abcd` (first 6 + last 4 chars)
- **Always add `🔍 Scan`** link to explorer (even if redundant with CA — user expects it)

## Implementation in Alert Functions
```python
# In format_clean_alert():
if ca:
    ca_link = _link(ca_short, f"{explorer}/address/{ca}")
    lines.append(f"📄 CA: {ca_link}")

if dev_addr:
    debank_url = dev.get("debank") or f"https://debank.com/profile/{dev_addr}"
    addr_link = _link(shorten_addr(dev_addr), debank_url)
    lines.append(f"👨‍💻 Dev: {addr_link}")
    
    tw = dev.get("twitter")
    if tw:
        tw_handle = tw.replace("https://twitter.com/", "").replace("https://x.com/", "")
        lines.append(f"   🐦 {_link(tw_handle, tw)}")

# Bottom links
links = []
if dex_url: links.append(_link("📊 Chart", dex_url))
if tw_url: links.append(_link("🐦 X", tw_url))
if ca: links.append(_link("🔍 Scan", f"{explorer}/address/{ca}"))
if links: lines.append(" · ".join(links))
```

## Pitfalls
- `parse_mode="HTML"` must be set (default in `send_message()`)
- HTML special chars in token names (Chinese, emojis) can break parsing — use `_sanitize_html()`
- Set `disable_web_page_preview=True` to avoid link preview clutter
- If HTML parsing fails, `send_message()` retries without parse_mode as fallback
