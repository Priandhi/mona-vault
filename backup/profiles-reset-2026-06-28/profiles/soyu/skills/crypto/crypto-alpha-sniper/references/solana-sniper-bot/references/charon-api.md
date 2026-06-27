# Charon Signal Server API

## Endpoint
```
GET https://api.thecharon.xyz/api/signals
Header: x-api-key: <CHARON_API_KEY>
```

## Response Shape
```json
{
  "count": 90,
  "signals": [
    {
      "ageMs": 2753716,
      "bondingComplete": true,
      "firstSeen": "2026-06-08T13:31:53.347Z",
      "holders": 256,
      "lastSeen": "2026-06-08T14:16:55.285Z",
      "liquidityUsd": 3840.78,
      "marketCapUsd": 12048.67,
      "mint": "Gw7YRUTc4uc4uBv1WLgciu2sZNeaBdcuYkkyGejzpump",
      "name": "Gotcha",
      "priceUsd": 0.00001204,
      "sourceCount": 4,
      "sources": ["..."],
      "symbol": "GOTCHA",
      "trending": { "buys": 2232, "sells": 446, "platform": "Pump AMM" },
      "volume24h": 309491.61,
      "volume5m": 6333.42
    }
  ]
}
```

## Key Fields for Filtering
- `bondingComplete` — bonding curve finished (required for safe entry)
- `holders` — holder count (min 150-200 recommended)
- `marketCapUsd` — market cap (min $15K-50K depending on risk)
- `volume24h` — 24h volume (min $10K)
- `liquidityUsd` — pool liquidity (min $2K-5K)
- `ageMs` — token age in milliseconds (max 72h recommended)
- `sourceCount` — how many aggregators report this token (higher = more reliable)
- `trending` — object with buy/sell counts and platform info

## Quality Score Formula
```
score = min(holders/200, 3) + min(vol/50K, 3) + min(mcap/50K, 2)
      + min(liq/10K, 2) + sources*0.5 + trending?2:0 + bonded?1:0
```

## Caching
- Cache signals for 30-60 seconds to avoid hammering the API
- Typical response: 80-100 signals, 50+ qualifying after filters

## Integration with Meridian
- Add `tools/charon-signals.js` module to Meridian codebase
- Import in `index.js` alongside screening imports
- Fetch Charon signals in parallel with Meteora pool discovery
- Cross-reference Charon data with Meteora candidates for enrichment
- Add Charon qualifying signals to LLM prompt as "early signals"
- See `references/meridian-charon-integration.md` for full integration steps
