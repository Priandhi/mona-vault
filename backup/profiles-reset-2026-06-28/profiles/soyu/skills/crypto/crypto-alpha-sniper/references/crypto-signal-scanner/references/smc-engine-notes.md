## Dozero.X SMC Engine Analysis

### What Dozero.X Does (that we should match):

1. **Multi-Timeframe Alignment**: D1, H4, H1, M15
2. **Fresh OB Detection**: Untested order blocks = highest probability
3. **Virgin FVG Detection**: Never-filled fair value gaps = strongest support/resistance
4. **CHoCH (Change of Character)**: First break against trend = reversal signal
5. **Liquidity Sweep**: Smart money hunts stop losses before reversing
6. **Displacement**: Strong candle showing institutional intent

### Key Differences: Reversal vs Momentum

| Factor | Reversal (SMC) | Momentum (Trend) |
|--------|---------------|------------------|
| Market | Ranging | Trending |
| ADX | < 25 | > 25 |
| Entry | At OB/FVG | At EMA20 pullback |
| SL | Below OB/FVG | Below EMA20 - 1.5 ATR |
| TP | Structure levels | ATR multiples |
| Win Rate | 60-70% | 55-65% |
| Best For | Range-bound tokens | Trending tokens |

### Confluence Scoring Guide

**≥90**: ELITE — Multiple confirmations, high probability
**75-89**: HIGH — Strong setup, good risk/reward
**60-74**: MEDIUM — Decent setup, proceed with caution
**<60**: LOW — Skip, wait for better setup

### Slevensy Bot Features (competitor analysis)

Slevensy Scanner Bot includes:
- Entry scan: every 180 seconds (event-driven)
- Market scan: every 30 minutes
- Onchain scan: every 15 minutes
- Crypto news integration
- Macro context (Fear & Greed + BTC dominance)
- Watchlist system
- Price alerts
- L/S ratio analysis

### Our Advantages Over Slevensy:
1. Dual Mode (momentum + reversal) — Slevensy may only do one
2. More detailed SMC analysis (multi-TF OB/FVG)
3. Custom chart generation
4. Open source / customizable
