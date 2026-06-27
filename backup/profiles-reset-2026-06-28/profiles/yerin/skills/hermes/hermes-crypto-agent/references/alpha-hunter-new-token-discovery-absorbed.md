---
name: alpha-hunter-new-token-discovery
description: >
  Discover newly launched crypto tokens across EVM and Solana chains using GeckoTerminal and PumpFun APIs.
  Deduplicates against a seen-list file to avoid resending. Outputs formatted alpha reports for Telegram.
triggers:
  - "find new crypto tokens"
  - "alpha scan"
  - "new token launch discovery"
  - "crypto alpha hunter"
  - "scan for new tokens"
---

# Alpha Hunter — New Token Discovery

## Overview

Automated workflow for finding newly launched crypto tokens across multiple chains, filtering for quality, deduplicating against previously sent results, and formatting reports for Telegram delivery.

## Architecture — Two-Layer Detection

```
LAYER 1: 🎯 Sniper Monitor (every 2 min, script-only, no AI)
   PumpFun new tokens (earliest signal — before CT shares)
   GeckoTerminal new_pools (Solana, Base, ETH)
   → Filter: socials + momentum + MCap range
   → Max 3 per alert, anti-spam
   → Script: ~/.hermes/scripts/pumpfun_sniper.py
   → Telegram Alpha topic

LAYER 2: 🔥 Alpha Hunter (every 20 min, AI-driven)
   Phase 1: Social signals — web_search CT/Twitter for token mentions (past 1hr)
   Phase 2: API scan — GeckoTerminal trending + PumpFun KOTH + DexScreener
   → Deeper analysis, VC backing, project research
   → Max 8 tokens per report
   → Telegram Alpha topic
```

**Why two layers:** GeckoTerminal/PumpFun API data lags 40+ minutes behind CT. By the time a token shows volume on APIs, CT already knows. The sniper monitor catches PumpFun mints at birth; the deep hunter does broader research with social signal priority.

**Speed rule:** Social signals from CT/Twitter > API data. If a token is trending on Twitter but not yet on GeckoTerminal, STILL report it with available data + note "early entry — not yet on DEX aggregators".

**Reference:** See `references/sniper-monitor-impl.md` for full sniper implementation details.

## Dedup Files

- Alpha Hunter: `~/.hermes/scripts/.alpha_seen.json`
- Sniper Monitor: `~/.hermes/scripts/.sniper_seen.json`
- Both use token address as primary dedup key

## Key APIs

### GeckoTerminal REST API (no auth required)

**PITFALL (June 2026):** GeckoTerminal API returns 403 Forbidden on VPS IPs (Tencent Cloud). Use DexScreener as primary fallback.

**DexScreener alternatives (verified working):**
- Boosted tokens: `https://api.dexscreener.com/token-boosts/latest/v1` (30 trending tokens)
- Token details: `https://api.dexscreener.com/tokens/v1/{chain_id}/{token_address}`
- Token profiles: `https://api.dexscreener.com/token-profiles/latest/v1`

Base: `https://api.geckoterminal.com/api/v2/`

| Endpoint | Use |
|---|---|
| `networks/{chain}/new_pools?page=1` | Brand new pools on a chain |
| `networks/{chain}/trending_pools?page=1` | Trending pools on a chain |
| `search/pools?query={term}` | Search for specific tokens |
| `networks/{chain}/pools/{pool_address}` | Detailed pool info |
| `networks/{chain}/tokens/{token_id}` | Token metadata (often empty for socials) |

Supported chain slugs: `eth`, `solana`, `base`, `bsc`, `arbitrum`, `optimism`, `polygon_pos`, `avalanche`

**Key fields from pool attributes:**
- `name`, `pool_created_at`, `base_token_price_usd`
- `volume_usd.h24` — 24h volume
- `fdv_usd` — fully diluted valuation
- `price_change_percentage.h24` — 24h price change
- `transactions.h24.buys` / `transactions.h24.sells`
- `reserve_in_usd`

