---
name: crypto-data-scrapers
description: >
  Scrape crypto market data from free APIs — DEXScreener (new pairs, trending),
  DeFiLlama (TVL, yields, protocols), CoinGlass (funding, OI), Fear & Greed index.
  Use when user asks about new token discovery, market overview, yield opportunities,
  or on-chain analytics. No auth required for most endpoints.
triggers:
  - new pairs scanner
  - trending tokens
  - DEXScreener data
  - DeFiLlama TVL/yields
  - market overview report
  - yield farming opportunities
  - chain TVL comparison
  - DEX volume data
---

# Crypto Data Scrapers

Free API-based scrapers for crypto market data. No auth required.

## Available Scrapers

| Scraper | File | Data | Schedule |
|---------|------|------|----------|
| DEXScreener | `dexscreener_scanner.py` | New pairs, trending, boosted | Every 10 min |
| DeFiLlama | `defillama_scanner.py` | TVL, yields, protocols, DEX volumes | Every 6 hours |
| Fear & Greed | Built into engine | Market sentiment | Every cycle |
| CoinGlass | Built into engine | Funding rate, OI, liquidations | Per trade |
| Charon | Direct API call | Early Solana token signals, bonding status, holders | Every 3 min |

## DEXScreener Scanner

**File:** `~/.hermes/scripts/dexscreener_scanner.py`

**API:** `https://api.dexscreener.com` (free, no auth)

**Key endpoints:**
- `/token-boosts/latest/v1` — Boosted/trending tokens
- `/token-profiles/latest/v1` — New token profiles
- `/tokens/v1/{chain}/{address}` — Token pair details
- `/latest/dex/search?q={query}` — Search tokens

**Usage:**
```bash
# One-shot scan
python3 dexscreener_scanner.py --min-score 40

# Search specific token
python3 dexscreener_scanner.py --search "bitcoin"

# Continuous monitoring
python3 dexscreener_scanner.py --watch --interval 300

# JSON output
python3 dexscreener_scanner.py --json
```

**Scoring system (0-100):**
- Volume score: 20 pts (>$100K = 20, >$50K = 15, >$10K = 10)
- Price momentum: 15 pts (>5% = 15, >2% = 10, >0% = 5)
- Buy pressure: 15 pts (ratio >2 = 15, >1.5 = 10, >1 = 5)
- Liquidity: 15 pts (>$100K = 15, >$50K = 10, >$10K = 5)
- FDV range: 10 pts ($100K-$50M = 10, $50K-$100M = 5)
- Boosted bonus: 10 pts

## DeFiLlama Scanner

**File:** `~/.hermes/scripts/defillama_scanner.py`

**APIs:**
- `https://api.llama.fi` — Protocols, chains, DEX volumes
- `https://yields.llama.fi` — Yield pools
- `https://stablecoins.llama.fi` — Stablecoin data

**Usage:**
```bash
# Full overview
python3 defillama_scanner.py

# Specific data
python3 defillama_scanner.py --protocols --limit 10
python3 defillama_scanner.py --yields --limit 20
python3 defillama_scanner.py --chains
python3 defillama_scanner.py --stablecoins
python3 defillama_scanner.py --volumes

# Telegram report
python3 defillama_scanner.py --report

# JSON output
python3 defillama_scanner.py --json
```

**Report format (Telegram):**
```
📊 DeFiLlama Market Report

🏆 Top Protocols:
  1. Lido (LDO) — $14.60B +3.5%
  2. EigenLayer — $10.2B -2.1%
  ...

⛓️ Chain TVL:
  Ethereum: $50.2B
  Solana: $5.1B
  ...

💰 Top Yields (safe):
  Aave USDC (Ethereum): 4.2% APY 💵
  Curve 3pool (Ethereum): 3.8% APY 💵
  ...

📈 DEX Volume 24h:
  Uniswap: $1.2B (+5.3%)
  ...
```

## Cron Jobs

```python
# DEXScreener — every 10 min
cronjob(action='create', schedule='every 10m',
        prompt='Run: python3 ~/.hermes/scripts/dexscreener_scanner.py --min-score 40')

# DeFiLlama — every 6 hours
cronjob(action='create', schedule='0 */6 * * *',
        prompt='Run: python3 ~/.hermes/scripts/defillama_scanner.py --report')
```

## Rate Limiting

- DEXScreener: 0.5s between token detail requests
- DeFiLlama: No rate limit (generous)
- Both: Respect 429 responses, back off 30s

## Charon Signal Server (Solana Token Discovery)

**API:** `https://api.thecharon.xyz/api/signals`
**Auth:** `x-api-key` header (NOT Bearer — Bearer returns 401)
**Rate limit:** Generous, but cache 3 min to be safe

**Usage (curl):**
```bash
curl -s "https://api.thecharon.xyz/api/signals" \
  -H "x-api-key: YOUR_KEY" | jq '.count'
```

