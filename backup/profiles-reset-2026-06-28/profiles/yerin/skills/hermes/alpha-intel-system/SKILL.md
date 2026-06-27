---
name: alpha-intel-system
description: Whale Tracker + Twitter Alpha Scanner system. Monitor Solana smart money + KOL token mentions → Telegram alerts. Use when user asks about alpha intel, whale tracking, KOL monitoring, or smart money alerts.
when_to_use:
  - User asks about whale tracking or smart money monitoring
  - User wants alpha signals from Twitter KOLs
  - User wants to check Meteora DLMM pool activity
  - Cron job runs alpha intel cycle
version: 1.2.0
related_skills:
  - crypto-alert-bot
---

# Alpha Intel System

Location: `~/mona-workspace/alpha-intel/`

## Architecture

```
alpha-intel/
├── alpha_intel.py              # Master orchestrator
├── whale-tracker/
│   └── whale_tracker.py        # Solana smart money via Meteora + Helius
├── twitter-scanner/
│   └── twitter_scanner.py      # KOL tweet scanner + DexScreener validation
├── shared/
│   └── config.json             # Shared config (API keys, intervals)
├── data/
│   ├── whale-db.json           # Tracked whale wallets
│   ├── pools-cache.json        # Meteora pool snapshot
│   ├── whale-alerts.json       # Whale activity log
│   ├── alpha-signals.json      # Twitter signal log
│   ├── kol-tracker.json        # KOL list
│   └── seen-txs.json           # Dedup cache
└── logs/
```

## Commands

```bash
cd ~/mona-workspace/alpha-intel

# Whale Tracker
python3 whale-tracker/whale_tracker.py discover   # Find top Solana LP wallets
python3 whale-tracker/whale_tracker.py monitor     # Check whale activity
python3 whale-tracker/whale_tracker.py pools       # Pool snapshot with whale indicators
python3 whale-tracker/whale_tracker.py status      # Stats

# Twitter Scanner
python3 twitter-scanner/twitter_scanner.py scan    # Full KOL scan → signals
python3 twitter-scanner/twitter_scanner.py report  # Recent signals report
python3 twitter-scanner/twitter_scanner.py kols    # List tracked KOLs

# Full Intel Cycle
python3 alpha_intel.py full    # All phases: discovery + monitor + scan + cross-ref
python3 alpha_intel.py quick   # Whale activity only
python3 alpha_intel.py status  # System dashboard
python3 alpha_intel.py report  # Last report
```

## Cron Jobs

- **🐋 Whale Monitor** (`33b950457df3`): every 5m, no_agent, alerts only (silent when no alerts)
- **🧠 Alpha Intel Full** (`bd2d6540a4de`): every 30m, no_agent, full report

Script files live in `~/.hermes/scripts/`:
- `whale_monitor.py` — quick whale activity check
- `full_intel.py` — full intel cycle orchestrator

## API Endpoints (verified June 2026)

- **Meteora Pool Discovery**: `https://pool-discovery-api.datapi.meteora.ag/pools?...`
- **Meteora DLMM**: `https://dlmm.datapi.meteora.ag/...`
- **Helius RPC**: `https://mainnet.helius-rpc.com/?api-key=...`
| DexScreener Token Detail | `https://api.dexscreener.com/latest/dex/tokens/{CA}` | Full pair data: price, volume 24h, liquidity, market cap, fdv, pairCreatedAt timestamp. Returns `pairs[]` array. |
| DexScreener Latest Profiles | `https://api.dexscreener.com/token-profiles/latest/v1` | Latest 30 token profiles with chainId, tokenAddress, description, and links[] (twitter, discord, telegram, website). No auth needed. Good for discovering brand-new tokens that just got profile pages. |
| Pump.fun Trending | `https://frontend-api-v3.pump.fun/coins/currently-live?limit=20&offset=0&sort=market_cap&order=DESC` | Currently live tokens on Solana pump.fun with name, symbol, market_cap, created_timestamp. Good for finding new Solana meme/community tokens. Very early stage — quality filter aggressively. |

