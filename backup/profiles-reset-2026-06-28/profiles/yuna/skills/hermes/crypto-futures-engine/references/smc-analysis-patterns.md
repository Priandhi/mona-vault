# SMC (Smart Money Concepts) Analysis Patterns

Reference for integrating Dozero-style SMC analysis into futures engines.

## Core SMC Components

### Order Block Detection

```python
def detect_order_blocks(opens, highs, lows, closes, volumes, atr):
    """Detect OBs with strength rating: weak/medium/strong/institutional"""
    obs = []
    for i in range(n - lookback, n - 1):
        body = abs(closes[i] - opens[i])
        if body < atr * 0.5:
            continue
            
        # Bullish OB: last down candle before strong up move
        if closes[i] < opens[i] and i < n - 1:
            next_body = closes[i+1] - opens[i+1]
            if next_body > atr * 1.0 and closes[i+1] > opens[i+1]:
                strength = rate_ob_strength(...)
                obs.append(OrderBlock(high, low, mid, is_bullish=True, strength))
        
        # Bearish OB: last up candle before strong down move
        if closes[i] > opens[i] and i < n - 1:
            next_body = opens[i+1] - closes[i+1]
            if next_body > atr * 1.0 and closes[i+1] < opens[i+1]:
                strength = rate_ob_strength(...)
                obs.append(OrderBlock(high, low, mid, is_bullish=False, strength))
    
    # Check freshness (untested = strongest)
    for ob in obs:
        if ob.low <= current_price <= ob.high:
            ob.tested = True
            ob.fresh = False
    
    return obs

def rate_ob_strength(high, low, volume, body, atr, ...):
    """Rate: institutional > strong > medium > weak"""
    if volume > 1000000 and body > atr * 2:
        return "institutional"
    if not tested:
        return "strong"
    if test_count <= 1:
        return "medium"
    return "weak"
```

### FVG Detection

```python
def detect_fvgs(highs, lows, closes, volumes, atr):
    """Detect FVGs with quality: tested/partial/virgin/virgin_hv"""
    fvgs = []
    for i in range(1, n - 1):
        # Bullish FVG
        gap = lows[i + 1] - highs[i - 1]
        if gap > atr * 0.3:
            quality = rate_fvg_quality(...)
            fvgs.append(EnhancedFVG(high, low, mid, is_bullish=True, quality))
        
        # Bearish FVG
        gap = lows[i - 1] - highs[i + 1]
        if gap > atr * 0.3:
            quality = rate_fvg_quality(...)
            fvgs.append(EnhancedFVG(high, low, mid, is_bullish=False, quality))
    
    return fvgs

def rate_fvg_quality(...):
    """Quality: virgin_hv > virgin > partial > tested"""
    if volume > 1000000:
        base = "virgin_hv"
    else:
        base = "virgin"
    
    if filled:
        return "tested"
    if partial:
        return "partial"
    return base
```

### Liquidity Sweep Detection

```python
def detect_liquidity_sweep(liq_levels, current_price, prev_close):
    """Detect smart money sweeping liquidity"""
    # Sweep low: price breaks below support then reclaims
    # Sweep high: price breaks above resistance then fails
    
    for liq in reversed(liq_levels[-5:]):
        if liq['type'] == 'low':
            if lows[-1] < liq['price'] and closes[-1] > liq['price']:
                return {'type': 'bullish_sweep', 'level': liq['price']}
        elif liq['type'] == 'high':
            if highs[-1] > liq['price'] and closes[-1] < liq['price']:
                return {'type': 'bearish_sweep', 'level': liq['price']}
```

## Multi-Timeframe SMC Pattern

```python
# Detect OB/FVG on EACH timeframe separately
for tf in ['D1', 'H4', 'H1', 'M15']:
    obs = detect_order_blocks(data[tf])
    fvgs = detect_fvgs(data[tf])
    
# Prefer H4 OB > H1 OB > M15 OB
# Prefer H1 FVG > H4 FVG (more precise)
```

## Confluence Scoring (100-point scale)

```
MTF Alignment:     20 pts (fully aligned) / 12 pts (mostly)
Fresh OB:          15 pts (H4) + 10 pts (H1) + 5 pts (M15)
Virgin FVG:        15 pts (H1) + 5 pts (H4)
CHOCH:             15 pts (M15 confirmation)
Liq Sweep + Disp:  15 pts (both) / 8 pts (one)
Smart Money Flow:  10 pts + 5 pts (whale)
Zone Bonus:        5 pts (discount for long, premium for short)
```

## Dual Mode Scanner

```python
class MarketMode(Enum):
    REVERSAL = "reversal"   # Ranging market → SMC patterns
    MOMENTUM = "momentum"   # Trending market → Trend + Pullback

def detect_market_mode(klines):
    adx = calculate_adx(klines, 14)
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    
    if adx > 25 and ema_aligned:
        return MarketMode.MOMENTUM, adx
    else:
        return MarketMode.REVERSAL, adx
```

## Momentum Entry Strategy

```python
def analyze_momentum(klines, ticker, funding):
    """For trending markets: enter on pullback to EMA20"""
    bullish = price > ema20 > ema50
    bearish = price < ema20 < ema50
    
    pullback_pct = abs(price - ema20) / ema20 * 100
    
    # Score: trend (20-30) + pullback (20-30) + volume (10-20) + RSI (20) + funding (10)
    # Entry at EMA20, SL = EMA20 - 1.5*ATR, TP = EMA20 + N*ATR
```

## Pitfalls

1. **Division by zero**: Always guard `vol_avg > 0` before dividing
2. **SMC threshold**: Start with 40, not 65+ (too few signals)
3. **Fresh OB rarity**: High-momentum tokens rarely have fresh OBs
4. **Virgin FVG rarity**: Most FVGs get tested quickly in crypto

## Signal Format (Dozero.x Style)

```
🟢 **{SYMBOL} LONG SIGNAL**
━━━━━━━━━━━━━━━━━━━━━━━━━━

**ENTRY:** ${entry:,.6f}
**STOP LOSS:** ${sl:,.6f}
**TP1 (1:1):** ${tp1:,.6f}

**ENTRY SOURCE:**
  • H4 BULLISH OB (FRESH)
  • H1 BULLISH FVG (VIRGIN)
  • M15 CHOCH BULLISH CONFIRMATION

**MARKET STRUCTURE:**
  D1: BULLISH
  H4: BULLISH  
  H1: BULLISH

**CONFIDENCE SCORE:** 75/100 (HIGH)
```
