# Web-Search Alpha Hunter

Alternative alpha discovery method to whale/KOL tracking. Searches the open web for new token launches, TGEs, and protocol launches across all chains.

## When to Use

- Cron job running alpha scan (every ~20 min)
- User asks "find new crypto projects" or "what's launching today"
- Complement to on-chain whale tracking (different signal source)

## Search Strategy (Parallel)

**⚠️ CRITICAL FIRST STEP: Always call DeFiLlama + CoinGecko Trending BEFORE any web_search queries.** web_search frequently returns HTTP 402 in cron runs. Don't waste the first minutes on queries that will fail — hit the structured APIs immediately, then try web_search in parallel. This is the #1 lesson from repeated cron failures.

Run these queries simultaneously via `web_search`:

1. `"crypto new token launch today"` — fresh listings
2. `"new crypto project alpha gem 2026"` — curated alpha finds
3. `"DeFi new protocol launch today"` — protocol launches
4. `"new NFT project mint 2026"` — NFT drops
5. `"DePIN mining project new"` — infrastructure plays

If initial results are thin, run secondary queries:
- `"new token listing dexscreener trending solana ethereum base"`
- `"[chain_name] new project launch token"`
- `"TGE token generation event June 2026"`
- `"new DeFi protocol mainnet launch token generation event"`

## Source Fallback Hierarchy

When `web_search` returns HTTP 402 (rate limited) AND `web_extract` fails (no firecrawl backend), use this priority order:

### Tier 1: Structured APIs (no browser, no auth, fast)

1. **DeFiLlama Protocols API** — `curl https://api.llama.fi/protocols` returns ALL protocols with `listedAt` timestamp, TVL, chains, category. Filter by `listedAt > (now - 14 days)` and `tvl > 10000` to find recently listed protocols with real TVL. **Best structured source for new DeFi protocol discovery.** Also works for individual protocol details: `curl https://api.llama.fi/protocol/{slug}` returns description, URL, Twitter, chain breakdown, TVL history, audit info, and per-token TVL breakdown (WHYPE, USDC, etc.).
2. **CoinGecko Trending API** — `curl https://api.coingecko.com/api/v3/search/trending` returns currently trending tokens. Good for finding tokens with momentum that may be new launches. Filter out established tokens (BTC, ETH, SOL, etc.) to isolate genuinely new/emerging entries.
3. **CoinGecko Coin Detail API** — `curl https://api.coingecko.com/api/v3/coins/{id}?localization=false&tickers=false&market_data=true&community_data=true` for full details: price, mcap, FDV, description, socials (`links.twitter_screen_name`, `links.telegram_channel_identifier`, `links.homepage[0]`), categories, sentiment votes, ATH/ATL. Rate limited (~10-15 calls/session).
4. **DexScreener Latest Token Profiles** — `curl https://api.dexscreener.com/token-profiles/latest/v1` returns ~30 most recent token profiles with chainId, tokenAddress, description, and links[] (twitter, discord, telegram, website). **No auth needed, no rate limit observed.** Best for discovering brand-new tokens that just got profile pages on DEXes. Pair with DexScreener detail API for price/volume data. **⚠️ Quality warning (June 2026)**: The vast majority (~90%) are pump.fun Solana memecoins with no substance. Filter aggressively: require description > 30 chars AND at least one non-meme link (website or twitter with real content). Most entries have empty descriptions or joke text. Cross-reference with DeFiLlama/CoinGecko to find the rare legitimate project.
5. **DexScreener Token Detail** — `curl https://api.dexscreener.com/latest/dex/tokens/{CA}` returns pairs[] with priceUsd, volume.h24, liquidity.usd, marketCap, fdv, pairCreatedAt. Use to verify tokens found via other sources.
6. **GeckoTerminal REST API** — `https://api.geckoterminal.com/api/v2/`. No auth, no rate limits observed. Key endpoints: `networks/{chain}/new_pools?page=1` (brand new pools per chain), `networks/{chain}/trending_pools?page=1` (trending per chain), `search/pools?query={term}` (search). Chain slugs: `eth`, `solana`, `base`, `bsc`, `arbitrum`, `optimism`, `polygon_pos`. Returns pool data with `volume_usd.h24`, `fdv_usd`, `price_change_percentage.h24`, `transactions.h24.buys/sells`, `pool_created_at`, and `relationships.base_token.data.id` (token address). **Best for finding brand-new pools by chain with volume/transaction filtering.** Full API examples in skill `alpha-hunter-new-token-discovery/references/api-examples.md`.
7. **Pump.fun Trending** — `curl https://frontend-api-v3.pump.fun/coins/currently-live?limit=20&offset=0&sort=market_cap&order=DESC&includeNsfw=false` returns currently live tokens on Solana pump.fun with name, symbol, market_cap, created_timestamp. **Very early stage — quality filter aggressively.** Most are sub-$10K mCap memes. Useful for spotting viral Solana narratives.