## Cron Management

User preference: when user says "stop semua" or "pause all", pause ALL cron jobs immediately — user is cost-conscious about API key usage. Use `cronjob(action='list')` first to get job IDs, then `cronjob(action='pause')` for each. Don't ask which ones — pause everything, user will re-enable individually.

Pausing pattern:
```
1. cronjob(action='list') → get all job_ids
2. For each active job: cronjob(action='pause', job_id=...)
3. Confirm with count: "X jobs paused"
```

## References

| File | Contents |
|------|----------|
| `references/telegram-groups.md` | Multi-channel Telegram alert routing architecture, setup steps, config structure |
| `references/web-search-alpha-hunter.md` | Web-search alpha discovery workflow — API-first discovery (DeFiLlama + CoinGecko), browser fallbacks (ICO Drops/Analytics), parallel search queries, filtering pipeline, report format, dedup file management, chain emojis, rate limit handling |

## Related Skills

- **`alpha-hunter-new-token-discovery`** — Direct API-based token discovery using GeckoTerminal REST API (new_pools, trending_pools, search) + PumpFun API for Solana social links. More reliable than web_search (no 402 rate limits) and browser scraping (no Cloudflare blocks). Use when you need to find brand-new pools by chain with volume/transaction filtering. Includes concrete curl examples and Python extraction scripts in `references/api-examples.md`.

## Web-Search Alpha Hunter — Discovery Workflow

The web-search alpha hunter runs as a cron job to find new token launches, TGEs, and protocol launches across all chains. **Full reference**: `references/web-search-alpha-hunter.md` — contains API patterns, browser extraction JS, chain ecosystem sources, filtering pipeline, report format, and dedup file management.

### Discovery Pipeline (priority order)

**CRITICAL: Always start with APIs. web_search hits HTTP 402 rate limits after ~15-20 calls. Don't burn queries on broad searches first.**

1. **API-first** (no browser, no auth, fast):
   - DeFiLlama `/protocols` → protocols listed last 14 days with TVL > $10K
   - CoinGecko `/search/trending` → trending tokens (filter established ones)
   - DexScreener `/token-profiles/latest/v1` → newest token profiles with social links
2. **Browser sources** (structured, reliable):
   - ICO Drops (`icodrops.com`) — always works, structured with VCs/dates
   - ICO Analytics (`icoanalytics.org/token-generation-events/`) — TGE table format
   - CoinMarketCap `/new/` — cross-chain new listings (JS extraction via `browser_console`)
3. **web_search** (backup only — often returns 402 in cron):
   - Chain-specific queries, narrative-specific queries
   - Multi-round: broad → chain-specific → ultra-specific

### "No Alpha" Report Format

When no new alpha passes quality gate, document what was evaluated and why filtered:

```
🔍 **ALPHA HUNTER — [Date] Scan Results**

No new alpha this round. Here's what was evaluated:

| Project | Status | Why Skipped |
|---------|--------|-------------|
| **Name** (Chain) | Stage | Reason |

**Already-seen projects (skipped):** [count/list]
**Bottom line:** [1-2 sentence summary]
```

### Key Pitfalls

- **Dedup file key drift**: `.alpha_seen.json` accumulates both `seen_titles`/`seen_urls` AND `titles`/`urls`. Always merge on read, write only `titles`/`urls`, pop legacy keys. See reference for consolidation script.
- **DeFiLlama large response**: Save to temp file first, then process. Direct pipe to python fails on ~8MB JSON.
- **CoinGecko rate limit**: ~10-15 calls before empty responses. Add 3s sleep between calls, batch efficiently.
- **Cloudflare-blocked sites**: coingecko.com, dexscreener.com browser, theblock.co — use their APIs instead.
- **Quality > Quantity**: Don't spam mediocre finds. "No new alpha" is valid output.

