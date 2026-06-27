# Full Market Scanner — DOZERO.X SMC Scoring

**Script:** `~/.hermes/scripts/scan_market_full.py`
**Status:** Production-ready, June 2026

## What it does

Scans ALL active USDT perpetual futures pairs on Binance using DOZERO.X SMC confluence scoring. Ranks by score to find the best trading opportunities.

## Workflow

1. Fetch all active USDT pairs from `GET /fapi/v1/exchangeInfo` (typically 600+)
2. Filter by 24h volume > $500K (typically 550+ remaining)
3. For each pair, fetch H1/H4/Daily klines (100 candles each)
4. Run full SMC analysis: MTF structure, Virgin FVG, BOS/CHOCH, liquidity sweep, displacement, premium/discount zone, RSI+EMA
5. Score 0-100, rank by score
6. Output: top 20 pairs with full breakdown

## Typical results (normal market)

| Category | Count | Description |
|----------|-------|-------------|
| ELITE (75+) | 0-2 | Auto-enter, extremely rare in ranging markets |
| STRONG (60-74) | 3-10 | Watchlist, enter if user approves |
| GOOD (50-59) | 10-30 | Monitor, potential setups developing |

## When to use

- User says "scan market", "cari setup", "apa yang bagus?"
- Engine scan cycle finds nothing (threshold too strict)
- Before entering a position (verify it's the best available)
- After closing all positions (find next opportunity)

## Performance

- 550 pairs × 4 TF × 100 candles = ~2,200 API calls
- Rate limited at 0.05s delay between pairs
- Total scan time: ~2-3 minutes
- Uses `urllib.request` (sync), not `aiohttp`

## Key insight from production

In ranging/sideways markets (June 2026), most pairs have `structure=ranging` on H4/H1. This means MTF alignment rarely exceeds 2/4, keeping scores below 75. The scanner correctly identifies this — don't lower threshold just because nothing hits 75+. Wait for trending conditions or accept STRONG (60+) setups with user approval.

## Fast-scan optimization (for impatient users)

Full 550-pair scan takes 2-3 minutes. User said "lama banget" (so slow) when scan took >1 minute AND found nothing. To speed up:

1. **Pre-filter by MTF alignment** — Fetch only H4 and Daily klines first (2 API calls per pair). Skip pairs where both are `ranging`. Only run full 4-TF analysis on pairs with ≥2/4 alignment. This typically eliminates 70-80% of pairs before expensive H1/M15 analysis.

2. **Parallel fetching** — Use `execute_code` with `threading` or `concurrent.futures` to fetch klines for multiple pairs simultaneously (5-10 concurrent requests). Binance allows burst requests as long as total stays under 1200/min.

3. **Cache exchange info** — `exchangeInfo` (600+ symbols) changes rarely. Cache for 1 hour. Same for `leverageBracket` and step sizes.

4. **Report incrementally** — Print STRONG/ELITE results as found (not after full scan). User sees progress and can act on first good setup without waiting for completion.

```python
# Pre-filter pattern
quick_score = {}
for sym in all_pairs:
    d_struct = get_structure(get_klines(sym, '1d', 50))
    h4_struct = get_structure(get_klines(sym, '4h', 50))
    bull = sum(1 for s in [d_struct, h4_struct] if s == 'uptrend')
    bear = sum(1 for s in [d_struct, h4_struct] if s == 'downtrend')
    if max(bull, bear) >= 1:  # At least 1/2 trending
        quick_score[sym] = max(bull, bear)

# Only full-analyze pairs with potential
candidates = sorted(quick_score, key=quick_score.get, reverse=True)[:50]
```

## Pitfalls

- **API rate limiting** — 550 pairs at 0.05s = 27.5s total delay. Binance allows ~1200 req/min but actual limit is lower. If IP banned (error -1003), wait 30 min.
- **Kline data freshness** — Uses latest 100 candles. During low-activity hours (Asian night), structure analysis may be noisy.
- **Volume filter matters** — Pairs below $500K 24h volume have poor liquidity and wider spreads, making SMC levels unreliable.