**CoinGecko rate limiting**: ~10-15 calls before getting empty responses (not HTTP errors, just empty body). Mitigation: (1) Add 3s sleep between calls, (2) batch queries efficiently, (3) prioritize trending + search endpoints over bulk list, (4) if rate-limited, switch to DeFiLlama or browser sources.

### Tier 2: Browser-based sources (structured, reliable)

7. **CoinMarketCap New Listings** (`coinmarketcap.com/new/`) — `browser_navigate` + `browser_console` JS extraction. **Best browser source for new token discovery across ALL chains.** CMC renders a table of tokens added in the last 30 days with name, price, 24h change, FDV, volume, chain, and "added" timestamp. Extract all rows via JS:
   ```python
   browser_navigate("https://coinmarketcap.com/new/")
   browser_console(expression='''
       const rows = document.querySelectorAll('table tbody tr');
       const data = [];
       rows.forEach((row, i) => {
           const cells = row.querySelectorAll('td');
           if (cells.length >= 9) {
               data.push({
                   rank: i+1,
                   name: cells[2]?.textContent?.trim() || '',
                   price: cells[3]?.textContent?.trim() || '',
                   change24h: cells[5]?.textContent?.trim() || '',
                   fdv: cells[6]?.textContent?.trim() || '',
                   volume: cells[7]?.textContent?.trim() || '',
                   chain: cells[8]?.textContent?.trim() || '',
                   added: cells[9]?.textContent?.trim() || '',
                   link: cells[2]?.querySelector('a')?.href || ''
               });
           }
       });
       JSON.stringify(data, null, 2);
   ''')
   ```
   Returns structured JSON array of ~100 tokens. **Filter out**: stock derivatives ("(Derivatives)" in name OR "Own Blockchain" as chain), established tokens, and already-seen entries. Then research top candidates by visiting individual CMC pages for social links:
   ```python
   browser_navigate("https://coinmarketcap.com/currencies/{slug}/")
   browser_console(expression='''
       const links = document.querySelectorAll('a[href]');
       const socials = [];
       links.forEach(a => {
           const h = a.href;
           if (h && (h.includes('twitter.com') || h.includes('x.com') || h.includes('t.me') || h.includes('discord')))
               socials.push(h);
       });
       JSON.stringify(socials);
   ''')
   ```
   Use `delegate_task` to research 3-6 candidate pages in parallel (each gets its own browser session). **This pattern found 4 quality alpha entries (Chainspin, Zest Protocol, Citrea, Dropee) in a single June 2026 run where web_search was completely down.**

8. **ICO Drops** (`icodrops.com`) — `browser_navigate` + `browser_snapshot`. Always works, structured data with funding/VCs/dates.
9. **ICO Analytics** (`icoanalytics.org/token-generation-events/`) — `browser_navigate` + `browser_snapshot`. Table format with TGE dates, amounts, categories.
10. **Direct project sites** — `browser_navigate` to project URLs found in prior scans or search result descriptions.

### Tier 3: News/general (may have Cloudflare)

8. **CoinDesk / The Block** — `browser_navigate` for news articles (may have Cloudflare).
9. **CoinGecko browser** — `browser_navigate` for price/volume verification (Cloudflare blocks often).

### Confirmed blocked sites (don't retry)

DexScreener, DexTools, CoinGecko browser — all return Cloudflare challenges. Use their APIs instead (DexScreener API, CoinGecko API). DexScreener API endpoints work fine without authentication.

**Do NOT waste time on**: X/Twitter search (requires login), airdrops.io (403 block), nftcalendar.io (challenge), rootdata.com (CAPTCHA), theblock.co (Cloudflare "Sorry, you have been blocked"). These are confirmed unscrapable.

**Cloudflare pattern (June 2026 verified)**: coingecko.com ("Just a moment... Verifying you are human"), dexscreener.com ("Performing security verification"), theblock.co ("Sorry, you have been blocked"). All three return Cloudflare challenges even with stealth browser. Don't retry — use their APIs or alternative sources.

When ALL browser sources fail, output whatever data was collected from API endpoints and `web_search` result descriptions alone.

