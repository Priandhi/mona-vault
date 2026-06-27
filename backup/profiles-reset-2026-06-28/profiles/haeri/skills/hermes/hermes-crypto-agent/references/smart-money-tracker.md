# Smart Money Tracker — Technical Reference

## Architecture: v5 Alchemy-Powered Daemon (Current)

**Script:** `~/.hermes/scripts/mona_smart_money_watcher.py`
**Systemd:** `smart-money-watcher.service` (user-level, auto-restart)
**Poll interval:** 30 seconds (Alchemy has no rate limit, but DexScreener enrichment needs breathing room)
**Topic:** 💎 Alpha (13)
**Components:**
- `mona_whale_registry.py` — Data layer: wallets, holdings, trades, win rate, multi-whale detection
- `mona_token_deep_scanner.py` — GoPlus security + dev wallet + holder concentration + social presence
- `mona_smart_money_watcher.py` — Main daemon: Alchemy detection + DexScreener enrichment + GoPlus security

### How it works (v5 Alchemy)
1. Poll `eth_blockNumber` every 1 second (cheap ~10 CU)
2. When new block detected → fetch `alchemy_getAssetTransfers` for all tracked wallets (~25 CU per wallet)
3. Filter incoming transfers (buys) and outgoing transfers (sells)
4. Skip IGNORED_TOKENS (WETH, USDC, USDT, DAI, USDbC)
5. Enrich via DexScreener for MC, liq, vol, price action
6. GoPlus security check (honeypot, sell tax, mint, pause)
7. MC filter ($5K-$1M range)
8. Record trade in whale registry, update holdings
9. Enhanced alert with win rate + holder heatmap + security score
10. Multi-whale convergence check (3+ whales → 🔥🔥🔥 SUPER ALERT)

### Evolution
- v1: Cron-based (5min) — too slow, user said "telat"
- v2: Block-aware daemon (1s) — Alchemy `eth_blockNumber` + `getAssetTransfers`
- v3: Zerion daemon (5s) — `operation_type=trade` + `direction=in/out`
- v4: Zerion + Whale Registry + GoPlus — enhanced alerts with win rate, security, holder heatmap
- v5: Alchemy + Whale Registry + GoPlus — **replaced Zerion due to persistent 429 rate limits**

## Alchemy API (Primary — No Rate Limit!)

**Endpoint:** `https://base-mainnet.g.alchemy.com/v2/{key}`
**Key:** `LUnQ5tB09bfQQGQ5Ri_MH`
**Rate limit:** 300M compute units/month (effectively unlimited for our use case)

**Key methods:**
```python
# Get current block
eth_blockNumber → hex block number

# Get ERC-20 transfers to/from wallet
alchemy_getAssetTransfers([{
    "fromBlock": hex(from_block),
    "toBlock": hex(to_block),
    "toAddress": wallet,        # for buys
    "fromAddress": wallet,      # for sells
    "category": ["erc20"],
    "maxCount": "0x32",
    "withMetadata": True,
    "excludeZeroValue": True
}])
```

**Cost per cycle (2 wallets × 2 calls):**
- `eth_blockNumber`: ~10 CU × 30/day = 300 CU/day
- `getAssetTransfers` × 4: ~100 CU × 30/day = 3,000 CU/day
- Total: ~3,300 CU/day = 0.001% of monthly budget

## Zerion API (Fallback Only — Severe Rate Limits!)

**Auth:** `Authorization: Basic base64("{api_key}:")`
**Key:** stored in `vault/.zerion_api_key`
**Rate limit:** 3 req/sec nominal, BUT persistent 429 errors after burst

**PITFALL (June 2026):** Zerion free tier has **persistent rate limiting** that doesn't reset quickly. Adding 8 wallets simultaneously caused 429 errors that lasted 30+ minutes. Even single requests returned 429 for extended periods. The rate limit seems to be per-minute or per-hour, not per-second. **Do NOT use Zerion for batch monitoring of multiple wallets.** Use Alchemy instead — no rate limit.

**PITFALL:** When Zerion hits 429, retry with exponential backoff (2s, 4s, 6s) max 3 attempts. If all fail, skip that wallet for the cycle.

## DexScreener Enrichment

