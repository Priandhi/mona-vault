# SMC (Smart Money Concepts) Analysis for Crypto Futures

## Overview

SMC analysis identifies institutional trading patterns. This reference covers the approach used to build Mona SMC Master v2.1, which matches/exceeds competitor bots (Dozero.x, Slevensy Scanner).

## Multi-Timeframe Analysis

Analyze each timeframe separately, then combine:

```
D1  — Trend direction + major S/R levels
H4  — Structure + bias
H1  — Entry signals
M15 — Precision entries + timing
```

**Rule: NEVER trade against the 4H trend**

## Order Block Detection

### Types
- **Bullish OB**: Last down candle before strong up move
- **Bearish OB**: Last up candle before strong down move

### Strength Rating
```python
class OBStrength(Enum):
    WEAK = "weak"           # Tested multiple times
    MEDIUM = "medium"       # Tested once
    STRONG = "strong"       # Untested (fresh)
    INSTITUTIONAL = "inst"  # High volume + displacement
```

### Detection Logic
```python
# Bullish OB: last down candle before strong up move
if closes[i] < opens[i] and i < n - 1:
    next_body = closes[i+1] - opens[i+1]
    if next_body > atr * 1.0 and closes[i+1] > opens[i+1]:
        # This is a bullish OB
        strength = rate_ob_strength(...)
```

### Fresh vs Tested
- **Fresh**: OB hasn't been retested since formation
- **Tested**: Price has returned to OB zone
- **Fresh OBs are higher probability entries**

## Fair Value Gap (FVG) Detection

### Types
- **Bullish FVG**: Gap between candle 1 high and candle 3 low
- **Bearish FVG**: Gap between candle 1 low and candle 3 high

### Quality Rating
```python
class FVGQuality(Enum):
    TESTED = "tested"           # Already filled
    PARTIAL = "partial"         # Partially filled
    VIRGIN = "virgin"           # Never filled
    VIRGIN_HIGH_VOL = "virgin_hv"  # Never filled + high volume
```

### Detection Logic
```python
# Bullish FVG
gap = lows[i + 1] - highs[i - 1]
if gap > atr * 0.3:
    # This is a bullish FVG
    quality = rate_fvg_quality(...)
```

### Virgin FVGs
- **Virgin FVG**: Never been filled = strongest signal
- **Virgin + High Volume**: Even stronger
- **Entry at virgin FVG = high probability**

## CHoCH (Change of Character) Detection

CHoCH = First break against the trend = reversal signal

### Detection Logic
```python
# Find swing points
swings = find_swing_points(highs, lows)

# Determine current bias
if len(swings) >= 4:
    rh = [s for s in swings[-6:] if s.is_high]
    rl = [s for s in swings[-6:] if not s.is_high]
    
    if rh[-1].price > rh[-2].price and rl[-1].price > rl[-2].price:
        current_bias = SMCBias.BULLISH
    elif rh[-1].price < rh[-2].price and rl[-1].price < rl[-2].price:
        current_bias = SMCBias.BEARISH

# Detect CHoCH
choch = detect_choch(swings, current_price, current_bias, ...)
```

## Liquidity Sweep Detection

Liquidity levels = where stop losses cluster (below swing lows, above swing highs)

### Detection Logic
```python
# Find liquidity levels
liq_levels = find_liquidity_levels(highs, lows)

# Detect sweep
sweep = detect_liquidity_sweep(liq_levels, current_price, prev_price)
```

### Smart Money Activity
When liquidity is swept, smart money has entered. This is a strong signal.

## Smart Money Flow Analysis

```python
class SmartMoneyFlow(Enum):
    ACCUMULATION = "accumulation"      # Buying quietly
    DISTRIBUTION = "distribution"      # Selling quietly
    MARKUP = "markup"                  # Price rising (public buying)
    MARKDOWN = "markdown"              # Price falling (public selling)
    NEUTRAL = "neutral"
```

### Detection Logic
- **Accumulation**: Price flat/down + volume rising + range contracting
- **Distribution**: Price flat/up + volume rising + range contracting
- **Markup**: Price rising + volume confirming
- **Markdown**: Price falling + volume confirming

## Confluence Scoring

### Score Components (out of 100)
```
MTF Alignment:     20 pts (fully aligned)
Fresh OBs:         25 pts (H4=15, H1=10, M15=5)
Virgin FVGs:       20 pts (H1=15, H4=5)
CHoCH:             15 pts
Liquidity Sweep:   15 pts (+ displacement)
Smart Money Flow:  10 pts
Zone Bonus:         5 pts (discount for long, premium for short)
```

### Confidence Levels
```
ELITE:  ≥90/100
HIGH:   ≥75/100
MEDIUM: ≥50/100
LOW:    <50/100
```

### Threshold
- **Minimum 60/100** for auto-send to Telegram
- **Minimum 50/100** for watchlist monitoring

## Chart Generation

Use matplotlib with dark theme:

```python
# Colors (MUST use tuples, NOT CSS rgba() strings)
colors = {
    'ob_bullish': (0, 1, 0.53, 0.2),  # green, alpha 0.2
    'ob_bearish': (1, 0.27, 0.27, 0.2),  # red, alpha 0.2
    'fvg_bullish': (0, 1, 0.53, 0.15),
    'fvg_bearish': (1, 0.27, 0.27, 0.15),
}
```

### Annotations
- **Order Blocks**: Colored rectangles (green=bullish, red=bearish)
- **FVGs**: Colored rectangles with lower opacity
- **Liquidity Levels**: Yellow dotted lines
- **Entry/SL/TP**: Horizontal lines with labels

## Signal Deduplication

Track sent signals to avoid duplicates:

```python
SENT_SIGNALS_FILE = Path.home() / '.hermes' / 'data' / 'sent_signals.json'

def is_signal_sent(pair: str, direction: str, entry: float) -> bool:
    key = f"{pair}_{direction}_{entry:.6f}"
    if key in sent_signals:
        sent_time = sent_signals[key].get('timestamp', 0)
        if time.time() - sent_time < 3600:  # 1 hour
            return True
    return False
```

## Auto-Send to Telegram

When signal found with confidence ≥60:
1. Format message (match Dozero.x style)
2. Generate chart with SMC annotations
3. Send to Telegram topic (Futures Trading topic)
4. Mark as sent in dedup file

## Pitfalls

1. **matplotlib rgba format**: Use tuples `(1, 0, 0, 0.5)`, NOT CSS strings `'rgba(255, 0, 0, 0.5)'`
2. **Division by zero**: Always protect financial calculations with `if denominator > 0 else 0`
3. **Fresh OB detection**: Check if OB has been retested since formation
4. **Virgin FVG detection**: Check if FVG has been filled
5. **CHoCH detection**: Need at least 4 swing points
6. **Smart Money Flow**: Volume must be > 0 for calculations

## File Structure

```
~/.hermes/scripts/
├── mona_smc_master.py          # Core SMC engine
├── mona_smc_master_v21.py      # Multi-TF version
├── mona_signal_generator.py    # Chart + explanation generator
├── mona_signal_scanner.py      # Auto-scan and send
└── mona_futures_v2/            # Main futures engine
    ├── engine.py
    ├── signals.py
    ├── config.py
    ├── data.py
    └── risk.py
```

## References

- Dozero.X SMC Engine: `~/.hermes/scripts/dozero_smc_engine.py`
- Mona SMC Master v2.1: `~/.hermes/scripts/mona_smc_master_v21.py`
- Signal Scanner: `~/.hermes/scripts/mona_signal_scanner.py`