**Relationships to extract:**
- `relationships.base_token.data.id` — gives `chain_tokenAddress` format
- `relationships.dex.data.id` — DEX name (e.g. `meteora-damm-v2`, `uniswap-v4-base`)

### PumpFun API (Solana tokens)

Base: `https://frontend-api-v3.pump.fun/`

| Endpoint | Use |
|---|---|
| `coins/{mint_address}` | Token info including socials |
| `coins?limit=20&offset=0&sort=created_timestamp&order=DESC` | Newest tokens (earliest signal) |
| `coins/king-of-the-hill?limit=20&offset=0` | Hot/graduating tokens (about to hit Raydium) |

**Key fields:**
- `name`, `symbol`, `description`
- `twitter` — Twitter/X handle or URL (may need `https://x.com/` prepended)
- `telegram` — Telegram URL
- `website`
- `mint` — Solana mint address
- `usd_market_cap` or `market_cap` — check both, prefer `usd_market_cap`

**Pitfall:** Token addresses from GeckoTerminal are in `solana_{address}` format. Strip the `solana_` prefix before calling PumpFun.

**Enrichment flow:** If PumpFun returns no socials for a Solana token, try DexScreener API: `https://api.dexscreener.com/latest/dex/tokens/{address}` — check `info.socials[]` and `info.websites[]`.

### CoinGecko API (free tier)

- `/api/v3/search/trending` — trending coins (mostly established)
- `/api/v3/coins/markets` — market data
- Rate limited on free tier (429 errors possible)

## Filtering Criteria

Quality filters to apply before sending:

1. **Volume threshold:** >$500 minimum, >$10K preferred for alpha
2. **Transaction activity:** At least 5+ buys in 24h (3+ for sniper)
3. **Age:** Created within last 7 days preferred, 30 days max
4. **MCap range (sniper):** $10K - $5M — early entries only
5. **Skip established tokens:** BTC, ETH, SOL, DOGE, PEPE, WIF, BONK etc.
6. **Skip stablecoins/pairs:** WETH/USDC, WBTC, DAI pairs
7. **Social presence:** Tokens with Twitter/Telegram/Website get priority
8. **Chain diversity:** Max 3 tokens per chain per report

## Social Signal Search Patterns (Phase 1 for Deep Hunter)

When the deep hunter runs, search CT/Twitter BEFORE API scan to catch tokens earlier:

```
web_search: "new solana token launch today" site:x.com (past 1 hour)
web_search: "just launched solana" OR "new token solana" site:x.com (past 1 hour)
web_search: "presale" OR "IDO" OR "fair launch" crypto today (past 1 hour)
web_search: "trending token" OR "gem found" solana OR base OR ethereum site:x.com (past 1 hour)
web_search: site:dexscreener.com new pairs solana (past 1 hour)
```

Extract token names/tickers from social results → then verify on GeckoTerminal/DexScreener API.

## Deduplication

**TWO dedup systems exist — they serve different purposes:**

### 1. Title/URL dedup (AI-driven scans)
File: `~/.hermes/scripts/.alpha_seen.json`

Used by agent-driven crons (no_agent=False) that do web_search + reasoning.

**Actual structure (evolved beyond original design):**
```json
{
  "seen_urls": ["https://...", "https://..."],
  "seen_titles": ["Title 1", "Title 2"],
  "titles": ["Formatted Title 1", "Formatted Title 2"],
  "urls": ["https://...", "https://..."],
  "last_updated": "2026-06-05T08:00:00",
  "last_scan": "2026-06-05T04:22:15",
  "updated": "2026-06-05T07:26:29"
}
```

- Check new finds against **all four** array fields: `seen_urls`, `seen_titles`, `titles`, `urls`
- `seen_urls`/`seen_titles` — raw scraped entries
- `titles`/`urls` — formatted/curated entries sent to Telegram
- Append to all relevant arrays after sending
- Update `last_updated` and `last_scan` timestamps

### 2. Contract-level dedup (API-driven scans) — CRITICAL
File: `~/.hermes/scripts/.alpha_seen_contracts.json`

