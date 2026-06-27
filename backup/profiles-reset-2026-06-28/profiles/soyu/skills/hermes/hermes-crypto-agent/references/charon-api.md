# Charon Signal API — Token Discovery

> Last verified: 2026-06-09

## Endpoint
```
GET https://api.thecharon.xyz/api/signals
Header: x-api-key: <CHARON_API_KEY>
```

Returns ~50-100 signals per call. All signals are bonding-complete and have trending data.

## Signal Fields

| Field | Type | Description |
|-------|------|-------------|
| `mint` | string | Token mint address |
| `symbol` | string | Token symbol |
| `name` | string | Token name |
| `priceUsd` | number | Current price in USD |
| `holders` | number | Number of holders |
| `marketCapUsd` | number | Market cap in USD |
| `liquidityUsd` | number | Liquidity in USD |
| `volume24h` | number | 24h volume USD |
| `volume5m` | number | 5-minute volume USD |
| `ageMs` | number | Token age in milliseconds |
| `bondingComplete` | boolean | Bonding curve complete |
| `sourceCount` | number | Number of data sources |
| `sources` | string[] | Source names (e.g., "axiom_trending", "jupiter_trending", "pump_graduated") |
| `trending` | object | Rich trending data (see below) |
| `graduated` | object | Graduation data (see below) |
| `feeClaim` | object | Fee distribution data |
| `firstSeen` | ISO date | When first seen by Charon |
| `lastSeen` | ISO date | Last seen timestamp |

## `trending` Object

| Field | Type | Description |
|-------|------|-------------|
| `organicScore` | number | 0-100, higher = more genuine trading |
| `organicScoreLabel` | string | "low" / "medium" / "high" |
| `buys` | number | Number of buy transactions |
| `sells` | number | Number of sell transactions |
| `buyVolume` | number | Buy volume USD |
| `sellVolume` | number | Sell volume USD |
| `volume24h` | number | 24h volume |
| `volume5m` | number | 5m volume |
| `stats24h` | object | 24h stats (see below) |
| `stats5m` | object | 5m stats (same structure as stats24h) |
| `tags` | string[] | Token tags (e.g., "unknown", "token-2022") |
| `launchpad` | string | Launch platform (e.g., "pump.fun") |
| `platform` | string | Trading platform (e.g., "Pump AMM") |

## `stats24h` / `stats5m` Object

| Field | Type | Description |
|-------|------|-------------|
| `priceChange` | number | Price change % |
| `numBuys` | number | Total buy transactions |
| `numSells` | number | Total sell transactions |
| `numNetBuyers` | number | Net buyers (buys - sells unique wallets) |
| `numTraders` | number | Unique traders |
| `buyVolume` | number | Buy volume USD |
| `sellVolume` | number | Sell volume USD |
| `holderChange` | number | Holder count change |
| `liquidityChange` | number | Liquidity change % |
| `volumeChange` | number | Volume change % |
| `buyOrganicVolume` | number | Organic buy volume |
| `sellOrganicVolume` | number | Organic sell volume |

## `graduated` Object (only for ~33% of signals)

| Field | Type | Description |
|-------|------|-------------|
| `dev` | string | Dev wallet address |
| `devHoldingsPercent` | number | Dev holdings % (HIGH = rug risk) |
| `numHolders` | number | Holders at graduation |
| `sniperCount` | number | Snipers that entered |
| `topHoldersPercent` | number | Top holders concentration % |
| `poolAddress` | string | Liquidity pool address |
| `program` | string | Program name (e.g., "pump") |
| `twitter` | string | Twitter URL |
| `website` | string | Website URL |

## Filter Strategy (7-Layer)

### Layer 1: Hard Filters
- Blocked symbols/mints, already traded, bonding complete
- Min holders, mcap range, min sources, max age

### Layer 2: Momentum
- `stats5m.priceChange` > -5% (reject big dumps)
- `volume5m` > $500 (must be actively traded)
- Volume acceleration: `(vol5m * 288) / vol24h` > 0.5x

### Layer 3: Organic
- `organicScore` ≥ 30 (reject bot/manipulation tokens)

### Layer 4: Distribution
- `devHoldingsPercent` < 20% (rug risk)
- `topHoldersPercent` < 50% (dump risk)
- `sniperCount` < 100 (competition)

### Layer 5: Volume
- Buy/sell ratio: `buys / sells` ≥ 0.8
- Net buyers (`stats24h.numNetBuyers`) ≥ 10

### Layer 6: Liquidity
- Liquidity/MarketCap ratio ≥ 3% (healthy pool)
- `stats24h.liquidityChange` > -20% (not rug)

### Layer 7: Quality Score (weighted ranking)
- organicScore/20 (max 5 pts)
- buyRatio/3 (max 3 pts)
- priceChange5m/10 (max 3 pts)
- log10(vol5m)/3 (max 2 pts)
- netBuyers/500 (max 2 pts)
- log10(holders)/2 (max 2 pts)
- sourceCount * 0.375 (max 1.5 pts)
- L/M ratio bonus (1 pt if 5-20%)
- Low dev bonus (1 pt if ≤5%)
- Penalties: high top holders, negative momentum, sell dominant
