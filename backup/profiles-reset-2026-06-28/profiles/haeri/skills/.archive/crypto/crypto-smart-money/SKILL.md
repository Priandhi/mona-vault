---
name: crypto-smart-money
description: "Smart money / whale wallet tracking on EVM chains. Covers DexScreener enrichment, Zerion API integration, real-time watcher architecture, token filtering, and alert formatting."
triggers:
  - smart money tracking
  - whale monitoring
  - wallet tracking
  - buy detection
  - token enrichment
  - DexScreener
  - Zerion API
---

# Crypto Smart Money Tracking

Track whale/informed trader wallets for new buys. Detect DEX swaps, enrich with market data, format rich alerts, deliver in real-time.

## Architecture Evolution

Four iterations, each improving on the last:

### v1: Cron-based polling (5min)
- Script runs via no_agent cron every 5 minutes
- Fetches Alchemy `getAssetTransfers` for watchlisted wallets
- Enriches from DexScreener
- **Problem**: 5min delay = missed fast-moving trades

### v2: Block-aware daemon (1s)
- Background daemon polls `eth_blockNumber` every 1s (cheap, ~10 CU)
- Only fetches transfers when new block detected (~2s on Base)
- **Problem**: Alchemy only has raw transfers, no trade classification

### v3: Zerion-powered daemon (5s)
- Polls Zerion `/wallets/{addr}/transactions` every 5s
- `operation_type=trade` filter = only swaps, not transfers
- `direction=in/out` = know exactly what was bought vs sold
- `fungible_info` = token name, symbol, icon, price, value USD
- No need for block tracking — Zerion handles it

### v4: Zerion + Whale Registry ← **CURRENT BEST**
Everything from v3, plus:
- **Whale Registry**: Separate data layer for wallets, holdings, trade history
- **Multi-whale convergence**: 3+ whales buying same token = 🔥🔥🔥 SUPER ALERT
- **Win rate tracking**: Per-whale performance (win rate, avg profit, PnL)
- **Sell detection**: Track sells with PnL calculation (entry vs exit)
- **Holder heatmap**: Show how many tracked whales hold each token
- **GoPlus security**: Honeypot detection, tax checks, contract audit
- **Token deep scan**: Dev wallet, holder concentration, social presence
- **MC filter**: Only alert tokens in $5K-$1M range (configurable)
- **Honeypot auto-skip**: Never alert on honeypot tokens

## Data Sources

### GoPlus Security API (free, no auth)
```
GET https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={contract}
```
Chain ID: 8453 (Base), 1 (Ethereum), 56 (BSC)

**Returns (critical fields):**
- `is_honeypot` — "1" = CANNOT SELL (auto-skip!)
- `is_open_source` — "1" = contract verified
- `buy_tax` / `sell_tax` — percentage (skip if sell_tax > 10%)
- `can_take_back_ownership` — "1" = rug risk
- `hidden_owner` — "1" = rug risk
- `is_mintable` — "1" = can inflate supply
- `can_pause` — "1" = can freeze trading
- `is_blacklisted` — "1" = can block wallets
- `selfdestruct` — "1" = can destroy contract
- `holder_count` — number of holders
- `top_10_holder_rate` — top 10 concentration (0-1)
- `trust_list` — "1" = in GoPlus trust list

**Security scoring:**
```python
score = 10
if is_honeypot: score -= 10      # Instant fail
if not is_open_source: score -= 3
if buy_tax > 10: score -= 2
if sell_tax > 10: score -= 3
if can_mint: score -= 2
if can_pause: score -= 2
if can_blacklist: score -= 2
if hidden_owner: score -= 2
if selfdestruct: score -= 3
if top_10_holder_rate > 0.8: score -= 2
if trust_list: score += 1
if renounced: score += 1
```

### DexScreener API (no auth required)
```
GET https://api.dexscreener.com/tokens/v1/{chain}/{contract}
```
Returns: priceUsd, marketCap, fdv, liquidity, volume (24h/6h/1h), priceChange (24h/1h/5m), txns (buys/sells), pairCreatedAt, url.

