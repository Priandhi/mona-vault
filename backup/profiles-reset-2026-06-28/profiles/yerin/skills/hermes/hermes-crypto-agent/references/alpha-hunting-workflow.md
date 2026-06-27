# Alpha Hunting — New Project Discovery Workflow

Workflow untuk cron job "Alpha Hunter" yang scan new projects across all chains. Berbeda dari token scanning (known CA → data) — ini discovery: finding NEW projects sebelum orang lain tahu.

## Execution order (fallback chain)

Priority turun — stop di step pertama yang return data bagus:

### Step 1: Terminal API calls (PREFERRED — fast, no auth needed)

Jangan buang waktu dengan web_search atau browser. Langsung ke API:

```bash
# DeFiLlama — new protocols (listedAt field, last 7 days)
curl -s "https://api.llama.fi/protocols" | python3 -c "
import json, sys, time, datetime
data = json.load(sys.stdin)
now = time.time()
for p in data:
    listed = p.get('listedAt', 0)
    if listed and (now - listed) < 7*24*3600:
        tvl = p.get('tvl') or 0
        print(f'{p.get(\"name\")} | {p.get(\"chain\")} | {p.get(\"category\")} | TVL: \${tvl:,.0f} | {datetime.datetime.fromtimestamp(listed).strftime(\"%Y-%m-%d\")} | Twitter: {p.get(\"twitter\",\"N/A\")} | URL: {p.get(\"url\",\"N/A\")}')
"

# DexScreener — latest token profiles (has descriptions + links)
curl -s "https://api.dexscreener.com/token-profiles/latest/v1"

# DexScreener — BOOSTED tokens (trending, actively promoted)
curl -s "https://api.dexscreener.com/token-boosts/latest/v1"
# Returns 30 tokens with boost info — good for finding trending tokens
# Fields: chainId, tokenAddress, description, icon, url

# DexScreener — single token deep details
curl -s "https://api.dexscreener.com/tokens/v1/{chain_id}/{token_address}"
# Returns array of pairs with full liquidity/volume/price data | python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data:
    desc = item.get('description', '')
    if desc and len(desc) > 30:
        links = [l.get('url','') for l in item.get('links',[]) if l.get('url')]
        print(f'{item.get(\"chainId\",\"?\").upper()} | {item.get(\"tokenAddress\",\"?\")[:20]}... | {desc[:150]} | Links: {links[:3]}')
"

# CoinGecko — trending (catch momentum shifts)
curl -s "https://api.coingecko.com/api/v3/search/trending" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for c in data.get('coins', []):
    item = c.get('item', {})
    print(f'{item.get(\"name\")} ({item.get(\"symbol\")}) - Rank: {item.get(\"market_cap_rank\")} - Score: {item.get(\"score\")}')
"
```

### Step 2: Direct curl to news sites (for news-based discovery)

When `web_search` is down (HTTP 402) and you need news about new launches, partnerships, or protocol updates:

```bash
# Cointelegraph — latest crypto news
curl -sL 'https://cointelegraph.com/' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
  2>/dev/null | grep -oP 'href="/news/[^"]+' | sort -u | head -15

# Filter by topic: tags/defi, tags/nft, tags/ai
curl -sL 'https://cointelegraph.com/tags/defi' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
  2>/dev/null | grep -oP 'href="/news/[^"]+' | sort -u | head -10

# Get article details
curl -sL "https://cointelegraph.com/news/{SLUG}" -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
  2>/dev/null | grep -oP '(?<=<meta name="description" content=")[^"]+|(?<=<meta property="og:title" content=")[^"]+' | head -2
```

Also works: `decrypt.co/news`, `coindesk.com`. See `references/news-site-scraping.md` for full recipes.

### Step 3: Browser (USELESS — skip it)

Most crypto sites block browser automation with Cloudflare:
- ❌ coingecko.com — "Verifying you are human"
- ❌ dexscreener.com — "Performing security verification"
- ❌ dextools.io — "Sorry, you have been blocked"
- ❌ birdeye.so — Cloudflare challenge
- ❌ theblock.co — Cloudflare block
- ❌ google.com — CAPTCHA/sorry page
- ❌ duckduckgo.com — "bots use DuckDuckGo too" CAPTCHA

Browser tool is essentially useless for crypto discovery. **BUT: direct `curl` to news sites works** (Step 2 above). The browser tool's Playwright/Chromium triggers bot detection, while plain `curl` with a User-Agent header does not for most news sites.

### Step 4: RSS feeds (fallback for news)

