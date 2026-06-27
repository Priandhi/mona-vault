# Dual Mode Scanner — Momentum + Reversal

## Architecture

Two scanning modes based on market conditions:

### Momentum Mode (trending markets)
- **Trigger:** ADX > 25 + EMA20/EMA50 aligned
- **Strategy:** Trend + Pullback entry
- **Entry:** At EMA20 pullback (1-5% from EMA)
- **Filters:** RSI not overbought (<70 for LONG, >30 for SHORT), high volume (> $50M), funding rate alignment
- **Scoring:** Trend strength (30) + Pullback quality (30) + Volume (20) + RSI (20) + Funding (10) = 100 max
- **Threshold:** ≥60 = signal

### Reversal Mode (ranging markets)
- **Trigger:** ADX < 20 or EMA not aligned
- **Strategy:** SMC patterns (OB, FVG, CHoCH)
- **Engine:** DozeroSMCEngine with confluence scoring
- **Threshold:** ≥75 = signal

### Auto-detection
```python
mode = detect_market_mode(klines)  # returns (MarketMode, adx_value)
if mode == MarketMode.MOMENTUM:
    result = analyze_momentum(klines, ticker, funding)
else:
    result = analyze_smc(klines, ohlcv)
```

## Implementation

Script: `~/.hermes/scripts/mona_dual_mode_scanner.py`
- Scans 100 high-volume USDT pairs from Binance Futures API
- Sorts by 24h quote volume descending
- Skips stablecoins (USDC, BUSD, TUSD, FDUSD, DAI, USDP, WBTC, WBETH, STETH, BETH)
- Returns top signals sorted by score

## Chart Generation

Script: `~/.hermes/scripts/mona_chart_pro.py` (TradingView-style)
- Dark theme (#1a1a2e background)
- Candlestick: body width 0.6, wick linewidth 1.5
- EMA20 (cyan) + EMA50 (orange) — filter out None values before plotting
- Volume bars at bottom
- Entry/SL/TP horizontal lines with price labels on right axis
- Current price marker with label
- Info box (entry, SL, TP, score) + Reasons box
- DPI 150, tight layout

### Pitfalls
- **matplotlib rgba format:** Use tuples `(r, g, b, a)` NOT CSS strings `'rgba(r, g, b, a)'` — matplotlib doesn't accept CSS rgba
- **EMA with None values:** `_ema()` returns `[None]*padding + ema_values`. Plotting with None crashes matplotlib. Filter: `x = [i for i, v in enumerate(ema) if v is not None]`, `y = [v for v in ema if v is not None]`
- **gridwidth not supported:** `plt.grid(gridwidth=0.5)` crashes. Remove parameter, use default.
- **Chart MUST be clean candlestick only.** User explicitly said "gak sesuai ekspektasi masih jelek" about SMC-heavy charts. NO SMC zones, NO OB rectangles, NO FVG boxes on chart. Just candles + EMA + Entry/SL/TP lines + volume.

## Cron Deployment

```python
# Deliver to topic 387 (futures), NOT origin/DM
cronjob(deliver='telegram:-1003899936547:387')
```

**Dedup (CRITICAL — updated June 2026):** Dedup is per **TOKEN only** (NOT per token+direction). Once ETHUSDT is sent as LONG, it won't appear again for 24h even as SHORT. Key: `symbol` (not `f"{symbol}_{direction}"`). File: `~/.hermes/data/sent_signals.json`. Cooldown: 24 hours. Cron prompt must say "MAX 1 signal per token" explicitly. Reset file when changing dedup logic. See main SKILL.md pitfall "Scanner dedup: per TOKEN, NOT per TOKEN+DIRECTION" for the full story.

## Full Pipeline Script

`~/.hermes/scripts/mona_dual_pro.py` — combines scanner + chart + message format:
1. Scan 100 pairs
2. Pick top 1 signal (score ≥ 70)
3. Fetch 1h klines (100 candles)
4. Calculate ATR, trend, S/R levels
5. Generate chart (TradingView-style)
6. Format message (entry, SL, TP, market context, reasons)
7. Print to stdout (for cron delivery)
