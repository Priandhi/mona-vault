# DexScreener API Reference

## Token Profile Endpoint
```
GET https://api.dexscreener.com/tokens/v1/base/{contract_address}
```

Returns array of pair objects. Use `[0]` for primary pair.

### Response Structure (key fields)
```json
{
  "chainId": "base",
  "dexId": "aerodrome",
  "pairAddress": "0x...",
  "baseToken": {"address": "0x...", "name": "...", "symbol": "..."},
  "quoteToken": {"address": "0x...", "name": "WETH", "symbol": "WETH"},
  "priceNative": "0.00001234",
  "priceUsd": "0.000025",
  "liquidity": {"usd": 50000, "base": 2000000, "quote": 30000},
  "volume": {"h24": 100000, "h6": 50000, "h1": 10000, "m5": 1000},
  "priceChange": {"h24": 15.5, "h6": 5.2, "h1": -1.3, "m5": 0.5},
  "txns": {"h24": {"buys": 500, "sells": 200}},
  "marketCap": 250000,
  "fdv": 500000,
  "pairCreatedAt": 1717000000000,
  "url": "https://dexscreener.com/base/0x...",
  "info": {
    "imageUrl": "https://...",
    "websites": [{"url": "https://project.com", "label": "Website"}],
    "socials": [
      {"type": "twitter", "url": "https://twitter.com/project"},
      {"type": "telegram", "url": "https://t.me/project"},
      {"type": "discord", "url": "https://discord.gg/project"}
    ]
  }
}
```

### Important Notes
- `marketCap` may be null — fallback to `fdv`
- `liquidity.usd` is the most reliable liquidity metric
- `info` object may be empty for new/unregistered tokens
- `pairCreatedAt` is Unix timestamp in milliseconds
- DEX name (`dexId`) tells you WHERE the swap happened, not WHAT the project is

### Multi-chain Support
```
/tokens/v1/base/{contract}     — Base
/tokens/v1/ethereum/{contract} — Ethereum
/tokens/v1/arbitrum/{contract} — Arbitrum
/tokens/v1/optimism/{contract} — Optimism
/tokens/v1/bsc/{contract}      — BSC
/tokens/v1/polygon/{contract}  — Polygon
/tokens/v1/avalanche/{contract} — Avalanche
```

### Rate Limits
- No auth required
- Rate limit: ~300 req/min
- Use caching (TTL 30-60s) to stay well under limits

### Search Endpoint
```
GET https://api.dexscreener.com/latest/dex/search?q={query}
```
Returns array of matching pairs. Useful for finding token by name/symbol.