**Endpoint:** `GET /tokens/v1/base/{contract}`

**Fields to extract:**
```python
{
    "price_usd": d.get("priceUsd"),
    "market_cap": d.get("marketCap") or d.get("fdv") or 0,
    "fdv": d.get("fdv") or 0,
    "liquidity_usd": d.get("liquidity", {}).get("usd", 0),
    "volume_24h": d.get("volume", {}).get("h24", 0),
    "volume_1h": d.get("volume", {}).get("h1", 0),
    "price_change_24h": d.get("priceChange", {}).get("h24", 0),
    "price_change_1h": d.get("priceChange", {}).get("h1", 0),
    "txns_buys_24h": d.get("txns", {}).get("h24", {}).get("buys", 0),
    "txns_sells_24h": d.get("txns", {}).get("h24", {}).get("sells", 0),
    "pair_created": d.get("pairCreatedAt"),
    "dex_url": d.get("url"),
}
```

## Token Filtering (CRITICAL)

```python
IGNORED_TOKENS=***    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",  # USDC
    "0x50c5725949a6f0c72e6c4a641f24049a917db0cb",  # DAI
    "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2",  # USDT
    "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca",  # USDbC
    "0x4200000000000000000000000000000000000006",  # WETH
    "",  # native ETH
}
```

Without WETH in ignore list: wrapping/unwrapping triggers false "WETH bought" alerts.

## Risk Scoring

```python
risk = 1
if liq < 5000: risk += 2; reasons.append("⚠️ Low liq")
elif liq < 20000: risk += 1; reasons.append("💧 Thin liq")
if age_hours < 1: risk += 1; reasons.append("🆕 <1h old")
if sells > 0 and buys > 0 and sells/(buys+sells) > 0.6:
    risk += 1; reasons.append("📉 Sell pressure")
if mc > 0 and mc < 50000: risk += 1; reasons.append("🔬 Micro cap")
risk = min(5, max(1, risk))
emoji = ["", "🟢", "🟡", "🟠", "🔴", "⛔"][risk]
```

## Systemd Service

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
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=default.target
```

**PITFALL:** Do NOT add `User=ubuntu` — causes `status=216/GROUP`. User-level services auto-run as logged-in user.

## State Management
- `~/.hermes/scripts/.smart_money_state.json` — seen TX hashes (capped at 500)
- `~/.hermes/scripts/.seen_smart_buys.json` — cooldown tracking (pruned after 1h)
- `~/.hermes/scripts/.smart_money_wallets.json` — watchlisted wallets

## Adding Wallets
```python
# Edit .smart_money_wallets.json
[
    {"address": "0x...", "label": "Whale Name", "tier": "🐋"},
    {"address": "0x...", "label": "Smart Trader", "tier": "🧠"},
]
```
Restart service after changes: `systemctl --user restart smart-money-watcher`

## Whale Registry (`mona_whale_registry.py`)

Data layer for smart money tracking. Stores wallets, holdings, trades, and calculates win rates.

**Data file:** `~/.hermes/scripts/.whale_registry.json`

**Key functions:**
```python
load_wallets() → list of wallet dicts
add_wallet(address, label, tier) → add new whale
get_wallet(address) → wallet info
update_holdings(address, contract, action, amount, price) → track buy/sell positions
get_holdings(address) → dict of current positions
get_token_whale_count(contract) → how many tracked whales hold this token
get_token_whale_list(contract) → list of whale wallets holding this token
record_trade(address, contract, symbol, action, price, amount, value_usd, tx_hash) → log trade
calculate_stats(address) → {wins, losses, win_rate, avg_profit, total_pnl}
check_multi_whale(contract, min_whales=3) → {is_multi_whale, count, whales}
```

**CLI usage:**
```bash
~/.hermes/venv-mona/bin/python ~/.hermes/scripts/mona_whale_registry.py list
~/.hermes/venv-mona/bin/python ~/.hermes/scripts/mona_whale_registry.py add 0xabc... "Whale Name"
~/.hermes/venv-mona/bin/python ~/.hermes/scripts/mona_whale_registry.py leaderboard
```

## Token Deep Scanner (`mona_token_deep_scanner.py`)

Security + dev history + holder concentration + social presence check.

**APIs used:**
- GoPlus Security (`api.gopluslabs.io`) — honeypot, sell tax, mint, pause, blacklist, hidden owner, selfdestruct, proxy, trust list, holder count, top 10 holder %
- Alchemy (`eth_getBalance`) — dev wallet balance check
- DexScreener (`/tokens/v1/base/{CA}`) — social links (Twitter, Telegram, Website)

**Security score (0-10):**
- Start at 10
- -10 if honeypot
- -3 if not open source
- -2 if buy tax > 10%
- -3 if sell tax > 10%
- -2 if can mint
- -2 if can pause
- -2 if can blacklist
- -2 if hidden owner
- -3 if selfdestruct
- +1 if trust list
- +1 if ownership renounced

**CLI usage:**
```bash
~/.hermes/venv-mona/bin/python ~/.hermes/scripts/mona_token_deep_scanner.py 0xabc...
```

## MC Filter (Configurable)

```python
MIN_MARKET_CAP = 5000      # Skip dust/scam tokens
MAX_MARKET_CAP = 1000000   # Skip established tokens (not early stage)
MIN_LIQUIDITY = 1000       # Skip no-liquidity tokens ($1K minimum)
```

Tokens outside this range are skipped silently (logged to stderr but no alert sent).

**Filter order:** MC filter → Liquidity filter → Security check → Alert. Always check liquidity BEFORE sending alerts — tokens with $0 liquidity are untradeable dust.

## Alpha Alert Format v2 (June 2026)

Clean, minimal, premium format with proper deployer info and clickable HTML links.

**Module:** `~/.hermes/scripts/mona_alpha_alert_clean.py`

**Three alert types:**
1. `format_clean_alert(token_data, whale_info, security, deployer_info, fee_recipient)` — single whale buy
2. `format_multi_whale_clean(token_data, whale_list, security, deployer_info)` — 3+ whales converge
3. `format_sell_alert_clean(token_data, whale_info, sell_amount, sell_value_usd, pnl_pct, pnl_usd)` — whale sell

**Example output (single buy):**
```
💎 $BUNTER · BASE

