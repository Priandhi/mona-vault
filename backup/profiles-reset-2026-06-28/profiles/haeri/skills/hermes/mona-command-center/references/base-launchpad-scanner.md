# Base Launchpad Scanner Reference

## Supported Launchpads

| Launchpad | API Status | Endpoint | Notes |
|-----------|-----------|----------|-------|
| Clanker | ✅ Works | `https://www.clanker.world/api/tokens` | No auth needed. Bare endpoint only — no sort/filter params. |
| Virtuals Protocol | ❌ 403 | `https://api.virtuals.io/api/virtuals` | Blocked on VPS. Fallback: detect from DexScreener description. |
| Creator.bid | ❌ 403 | `https://creator.bid/api` | Blocked. Fallback: DexScreener. |
| Flaunch | ❌ 403 | `https://flaunch.xyz/api` | Blocked. Fallback: DexScreener. |
| Bankr.bot | ❌ 404 | `https://api.bankr.bot` | Not found. Fallback: DexScreener. |

## Clanker API Details

```python
url = "https://www.clanker.world/api/tokens"
headers = {
    "accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.clanker.world/",
}
```

Response: `{data: [{id, created_at, admin (deployer), contract_address, name, symbol, description, supply, img_url, pool_address, starting_market_cap, tags, chain_id}], total, tokensDeployed}`

**PITFALL**: Clanker tokens have NO liquidity/volume data. Must fetch from DexScreener: `https://api.dexscreener.com/tokens/v1/base/{contract_address}`

**PITFALL**: Adding `?sort=created_at&order=desc` returns 400. Use bare URL.

## Real-Time Scanner Architecture

Multi-API polling with deduplication:

1. **Clanker API** — Direct, most reliable for Base tokens
2. **DexScreener boosts** — `https://api.dexscreener.com/token-boosts/latest/v1` (30 trending)
3. **DexScreener profiles** — `https://api.dexscreener.com/token-profiles/latest/v1` (30 newly listed)

Deduplicate by contract address. Normalize all to same format before quality check.

Launchpad detection: check `source` field first (set by Clanker API), then pattern match name/symbol/description against known keywords.

## Quality Filters

```python
QUALITY_THRESHOLDS = {
    "min_liquidity_usd": 5000,
    "min_volume_24h": 2000,
    "max_token_age_hours": 168,
}
```

Score 2-5: liquidity >$5K (+2), volume >$2K (+2), age <7d (+1), positive momentum (+1).

## Output Format

```
⚡ BASE REAL-TIME SCAN
━━━━━━━━━━━━━━━━━━━━━━

1. Token Name (SYMBOL)
   🤖 Launchpad: Clanker
   ⭐ Quality: 4/5
   💧 Liquidity: $12,640
   📊 Volume 24h: $172,602
   🆕 Age: 3.9h
   📄 0x36C9A2e5c80e167e37...
   🔗 View on DEX
```

## Cron: every 5m, deliver to Alpha topic, silent when empty

## Files

- `mona_base_launchpad_scanner.py` — Full scanner (Clanker + DexScreener)
- `mona_base_realtime_scanner.py` — Real-time multi-API scanner
- `mona_alpha_scanner_smart.py` — General chain scanner
- `mona_token_analyzer.py` — Deep on-chain analysis