```bash
# Decrypt RSS
curl -sL "https://decrypt.co/feed" | python3 -c "
import sys, re
content = sys.stdin.read()
titles = re.findall(r'<title>(.*?)</title>', content)
for t in titles[:15]: print(t)
"

# CoinDesk RSS
curl -sL "https://www.coindesk.com/arc/outboundfeeds/rss/" | python3 -c "
import sys, re
content = sys.stdin.read()
items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
for item in items[:10]:
    title = re.search(r'<title>(.*?)</title>', item)
    link = re.search(r'<link>(.*?)</link>', item)
    if title and link: print(f'{title.group(1)} | {link.group(1)}')
"
```

### Step 5: Binance new listings (for CEX alpha)

```bash
curl -sL "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&catalogId=48&pageNo=1&pageSize=10" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for a in data.get('data',{}).get('catalogs',[{}])[0].get('articles',[]):
    print(a.get('title','?'))
"
```

## Quality filter (CRITICAL)

Jangan spam Telegram dengan mediocre finds. Filter KETAT:

| Signal | Threshold | Action |
|--------|-----------|--------|
| TVL = $0 | Noise | SKIP unless project has working product + active socials |
| TVL < $1K | Very early | Only report if backed by known team/fund |
| TVL $1K-$100K | Early | Report if interesting category + working URL |
| TVL > $100K | Promising | Report |
| No Twitter/social | Suspect | SKIP |
| URL returns 404/timeout | Dead | SKIP |
| Only on pump.fun | Meme | Only report if viral ($100K+ volume, trending) |
| Established token (BTC, ETH, SOL, DOGE, PEPE) | Not alpha | SKIP always |

**Rule: Max 3 per chain. Quality over quantity.**

### Smart Scanner Quality Score System (DexScreener)

When using DexScreener boosted tokens API, apply quality scoring:

| Criteria | Points | Threshold |
|----------|--------|-----------|
| Liquidity > $10K | +2 | Minimum to report |
| Volume 24h > $5K | +2 | Minimum to report |
| Token age < 72h | +1 | New token bonus |
| Positive 24h change | +1 | Momentum signal |

**Minimum score to report: 3/5** (must have liquidity + volume)

Files:
- `~/.hermes/scripts/mona_alpha_scanner_smart.py` — Smart scanner with DexScreener + quality filters
- `~/.hermes/scripts/mona_token_analyzer.py` — Deep on-chain analysis (deployer, launchpad, safety)

## DeFiLlama protocol detail lookup

After finding a promising protocol, get more detail:

```bash
curl -s "https://api.llama.fi/protocol/{slug}" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Name: {data.get(\"name\")}')
print(f'Desc: {data.get(\"description\",\"\")[:300]}')
print(f'Chain: {data.get(\"chain\")} | Chains: {data.get(\"chains\",[])}')
print(f'Category: {data.get(\"category\")}')
print(f'Twitter: {data.get(\"twitter\",\"N/A\")}')
print(f'URL: {data.get(\"url\",\"N/A\")}')
print(f'Audits: {data.get(\"audits\",\"N/A\")}')
print(f'Audit links: {data.get(\"audit_links\",[])}')
"
```

## Deduplication — alpha_seen.json

File: `~/.hermes/scripts/.alpha_seen.json`

Structure:
```json
{
  "seen_urls": ["url1", "url2", ...],
  "seen_titles": ["title1", "title2", ...],
  "last_updated": "ISO timestamp",
  "last_scan": "ISO timestamp"
}
```

**Pitfall: File corruption.** The file can get concatenated duplicate JSON objects (two `{...}` blocks back-to-back). Parse with brace counting:

```python
with open(path, 'r') as f:
    content = f.read()
brace_count = 0
end_pos = 0
for i, c in enumerate(content):
    if c == '{': brace_count += 1
    elif c == '}': brace_count -= 1
    if brace_count == 0 and i > 0:
        end_pos = i + 1
        break
seen = json.loads(content[:end_pos])
```

## Telegram delivery format

```
🔷 ETHEREUM
━━━━━━━━━━━
🔹 Project Name — One-line description
   📊 TVL: $X | Chain: ETH | Category: DeFi
   🔗 Website | Twitter | Discord

🔵 BASE
━━━━━━━━━━━
🔹 Project Name — One-line description
   ...
```

Chain emojis: 🔷ETH 🔵BASE 🟣SOL 🟡BSC 🔶ARB 🔴OP 🟢AVAX 💎SUI 🅰️APTOS 🔵TON 🐻BERA ⚡HL

## Cron job config

```
schedule: every 20 minutes
target: telegram:-1003899936547:13 (Alpha topic)
no_agent: false (needs web_search + terminal + reasoning)
```

If genuinely nothing new: respond "No new alpha this round" (DO NOT send empty message to Telegram).
