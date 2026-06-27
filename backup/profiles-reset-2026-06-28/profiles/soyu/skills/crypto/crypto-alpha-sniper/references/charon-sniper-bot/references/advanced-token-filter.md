# Advanced Token Filter — 7-Layer Strategy

## Overview

The v1 filter used basic thresholds (holders, mcap, volume, liquidity) and a simple score.
The v2 filter uses ALL available Charon API fields for 7 layers of qualification.

**Result:** Pass rate dropped from 50% (25/50) to 2% (1/50). Win rate estimated to improve from ~30% to ~50-60%.

## Layer Design

### Layer 1: Hard Filters (instant reject)
- blockedSymbols / blockedMints
- already traded / already open
- bondingComplete required
- Age < 12h
- Holders ≥ 150
- MCap $15K–$3M
- Sources ≥ 2

### Layer 2: Momentum Filter
- `minPriceChange5m: -5` — allow slight dip, reject big dumps
- `minVolume5m: 500` — minimum 5m volume in USD
- `minVolAcceleration: 0.5` — 5m volume must be at least 0.5x of expected (24h/288)

### Layer 3: Organic Filter
- `minOrganicScore: 30` — reject low-organic tokens (likely bots/manipulation)
- Source: `trending.organicScore` (0-100)

### Layer 4: Distribution Filter
- `maxDevHoldings: 20` — dev holds max 20% (rug risk)
- `maxTopHolders: 50` — top holders max 50% (dump risk)
- `maxSnipers: 100` — max 100 snipers already in (competition)

### Layer 5: Volume Filter
- `minBuyRatio: 0.8` — buys must be at least 80% of sells
- `minNetBuyers: 10` — at least 10 net buyers in 24h
- Source: `trending.buys/sells`, `trending.stats24h.numNetBuyers`

### Layer 6: Liquidity Filter
- `minLiqRatio: 3` — liquidity must be at least 3% of mcap
- `minLiqChange: -20` — allow up to -20% liq change

### Layer 7: Quality Score (weighted ranking)

| Factor | Weight | Max Points | Source |
|---|---|---|---|
| Organic score (/20) | 0.05 | 5.0 | trending.organicScore |
| Buy ratio (/3) | 0.33 | 3.0 | trending.buys / trending.sells |
| 5m momentum (/10) | 0.1 | -2 to +3 | trending.stats5m.priceChange |
| Volume 5m (log10/3) | 0.33 | 2.0 | volume5m |
| Net buyers (/500) | 0.004 | 2.0 | trending.stats24h.numNetBuyers |
| Holders (log10/2) | 0.5 | 2.0 | holders |
| Sources (*0.375) | 0.375 | 1.5 | sourceCount |
| L/M ratio bonus | flat | 1.0 | liqRatio 5-20% |
| Low dev bonus | flat | 1.0 | devHoldings ≤ 5% |
| Low sniper bonus | flat | 0.5 | sniperCount ≤ 20 |
| **Penalty:** high top holders | -1 to -2 | | topHolders > 30% |
| **Penalty:** negative momentum | -1 to -2 | | priceChange5m < -5% |
| **Penalty:** sell dominant | -1 to -3 | | buyRatio < 0.5 |

**Max theoretical score:** ~21.5 points
**Observed top scores:** 13-15 (real data from Jun8)

## Example: Teletubby Score Breakdown

```
Organic: 74/100 → +3.7 pts
Buy ratio: 3.3x → +1.1 pts
5m momentum: +11.6% → +1.2 pts
Volume 5m: $3,252 → +0.8 pts
Net buyers: 1,039 → +2.0 pts
Holders: 674 → +1.4 pts
Sources: 4 → +1.5 pts
L/M ratio: 21% → +1.0 pt
Low dev: 0% → +1.0 pt
Low snipers: 38 → +0.5 pt
No penalties
TOTAL: 13.1 pts ← TOP CANDIDATE
```

## Config Addition

Add these to `config.json` → `filter` section:

```json
{
  "minPriceChange5m": -5,
  "minVolume5m": 500,
  "minVolAcceleration": 0.5,
  "minOrganicScore": 30,
  "maxDevHoldings": 20,
  "maxTopHolders": 50,
  "maxSnipers": 100,
  "minBuyRatio": 0.8,
  "minNetBuyers": 10,
  "minLiqRatio": 3,
  "minLiqChange": -20
}
```

## Tuning Guide

- **Too few signals (< 1/day):** Relax `minOrganicScore` to 20, `minBuyRatio` to 0.5
- **Too many losses:** Tighten `minOrganicScore` to 40, `minNetBuyers` to 50
- **Missing pumps:** Lower `minPriceChange5m` to -10 (allow dips before pump)
- **Rug pulls:** Tighten `maxDevHoldings` to 5, `maxTopHolders` to 30