**Key fields for enrichment:**
- `marketCap` / `fdv` — market cap / fully diluted valuation
- `liquidity.usd` — pool liquidity
- `volume.h24` / `volume.h1` — trading volume
- `priceChange.h24` / `priceChange.h1` — price movement
- `txns.h24.buys` / `txns.h24.sells` — buy/sell pressure
- `pairCreatedAt` — token age (ms timestamp)

**Rate limit**: ~300 req/min, use `time.sleep(0.3)` between calls.

**Project links extraction (from `info` field):**
```python
info = d.get("info", {})
websites = info.get("websites", [])
if websites:
    result["website"] = websites[0].get("url") if isinstance(websites[0], dict) else websites[0]
socials = info.get("socials", [])
for s in socials:
    if isinstance(s, dict):
        s_type = s.get("type", "").lower()
        s_url = s.get("url", "")
        if s_type == "twitter": result["twitter"] = s_url
        elif s_type == "telegram": result["telegram"] = s_url
        elif s_type == "discord": result["discord"] = s_url
```
Use these links in alerts instead of hardcoded DEX swap URLs.

### Zerion API (requires API key)
```
Basic auth: base64("{api_key}:")
Authorization: Basic {base64_encoded}
```

**Key endpoints:**
- `GET /wallets/{addr}/transactions/` — transaction history
  - `filter[chain_ids]=base` — filter by chain
  - `filter[operation_types]=trade` — only swaps
  - `filter[trash]=no_filter` — include all
  - `page[size]=N` — pagination
- `GET /wallets/{addr}/portfolio/` — portfolio overview

**Trade response structure:**
```json
{
  "attributes": {
    "operation_type": "trade",
    "hash": "0x...",
    "transfers": [
      {
        "fungible_info": {"name": "...", "symbol": "...", "implementations": [...]},
        "direction": "in",  // what wallet RECEIVED
        "quantity": {"float": 123.45},
        "value": 50.0,  // USD value
        "price": 0.4
      }
    ]
  }
}
```

**To get Base chain contract address:**
```python
contract = None
for impl in fungible.get("implementations", []):
    if impl.get("chain_id") == "base":
        contract = impl.get("address")
        break
```

## Token Filtering (CRITICAL)

**ALWAYS exclude these from buy detection** — they are swap inputs/outputs, not actual buys:
```python
IGNORED_TOKENS = {
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",  # USDC
    "0x50c5725949a6f0c72e6c4a641f24049a917db0cb",  # DAI
    "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2",  # USDT
    "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca",  # USDbC
    "0x4200000000000000000000000000000000000006",  # WETH
    "",  # native ETH
}
```

Without this filter, every swap WETH→TOKEN will also trigger a "TOKEN bought" alert AND a "WETH received" alert.

## Known DEX Routers on Base
```python
DEX_ROUTERS = {
    "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43": "Aerodrome",
    "0x2626664c2603336E57B271c5C0b26F421741e481": "Uniswap V3",
    "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD": "Uniswap Universal",
    "0x6fB3e0A12C3E6C1a5D5C5c2f0dB2E68deC0Ff083": "Aerodrome Slipstream",
    "0x111111125421cA6dc452d289314280a0f8842A65": "1inch",
    "0xDef1C0ded9bec7F1a1670819833240f027b25EfF": "0x Protocol",
}
```

## Risk Scoring (1-5)
```python
risk = 1
if liquidity < 5000: risk += 2       # "⚠️ Low liq"
elif liquidity < 20000: risk += 1    # "💧 Thin liq"
if age_hours < 1: risk += 1          # "🆕 <1h old"
if sell_ratio > 0.6: risk += 1       # "📉 Sell pressure"
if market_cap < 50000: risk += 1     # "🔬 Micro cap"
# emoji: 🟢1 🟡2 🟠3 🔴4 ⛔5
```

## Whale Registry Pattern

Separate data layer from detection/analysis layers:

```
mona_whale_registry.py      — Data layer (wallets, holdings, trade history, stats)
mona_token_deep_scanner.py  — Analysis layer (GoPlus, dev wallet, holders, social)
mona_smart_money_watcher.py — Detection layer (Zerion polling, alert formatting)
```