## EVM Smart Money Tracker (Base Chain)

Real-time whale wallet monitoring using Alchemy API + DexScreener enrichment.

**Architecture:**
- `~/.hermes/scripts/mona_smart_money_tracker.py` — Single-scan version (for cron)
- `~/.hermes/scripts/mona_smart_money_watcher.py` — Real-time daemon (15s polling, systemd)
- `~/.hermes/scripts/.smart_money_wallets.json` — Tracked wallets list
- `~/.hermes/scripts/.seen_smart_buys.json` — Dedup cache (1h TTL)
- `~/.hermes/scripts/.smart_money_state.json` — Last processed block

**Alchemy API for Base chain:**
- Endpoint: `https://base-mainnet.g.alchemy.com/v2/{key}`
- `eth_blockNumber` → current block
- `alchemy_getAssetTransfers` → ERC-20 transfers to/from wallet (filter `category: ["erc20"]`, `toAddress`, `excludeZeroValue: true`)
- Free tier: 300M compute units/month, enough for 15s polling

**Buy detection logic:**
1. Get recent ERC-20 transfers TO the smart money wallet
2. Filter OUT stablecoins (USDC, USDT, DAI, USDbC) — those are just transfers
3. Check if `from` address is a known DEX router (Aerodrome, Uniswap, 1inch, etc.)
4. Remaining tokens = likely buys from DEX swaps
5. Enrich with DexScreener: `https://api.dexscreener.com/tokens/v1/base/{contract}`
6. Calculate risk score (1-5) based on liquidity, age, sell pressure, market cap

**DexScreener enrichment fields (verified June 2026):**
- `marketCap`, `fdv` — both available in pair data
- `priceUsd` — current price
- `liquidity.usd` — pool liquidity
- `volume.h24`, `volume.h6`, `volume.h1` — volume at different timeframes
- `priceChange.h24`, `priceChange.h1`, `priceChange.m5` — price changes
- `txns.h24.buys`, `txns.h24.sells` — buy/sell transaction counts
- `pairCreatedAt` — pair creation timestamp (ms) — use for token age

**Real-time daemon (15s polling):**
```python
# Key pattern: poll loop with block tracking
while running:
    current_block = get_current_block()
    if current_block > last_block:
        transfers = get_transfers_for_wallet(wallet, last_block, current_block)
        # process transfers, enrich, alert
        last_block = current_block
    time.sleep(15)
```

**Systemd service for auto-restart:**
```ini
# ~/.config/systemd/user/smart-money-watcher.service
[Unit]
Description=Mona Smart Money Watcher
After=network.target
[Service]
Type=simple
WorkingDirectory=/home/ubuntu/.hermes/scripts
ExecStart=/home/ubuntu/.hermes/venv-mona/bin/python -u mona_smart_money_watcher.py
Restart=always
RestartSec=5
[Install]
WantedBy=default.target
```
Enable: `systemctl --user daemon-reload && systemctl --user enable --now smart-money-watcher.service`

## Smart Money Watcher v5+ Enhancements (June 2026)

### Liquidity Filter
Skip tokens with liquidity < $1,000 to avoid dust/scam/no-liq alerts:
```python
MIN_LIQUIDITY = 1_000
liq = td.get("liquidity_usd", 0) or 0
if liq < MIN_LIQUIDITY:
    continue  # skip
```

### Project Links from DexScreener
DexScreener API returns `info` object with `websites[]` and `socials[]` arrays. Extract and include in alerts:
```python
info = d.get("info", {})
websites = info.get("websites", [])
if websites:
    result["website"] = websites[0].get("url") if isinstance(websites[0], dict) else websites[0]
socials = info.get("socials", [])
for s in socials:
    s_type = s.get("type", "").lower()  # "twitter", "telegram", "discord"
    s_url = s.get("url", "")
```
Include in alert links: 🌐 Website, 🐦 Twitter, 📱 Telegram, 💬 Discord. Remove hardcoded Aerodrome swap links — use project links instead.