📊 MC $50K · VOL $12K · 57tx/1h
📈 24h +150.0% · ⏳ 2h
🛡️ ✅ Safe · ⚠️ Unverified · 0% Tax

📄 CA: <a href="https://basescan.org/address/0x...">0x1234…5678</a>
👨‍💻 Dev: <a href="https://debank.com/profile/0x...">0xabcd…ef12</a>
   🐦 <a href="https://twitter.com/bunterdev">bunterdev</a>
<a href="https://dexscreener.com/...">📊 Chart</a> · <a href="https://twitter.com/...">🐦 X</a> · <a href="https://basescan.org/...">🔍 Scan</a>
```

**Key patterns:**
- ALL links use HTML `<a href>` — Telegram `parse_mode="HTML"` makes them clickable
- CA links to BaseScan/Etherscan
- Dev address links to DeBank profile
- Twitter shows just handle (not full URL)
- Chart links to DexScreener
- Scan links to block explorer
- `deployer_info` = actual contract deployer (from `get_social_context`)
- `whale_info` = the buyer/tracked wallet (NOT the dev)
- If `deployer_info` is None, formatter shows "🐋 Buyer" instead of "👨‍💻 Dev"
- `fee_recipient` dict with `{address, twitter, debank}` for bankr.bot etc.
- `get_launchpad_info()` auto-detects launchpad from DexScreener `dex_id` field

**Custom emoji attempt (FAILED, don't retry):**
Tried using Telegram premium custom emoji from CryptachEmoji4 pack. Built `mona_emoji.py` with 200 emoji IDs, `send_premium_message()` with JSON body entities. Technically worked (sent with entities), but:
- Many emoji missing from pack (⚠️, 💸, 🔗, 🐦, 🐋, 📤)
- Required substitutions (🐦→🦅, 🐋→🐂, 👨‍💻→🧑‍💻, ⚠️→⚡)
- Offset tracking for entities is fragile
- `parse_mode="HTML"` + `entities` interaction unclear
- Not worth the complexity — standard Unicode emoji + clickable HTML links = good enough
- Files left in place (`mona_emoji.py`) but UNUSED by watcher
- `get_launchpad_info()` auto-detects launchpad from DexScreener `dex_id` field

**Watcher integration (correct pattern):**
```python
from mona_alpha_alert_clean import format_clean_alert, format_multi_whale_clean