**Data files (JSON):**
- `.whale_registry.json` — Wallet list with labels and tiers
- `.whale_holdings.json` — Holdings per whale: `{wallet: {token: {amount, avg_cost, first_buy}}}`
- `.whale_trade_history.json` — All trades for PnL calculation

**Win rate calculation (average cost basis):**
1. Group trades by token per whale
2. For completed trades (sold ≥80% of bought): PnL = revenue - (avg_entry × sold_amount)
3. Win rate = wins / completed_trades
4. Avg profit = mean(profit_pct) across all completed trades

**Multi-whale convergence:**
```python
def check_multi_whale(token_contract, min_whales=3):
    # Count how many tracked whales currently hold this token (amount > 0)
    # If count >= min_whales → send 🔥🔥🔥 CONVERGENCE ALERT
```

**Sell detection (via Zerion):**
When `direction=out` on a non-stable/non-WETH token → it's a sell.
Calculate PnL: `(exit_price - avg_entry_price) / avg_entry_price * 100`

## Alert Format — Clean Minimal (v2, CURRENT)

User explicitly rejected verbose v4 format. Wants **clean, minimal, emoji-premium** alerts.
No whale tracking details, no entry/SL/TP, no risk scores in the alert. Just the essentials.

### Design Principles
- **Minimal lines** — only show what matters (token, metrics, safety, dev, links)
- **Clickable links** — use Telegram HTML `<a href="url">text</a>`, strip `https://` from display text
- **Deployer ≠ Whale** — "Dev" = contract deployer (from social context), NOT the buying whale
- **Fee recipient** — show bankr.bot fee recipient with social links when available
- **No verbose sections** — no risk scores, no whale holder heatmap, no win rate in alert

### Implementation: `mona_alpha_alert_clean.py`
Separate module with 3 functions:
- `format_clean_alert(token_data, whale_info, security, deployer_info, fee_recipient)` — single whale buy
- `format_multi_whale_clean(token_data, whale_list, security, deployer_info)` — 3+ whales
- `format_sell_alert_clean(token_data, whale_info, sell_amount, sell_value_usd, pnl_pct, pnl_usd)` — sell

Watcher imports: `from mona_alpha_alert_clean import format_clean_alert, format_multi_whale_clean`

### Premium Emoji (Attempted → Dropped)
Custom emoji from CryptachEmoji4 pack was attempted but dropped in favor of simple HTML links. The `mona_emoji.py` helper and `send_premium_message()` still exist but are NOT used by the watcher. The watcher uses plain `send_message()` with HTML parse mode.

**Why dropped:** Added complexity (emoji substitution, ZWJ sequence matching, entity offset tracking, JSON body requirement) without clear user-visible benefit. User was satisfied with clean HTML links instead.

**Current data flow (simple HTML):**
```python
from mona_alpha_alert_clean import format_clean_alert
from mona_telegram import send_message, TOPIC_ALPHA

msg = format_clean_alert(td, w, security, deployer_info=deployer_info)
send_message(TOPIC_ALPHA, msg)  # HTML parse_mode by default
```

### Clickable HTML Links
All links in alerts are `<a href>` tags rendered via Telegram's HTML parse mode:

```python
def _link(text, url):
    """Create Telegram HTML link."""
    return f'<a href="{url}">{text}</a>'
```

**Link targets:**
- **CA** → `https://basescan.org/address/{ca}` (or etherscan.io for ETH)
- **Dev address** → `https://debank.com/profile/{dev_addr}`
- **Twitter handle** → `https://twitter.com/{handle}` (strip `https://` from display)
- **Chart** → DexScreener URL from enrichment
- **Scan** → Same as CA link (BaseScan/Etherscan)

**Display text:** Strip `https://` prefix for cleaner look. Twitter shows handle only, not full URL.