### Social Context Enrichment (Deployer + Buyer)
Module: `~/.hermes/scripts/mona_social_context.py`

**Deployer detection via Alchemy binary search:**
1. Binary search for contract creation block using `eth_getCode` (check if code exists at block N)
2. Once found (within 100-block range), linear scan to exact block
3. For each tx in that block, get receipt and check `contractAddress` or logs matching the target contract
4. First match = deployer's `from` address

**Why not BaseScan/Etherscan:** BaseScan API v1 deprecated. Etherscan V2 free tier doesn't support Base chain (returns "Free API access is not supported for this chain"). Blockscout doesn't expose `contractCreator` directly.

**DeBank API status (June 2026):** Public endpoints (`/user/address/{addr}`, `/user/{addr}`, `/user/addr/{addr}`) all return 404. The old DeBank Cloud API is no longer publicly accessible. Wallet social profile lookup is currently broken — need alternative (Zapper API also 404).

**Integration pattern:**
```python
from mona_social_context import get_social_context, format_social_context, score_deployer_reputation

# Before sending alert:
social_ctx = get_social_context(token_addr, wallet_addr)
deployer_rep = score_deployer_reputation(social_ctx)
social_text = format_social_context(social_ctx)
msg += f"\n\n{social_text}"
```

## Alert Format (Smart Money)

```
🟢 SMART MONEY BUY — $SYMBOL (BASE)
━━━━━━━━━━━━━━━━━━━━━━

🐋 Wallet Label
👤 0x...address

💰 Got: 1234.56 TOKEN
📊 Via: Aerodrome
🪙 Token: Name ($SYMBOL)

💎 Price: $0.001234
🧢 MC: $1.2M | FDV: $2.5M
💧 Liquidity: $50K
📊 Vol 24h: $120K | 1h: $8K
📈 24h: 🟢 +45.2% | 1h: 🟢 +5.1%
🔄 Txns 24h: 🟢150 🔴80 (65% buy)
⏰ Age: 3.2h

🟢 Risk: 2/5 — 🆕 <1h old · 💧 Thin liq

📄 0x...contract
📊 Chart · 🔄 Swap · 👤 DeBank

⚡ 2026-06-06 18:00 WIB — REAL-TIME
```

## Pitfalls

