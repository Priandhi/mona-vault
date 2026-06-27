# Browser Scraping Fallback — Reference

## When to Use

Trigger this fallback when:
- `web_search` returns HTTP 402 (Brave Search quota exhausted)
- GeckoTerminal API doesn't cover the chain (e.g. Monad, Hyperliquid, Berachain pre-launch)
- You need ICO/IDO/launchpad data not available via DEX APIs

## ICOdrops Scraping

URL: `https://icodrops.com/`

The main page snapshot contains two key sections:
- **ACTIVE** — Currently active ICOs/IDOs/points farming (46+ entries typical)
- **UPCOMING** — Upcoming token launches with dates (248+ entries typical)
- **ENDED** — Recently completed launches

Each entry is a link with format:
```
link "Name Ticker Category Type Status Details Raised VCs +N"
```

Example parsed entries:
```
BitFi BFI DeFi ICM on Sonar Jun 8, 2026 -- Fundamental Labs...
CAP CAP CAP NEW DeFi Auction Auction Jun 10, 2026 $9.9 M...
MetaY CLAW AI IDO on Poolz from May 18, 2026 No Data
```

### Project Detail Pages

Navigate to `https://icodrops.com/{slug}/` for full details:
- Rounds with dates, amounts, types (IDO/Private/Seed)
- Investor list with tiers
- Category ranking
- Social links (Website, Twitter, Whitepaper)
- Activity timeline (farming, retrodrop status)

**Pitfall:** Slugs can collide. If you get 404 or wrong project, try `{slug}-2` or `{slug}-3`.

## CoinGecko API (Free, No Browser Needed)

```bash
# Trending coins
curl -s 'https://api.coingecko.com/api/v3/search/trending' | python3 -m json.tool

# Market data (top N)
curl -s 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&sparkline=false'

# Look for: newly appearing coins, unusual volume spikes, significant price moves
```

## CoinDesk Scraping

URL: `https://www.coindesk.com/`

Main page shows latest articles. Filter by category:
- DeFi section for new protocol launches
- Look for "launch", "TGE", "token", "airdrop" keywords in headlines

**Note:** Tag pages (e.g. `/tag/defi`) may 404. Navigate via main page category links.

## Poolz Finance (Launchpad)

URL: `https://www.poolz.finance/`

Shows upcoming projects on the Poolz launchpad. Useful for finding new IDOs before they start.

## Quality Assessment Checklist

When evaluating browser-scraped finds:

1. **VC Backing** — Tier 1/2 VCs (Coinbase Ventures, a16z, Paradigm, Dragonfly, Polychain) = strong signal
2. **Raise Amount** — >$1M = meaningful, >$5M = serious, >$10M = high conviction
3. **Category Rank** — Top 5 in category on ICOdrops = noteworthy
4. **Activity Status** — Active farming/IDO = immediate opportunity
5. **Social Presence** — Twitter + Website minimum; Telegram/Discord = bonus
6. **Timeline** — TGE within 30 days = urgent alpha; no date = speculative
7. **Narrative Fit** — AI, DePIN, RWA, restaking = hot narratives in 2025-2026
