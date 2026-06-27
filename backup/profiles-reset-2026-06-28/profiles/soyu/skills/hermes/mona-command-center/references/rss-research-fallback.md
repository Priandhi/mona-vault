# RSS-Based Research Fallback Pattern

When building cron jobs that need web research (daily digests, news monitoring, alpha intel), the primary data source chain often fails:

1. `web_search` → Brave API returns HTTP 402 (quota exhausted)
2. `web_extract` → Needs non-Brave backend (firecrawl/tavily/exa), often unconfigured
3. `browser_navigate` to Google → CAPTCHA / bot detection
4. `browser_navigate` to DuckDuckGo → CAPTCHA challenge

**Reliable fallback: curl RSS feeds directly.**

## Verified Working RSS Endpoints (No Auth Required)

| Source | RSS URL | Content |
|--------|---------|---------|
| CoinDesk | `https://www.coindesk.com/arc/outboundfeeds/rss/` | BTC, ETH, DeFi, regulation, TradFi×crypto |
| Decrypt | `https://decrypt.co/feed` | Crypto, AI, NFT, regulation |
| Cointelegraph | `https://cointelegraph.com/rss` | Markets, analysis, DeFi, regulation |
| CoinDesk (tag) | `https://www.coindesk.com/arc/outboundfeeds/rss/?tag=defi` | DeFi-specific filtered |

**NOT working (Cloudflare/blocked):**
- TheBlock → Cloudflare challenge page
- Blockworks → Returns empty/minimal
- DLNews → Inconsistent

## Implementation Pattern

```python
from hermes_tools import terminal
import re

def fetch_rss(url, max_items=20):
    """Fetch RSS feed and extract titles + links + dates."""
    r = terminal(f'curl -sL --max-time 15 "{url}" | grep -E "<title>|<link>|<pubDate>" | head -80', timeout=20)
    raw = r.get("output", "")
    
    items = []
    # Parse RSS XML with regex (lightweight, no lxml dependency)
    title_pattern = re.compile(r'<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>')
    link_pattern = re.compile(r'<link[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>')
    date_pattern = re.compile(r'<pubDate>(.*?)</pubDate>')
    
    titles = title_pattern.findall(raw)
    links = link_pattern.findall(raw)
    dates = date_pattern.findall(raw)
    
    # Skip first 2 entries (channel title + link)
    titles = titles[2:]
    links = links[2:]
    
    for i in range(min(len(titles), len(links), max_items)):
        items.append({
            "title": titles[i].strip(),
            "url": links[i].strip(),
            "date": dates[i].strip() if i < len(dates) else "",
        })
    
    return items
```

## Cron Job Template

```yaml
action: create
name: "Daily Research Digest"
schedule: "every 24h"
deliver: "telegram:<chat_id>:<topic_id>"
prompt: |
  Research task:
  1. Fetch RSS from CoinDesk, Decrypt, Cointelegraph via curl
  2. Filter for last 24h articles
  3. Pick 5-10 most interesting/innovative stories
  4. Format as concise research report with links
  5. Focus on what's NEW and ACTIONABLE
  6. Output the report as your final response
```

## PITFALL: Cron Auto-Delivery vs `hermes send`

When a cron job has `deliver:` configured, `hermes send` to the SAME target is blocked by the system with message: "This cron job will already auto-deliver its final response to that same target."

**Solution**: Don't use `hermes send` in cron jobs with `deliver:` configured. Just output the content as your final response — the system handles delivery automatically.

If you need to send to a DIFFERENT target (not the cron's delivery target), `hermes send` works fine.

## Multi-Source Aggregation Pattern

Best results come from combining multiple RSS feeds:

```python
sources = [
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Decrypt", "https://decrypt.co/feed"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
]

all_items = []
for name, url in sources:
    items = fetch_rss(url)
    for item in items:
        item["source"] = name
    all_items.extend(items)

# Deduplicate by URL
seen = set()
unique = []
for item in all_items:
    if item["url"] not in seen:
        seen.add(item["url"])
        unique.append(item)

# Sort by date (most recent first)
unique.sort(key=lambda x: x["date"], reverse=True)
```

## Filtering for Specific Topics

RSS feeds don't support topic filtering natively (except CoinDesk tag feeds). To filter:

1. Fetch all items from a feed
2. Filter by title/description keywords
3. CoinDesk supports tag-based feeds: `?tag=defi`, `?tag=bitcoin`, `?tag=nft`

```python
def filter_by_keywords(items, keywords):
    """Filter items whose title contains any keyword (case-insensitive)."""
    return [
        item for item in items
        if any(kw.lower() in item["title"].lower() for kw in keywords)
    ]
```