### Data Flow (CRITICAL)
```
Watcher detects buy
  → get_social_context(token_addr, wallet_addr) → {deployer: {address, twitter, ...}, buyer: {...}}
  → Build deployer_info dict from social_ctx["deployer"]
  → Pass deployer_info to format_clean_alert() — NOT whale address
  → send_message(TOPIC_ALPHA, msg)
```

**Common bug:** Passing whale/buyer address as deployer. The `deployer_info` param MUST come from `social_ctx["deployer"]`, not from `w` (whale dict).

### Buy Alert (Clean, with clickable HTML links)
```
💎 $SYMBOL · BASE

🚀 Virtuals Protocol
📊 MC $649K · VOL $72K · 581tx/1h
📈 24h +70.7% · ⏳ 1d
🛡️ ✅ Safe · ✅ Verified · 0% Tax

📄 CA: 0x296e…A76f ← links to BaseScan
👨‍💻 Dev: 0x384d…78b3 ← links to DeBank
   🐦 devhandle ← links to Twitter
   🌐 debank.com/profile/0x... ← links to DeBank
💸 Fee → 0xdead…beef ← links to DeBank
   🐦 bankrdotbot ← links to Twitter
📊 Chart · 🐦 X · 🔍 Scan ← all clickable
```

### Multi-Whale Alert (Clean, with clickable links)
```
💎🔴 $SYMBOL · BASE

🐋 3 whales · 1d window ← whale addresses link to DeBank
   0x1410… $12.0K · 0x539f… $8.5K · 0x8d73… $5.2K

📊 MC $649K · VOL $72K · 581 tx/1h
📈 1H +0.0% · 🕐 Age: 1d
🛡️ ✅ Safe · 0% Tax

📄 CA: 0x296e…A76f ← links to BaseScan
👨‍💻 Dev: 0x384d…78b3 ← links to DeBank
   🐦 devhandle ← links to Twitter
📊 Chart · 🐦 X · 🔍 Scan
```

### Sell Alert (Clean, with clickable links)
```
🔴 $SYMBOL · BASE

🐋 0xb511…dbb8 sold ← links to DeBank
📤 $1.3K
🟢 PnL: +45% (+$410)

📄 CA: 0x296e…A76f ← links to BaseScan
📊 Chart ← links to DexScreener
```

### Old Verbose Format (DO NOT USE — user rejected)
The v4 format with risk scores, whale holder heatmap, win rate, and verbose sections was explicitly rejected by user. Keep for reference only — never send this to Telegram.

### Market Maker / High-Frequency Trader Detection
Some wallets are market makers or HFT bots — they generate massive sell spam that drowns out real signals. Detect and remove them:

**Detection pattern:**
```python
# If wallet has >20 sells in last hour with same tokens repeating, it's likely HFT
trades = get_trade_history(address=wallet_addr, limit=30)
recent_sells = [t for t in trades if t.get('direction') == 'sell']
if len(recent_sells) > 20:
    # Check if same tokens repeating
    tokens = [t.get('symbol') for t in recent_sells]
    from collections import Counter
    counts = Counter(tokens)
    if any(c > 5 for c in counts.values()):
        print(f"⚠️ {wallet_addr[:10]} is likely HFT/market maker — consider removing")
```

**Action:** Remove from tracking with `remove_wallet(address)`. These wallets add noise without signal value.

## Implementation Files (v4 Architecture)

| File | Purpose |
|---|---|
| `mona_alpha_alert_clean.py` | Alert formatting — clean minimal format with clickable HTML links, deployer, social links, fee recipient |
| `mona_emoji.py` | Custom emoji helper (UNUSED — dropped in favor of simple HTML links. Kept for reference only) |
| `mona_whale_registry.py` | Data layer — wallet CRUD, holdings tracking, trade history, win rate, leaderboard |
| `mona_token_deep_scanner.py` | Analysis — GoPlus security, dev wallet, holder concentration, social presence |
| `mona_smart_money_watcher.py` | Detection — Zerion polling, sell detection, multi-whale, alert formatting |
| `.whale_registry.json` | Whale wallet list with labels and tiers |
| `.whale_holdings.json` | Holdings per whale (token → amount, avg_cost) |
| `.whale_trade_history.json` | All trades for PnL calculation |
| `.smart_money_state.json` | Watcher state (seen_tx_hashes) |
| `.seen_smart_buys.json` | Cooldown tracking (wallet:token → timestamp) |

