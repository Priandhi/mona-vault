# DexScreener API Reference

## Base URL
`https://api.dexscreener.com`

## Key Endpoints

### GET /tokens/v1/{chainId}/{tokenAddress}
Full pair data for a token on a specific chain.

**Example:** `/tokens/v1/base/0x833589fcd6edb6e08f4c7c32d4f71b54bda02913`

**Response:** Array of pair objects:
```json
[{
  "chainId": "base",
  "dexId": "aerodrome",
  "url": "https://dexscreener.com/base/0x...",
  "pairAddress": "0x...",
  "baseToken": {"address": "0x...", "name": "Token", "symbol": "TKN"},
  "quoteToken": {"address": "0x...", "name": "Wrapped Ether", "symbol": "WETH"},
  "priceNative": "0.00001234",
  "priceUsd": "0.0456",
  "liquidity": {"usd": 50000, "base": 1000000, "quote": 25},
  "volume": {"h24": 120000, "h6": 50000, "h1": 10000, "m5": 2000},
  "priceChange": {"m5": 0.5, "h1": -2.3, "h6": 5.1, "h24": 15.2},
  "txns": {
    "m5": {"buys": 10, "sells": 5},
    "h1": {"buys": 100, "sells": 80},
    "h6": {"buys": 500, "sells": 400},
    "h24": {"buys": 2000, "sells": 1800}
  },
  "pairCreatedAt": 1717000000000,
  "marketCap": 5000000,
  "fdv": 8000000,
  "info": {"imageUrl": "...", "websites": [...], "socials": [...]}
}]
```

### GET /token-boosts/latest/v1
Latest boosted tokens (paid promotions). Good for discovering new tokens.

### GET /token-profiles/latest/v1
Latest token profiles. Another discovery source.

## Enrichment Pattern
```python
def enrich_token(contract, chain="base"):
    url = f"https://api.dexscreener.com/tokens/v1/{chain}/{contract}"
    data = call_api(url)
    if not data or not isinstance(data, list) or len(data) == 0:
        return None
    d = data[0]
    base = d.get("baseToken", {})
    return {
        "name": base.get("name", "Unknown"),
        "symbol": base.get("symbol", "???"),
        "contract": contract,
        "price_usd": d.get("priceUsd"),
        "market_cap": d.get("marketCap") or d.get("fdv") or 0,
        "fdv": d.get("fdv") or 0,
        "liquidity_usd": d.get("liquidity", {}).get("usd", 0) or 0,
        "volume_24h": d.get("volume", {}).get("h24", 0) or 0,
        "volume_1h": d.get("volume", {}).get("h1", 0) or 0,
        "price_change_24h": d.get("priceChange", {}).get("h24", 0) or 0,
        "price_change_1h": d.get("priceChange", {}).get("h1", 0) or 0,
        "txns_buys_24h": d.get("txns", {}).get("h24", {}).get("buys", 0),
        "txns_sells_24h": d.get("txns", {}).get("h24", {}).get("sells", 0),
        "pair_created": d.get("pairCreatedAt"),
        "dex_url": d.get("url"),
    }
```

## Formatting Helpers
```python
def fmt_mc(val):
    if not val or val == 0: return "N/A"
    if val >= 1e6: return f"${val/1e6:.2f}M"
    if val >= 1e3: return f"${val/1e3:.1f}K"
    return f"${val:,.0f}"

def fmt_price(val):
    if not val: return "N/A"
    val = float(val)
    if val < 0.000001: return f"${val:.10f}"
    if val < 0.001: return f"${val:.8f}"
    if val < 1: return f"${val:.6f}"
    return f"${val:.4f}"

def fmt_age(hours):
    if hours is None: return "?"
    if hours < 1: return f"{hours*60:.0f}m"
    if hours < 24: return f"{hours:.1f}h"
    if hours < 720: return f"{hours/24:.1f}d"
    return f"{hours/720:.1f}mo"
```

## Rate Limits
- No official rate limit documented
- Safe: 3-5 requests/second with `time.sleep(0.3)` between calls
- Use `User-Agent` header to avoid blocks