- **CRON DOUBLE-SEND (critical)**: When a `no_agent` cron script calls `send_message()` AND the cron delivers stdout, messages get sent TWICE to the same topic. Fix: either (a) remove `send_message()` from script and just `print()` the message (cron delivers stdout), OR (b) keep `send_message()` and set cron `deliver: 'local'`. NEVER both. This caused "2 bot" duplicate alerts for alpha scanner.
- **`hermes send` CLI syntax for cron delivery**: The correct syntax is `hermes send -t "telegram:CHAT_ID:THREAD_ID" "message"` or `hermes send -t "telegram:CHAT_ID:THREAD_ID" -f /tmp/file.txt`. The flag `-m` is for MODEL, NOT message — using `-m` causes `error: unrecognized arguments`. For messages with `$` signs (common in crypto: `$TEA`, `$BTC`), ALWAYS write to a temp file first and use `-f` to avoid shell interpolation eating the dollar signs. Pattern: `write_file("/tmp/alert.txt", msg)` then `terminal('hermes send -t "telegram:CHAT_ID:THREAD_ID" -f /tmp/alert.txt')`.
- **Telegram send "Unauthorized"**: `hermes send` returns `Telegram send failed: Unauthorized` when the bot token is invalid, bot was removed from the group, or bot lacks permissions. In cron jobs (no user present), output the report as stdout fallback — the cron system delivers it. Don't retry endlessly.
- **Cron job `script` parameter**: MUST be a filename relative to `~/.hermes/scripts/` (e.g. `whale_monitor.py`). NOT inline code, NOT absolute paths. Copy scripts there first: `cp path/to/script.py ~/.hermes/scripts/`. Inline code in `script` param gets interpreted as a file path and fails with "Script not found".
- `dlmm-api.meteora.ag` returns 403/404 — use `dlmm.datapi.meteora.ag` instead
- Helius `getTokenLargestAccounts` returns TOKEN ACCOUNT addresses, not wallet owners — must call `getAccountInfo` with `jsonParsed` encoding to get `owner` field. Two-step process: (1) get token accounts, (2) resolve each account to owner wallet.
- **Nitter instances are ALL DEAD as of June 2026** (privacydev=timeout, poast=403, adminforge=301, sneed=525). Code must: (1) short timeout (5s not 15s), (2) track `_NITTER_DEAD` set to skip dead instances for rest of session, (3) break early if all instances dead, (4) 60s max SIGALRM on full intel cycle's Twitter phase. Without these, full intel cycle hangs 5+ minutes.
- **Twitter/X login from VPS is BLOCKED (June 2026)** — Twitter detects VPS IP and shows "We've temporarily limited your login." The VPS IP (43.163.85.51) is permanently flagged. Browser-based Twitter login will NOT work. Workaround: user must provide cookies from their local browser. See mona-provider-health skill for cookie extraction steps.
- **Full intel cycle performance**: whale discovery runs Helius RPC per pool (slow). Skip discovery if `whale-db.json` last_update < 6 hours ago and has >10 whales. Only run `monitor` (fast) on subsequent cycles.
- Rate limit: 0.2-0.5s between Helius calls, 1.5s between Nitter scrapes
- `seen-txs.json` dedup cache grows — trimmed to last 5000 automatically
- Solana CLI install fails on some VPS (SSL error with `release.solana.com`) — fallback: use Node.js `@solana/web3.js` `Keypair.generate()` for keypair generation
- `no_agent: true` cron jobs run script stdout verbatim — empty stdout = silent (no message sent), which is the watchdog pattern for "nothing to report"
- Puppeteer for headless PNG capture: needs `--no-sandbox --disable-setuid-sandbox` flags on VPS, write capture script to file (bash `$` interpolation breaks inline node -e with puppeteer selectors)
- **Deployer ≠ Whale (CRITICAL)** — When building alert messages, the "Dev" label should show the CONTRACT DEPLOYER (who created the token), NOT the whale/buyer. The watcher fetches deployer info via `social_ctx['deployer']` from `mona_social_context.get_social_context()`. Pass this as `deployer_info` to the alert formatter, NOT the whale's address. If deployer info is unavailable, fall back to showing whale as "🐋 Buyer" instead of "👨‍💻 Dev". Implementation: `deployer_info = {"address": dep["address"], "twitter": ..., "debank": ...}` from `social_ctx["deployer"]`. NEVER pass `w["address"]` (whale) as deployer_info.
- **Systemd service = auto-restart trap** — The `smart-money-watcher.service` has `Restart=always`. When you `kill -9` the process, systemd restarts it within 5 seconds. To actually stop it: `systemctl --user stop smart-money-watcher && systemctl --user disable smart-money-watcher`. For permanent removal: also delete `~/.config/systemd/user/smart-money-watcher.service` and `systemctl --user daemon-reload`. Check with: `ps -o ppid= -p <PID>` → if parent is `systemd --user`, it's a service-managed process.
- **Browser extraction for JS-heavy sites**: When `web_extract` returns empty (common with crypto news sites), use `browser_navigate` + `browser_console` to extract article text via JS:
  ```
  browser_navigate(url)
  browser_console(expression='Array.from(document.querySelectorAll("article p")).map(p=>p.textContent.trim()).filter(t=>t.length>20).join("\\n\\n")')
  ```
  This returns clean paragraph text without needing full snapshot parsing. Works on Blockchain Reporter, CoinDesk, The Block, and most WordPress-based crypto news sites.