**CLI commands:**
```bash
python3 mona_whale_registry.py list          # List all tracked whales
python3 mona_whale_registry.py add <addr> <label>  # Add whale
python3 mona_whale_registry.py leaderboard   # Win rate ranking
python3 mona_whale_registry.py stats <addr>  # Single whale stats
python3 mona_token_deep_scanner.py <contract>  # Deep scan token
```

## Multi-Provider Fallback Architecture (v5, June 2026)

Single-provider systems fail silently when the API goes down. Use a **fallback chain with circuit breaker**:

```
Provider Chain: Alchemy (priority 1) → Zerion (priority 2) → Helius (priority 3)
```

### Circuit Breaker Pattern

```python
class ProviderChain:
    def __init__(self):
        self.providers = [
            {'name': 'alchemy', 'priority': 1, 'failures': 0, 'max_failures': 5, 'cooldown': 300, 'last_failure': 0},
            {'name': 'zerion',  'priority': 2, 'failures': 0, 'max_failures': 5, 'cooldown': 300, 'last_failure': 0},
            {'name': 'helius',  'priority': 3, 'failures': 0, 'max_failures': 5, 'cooldown': 300, 'last_failure': 0},
        ]
    
    def get_active_provider(self):
        now = time.time()
        for p in sorted(self.providers, key=lambda x: x['priority']):
            if p['failures'] >= p['max_failures']:
                if now - p['last_failure'] > p['cooldown']:
                    p['failures'] = 0  # Reset after cooldown
                else:
                    continue
            return p
        return None  # All providers down
    
    def record_failure(self, provider):
        provider['failures'] += 1
        provider['last_failure'] = time.time()
    
    def record_success(self, provider):
        provider['failures'] = 0  # Reset on success
```

### Provider API Keys

| Provider | Key Location | Chains | Rate Limit |
|----------|-------------|--------|------------|
| Alchemy | `vault/.alchemy_key` | ETH, Base, Arb | 300M CU/month |
| Zerion | `vault/.zerion_api_key` | 60+ chains | 3 req/sec |
| Helius | `vault/.meridian_env` (`HELIUS_API_KEY=`) | Solana + EVM | 10 req/sec |

**PITFALL:** Helius key is stored inside `.meridian_env` as `HELIUS_API_KEY=xxx`, not as a standalone file. Parse with:
```python
for line in vault.joinpath('.meridian_env').read_text().splitlines():
    if line.startswith('HELIUS_API_KEY='):
        helius_key = line.split('=', 1)[1].strip()
```

### Whale Scoring with Decay

```python
def calculate_decay_win_rate(trades):
    """Weight recent trades more heavily than old ones"""
    now = time.time()
    weighted_wins = 0
    total_weight = 0
    for trade in trades:
        age_days = (now - trade['timestamp']) / 86400
        weight = 0.95 ** age_days  # 5% decay per day
        total_weight += weight
        if trade['pnl'] > 0:
            weighted_wins += weight
    return weighted_wins / max(total_weight, 1)

def classify_whale(decay_win_rate, avg_trade_usd):
    if decay_win_rate >= 0.70 and avg_trade_usd >= 10000:
        return 'tier1_elite'  # 🏆 Elite — high conviction
    elif decay_win_rate >= 0.55 and avg_trade_usd >= 5000:
        return 'tier2_good'   # 🥈 Good — reliable
    else:
        return 'tier3_normal'  # 📊 Normal — follow with caution

def should_blacklist(whale):
    """Auto-blacklist whales with poor performance"""
    if whale['total_trades'] >= 5 and whale['win_rate'] < 0.30:
        return True  # Blacklist for 7 days
    return False
```

### Convergence Detection

When 3+ non-blacklisted whales buy the same token within 1 hour → convergence alert.

