# Charon API — Complete Signal Field Reference

**Endpoint:** `GET https://api.thecharon.xyz/api/signals`
**Auth:** `x-api-key` header (NOT Bearer)
**Returns:** `{ count: N, signals: [...] }`

## Per-Signal Fields (as of Jun 2026)

| Field | Type | Description | Used in Filter? |
|---|---|---|---|
| `symbol` | string | Token ticker | blockedSymbols check |
| `name` | string | Token full name | display only |
| `mint` | string | Solana mint address | blockedMints check |
| `holders` | number | Current holder count | ✅ minHolders |
| `marketCapUsd` | number | Market cap in USD | ✅ minMcap/maxMcap |
| `volume24h` | number | 24h trading volume | ✅ minVolume24h |
| `volume5m` | number | 5-minute volume | ✅ NEW: momentum filter |
| `liquidityUsd` | number | Pool liquidity in USD | ✅ minLiquidity |
| `priceUsd` | number | Current price in USD | display/DRY RUN fallback |
| `ageMs` | number | Token age in milliseconds | ✅ maxAgeHours |
| `sourceCount` | number | How many sources report this | ✅ minSources |
| `sources` | string[] | List of source names | informational |
| `bondingComplete` | boolean | Bonding curve completed | ✅ requireBondingComplete |
| `firstSeen` | string | ISO timestamp first detected | informational |
| `lastSeen` | string | ISO timestamp last seen | informational |
| `trending` | object/null | Rich trending data (see below) | ✅ organicScore, buys/sells |
| `graduated` | object/null | Pump.fun graduation data (see below) | ✅ devHoldings, snipers |
| `feeClaim` | object/null | Fee distribution data | informational |

## `trending` Object (when present)

```json
{
  "buyVolume": 1446.13,
  "buys": 668,
  "sells": 202,
  "sellVolume": 1805.62,
  "organicScore": 74.33,        // 0-100, higher = more organic trading
  "organicScoreLabel": "medium", // low/medium/high
  "platform": "Pump AMM",
  "launchpad": "pump.fun",
  "jupiterAsset": true,
  "tags": ["unknown", "token-2022"],
  "totalSupply": 919092842.56,
  "volume24h": 995912.18,
  "volume5m": 3251.75,
  "createdAt": "2026-06-08T09:46:52.986Z",
  "graduatedAt": "2026-06-08T09:46:52Z",
  "stats24h": {
    "buyVolume": 504301.12,
    "sellVolume": 491611.06,
    "numBuys": 13670,
    "numSells": 10290,
    "numNetBuyers": 1039,        // net buyers (buys - sells unique wallets)
    "numTraders": 3437,
    "numOrganicBuyers": 113,
    "priceChange": 1212.93,      // % change in 24h
    "holderChange": 2596,        // net new holders
    "liquidityChange": 211.62,   // % liquidity change
    "buyOrganicVolume": 39959.23,
    "sellOrganicVolume": 38976.29
  },
  "stats5m": {
    "buyVolume": 1446.13,
    "sellVolume": 1805.62,
    "numBuys": 23,
    "numSells": 13,
    "numNetBuyers": 26,
    "numTraders": 29,
    "numOrganicBuyers": 3,
    "priceChange": 11.64,        // % change in 5m
    "holderChange": 0.14,
    "liquidityChange": 0.60,
    "volumeChange": 110.41,
    "buyOrganicVolume": 209.21,
    "sellOrganicVolume": 27.09
  }
}
```

## `graduated` Object (only for pump.fun graduates, ~33% of signals)

```json
{
  "dev": "3cjGb19dWCeKUjBifwWqVaa6ePnWYR5Zcsj58DuWez5d",
  "devHoldingsPercent": 0,        // % of supply held by dev (rug risk indicator)
  "graduationDate": 1780912013383,
  "numHolders": 923,
  "poolAddress": "HzzvYVeXjMjUyGLc9qpTQieQATtvYVFa6NX8zBuQY9ZL",
  "program": "pump",
  "sniperCount": 38,              // how many snipers already in (competition indicator)
  "topHoldersPercent": 15.63,     // top 10 holders % (concentration/dump risk)
  "twitter": "https://x.com/...",
  "website": "https://x.com/...",
  "telegram": null
}
```

## `feeClaim` Object

```json
{
  "distributedSol": 0.566,
  "recipients": 1,
  "shareholders": [
    {
      "address": "Ep4ZpKGQ1fcNYmwhzxbFoDy8TAn8Vj82zHtm8bBqr8bY",
      "bps": 10000
    }
  ],
  "signature": "5MrSxp2a..."
}
```

## Distribution Stats (from 98 signals, Jun 8 2026)

- 100% bonded
- 100% have trending data
- 33% have graduated data (pump.fun graduates)
- 39% organic score ≥ 60 (high quality)
- 49% buy-dominant (buys > sells)
- Average organic score: 45.8
- Average buy/sell ratio: 2.05x
- Average holders: 4,385
- Average mcap: $2.4M
- Average liquidity: $96K

## Key Insights for Filtering

1. **organicScore** is the single best predictor of quality. Score ≥ 60 = genuine interest. Score < 30 = likely bots/manipulation.
2. **buyRatio** (buys/sells) > 1.5x = strong upward pressure. < 0.8x = avoid.
3. **5m priceChange** > 0 = momentum. < -5% = falling knife, avoid.
4. **devHoldingsPercent** > 20% = high rug risk. 0% = safe.
5. **sniperCount** > 100 = too much competition, harder to profit.
6. **topHoldersPercent** > 50% = concentration risk, dump likely.
7. **liquidityChange** (24h) growing = healthy pool. Shrinking = exit liquidity drying up.
8. **holderChange** (24h) positive = adoption. Negative = people leaving.
