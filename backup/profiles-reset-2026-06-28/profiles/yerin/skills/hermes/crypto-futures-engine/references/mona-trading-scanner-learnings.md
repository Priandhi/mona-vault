# Mona Trading Scanner — Session Learnings (Jun 8, 2026)

## Chart Generation — USER PREFERENCE (CRITICAL)

**User explicitly said: "candle stick aja jangan gini"** when shown SMC-annotated charts.

**RULE: Charts must be SIMPLE candlestick only:**
- ✅ Candlestick (green/red)
- ✅ EMA20/EMA50 lines
- ✅ Entry/SL/TP horizontal lines
- ✅ Volume bars (bottom panel)
- ❌ NO SMC zones (Order Blocks, FVG, Liquidity)
- ❌ NO overlays that clutter the chart
- ❌ NO emojis in chart titles (font rendering issues — DejaVu Sans missing glyphs)

**Implementation:** `mona_simple_chart.py` — uses matplotlib with dark theme (#1a1a2e bg).

## Dual Mode Scanner Pattern

SMC-only scanning fails for high-momentum tokens (fresh OBs/virgin FVGs are rare in trending markets). Solution: **Dual Mode**:

1. **Momentum Mode** (ADX > 25 + EMA aligned): Trend + Pullback entry
   - Entry at EMA20 pullback
   - SL below EMA20 - 1.5x ATR
   - TP1 = entry + 1.5x ATR, TP2 = entry + 3x ATR
   - Score factors: trend strength (30), pullback quality (30), volume (20), RSI filter (20), funding (10)

2. **Reversal Mode** (ADX < 25): SMC patterns
   - Fresh OB + Virgin FVG + CHoCH/BOS
   - Liquidity sweep + displacement
   - Multi-timeframe alignment

**Threshold:** Momentum mode needs score ≥60 to signal. Reversal mode needs ≥40.

## SMC Engine Strictness Problem

The DozeroSMCEngine confluence threshold (75) is too strict for most tokens. When scanning:
- Fresh OBs are rare in trending markets
- Virgin FVGs are even rarer
- Most tokens score 20-40 on SMC confluence

**Solution:** Use SMC for reversal setups only. For trending tokens, use momentum mode.

## Cron Job Signal Delivery

- Send to specific topic: `deliver: 'telegram:-1003899936547:387'`
- Only send TOP 1 signal per scan (not multiple)
- Use `mona_scanner_notifier.py` for clean pipeline: scan → chart → send
- Deduplication: 1 hour cooldown per signal

## Key Files

- `mona_smc_master.py` — SMC engine v2.0 (OB strength, FVG quality, smart money flow)
- `mona_smc_master_v21.py` — Multi-TF OB/FVG detection
- `mona_signal_generator.py` — Chart + explanation + Telegram notification
- `mona_signal_scanner.py` — Top 20 pair scanner with dedup
- `mona_simple_chart.py` — Simple candlestick chart (USER PREFERRED)
- `mona_scanner_notifier.py` — Clean pipeline: scan → chart → Telegram
- `mona_onchain_v12.py` — Onchain analyzer (BTC network, price, fees, DeFi TVL)