Used by script-only crons (no_agent=True) that poll APIs (DexScreener, Clanker, etc).

**Structure:** `{contract_address: iso_timestamp, ...}`
**Auto-prune:** Entries older than 48h are automatically removed on load.

**Implementation pattern (MUST be in every scanner script):**
```python
SEEN_FILE = os.path.expanduser("~/.hermes/scripts/.alpha_seen_contracts.json")
SEEN_MAX_AGE_HOURS = 48

def load_seen_contracts():
    if not os.path.exists(SEEN_FILE):
        return {}
    with open(SEEN_FILE) as f:
        data = json.load(f)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=SEEN_MAX_AGE_HOURS)
    return {c: ts for c, ts in data.items() 
            if datetime.fromisoformat(ts) > cutoff}

def save_seen_contracts(seen_dict):
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    with open(SEEN_FILE, 'w') as f:
        json.dump(seen_dict, f)

# In main scan loop:
seen = load_seen_contracts()
# Filter: skip if contract in seen
unique = [t for t in all_tokens if t["contract"].lower() not in seen]
# After reporting: save new contracts
for t in reported_tokens:
    seen[t["contract"].lower()] = datetime.now(timezone.utc).isoformat()
save_seen_contracts(seen)
```

**WHY this matters:** User explicitly complained — "stop spam token yang udah di scan habisin apikey jir". Without persistent dedup, every cron run re-scans and re-reports the same tokens, wasting API calls and annoying the user.

**CRON CONFIG RULE:** Scanner crons that just poll APIs and format output MUST use `no_agent=True` + `script` param. This eliminates LLM token cost entirely. Only use `no_agent=False` when the cron needs web_search or complex reasoning.

## Report Format

Chain emoji headers: 🔷ETH 🔵BASE 🟣SOL 🟡BSC 🔶ARB etc.

Each token entry includes:
- Name + ticker
- Volume 24h + FDV
- 24h price change %
- Creation date
- Social links (Twitter, Telegram, Website) — **MUST be clickable markdown links**
- DexScreener pool link — **MUST be clickable markdown link**
- Risk notes if no socials found

### Telegram Link Format Rules (CRITICAL)

All links MUST use Telegram clickable markdown: `[text](url)` format.

- ✅ `[Twitter](https://x.com/username)` — full URL, clickable
- ❌ `@username` — NOT clickable in Telegram, user complained
- ✅ `[DexScreener](https://dexscreener.com/solana/ADDRESS)`
- ✅ `[Website](https://example.com)`
- ✅ `[Telegram](https://t.me/groupname)`

If PumpFun returns just a handle (e.g. `@bountyclubfun`), prepend `https://x.com/` to make it `https://x.com/bountyclubfun`.

If no Twitter found: write `🐦 Twitter not found — DYOR` (not a broken handle).

## Fallback: Browser Scraping When APIs Are Down

When `web_search` returns HTTP 402 (Brave quota exhausted) and GeckoTerminal APIs are insufficient, fall back to browser-based scraping. **Not all sites are accessible** — use this accessibility map:

| Source | Browser Access | Notes |
|---|---|---|
| **ICOdrops** ✅ | Works | Best for upcoming/active ICOs, IDOs, token launches. Rich data: VC backing, rounds, timelines |
| **CoinDesk** ✅ | Works | General crypto news, DeFi launches, institutional moves |
| **CoinGabbar** ✅ | Works | Presale/ICO news, listing dates, price predictions |
| **CoinGecko API** ✅ | Works via curl | `/api/v3/search/trending` and `/api/v3/coins/markets` |
| **Poolz Finance** ✅ | Works | Launchpad with upcoming IDO projects |
| **TheBlock** ❌ | Cloudflare hard block | "Sorry, you have been blocked" — skip |
| **DefiLlama** ❌ | Cloudflare challenge | "Just a moment..." verification — skip |
| **RootData** ❌ | CAPTCHA | Verification popup blocks access — skip |

### Browser Scraping Workflow

