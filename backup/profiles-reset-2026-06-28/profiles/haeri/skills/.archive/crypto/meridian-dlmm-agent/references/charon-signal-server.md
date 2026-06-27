# Charon Signal Server Integration

## What is Charon?

Charon (`api.thecharon.xyz`) is a signal server by **Meridian Protocol** that provides early token discovery signals on Solana. It aggregates data from multiple sources and provides pre-screened token candidates before they hit standard Meteora DLMM screening.

## API

```
Base URL: https://api.thecharon.xyz
Auth: x-api-key header (NOT Bearer token)
Endpoint: GET /api/signals
```

```bash
curl -s "https://api.thecharon.xyz/api/signals" \
  -H "x-api-key: YOUR_KEY"
```

**PITFALL:** Auth uses `x-api-key` header. `Authorization: Bearer` returns `401 Unauthorized`.

## Response Structure

```json
{
  "count": 93,
  "signals": [
    {
      "ageMs": 2753716,
      "bondingComplete": true,
      "firstSeen": "2026-06-08T13:31:53.347Z",
      "lastSeen": "2026-06-08T14:16:55.285Z",
      "holders": 256,
      "liquidityUsd": 3840.79,
      "marketCapUsd": 12048.68,
      "mint": "Gw7YRUTc4uc4uBv1WLgciu2sZNeaBdcuYkkyGejzpump",
      "name": "Gotcha",
      "symbol": "GOTCHA",
      "priceUsd": 0.00001204,
      "sourceCount": 4,
      "sources": [...],
      "trending": true,
      "volume24h": 309491.61,
      "volume5m": 6333.43,
      "graduated": false,
      "feeClaim": { ... }
    }
  ]
}
```

## Signal Fields

| Field | Type | Description |
|---|---|---|
| `ageMs` | number | Token age in milliseconds |
| `bondingComplete` | bool | Whether bonding curve is complete |
| `holders` | number | Current holder count |
| `liquidityUsd` | number | Pool liquidity in USD |
| `marketCapUsd` | number | Market cap in USD |
| `mint` | string | Solana token mint address |
| `sourceCount` | number | How many data sources report this token |
| `trending` | bool | Whether token is currently trending |
| `volume24h` | number | 24-hour trading volume in USD |
| `volume5m` | number | 5-minute trading volume in USD |
| `graduated` | bool | Whether token has graduated (e.g. from pump.fun) |
| `feeClaim` | object | Fee distribution data (distributedSol, recipients, shareholders) |

## Integration Strategy

### Pre-Screening Filter
Use Charon as a **pre-filter** before Meridian's standard screening:

1. Fetch Charon signals
2. Filter by basic thresholds (holders, mcap, volume, age)
3. Cross-reference with Meteora DLMM pool addresses
4. Pass matching pools to Meridian's standard screening

### Threshold Mapping (Charon → Meridian)

| Charon Field | Meridian Equivalent | Suggested Filter |
|---|---|---|
| `holders` | `minHolders` | ≥ 200 |
| `marketCapUsd` | `minMcap` | ≥ $50,000 |
| `volume24h` | `minVolume` | ≥ $10,000 |
| `ageMs` | `minAgeBeforeYieldCheck` | ≥ 30 min (1,800,000 ms) |
| `bondingComplete` | — | Must be `true` |
| `sourceCount` | — | ≥ 3 (multi-source verification) |
| `liquidityUsd` | `minTvl` | ≥ $5,000 |

### Quality Signals from Charon

- **`sourceCount ≥ 4`** — token seen by multiple aggregators, higher confidence
- **`trending: true`** — active momentum, but verify with Meridian's organic score
- **`graduated: true`** — survived pump.fun bonding curve, less likely to be dust
- **`feeClaim.distributedSol > 0`** — active fee generation, good for LP

### Red Flags from Charon

- `holders < 100` with high `volume24h` — likely wash trading
- `ageMs < 600000` (10 min) — too new, wait for stabilization
- `bondingComplete: false` — still in bonding curve, not on Meteora yet
- `sourceCount < 2` — single-source only, lower confidence

## Environment Variables

```env
CHARON_API_KEY=bb1eba8198941bfbac811d6e49b06a700419ec45471918ff
```

Added to Meridian's `.env`. Read by `tools/charon-signals.js` via `process.env.CHARON_API_KEY`.

## Native Integration (June 2026 — DONE)

Charon is now natively integrated into Meridian's screening pipeline via `tools/charon-signals.js`. No wrapper scripts needed. See main SKILL.md "Charon Signal Server" section for full integration details.

## Standalone Pre-Screening Script Pattern

```bash
#!/bin/bash
# Fetch Charon signals and filter for Meridian-compatible candidates
curl -s "https://api.thecharon.xyz/api/signals" \
  -H "x-api-key: $SIGNAL_SERVER_KEY" | \
  python3 -c "
import sys, json
data = json.loads(sys.stdin.read(), strict=False)
for s in data['signals']:
    if (s.get('holders', 0) >= 200 and
        s.get('marketCapUsd', 0) >= 50000 and
        s.get('volume24h', 0) >= 10000 and
        s.get('bondingComplete') == True and
        s.get('sourceCount', 0) >= 3):
        print(f\"{s['symbol']:15} | {s['holders']:>5} holders | \${s['marketCapUsd']:>10,.0f} mcap | \${s['volume24h']:>12,.0f} vol24h | {s['sourceCount']} src\")
"
```
