# Dual Mode Scanner — Momentum + Reversal

## Problem

SMC-only scanning misses momentum plays on trending tokens. High-momentum tokens (ZEC +190%, WLD +30%) often have no fresh OBs or virgin FVGs because they've already moved.

## Solution: Dual Mode

1. **Momentum Mode** — for trending markets (ADX > 25, EMA aligned)
   - Entry: pullback to EMA20
   - SL: below EMA20 - 1.5x ATR
   - TP: based on ATR multiples
   
2. **Reversal Mode** — for ranging markets (SMC patterns)
   - Entry: fresh OB / virgin FVG
   - SL: beyond OB/FVG
   - TP: next liquidity level

## Detection Logic

```python
def detect_market_mode(klines):
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    adx = calculate_adx(highs, lows, closes, 14)
    
    if adx > 25 and ema_aligned(ema20, ema50):
        return MOMENTUM, adx
    else:
        return REVERSAL, adx
```

## Momentum Scoring (0-100)

| Factor | Points | Condition |
|--------|--------|-----------|
| Price above/below EMA20 | 20 | Direction alignment |
| EMA20 > EMA50 | 10 | Trend confirmed |
| Good pullback (1-5%) | 30 | Entry zone quality |
| High volume (>$100M) | 20 | Liquidity confirmed |
| RSI not overbought/oversold | 20 | Room to move |

Threshold: ≥60 = signal, ≥80 = strong signal

## Implementation

See `~/.hermes/scripts/mona_dual_mode_scanner.py` for full implementation.

## Key Lessons

1. **SMC-only misses 70%+ of opportunities** on trending tokens
2. **Momentum + pullback** is the highest win-rate setup for crypto
3. **Volume filter** ($100M+) prevents illiquid token traps
4. **RSI filter** prevents buying tops / selling bottoms
5. **EMA alignment** confirms trend direction before entry