```
1. browser_navigate("https://icodrops.com/")
2. Parse ACTIVE + UPCOMING sections from snapshot
3. Cross-reference titles/urls against .alpha_seen.json
4. For promising new finds → browser_navigate to project page for details
5. Extract: VC backing, round size, timeline, socials, category rank
6. Format + send
```

### ICOdrops Data Fields

From project pages, extract:
- **Category rank** (e.g. "#1 in AI", "#235 in Infrastructure")
- **Rounds**: IDO/Private/Seed with dates and amounts
- **Investors**: Fund name, tier, stage
- **Activities**: Points farming, retrodrop status, active/upcoming
- **Socials**: Website, Twitter, Whitepaper links
- **Overview**: Project description snippet

## Pitfalls

1. **Cloudflare blocks:** CoinGecko, DexScreener, GeckoTerminal web all have aggressive bot detection. Use the REST APIs directly via `terminal`/`curl`, not browser.
2. **Web search 402:** Brave Search returns HTTP 402 when quota exceeded. Fall back to browser scraping (ICOdrops, CoinDesk, CoinGecko API via curl).
3. **GeckoTerminal token info returns empty socials** for most tokens. Use PumpFun API for Solana token socials instead.
4. **Pool address vs token address:** GeckoTerminal pool addresses are different from token addresses. Extract token address from `relationships.base_token.data.id`.
5. **Multiple pools per token:** The same token can have many pools. Use the highest-volume pool for the report.
6. **Rate limits:** GeckoTerminal API appears to have no strict rate limits on the free tier. CoinGecko free tier does (429 errors).
7. **ICOdrops slug collisions:** Multiple projects can share similar names. E.g. "codex" (no-code DApp, old) vs "codex-2" (stablecoin blockchain, $15.8M VC). Always verify the project page content matches expectations. If a 404 or wrong project appears, try appending `-2` or searching by ticker.
8. **CoinDesk tag pages 404:** URLs like `/tag/defi/` or `/tag/new-tokens/` may return 404. Use the main tag page structure (`/tag/{tag}` without trailing slash) or navigate via the site's category links instead.
9. **Bot detection escalation:** Some sites (TheBlock, DefiLlama, RootData) are completely inaccessible via browser automation. Don't waste retries — skip and use alternative sources.
10. **Seen list structure evolved:** The `.alpha_seen.json` file has grown beyond the original `{titles, urls}` format. It now includes `seen_urls`, `seen_titles`, `titles`, `urls`, `last_updated`, `last_scan`, `updated` fields. Always check ALL array fields when deduplicating to avoid resending.
11. **Cron script output discipline:** When writing `no_agent=True` cron scripts, stdout = Telegram delivery message (clean, formatted). stderr = debug logs (not delivered). Empty stdout = silent (nothing sent). Use `print(msg, file=sys.stderr)` for debug. Prefix nothing to stdout — the cron system delivers it verbatim.
12. **Anti-spam preference:** User explicitly says "jangan terlalu spam" and "stop spam token yang udah di scan habisin apikey". Max 3 tokens per sniper alert, max 8 per deep hunter report. Strict quality filters. If nothing quality found, output empty (silent) — don't send "no tokens found" noise. **NEVER re-scan a token that's already been reported** — use persistent contract-level dedup (see Deduplication section).
13. **GeckoTerminal chain slugs:** Use `eth` not `ethereum`. Confirmed working: `solana`, `base`, `eth`, `bsc`, `arbitrum`. `ethereum` returns 404.
14. **GeckoTerminal 403 on VPS:** GeckoTerminal API returns 403 Forbidden from VPS IPs (confirmed Tencent Cloud). Use DexScreener API as primary: `/token-boosts/latest/v1` for trending, `/tokens/v1/{chain}/{CA}` for details. No auth needed.
15. **PumpFun social field inconsistency:** The `twitter` field sometimes returns a full URL, sometimes just a handle with `@`, sometimes empty. Always normalize: if it doesn't start with `http`, prepend `https://x.com/` and strip leading `@`.