# Build deployer_info from social context (NOT from whale_info!)
deployer_info = None
if social_ctx and social_ctx.get("deployer") and social_ctx["deployer"].get("address"):
    dep = social_ctx["deployer"]
    deployer_info = {"address": dep["address"]}
    if dep.get("twitter"):
        deployer_info["twitter"] = f"https://twitter.com/{dep['twitter']}" if not dep["twitter"].startswith("http") else dep["twitter"]
    deployer_info["debank"] = f"https://debank.com/profile/{dep['address']}"

msg = format_clean_alert(td, w, security, deployer_info=deployer_info)
send_message(TOPIC_ALPHA, msg)
```

**PITFALL:** Do NOT pass whale/buyer address as deployer. The `whale_info` param is the BUYER. Use `deployer_info` for the actual contract creator. Without `deployer_info`, alerts show "🐋 Buyer: 0x..." instead of "👨‍💻 Dev: 0x...".

**PITFALL:** `send_message()` in `mona_telegram.py` defaults to `parse_mode="HTML"`. HTML `<a href>` links work out of the box. If HTML parsing fails, it auto-retries without parse_mode.

## Social Context Enrichment

When a whale buys a token, enrich the alert with deployer and buyer social profiles:

**Components:**
- `mona_social_context.py` — Deployer detection + wallet profile lookup
- `mona_alpha_alert_clean.py` — Clean alert formatter (v2, June 2026)
- Deployer: found via Alchemy binary search
- Wallet profiles: from DeBank API

**Integration point (v2 — June 2026):** After building social context, build `deployer_info` dict and pass to formatter. See "Alpha Alert Format v2" section above for the correct pattern.

**CRITICAL BUG FIX (June 2026):** The watcher was passing whale (buyer) address as "Dev" to the alert formatter. The `whale_info` parameter is the BUYER, not the deployer. Always use `deployer_info` for the actual contract deployer.

**CRITICAL — Platform separation:** Each social platform has its own emoji and URL:
- 🐦 Twitter → `https://twitter.com/handle`
- 📱 Telegram → `https://t.me/username`
- 💬 Discord → plain text (no public profile URL)
- 🐙 GitHub → `https://github.com/username`

NEVER mix Twitter handles with Telegram links.

**Rate limiting:** Deployer lookup uses ~20-30 Alchemy API calls (binary search). Add 200ms delay between calls, cache for 1 hour, max 1 lookup per 5 seconds.

## Sell Detection

Sell detection uses outgoing ERC-20 transfers:
```python
# Get transfers FROM wallet
alchemy_getAssetTransfers([{
    "fromAddress": wallet,
    "category": ["erc20"],
    ...
}])
```

For each outgoing transfer:
1. Skip if token is in IGNORED_TOKENS (stables, WETH)
2. Skip if recipient is the same wallet (self-transfer)
3. Enrich via DexScreener
4. Calculate PnL from whale registry holdings
5. Send sell alert with entry/exit price and PnL
6. Update holdings (reduce position)

## Multi-Whale Convergence

When 3+ tracked whales buy the same token, a 🔥🔥🔥 SUPER ALERT is sent AFTER the individual buy alert.

Detection:
```python
from mona_whale_registry import check_multi_whale
result = check_multi_whale(token_contract, min_whales=3)
if result["is_multi_whale"]:
    # Send convergence alert with list of whales and their win rates
```

## Adding Wallets (One-by-One!)

**PITFALL:** Add wallets ONE AT A TIME, not all at once. When using Zerion (fallback), adding 8 wallets simultaneously caused persistent 429 rate limits that lasted 30+ minutes. Even with Alchemy (no rate limit), adding one-by-one is safer for initial state management.

```python
# Correct: add 1, restart, verify, add next
from mona_whale_registry import add_wallet
add_wallet("0xabc...", "Whale 1", "🐋")
# restart service, verify no errors, then add next
```