```python
def detect_convergence(recent_buys, min_whales=3, window_seconds=3600):
    """Detect when multiple whales buy same token"""
    token_buys = {}  # token → [(wallet, timestamp, amount)]
    for buy in recent_buys:
        token = buy['token']
        if token not in token_buys:
            token_buys[token] = []
        token_buys[token].append(buy)
    
    alerts = []
    for token, buys in token_buys.items():
        # Filter to window
        now = time.time()
        recent = [b for b in buys if now - b['timestamp'] < window_seconds]
        # Count unique non-blacklisted wallets
        unique_wallets = set(b['wallet'] for b in recent if not is_blacklisted(b['wallet']))
        if len(unique_wallets) >= min_whales:
            intensity = '🔥' * min(len(unique_wallets), 5)
            alerts.append({
                'token': token,
                'whales': len(unique_wallets),
                'total_usd': sum(b['amount_usd'] for b in recent),
                'intensity': intensity,
            })
    return alerts
```

## Pitfalls

### NoAgent cron double-send
If a no_agent cron script calls `send_message()` AND the cron system delivers stdout → **duplicate messages**. Choose ONE:
- Option A: Script handles delivery via `send_message()`, set cron `deliver: local`
- Option B: Script prints to stdout only, cron delivers. Debug output → stderr.

**Always use Option B for no_agent crons.** Debug prints go to `sys.stderr`, clean message goes to `sys.stdout`.

### State file management
- Save state periodically (every 10-12 cycles), not every cycle
- Prune seen entries older than 1-24 hours
- Use JSON for state (seen hashes, seen buys)
- Keep hash lists capped at 500 entries

### Systemd user service
- Don't set `User=` in user-level service files (causes `status=216/GROUP`)
- Use `systemctl --user` not `sudo systemctl`
- `Restart=always` + `RestartSec=5` for auto-recovery

### USDC/WETH filter must include ALL stablecoin addresses
If you miss even one stablecoin address, swaps will trigger false "buy" alerts.
Always lowercase the contract address before comparing:
```python
if token_addr.lower() in IGNORED_TOKENS:
    continue
```

### Zerion sell detection
Sells appear as `direction=out` on non-stable tokens. When wallet sends TOKEN and receives WETH:
- `received` list = WETH (filtered out by IGNORED_TOKENS)
- `sent` list = TOKEN (this is the sell!)
Check BOTH lists, not just received.

### GoPlus API response keys
Response keys are LOWERCASE contract addresses. Always use `.lower()` when looking up:
```python
result = data["result"].get(token_contract.lower(), {})
```

### Telegram send_message — sanitize + truncate + fallback
Telegram max message = 4096 chars. HTML parse errors (special chars in token names like Chinese characters, unclosed tags) cause HTTP 400.

**Always sanitize HTML before sending:**
```python
def _sanitize_html(text):
    """Clean HTML to prevent Telegram parse errors."""
    import re
    # Fix unclosed tags
    for tag in ['b', 'i', 'code', 'pre', 'a']:
        opens = len(re.findall(f'<{tag}[ >]', text))
        closes = len(re.findall(f'</{tag}>', text))
        if opens > closes:
            text += f'</{tag}>' * (opens - closes)
    # Remove broken entities
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', text)
    # Fix angle brackets in non-tag contexts
    text = re.sub(r'<(?!/?(b|i|code|pre|a|em|strong|u|s|strike|del|ins|u)[ >])', '&lt;', text)
    return text
```

**Always truncate:**
```python
if len(text) > 4000:
    text = text[:3990] + "\n\n... <i>(truncated)</i>"
```

**Always retry without parse_mode on failure:**
```python
try:
    # send with HTML
except Exception as e:
    error_body = ''
    if hasattr(e, 'read'):
        try: error_body = e.read().decode()[:200]
        except: pass
    print(f"[ERROR] send_message: {e} | body: {error_body}", file=sys.stderr)
    payload["parse_mode"] = ""
    # retry without HTML
```

Also set `disable_web_page_preview: True` to avoid link previews cluttering alerts.