**Cron session lesson (June 5, 2026)**: DeFiLlama protocols API + CoinGecko APIs + DexScreener APIs together form a powerful discovery pipeline that requires no browser automation and no API keys. Found 5 genuinely new projects in a single run where web_search was completely down (HTTP 402 on all queries) and all browser targets were Cloudflare-blocked. DeFiLlama alone found 14 new protocols with >$100K TVL in the last 14 days. The combination of DeFiLlama (what's new), CoinGecko (market data + socials), and DexScreener (newest token profiles) covers the full discovery → detail → socials pipeline.

## Best Data Sources

| Source | URL | Why |
|--------|-----|-----|
| DeFiLlama Protocols | api.llama.fi/protocols | **Best structured source for new DeFi protocols.** Returns ALL protocols with `listedAt` timestamp, TVL, chains, category. Filter by recency + TVL threshold. No auth, no rate limit, fast. |
| DeFiLlama Protocol Detail | api.llama.fi/protocol/{slug} | Individual protocol details: description, URL, Twitter, chain TVL breakdown. Use slug from protocols list. |
| CoinGecko Trending | api.coingecko.com/api/v3/search/trending | Currently trending tokens. Good for momentum-based finds and new launches gaining attention. |
| CoinGecko Coin Detail | api.coingecko.com/api/v3/coins/{id} | Full details: price, mcap, FDV, socials (Twitter, Telegram, Discord), description, exchanges, contract address. Rate limited (~10-15 calls/session). |
| GeckoTerminal New Pools | api.geckoterminal.com/api/v2/networks/{chain}/new_pools | **Best for per-chain new pool discovery.** Volume, FDV, price change, txn counts, creation date. No auth, no rate limits. Chain slugs: eth, solana, base, bsc, arbitrum, optimism, polygon_pos. |
| GeckoTerminal Trending | api.geckoterminal.com/api/v2/networks/{chain}/trending_pools | Trending pools per chain. Good for momentum-based finds on specific ecosystems. |
| GeckoTerminal Search | api.geckoterminal.com/api/v2/search/pools?query={term} | Cross-chain token search. Returns multiple pools — pick highest volume. |
| PumpFun Token Info | frontend-api-v3.pump.fun/coins/{mint} | Solana token socials (twitter, telegram, website). Strip `solana_` prefix from GeckoTerminal token IDs. |
| ICO Drops | icodrops.com | **Best structured browser source.** Use `browser_navigate` (NOT `web_extract`) — returns clickable links with labels like "DeFi", "Airdrop", "Token Launch", dates, and funding amounts. |
| ICO Analytics | icoanalytics.org/token-generation-events/ | **Best structured TGE source.** Table format with columns: PROJECT (name + ticker), DATE, DETAILS (Sale/TGE/Product release), TOTAL ROUNDS, TOTAL RAISED, PROJECT CATEGORY tags. |
| Phemex News | phemex.com/news | Curated monthly crypto event calendars |
| CoinMarketCap New | coinmarketcap.com/new/ | **Best browser source for cross-chain new token discovery.** JS-rendered table with 100 tokens, 30-day window. Use browser_console JS extraction pattern (see Tier 2 #7). Filters: skip "Derivatives" and "Own Blockchain" chain entries. |
| Blockchain Reporter | blockchainreporter.net | Event roundups. **RSS feed available**: `curl -s "https://blockchainreporter.net/feed/"` returns XML with `<item>` elements containing `<title>`, `<link>`, `<pubDate>`. Parse with `xml.etree.ElementTree`. No auth, no browser needed. Good for catching breaking news about new launches. |
| CryptoPotato RSS | cryptopotato.com/feed/ | **Working RSS feed** (verified June 2026). Returns clean XML with `<title>`, `<link>`, `<description>`. Good for market sentiment and new project coverage. No auth, no browser. |
| Decrypt RSS | decrypt.co/feed/ | **Working RSS feed** (verified June 2026). Returns XML news items. Covers broader crypto/tech intersection. No auth, no browser. |
| CryptoRank | cryptorank.io/drophunting | Airdrop guides with dates |
| MEXC News | mexc.com/news | Curated monthly event roundups — "Crypto Market Prepares For Major Events" articles list exact TGE/mainnet dates for the month. |
| Airdrops.io | airdrops.io/latest/ | Active airdrop claims with deadlines — find tokens with live claim windows. Good for "airdrop deadline" narrative alpha. |

### DeFiLlama Protocols API Pattern

```bash
# Get all recently listed protocols with significant TVL
curl -sL "https://api.llama.fi/protocols" | python3 -c "
import json, sys
from datetime import datetime
data = json.load(sys.stdin)
now_ts = int(datetime.now().timestamp())
cutoff = now_ts - 14*86400  # last 14 days
recent = [p for p in data if p.get('listedAt', 0) and p['listedAt'] > cutoff and (p.get('tvl', 0) or 0) > 10000]
recent.sort(key=lambda x: x.get('tvl', 0) or 0, reverse=True)
for p in recent[:20]:
    chain = ', '.join(p.get('chains', []))
    tvl = p.get('tvl', 0) or 0
    dt = datetime.fromtimestamp(p['listedAt']).strftime('%Y-%m-%d')
    print(f'[{dt}] {p.get(\"name\")} | chains: {chain} | TVL: \${tvl:,.0f} | cat: {p.get(\"category\")}')
"
```

### CoinGecko API Pattern

```bash
# Trending tokens
curl -sL "https://api.coingecko.com/api/v3/search/trending"

# Search for project
curl -sL "https://api.coingecko.com/api/v3/search?query={name}"

# Full coin details (with socials)
curl -sL "https://api.coingecko.com/api/v3/coins/{id}?localization=false&tickers=false&market_data=true&community_data=true"

# Parse socials from coin detail
# links.twitter_screen_name, links.telegram_channel_identifier, links.homepage[0], links.official_forum_url
```

### ICO Drops Browser Pattern

ICO Drops is JS-heavy — `web_extract` returns empty. Use `browser_navigate` + `browser_snapshot`:

```
1. browser_navigate("https://icodrops.com/")
2. browser_snapshot(full=true)  → get all project links with labels
3. Parse ACTIVE section (currently live sales/farming)
4. Parse UPCOMING section (future TGEs with dates)
5. Each link has: project name, ticker, category (DeFi/DePIN/etc), status, funding amount
6. Click individual projects for details (social links, tokenomics)
```

The snapshot output format is: `link "ProjectName TICKER Category Status Details $XM Funding" [ref=eN]` — extract project name, ticker, category, and date from these labels.

## Chain-Specific Ecosystem Sources

When scanning for alpha, check chain-native ecosystems — these often have projects not yet on aggregators:

### Monad Ecosystem (Hot — June 2026)
- **Kuru** (`kuru.io`) — Fully on-chain orderbook DEX on Monad's parallel EVM (10K TPS). $2M seed. Tracked on DefiLlama. No TGE yet — early testnet positioning.
- **Nad.fun** (`nad.fun`) — Monad-native memecoin launchpad + social playground + AI agent trading. $200K hackathon (Feb 2026). Active token launches.
- **Satsuma** (`satsuma.exchange`) — DEX on Monad. TGE + airdrop claims. Orange Points system.
- **Kintsu** — Liquid staking on Monad.
- **Block Street** — On-chain financial infrastructure on Monad.
- **Perpl** (`perpl.xyz`) — Fully on-chain CLOB perpetual futures DEX on Monad. $9.25M raised (Brevan Howard, CMS Holdings, Dragonfly Capital). In incentivized activities phase, no TGE yet. High-quality backing makes this a strong watchlist candidate.
- Search: `"Monad ecosystem new project token"`, `"Monad mainnet DeFi"`

### Berachain Ecosystem
- **Boyco** — Pre-launch liquidity platform ($3.1B TVL at mainnet)
- Search: `"Berachain new protocol launch"`, `"Berachain ecosystem DeFi"`

### Base Ecosystem
- **Aerodrome Finance** — Central AMM/liquidity marketplace
- Search: `"Base chain new DeFi protocol"`, `"Base ecosystem token launch"`

### Sui Ecosystem
- **Hashi** — Bitcoin-native financial primitive on Sui devnet
- Search: `"Sui new project launch"`, `"Sui ecosystem DeFi"`

### DeFAI / Cross-Chain (Emerging Narrative)
- **Pheasant Network** (`home.pheasant.network`) — DeFAI protocol with AI-powered intent mechanism. $2M seed. Supports Ethereum + 30+ L2s. $200M+ cross-chain volume processed. Q2 2026 TGE for $PNT. Search: `"DeFAI new protocol launch"`, `"AI intent crypto cross-chain"`

## Filtering Pipeline

Multi-stage filtering to separate signal from noise:

1. **Collect** all raw results from primary + secondary queries (typically 60-100+)
2. **Dedup** against `~/.hermes/scripts/.alpha_seen.json` (url + title)
3. **Remove generic aggregators** — skip these domains entirely:
   - `coindesk.com/news/`, `cointelegraph.com/news/`, `decrypt.co/news/`, `theblock.co/news/`
   - `youtube.com`, `reddit.com`
   - These are news articles about crypto, NOT new project discoveries
4. **Remove established tokens** — skip if title contains:
   - `bitcoin`, `btc`, `ethereum price`, `solana price`, `dogecoin`, `pepe`, `shiba`
   - `cardano`, `ripple`, `xrp`, `bnb price`, `polkadot`, `chainlink`, `uniswap`, `aave price`, `lido`, `maker`
5. **URL dedup** within results (same URL from multiple queries)
6. **Quality gate**: Only include if:
   - Launched within days/weeks OR TGE imminent
   - Has active socials (Twitter, Discord, Telegram, website)
   - Looks promising (real utility, viral narrative, or institutional backing)
   - Max 3 per chain
   - **Existing token + major upgrade IS valid alpha**: If an already-listed token is shipping a significant new product/pivot (e.g. Boson Protocol pivoting to agentic commerce with x402B mainnet June 2026), that's worth reporting. Flag it as "existing token, major upgrade" so readers know it's not a new listing. The value is in the product catalyst, not the token novelty.
7. **Verify** via CoinGecko/CMC if possible (price, volume, market cap)

### Multi-Round Search Strategy

One round of searches often yields aggregator pages, not specific projects. Run 2-3 rounds:

- **Round 1** (5-8 queries): Broad discovery — "new token launch today", "DeFi new protocol", etc.
- **Round 2** (8-10 queries): Chain-specific + narrative-specific — "base chain new token", "berachain new protocol", "DePIN new project", "new memecoin launched today"
- **Round 3** (4-6 queries): Ultra-specific — "site:dexscreener.com new token", specific project names found in round 1-2, "new crypto presale [month] [year]"

**Round 2 deep-dive pattern**: After Round 1 yields project names from aggregators (ICO Drops, ICO Analytics), search each project individually for details:
```
"ProjectName TICKER crypto TGE 2026"
"ProjectName token launch details"
```
This fills in social links, exact dates, funding details, and chain info that aggregator listings omit. Verified effective for: Perpl (found Monad perp DEX details), Pheasant Network (found DeFAI + $200M cross-chain volume), o1 exchange (found AI DEX details).

Aggregate all rounds, then apply the full filtering pipeline.

### API-First Discovery Pattern (June 2026)

When web_search is down (HTTP 402), use API-first discovery:

1. **DeFiLlama** → find protocols listed in last 7-14 days with TVL > $10K
2. **DeFiLlama per-chain filter** → filter the same `/protocols` data by `chains` array for specific ecosystems (Berachain, Monad, Sui, etc.) to find chain-native launches
3. **GeckoTerminal** → `networks/{chain}/new_pools` for brand-new pools per chain, `networks/{chain}/trending_pools` for momentum. Filter by volume > $500, buys > 5. Extract token address from `relationships.base_token.data.id`, then use PumpFun API for Solana social links.
4. **CoinGecko Trending** → find tokens with momentum (check if any are new launches, filter out established tokens like BTC/ETH/SOL)
5. **DexScreener Latest Profiles** → `token-profiles/latest/v1` for brand-new tokens with social links already attached
6. **CoinGecko Coin Detail** → lookup each find for socials + market data
7. **Dedup** against seen file → filter out already-reported
8. **Quality gate** → only report genuinely promising finds (TVL > $100K preferred, active socials required, meaningful narrative)

This pattern found 5 new alpha entries (Huma Finance V2 $158M TVL, Hyperdrive HL Earn $382K, Ryze Protocol $312K, Turbo DEX $24K, Prodigy.Fi $15K) in a June 5 run with zero web_search calls. DeFiLlama provides the "what's new" signal, CoinGecko/DexScreener provides "is it tradeable + socials."

**Per-chain DeFiLlama filter pattern** (useful for finding ecosystem-specific launches):
```bash
curl -sL "https://api.llama.fi/protocols" | python3 -c "
import json, sys, time
data = json.load(sys.stdin)
now = time.time()
chain_new = [p for p in data if p.get('listedAt',0) and (now - p['listedAt']) < 14*86400 and 'Berachain' in p.get('chains',[])]
chain_new.sort(key=lambda x: x.get('tvl',0) or 0, reverse=True)
for p in chain_new[:10]:
    print(f\"{p['name']} | {p['category']} | TVL: \${p.get('tvl',0) or 0:,.0f}\")
"
```
Replace `'Berachain'` with `'Monad'`, `'Sui'`, `'Hyperliquid L1'`, etc.

## Report Format

```
🔍 **ALPHA HUNTER — [Date] Scan Results**

[N] new finds across multiple chains. All verified NOT in previous reports.

---

🔷 **[CHAIN] — [Project Name] ($TICKER)**
[One-line description]
• TGE: [date]
• [Key metric or feature]
• [Key metric or feature]
• 🌐 [website]
• 🐦 @[twitter]
• 💬 [discord/telegram]

[Repeat for each find]

---

⚡ **Quick Take:** [1-2 sentence analysis of best picks]

Seen list updated ✅ | Next scan in ~20 min
```

### "No Alpha" Report Format

When no new alpha passes the quality gate, still document what was evaluated and why it was filtered. This prevents re-evaluating the same projects next scan:

```
🔍 **ALPHA HUNTER — [Date] Scan Results**

No new alpha this round. Here's what was evaluated:

| Project | Status | Why Skipped |
|---------|--------|-------------|
| **Name** (Chain) | Stage | Reason (already launched, no TGE, too early, etc.) |

**Already-seen projects (skipped):** [list of known projects from seen file]

**Bottom line:** [1-2 sentence summary of market state]
```

This pattern also serves as a "negative cache" — next scan can quickly confirm these projects are still filtered without re-researching.

### Chain Emojis

| Chain | Emoji |
|-------|-------|
| Ethereum | 🔷 |
| Base | 🔵 |
| Solana | 🟣 |
| Sui | 🟢 |
| TON | 💎 |
| Aptos | 🔶 |
| Arbitrum | 🔹 |
| Optimism | 🔴 |
| BSC | 🟡 |
| Monad | 🟠 |
| Hyperliquid | ⚡ |
| Berachain | 🐻 |
| Avalanche | 🔺 |
| zkSync | 🔷 |
| Multi-chain | 🟡 |

## Dedup File Management

Location: `~/.hermes/scripts/.alpha_seen.json`

Format — keys are `titles` and `urls` (NO `seen_` prefix):
```json
{
  "titles": ["Project1 TGE June 2026", "Project2 DeFi Launch"],
  "urls": ["https://project1.com", "https://project2.io"],
  "last_updated": "2026-06-05T07:45:19.007080",
  "last_scan": "2026-06-05T07:45:19.007076"
}
```

**Actual file shape** (as of June 5, 2026): The file has accumulated BOTH `seen_titles`/`seen_urls` AND `titles`/`urls` as parallel arrays with duplicated data. The cron sessions keep appending to ALL FOUR arrays instead of consolidating. Next session MUST merge on first read using the pattern below.

- Read BEFORE searching (to filter out already-seen projects)
- Dedup by BOTH `titles` and `urls` (title catches same-project-different-url cases)
- **Title comparison is case-insensitive** — store lowercase, compare lowercase
- **MERGE legacy keys on read**: The file may have accumulated `seen_titles`/`seen_urls` alongside `titles`/`urls` from different scripts. Always merge both pairs. On write, consolidate to only `titles`/`urls` and remove legacy keys. **Concrete pattern** (use in `execute_code`):
  ```python
  import json
  from datetime import datetime
  with open('/home/ubuntu/.hermes/scripts/.alpha_seen.json', 'r') as f:
      data = json.load(f)
  # Merge legacy + canonical keys into sets
  all_titles = set(data.get('titles', []) + data.get('seen_titles', []))
  all_urls = set(data.get('urls', []) + data.get('seen_urls', []))
  # ... add new entries to sets ...
  # Write back with ONLY canonical keys
  data['titles'] = sorted(all_titles)
  data['urls'] = sorted(all_urls)
  data.pop('seen_titles', None)
  data.pop('seen_urls', None)
  data.pop('updated', None)  # legacy timestamp key
  data['last_updated'] = datetime.utcnow().isoformat()
  with open('/home/ubuntu/.hermes/scripts/.alpha_seen.json', 'w') as f:
      json.dump(data, f, indent=2)
  ```
- Normalize keys on first read: if `titles`/`urls` missing, init as empty arrays
- **KNOWN STATE (June 5, 2026, 2nd occurrence)**: The file was AGAIN left with duplicated data across legacy AND canonical keys — a cron session appended to `seen_titles`/`seen_urls` instead of consolidating. Next session MUST merge on first read using the pattern above. The inline instruction override pitfall has been reinforced. Fix command:
  ```bash
  python3 -c "
  import json; from datetime import datetime
  data=json.load(open('/home/ubuntu/.hermes/scripts/.alpha_seen.json'))
  all_t=sorted(set(data.get('titles',[])+data.get('seen_titles',[])))
  all_u=sorted(set(data.get('urls',[])+data.get('seen_urls',[])))
  data['titles']=all_t; data['urls']=all_u
  for k in ['seen_titles','seen_urls','updated']: data.pop(k,None)
  data['last_updated']=datetime.utcnow().isoformat()
  json.dump(data,open('/home/ubuntu/.hermes/scripts/.alpha_seen.json','w'),indent=2)
  "
  ```
- Update AFTER compiling report (add new entries to both arrays)
- ⚠️ The canonical keys are plain `urls`/`titles` — NOT `seen_urls`/`seen_titles`. Using wrong keys means the dedup check never matches and you re-report old finds.

## Delivery

- **Primary**: `hermes send -t "telegram:CHAT_ID:THREAD_ID" -f /tmp/alpha_msg.txt`
- **Fallback**: Output report as stdout — cron system delivers it automatically
- Write message to `/tmp/alpha_msg.txt` first (avoids `$` shell interpolation in crypto tickers)
- If Telegram send fails (Unauthorized, bot removed), the cron stdout fallback still delivers the report
- **`hermes send` skip in cron context**: When the cron job's delivery target is the SAME as the `hermes send` target, the CLI returns `"Skipped send_message to telegram:... This cron job will already auto-deliver its final response to that same target."` This is NOT an error — it's a deduplication mechanism. In this case, just output the report as your final response text and the cron system handles delivery. Do NOT retry or try alternative send methods — the auto-deliver will work. **⚠️ Delivery target mismatch**: The cron job's auto-deliver target (configured in `delivery` field of the cron job) may DIFFER from the `hermes send` target. Example: cron delivers to user DM (`telegram:USER_ID`) but `hermes send` targets a group topic (`telegram:-100GROUP:TOPIC_ID`). When `hermes send` is skipped due to dedup, the message goes to the cron's delivery target (DM), NOT the intended topic. To ensure delivery to a specific topic, the cron job's `delivery` field must be set to that topic target. If the cron delivery target is a DM and you need topic delivery, there's no workaround within the cron execution — the message will go to the DM. This is a cron configuration issue, not a skill issue.

## Pitfalls

- **Dedup file key drift**: The `.alpha_seen.json` file can accumulate BOTH `seen_titles`/`seen_urls` AND `titles`/`urls` key pairs from different scripts/sessions. On read, MERGE both pairs into a single dedup set. On write, consolidate to ONLY `titles`/`urls` (the canonical keys per this reference). If you only check one pair, you'll re-report finds from the other pair. Pattern: `all_seen_titles = set(seen.get("titles", []) + seen.get("seen_titles", []))` then on write use only `titles`/`urls` keys and pop the legacy `seen_titles`/`seen_urls` keys.
- **CRITICAL: Never append to BOTH key pairs** (June 2026, repeated failure): A cron session appended new entries to `seen_titles`, `seen_urls`, `titles`, AND `urls` — all four arrays — without consolidating. This happened AGAIN on June 5 despite the pitfall being documented. **ROOT CAUSE**: The cron task's inline instructions said "update the file with new entries" and the agent followed a naive append pattern instead of the consolidation pattern below. **LESSON**: The reference ALWAYS overrides inline task instructions for file management. The correct pattern is ALWAYS: (1) merge all key pairs into Python sets on read, (2) add new entries to the sets, (3) write back with ONLY `titles`/`urls` keys, (4) `pop()` the legacy keys. Never write to `seen_titles`/`seen_urls` — they should only be read for backward compatibility. **Concrete anti-pattern that keeps recurring**:
  ```python
  # ❌ WRONG — this is what the cron agent did (appends to ALL arrays)
  seen.setdefault('seen_titles', []).append(title)
  seen.setdefault('seen_urls', []).append(url)
  seen.setdefault('titles', []).append(title)
  seen.setdefault('urls', []).append(url)
  
  # ❌ ALSO WRONG — naive extend() on existing arrays
  seen["titles"].extend(new_entries)
  seen["urls"].extend(new_urls)
  # This skips legacy key consolidation and creates unbounded growth
  
  # ✅ RIGHT — merge into sets, write canonical keys only
  all_titles = set(data.get('titles', []) + data.get('seen_titles', []))
  all_urls = set(data.get('urls', []) + data.get('seen_urls', []))
  all_titles.add(new_title)
  all_urls.add(new_url)
  data['titles'] = sorted(all_titles)
  data['urls'] = sorted(all_urls)
  data.pop('seen_titles', None)
  data.pop('seen_urls', None)
  data.pop('updated', None)
  ```
- **Inline cron task instructions are LOWER priority than this reference** (June 2026, reinforced): When the cron task template says "update the file with new entries" without specifying HOW, the agent must follow the consolidation pattern from this reference — NOT invent its own append logic. The reference exists precisely because inline task instructions are too vague to prevent the legacy-key-append anti-pattern. If a future cron task gives file management instructions that conflict with this reference, THIS REFERENCE WINS. Pattern: always use `execute_code` with the full consolidation script (merge sets → write canonical keys → pop legacy keys), even if the task says something simpler like "add to the file."
- **`hermes_tools.read_file` deduplicates content**: Inside `execute_code`, the imported `read_file` from `hermes_tools` returns `{'status': 'unchanged', 'content_returned': False}` on second read of the same file within a session. For the dedup JSON file, ALWAYS use Python's built-in `with open(path) as f: data = json.load(f)` instead of `hermes_tools.read_file`. The `terminal('cat ...')` fallback also works but is less clean.
- **DeFiLlama large response piping failures**: The `/protocols` endpoint returns ~8MB JSON. Piping directly from `curl` to `python3 -c` via shell heredoc frequently fails with `JSONDecodeError: Expecting value: line 1, column 0` — the shell mangles the large stdin. **Fix**: Always save to a temp file first, then process: `curl -s 'https://api.llama.fi/protocols' -o /tmp/llama_protocols.json` then `python3 << 'PYEOF' ... open('/tmp/llama_protocols.json') ... PYEOF`. This two-step pattern is reliable. Verified June 2026 — direct pipe failed 3 times in a row, file-based approach worked immediately.
- **Brave Search rate limiting (HTTP 402)**: After ~15-20 `web_search` calls in quick succession within `execute_code`, Brave Search starts returning `{"success": false, "error": "Brave Search returned HTTP 402"}`. This persists for several minutes. **Mitigation**: (1) Batch queries efficiently — don't re-search for things you already have data on, (2) Use API-based sources (DeFiLlama, CoinGecko) as primary when rate-limited, (3) If rate-limited mid-scan, proceed with data already collected rather than retrying — the 402 doesn't recover quickly enough to matter within a single cron run, (4) Prioritize the most valuable queries first (specific project names, TGE dates) over broad discovery queries, (5) ICO Analytics TGE page is the single best browser-based structured source.
- **CoinGecko API rate limiting**: After ~10-15 API calls, CoinGecko returns empty responses (not HTTP errors — the response body is empty or HTML). **Mitigation**: (1) Add 3s sleep between calls, (2) batch queries — don't re-fetch data you already have, (3) use DeFiLlama for bulk protocol discovery (no rate limit), reserve CoinGecko for detail lookups of specific finds, (4) if rate-limited, proceed with data already collected.
- **GeckoTerminal token info returns empty socials**: The `networks/{chain}/tokens/{token_id}` endpoint almost always returns `null` for name, symbol, and empty arrays for websites/socials. For Solana tokens, use PumpFun API instead: strip `solana_` prefix from GeckoTerminal's `relationships.base_token.data.id` to get the mint address, then call `frontend-api-v3.pump.fun/coins/{mint}`. Returns `twitter`, `telegram`, `website` fields. For EVM tokens, social lookup is harder — try CoinGecko search or the project's own website.
- **Title dedup false positives from substring matching**: When comparing candidate titles against the seen list, loose substring matching causes false positives. Example: "OpenSea" falsely matching against "MegaETH Season 1" because "sea" is a substring of "season". **Fix**: Use the project's primary identifier (name slug or ticker) as the match key, not arbitrary substrings. Pattern:
  ```python
  def is_seen_new(project_name, seen_titles_lower):
      slug = project_name.lower().replace(" ", "")
      for st in seen_titles_lower:
          if slug in st.replace(" ", ""):
              return True
      return False
  ```
  This prevents partial-word false positives while still catching the same project reported under slightly different titles.
- **`hermes send_message` not available in cron toolset**: Cron jobs running via `execute_code` do NOT have `send_message` as a callable tool. The `hermes send` CLI also fails when the shell tries to interpolate `$` signs in crypto tickers (`$TEA`, `$MEGA`, `$BTC`). **Solution**: Write the report to stdout — the cron delivery system handles routing automatically. If you must use `hermes send`, write to a temp file first with `write_file("/tmp/alpha_msg.txt", msg)` then `terminal('hermes send -t "telegram:CHAT_ID:THREAD_ID" -f /tmp/alpha_msg.txt')`.
- **web_extract fails** on most crypto news/project sites (Brave Search backend, JS-heavy pages). Confirmed failures (June 2026): Blockchain Reporter, ICO Analytics, CoinMarketCap, CoinMooner, DefiLlama, crypto.news, Hyperliquid announcements, Business Insider. **Error**: `"Brave Search (Free) is a search-only backend and cannot extract URL content. Set web.extract_backend to firecrawl, tavily, exa, or parallel."` — this is a backend limitation, not a URL issue. **Rely on API endpoints** (DeFiLlama, CoinGecko) and `web_search` result descriptions rather than spending time on `web_extract`. When you MUST get full page content, use `browser_navigate` + `browser_console` to extract paragraph text via JS.
- **CoinMarketCap/CoinMooner** pages require JS rendering — `web_extract` returns empty. Use `browser_navigate` + `browser_console` JS extraction instead (see Tier 2 #7 for the exact CMC table extraction pattern). For individual project pages, use `delegate_task` to research multiple CMC URLs in parallel — each subagent gets its own browser session, avoiding sequential page loads.
- **Cloudflare/browser-blocking sites**: Several key crypto sites aggressively block automated browsers with Cloudflare challenges: `airdrops.io` (403 block), `nftcalendar.io` (challenge page), `coingecko.com` (verification page), `dexscreener.com` (verification page), `dextools.io` (block page), `rootdata.com` (CAPTCHA). These cannot be bypassed with browser tools. **Fallback**: Use their APIs (CoinGecko API, DexScreener API) or find the same data on alternative sources. Don't waste time retrying blocked sites — move to the next data source.
- **Twitter links** return "JavaScript not available" in search — don't rely on Twitter search results for social links. Find handles via project websites or Linktree pages.
- **Established vs new**: Always cross-check if a token is already on CoinGecko with significant market cap. A token that's been trading for months isn't "new alpha" even if it's trending.
- **Quality > Quantity**: Don't spam with mediocre finds. If nothing genuinely new and promising is found, report "No new alpha this round" and exit silently. The cron job's `[SILENT]` mechanism handles this — just print "No new alpha this round" and the system suppresses delivery.
- **"No new alpha" is a valid outcome**: When all discovered projects are already in the seen list, already launched weeks ago, or lack quality signals (no socials, no funding, too early stage), the correct action is to NOT send to Telegram. Don't force mediocre finds through just to have output. The quality gate is the skill's most valuable feature — violating it degrades trust.
- **TGE clusters are signals**: When multiple TGEs cluster on the same date (e.g. Tea, DeFi.app, YOM, Satsuma all launching June 4-5, 2026), that date becomes a market event. Note the cluster in reports — readers benefit from knowing "TGE wave day" even if individual projects were already reported. Cross-reference with market sentiment and exchange listings.
- **Presale-only tokens**: Note when a project is still in presale (not yet tradeable). Flag this clearly in the report — it's a different risk profile than live tokens.
- **Chain emoji accuracy**: Double-check chain emoji mapping. Common mistake: using 🟢 (Sui) for Avalanche (should be 🔺), or 🟣 (Solana) for Monad (should be 🟠).
- **Browser extraction pattern for articles**: When `web_extract` returns empty, use this pattern to get article text:
  ```python
  browser_navigate(url)
  browser_console(expression='document.querySelectorAll("article p").length')  # verify content exists
  browser_console(expression='Array.from(document.querySelectorAll("article p")).map(p=>p.textContent.trim()).filter(t=>t.length>20).join("\\n\\n")')
  ```
  This returns clean paragraph text from news articles without needing full snapshot parsing.
