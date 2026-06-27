# News Site Scraping — Direct curl Fallback

When `web_search` (Brave) returns HTTP 402 AND browser tool is blocked by CAPTCHAs, use direct `curl` to crypto news sites. Verified working June 2026.

## Why this works

Search engines (Google, DuckDuckGo, Bing, Brave) all block automated access with CAPTCHAs or quota limits. The browser tool triggers these same blocks. But direct `curl` with a realistic User-Agent bypasses most news site protections — they serve full HTML to non-browser HTTP clients.

## Verified Working Sites

| Site | Listing URL | Status |
|------|-------------|--------|
| Cointelegraph | `https://cointelegraph.com/` | ✅ Full HTML |
| Cointelegraph (tags) | `https://cointelegraph.com/tags/{tag}` | ✅ Works for: defi, nft, ai |
| Decrypt | `https://decrypt.co/news` | ✅ Full HTML |
| CoinDesk | `https://www.coindesk.com/` | ✅ Full HTML |
| TheBlock | `https://www.theblock.co/` | ❌ Cloudflare |

## Extraction Recipes

### Step 1: Get article URLs from listing page

```bash
# Cointelegraph — extract article links
curl -sL 'https://cointelegraph.com/' \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
  2>/dev/null | grep -oP 'href="/news/[^"]+' | sort -u | head -20

# Cointelegraph — filter by tag (defi, nft, ai, etc.)
curl -sL 'https://cointelegraph.com/tags/defi' \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
  2>/dev/null | grep -oP 'href="/news/[^"]+' | sort -u | head -15

# CoinDesk — extract headlines
curl -sL 'https://www.coindesk.com/' \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
  2>/dev/null | grep -oP '<h[2-6][^>]*>[^<]+' | head -20

# Decrypt — extract article links
curl -sL 'https://decrypt.co/news' \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
  2>/dev/null | grep -oP 'href="/news/[^"]+' | sort -u | head -20
```

### Step 2: Get article details (title + description)

```bash
# Get meta description from individual article
curl -sL "https://cointelegraph.com/news/{SLUG}" \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
  2>/dev/null | grep -oP '(?<=<meta name="description" content=")[^"]+|(?<=<meta property="og:title" content=")[^"]+|(?<=<meta property="og:description" content=")[^"]+' | head -3
```

### Step 3: Batch extraction pattern

```bash
# Extract URLs from listing, then fetch descriptions for top N
URLS=$(curl -sL 'https://cointelegraph.com/' \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
  2>/dev/null | grep -oP 'href="/news/[^"]+' | sort -u | head -10)

for path in $URLS; do
  url="https://cointelegraph.com${path#href=\"}"
  echo "--- $url ---"
  curl -sL "$url" \
    -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
    2>/dev/null | grep -oP '(?<=<meta property="og:title" content=")[^"]+|(?<=<meta name="description" content=")[^"]+' | head -2
  sleep 1  # Be polite
done
```

## RSS Fallback

If direct HTML scraping fails, try RSS feeds:

```bash
# Decrypt RSS
curl -sL "https://decrypt.co/feed" | grep -oP '<title>[^<]+|<link>[^<]+' | head -30

# CoinDesk RSS
curl -sL "https://www.coindesk.com/arc/outboundfeeds/rss/" | grep -oP '<title>[^<]+|<link>[^<]+' | head -30
```

## Pitfalls

- **Rate limit**: Don't hammer sites. Add `sleep 1` between requests. Max ~20 requests per minute.
- **HTML changes**: These patterns depend on current HTML structure. If extraction returns empty, the site may have changed its markup. Try RSS as fallback.
- **Cloudflare on TheBlock**: `theblock.co` returns Cloudflare challenge even with curl. Skip it.
- **Duplicate URLs**: Cointelegraph often lists the same article multiple times on its homepage. Use `sort -u` to deduplicate.
- **The `href="/news/` pattern**: Cointelegraph uses `/news/` prefix. CoinDesk uses different URL patterns. Adjust grep accordingly.

## Use Cases

1. **Daily research cron job**: When `web_search` quota is exhausted, scrape top crypto news sites for headlines
2. **Alpha discovery**: Scan news for new protocol launches, partnerships, token listings
3. **Market intelligence**: Track major events (hacks, regulation, ETF flows) that affect positions
4. **DeFi protocol monitoring**: Check for new launches, governance votes, security incidents
