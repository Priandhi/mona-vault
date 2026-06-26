---
date: 2026-06-18
agent: MONA — The Architect
task: Upgrade FOMO alerts with token name + chart + buy/sell detection
result: Rich alerts now include token symbol, amount (K/M/B formatted), DEX, chart link, solscan, wallet links
decisions:
  - Upgraded Helius subscription from "signatures" to "full" transactionDetails
  - parse_swap() identifies token by biggest balance change (excl WSOL)
  - WSOL change tracked separately (used for direction inference on USDC pairs)
  - Token balance matching by OWNER field (not accountIndex) — fixes bug where wallet's USDC token account wasn't matched
  - DexScreener API for token symbol lookup (cached 1hr)
  - Format amount K/M/B for memecoins (5M BONK, 1.5B PEPE, etc.)
issues:
  - Initial bug: token balance filter `accountIndex == wallet_idx` missed token accounts at different indices → fixed to use `owner == wallet_address`
  - DNS resolution `tokens.jup.ag` fails from VPS → switched to DexScreener
  - tool param munging of API keys/bot tokens in write_file/execute_code → workaround: use config file
next:
  - Wait for first real swap to verify end-to-end (most recent tx from tracked wallets were USDC P2P transfers, not swaps)
  - Consider innerInstructions parsing for more reliable DEX detection
---

# FOMO Alert Format Upgrade

## User Complaint
> "detail tx gak lengkap gak ada nama token dan chart"

## Solution

### Old Format
```
🔔 FOMO TRADE
@0xVantaa  Vanta
DEX   : SOL
Wallet: AfYkuxAG...b42b
TX    : 62c9diy1...Fn6N
Time  : 11:27:59
[View on Solscan]
```

### New Format (BUY example)
```
🟢 FOMO BUY SOL
────────────────────────────
@frankdegods  frank
Token : BONK    (+5.00M)
SOL   : 0.5000 SOL  (-0.5000)
DEX   : Jupiter
Wallet: 498g1r...zYpY
TX    : 5j7K8fG9...xY5z
Time  : 12:41:14
Slot  : 350000000
────────────────────────────
📈 Chart | 🔍 Solscan TX | 👛 Wallet
```

## Implementation Details

### 1. Subscribe with full tx details
```python
"transactionDetails": "full",  # was "signatures"
"maxSupportedTransactionVersion": 0
```

### 2. parse_swap(tx_data, wallet)
- Identifies token with biggest balance change
- Tracks WSOL separately (for USDC pairs)
- Detects direction: BUY / SELL / TRANSFER / FAILED / UNKNOWN
- Detects DEX from instruction programId (Jupiter/Raydium/Orca/Meteora/Pump.fun/etc)

### 3. lookup_token_metadata(mint)
- Calls DexScreener `/latest/dex/tokens/{mint}` (only working source from VPS)
- Picks highest liquidity pair
- Caches for 1 hour
- Returns: symbol, name, url, priceUsd, pairAddress

### 4. format_rich_alert(...)
- Token amount formatter: K (1K-999K), M (1M-999M), B (1B+)
- Direction icons: 🟢 BUY / 🔴 SELL / ❌ FAILED / ↔️ TRANSFER / ⚪ UNKNOWN
- Links: DexScreener chart + Solscan TX + Solscan wallet

### 5. Bug Fix
**Was:** `if t["accountIndex"] == wallet_idx` — only matched token accounts at wallet's signer index
**Now:** `if t["owner"] == wallet_address` — matches all token accounts owned by wallet, regardless of index
**Result:** Now detects swaps where wallet's token account is at a different account index (e.g., index 2 for USDC ATA when wallet is signer at index 1)

## Files Touched
- `/home/ubuntu/scripts/fomo_websocket.py` (525 lines, fully upgraded)
- `/home/ubuntu/scripts/fomo_config.json` (new — stores API key + bot token to avoid tool munging)
- `/home/ubuntu/.hermes/profiles/mona-bot/home/.pm2/dump.pm2` (PM2 state saved)

## Status
✅ fomo-websocket ONLINE, subscribed to 12 wallets via WSS, latency ~400ms