### Deployer ≠ Whale (CRITICAL PITFALL)
The `format_clean_alert()` function has both `whale_info` (buyer) and `deployer_info` (contract creator) params.
**NEVER** pass whale address as deployer. Build `deployer_info` from `social_ctx["deployer"]`:
```python
deployer_info = None
if social_ctx and social_ctx.get("deployer") and social_ctx["deployer"].get("address"):
    dep = social_ctx["deployer"]
    deployer_info = {"address": dep["address"]}
    if dep.get("twitter"):
        deployer_info["twitter"] = f"https://twitter.com/{dep['twitter']}" if not dep["twitter"].startswith("http") else dep["twitter"]
    deployer_info["debank"] = f"https://debank.com/profile/{dep['address']}"
msg = format_clean_alert(td, w, security, deployer_info=deployer_info)
```

### Telegram HTML Links — Strip Protocol
When building clickable links for Telegram HTML parse mode, strip `https://` from display text:
```python
def _make_link(text, url):
    if url:
        return f'<a href="{url}">{text}</a>'
    return text

# Usage:
lines.append(f"   🐦 {_make_link(tw.replace('https://',''), tw)}")
```
This gives `twitter.com/devhandle` instead of `https://twitter.com/devhandle` — cleaner display.

### MC filter placement
Apply MC filter AFTER DexScreener enrichment but BEFORE security check.
This saves API calls to GoPlus for tokens that would be filtered anyway.

### Liquidity filter (CRITICAL)
Always check liquidity BEFORE sending alerts. Tokens with $0 liquidity are untradeable:
```python
MIN_LIQUIDITY = 1_000  # $1K minimum
liq = td.get("liquidity_usd", 0) or 0
if liq < MIN_LIQUIDITY:
    print(f"⏭️ Skip {symbol}: Liquidity ${liq:,.0f} below ${MIN_LIQUIDITY:,.0f}", file=sys.stderr)
    continue
```
Place this check AFTER MC filter, BEFORE security check. Without it, alerts fire for tokens that can't be traded.

### Never hardcode DEX swap URLs
Don't use hardcoded links like `aerodrome.finance/swap?...` — use project links from DexScreener `info` field instead (website, twitter, telegram). If no project links available, fall back to DexScreener chart URL only.

## Implementation Files
See `references/` for Zerion API details, DexScreener field reference, and clickable HTML link patterns.

## Social Context Enrichment (Deployer + Buyer Intelligence)

Enrich alerts with social profiles of deployers and buyers. Separate module: `mona_social_context.py`.

### Deployer Detection via Alchemy Binary Search
BaseScan API v1 is deprecated. Use Alchemy to find contract deployer:
1. Binary search for creation block: `eth_getCode` at block N vs N+1
2. Scan transactions in creation block: `eth_getBlockByNumber` + `eth_getTransactionReceipt`
3. Match `receipt.contractAddress` to target contract
4. `tx.from` = deployer address

**CRITICAL — Rate limiting:**
- Binary search makes ~20 `eth_getCode` calls per contract
- Alchemy free tier: 330 compute units/second
- **Always** add `time.sleep(0.2)` between Alchemy calls
- **Always** cache deployer results (TTL: 1 hour)
- Max 1 deployer lookup per 5 seconds (global rate limit)
- Limit scan range to 200 blocks max
- Limit to 50 transactions per block
- On HTTP 429: back off 2 seconds, skip token

### Wallet Profile Lookup
DeBank API endpoints have changed. Test before relying on them:
- `api.debank.com/user/{addr}` — may return 404
- Fallback: show deployer address without social profile
- ENS resolution can provide name but not Twitter

### Integration Pattern
```python
# In watcher, before sending alert:
social_ctx = get_social_context(token_addr, wallet_addr)
deployer_rep = score_deployer_reputation(social_ctx)
msg += format_social_context(social_ctx)
```

### Reputation Scoring (0-10)
- Base: 5 (neutral)
- Twitter followers: >50K = +3, >10K = +2, >1K = +1, <10 = -2
- Has Twitter linked: +1, No Twitter: -1
- Bio contains tech keywords (founder, ceo, engineer): +0.5
- Bio contains scam keywords (airdrop, free, pump, moon): -2