**Response fields per signal:**
- `symbol`, `name`, `mint` — identification
- `holders` — holder count
- `marketCapUsd`, `volume24h`, `volume5m` — market metrics
- `liquidityUsd` — pool liquidity
- `priceUsd` — current price
- `ageMs` — age in milliseconds
- `bondingComplete` — bonding curve finished (boolean)
- `sourceCount` — number of aggregators reporting
- `trending` — trending status
- `firstSeen`, `lastSeen` — timestamps
- `feeClaim` — fee distribution data

**Quality filter pattern:**
```javascript
const qualifying = signals.filter(s =>
  s.bondingComplete &&
  s.holders > 100 &&
  (s.marketCapUsd || 0) > 10_000 &&
  (s.volume24h || 0) > 10_000 &&
  (s.liquidityUsd || 0) > 2_000 &&
  s.ageMs < 72 * 3600 * 1000  // < 72 hours
);
```

**Typical response:** 89-95 active signals, ~50-60 pass quality filter.

**Integrated with:** Meridian DLMM agent screening pipeline (see `meridian-dlmm-agent` skill).

## Swap Mining on RAM-Constrained VPS

When VPS RAM is insufficient for RandomX (e.g., 1.9GB total):

1. **Add swap file**: `sudo dd if=/dev/zero of=/swapfile bs=1M count=4096 && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`
2. **Mine 1 thread only**: `-genproclimit=1` to minimize RAM usage
3. **Expect low hashrate**: ~100-200 H/s on 2-core Xeon with swap (vs ~400 H/s with real RAM)
4. **Monitor OOM**: `dmesg | grep -i oom`
5. **Cleanup**: `sudo swapoff /swapfile && sudo rm /swapfile`

## Telegram Bot Commands for Mining Monitor

### Command Registration
`POST /bot{token}/setMyCommands` with `[{"command":"name","description":"desc"}]`

### Polling Handler
`GET /bot{token}/getUpdates?offset=LAST_ID+1&limit=10&timeout=5`

### Useful Mining Commands
```
/juno_sync    → Manual status sync
/juno_stop    → pm2 stop
/juno_start   → pm2 start
/juno_cleanup → pm2 delete + rm -rf /opt/juno-mining
```

### Setup Pattern
1. Register commands via `setMyCommands`
2. Poll `getUpdates` every 1 min via cron
3. Parse `message.text` for `/command`
4. Execute bash, reply via `sendMessage` with `message_thread_id` for topic targeting
5. Track `last_id` in state file to avoid reprocessing

## CPU Mining

For RandomX/CPU mining feasibility, software, pools, and VPS requirements:
→ `references/cpu-mining-reference.md`

## Pitfalls

1. **DEXScreener API can return null TVL** — always use `x.get("tvl") or 0` not `x.get("tvl", 0)`
2. **DeFiLlama APY > 1000%** — usually unsustainable, filter out
3. **Boosted tokens** — may be paid promotions, not fundamentals
4. **New pairs** — high risk, low liquidity, could be rugs
5. **Nitter/RSSHub** — Twitter scraping currently broken (Jun 2026), use syndication API instead (see below)
6. **Seed phrase security** — NEVER store user seed phrases in agent memory, files, or logs. Only accept public addresses (J1, ETH, etc.). If user sends seed phrase, refuse and explain why.

## Telegram Bot Commands for Mining Monitor

**ALL standard approaches are blocked from VPS IPs:**
- Login from VPS → "temporarily limited"
- Guest API → returns empty
- Syndication timeline → HTML only
- Nitter instances → all down/blocked
- RSSHub → Cloudflare blocked
- oEmbed → disabled

### ✅ WORKING: Syndication Tweet Result API

Fetch individual tweets **without any auth**:

```bash
curl -s "https://cdn.syndication.twimg.com/tweet-result?id=TWEET_ID&token=0" \
  -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"
```

**Returns:** JSON with `text`, `user.screen_name`, `created_at`, `favorite_count`, `article` (for Twitter Articles), `entities.urls`, etc.

**Limitations:**
- One tweet at a time (need tweet ID)
- No user timeline feed
- No search
- Rate limit unknown but generous for occasional use

**To get tweet ID:** extract from URL — `x.com/USER/status/ID`

**To resolve t.co links:** `curl -s -L "https://t.co/XXXXX" -H "User-Agent: Mozilla/5.0"`

### ❌ FAILED Approaches (do not retry)

| Approach | Why it fails |
|----------|-------------|
| `api.x.com/1.1/guest/activate.json` | Returns empty from VPS |
| `publish.twitter.com/oembed` | Disabled |
| `syndication.twimg.com/srv/timeline-profile` | Returns HTML, not JSON |
| Nitter (all instances) | Down or Cloudflare-blocked |
| RSSHub | Cloudflare-blocked |
| Direct login | IP banned |

### Workaround for Airdrop Twitter Tasks

Since VPS cannot interact with Twitter:
1. **User forwards/screenshots tweets** → Mona analyzes content
2. **Mona provides instructions** → User executes manually from phone
3. **Residential proxy** (~$5-10/mo) — only way to automate from VPS
4. **Skip Twitter tasks** — focus on on-chain airdrops instead
