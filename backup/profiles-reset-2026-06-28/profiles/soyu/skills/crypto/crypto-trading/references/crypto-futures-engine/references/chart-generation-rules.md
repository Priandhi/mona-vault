## Chart Generation Rules

**CRITICAL**: User HATES SMC zones on charts. Always generate SIMPLE charts:
- ✅ Candlestick (green/red)
- ✅ EMA20/EMA50 trend lines
- ✅ Entry/SL/TP horizontal lines with labels
- ✅ Volume bars
- ❌ NO Order Block rectangles
- ❌ NO FVG zones
- ❌ NO Liquidity level boxes
- ❌ NO SMC annotations on chart

Use `mona_chart_simple.py` for clean charts.

### matplotlib Pitfalls
- Use `matplotlib.use('Agg')` for headless servers
- Use tuple colors `(r, g, b, a)` NOT CSS `'rgba(r,g,b,a)'` strings
- Example: `(0, 1, 0.53, 0.2)` instead of `'rgba(0, 255, 136, 0.2)'`

### Dual Mode Scanner
For market scanning, use dual mode approach:
1. **Momentum Mode** (ADX > 25): Trend + Pullback at EMA20
2. **Reversal Mode** (ADX < 25): SMC patterns (OB, FVG, CHoCH)

Always deduplicate signals with 1-hour cooldown per symbol+direction.
