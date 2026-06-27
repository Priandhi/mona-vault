# API Reference — Token Discovery

## GeckoTerminal: New Pools on a Chain

```bash
curl -s "https://api.geckoterminal.com/api/v2/networks/solana/new_pools?page=1"
```

Response structure:
```json
{
  "data": [
    {
      "id": "solana_POOL_ADDRESS",
      "type": "pool",
      "attributes": {
        "name": "TOKEN / SOL",
        "address": "POOL_ADDRESS",
        "base_token_price_usd": "0.00000123",
        "fdv_usd": "123456.78",
        "volume_usd": {"h24": "50000.00", "h6": "20000.00", "h1": "5000.00"},
        "price_change_percentage": {"h24": "150.5", "h6": "50.2", "h1": "10.1"},
        "transactions": {
          "h24": {"buys": 500, "sells": 300, "buyers": 200, "sellers": 150}
        },
        "pool_created_at": "2026-06-04T12:00:00Z",
        "reserve_in_usd": "50000.00"
      },
      "relationships": {
        "base_token": {"data": {"id": "solana_TOKEN_MINT_ADDRESS", "type": "token"}},
        "quote_token": {"data": {"id": "solana_SO11111111111111111111111111111111", "type": "token"}},
        "dex": {"data": {"id": "raydium", "type": "dex"}}
      }
    }
  ]
}
```

## GeckoTerminal: Search for Specific Token

```bash
curl -s "https://api.geckoterminal.com/api/v2/search/pools?query=KINS"
```

Returns multiple pools. Pick the one with highest `volume_usd.h24`.

## GeckoTerminal: Specific Pool Details

```bash
curl -s "https://api.geckoterminal.com/api/v2/networks/solana/pools/POOL_ADDRESS"
```

Same structure as above but single pool.

## PumpFun: Solana Token Socials

```bash
# Extract mint address: strip "solana_" prefix from GeckoTerminal token ID
curl -s "https://frontend-api-v3.pump.fun/coins/MINT_ADDRESS"
```

Response:
```json
{
  "mint": "Tqj8yFmagrg7oorpQkVGYR52r96RFTamvWfth9bpump",
  "name": "Kintara",
  "symbol": "KINS",
  "description": "",
  "image_uri": "https://ipfs.io/ipfs/...",
  "twitter": "https://x.com/PlayKintara/status/...",
  "telegram": "https://t.me/...",
  "website": "https://kintara.gg/",
  "market_cap": 39627.24,
  "created_timestamp": 1779471284000
}
```

**Pitfall:** Not all PumpFun tokens have socials. Empty strings are common.

## CoinGecko: Trending (for reference, mostly established tokens)

```bash
curl -s "https://api.coingecko.com/api/v3/search/trending"
```

## Practical Extraction Script

```python
import json
from hermes_tools import terminal

# Get new pools
r = terminal('curl -s "https://api.geckoterminal.com/api/v2/networks/solana/new_pools?page=1" 2>/dev/null')
data = json.loads(r["output"])

for pool in data.get("data", []):
    attrs = pool["attributes"]
    vol = float(attrs.get("volume_usd", {}).get("h24", 0))
    buys = attrs.get("transactions", {}).get("h24", {}).get("buys", 0)
    created = attrs.get("pool_created_at", "")
    
    # Filter
    if vol < 500 or buys < 5:
        continue
    
    # Extract token ID for PumpFun lookup
    token_id = pool["relationships"]["base_token"]["data"]["id"]
    mint = token_id.replace("solana_", "")
    
    # Get socials from PumpFun
    social_r = terminal(f'curl -s "https://frontend-api-v3.pump.fun/coins/{mint}" 2>/dev/null')
    social = json.loads(social_r["output"])
    
    print(f"{attrs['name']} | vol: ${vol:,.0f} | twitter: {social.get('twitter','none')}")
```

## Chain Slug Reference

| Chain | GeckoTerminal Slug |
|---|---|
| Ethereum | `eth` (NOT `ethereum` — returns 404) |
| Solana | `solana` |
| Base | `base` |
| BNB Chain | `bsc` |
| Arbitrum | `arbitrum` |
| Optimism | `optimism` |
| Polygon | `polygon_pos` |
| Avalanche | `avalanche` |

## PumpFun: Newest Tokens (earliest signal)

```bash
curl -s "https://frontend-api-v3.pump.fun/coins?limit=20&offset=0&sort=created_timestamp&order=DESC"
```

## PumpFun: King of the Hill (graduating/hot)

```bash
curl -s "https://frontend-api-v3.pump.fun/coins/king-of-the-hill?limit=20&offset=0"
```

Note: KOTH endpoint may return invalid JSON intermittently. Wrap in try/catch.

## DexScreener: Token Social Enrichment

Use when PumpFun returns no socials for a token.

```bash
curl -s "https://api.dexscreener.com/latest/dex/tokens/TOKEN_ADDRESS"
```

Response structure:
```json
{
  "pairs": [{
    "dexId": "raydium",
    "priceUsd": "0.000123",
    "volume": {"h24": 50000},
    "priceChange": {"h24": 150.5},
    "fdv": 123000,
    "liquidity": {"usd": 45000},
    "info": {
      "websites": [{"url": "https://example.com"}],
      "socials": [
        {"type": "twitter", "url": "https://x.com/username"},
        {"type": "telegram", "url": "https://t.me/groupname"}
      ]
    }
  }]
}
```

**Pitfall:** `info.socials` may be empty for very new tokens. Always check `pairs[0].info` exists before accessing.
