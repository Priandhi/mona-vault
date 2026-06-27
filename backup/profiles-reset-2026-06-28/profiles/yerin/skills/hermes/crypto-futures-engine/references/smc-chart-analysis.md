# SMC Chart Analysis + Visual Signal Generation

## Architecture: Mona SMC Master v2.1

```
mona_smc_master.py          # Core SMC engine (enhanced OB/FVG detection)
mona_smc_master_v21.py      # Multi-TF version (D1/H4/H1/M15)
mona_signal_generator.py    # Chart + explanation + Telegram notification
dozero_smc_engine.py        # Base SMC engine (swing points, FVG, BOS/CHOCH)
```

## Key Components

### 1. Enhanced Order Block Detection
- **Strength Rating**: WEAK (tested 2+), MEDIUM (tested 1), STRONG (fresh/untested), INSTITUTIONAL (high vol + displacement)
- **Multi-TF**: Detect OBs on EACH timeframe separately, then combine
- **Fresh Priority**: Entry preferentially uses FRESH OBs matching direction

### 2. Enhanced FVG Detection
- **Quality Rating**: TESTED, PARTIAL, VIRGIN, VIRGIN_HIGH_VOL
- **Fill Tracking**: Calculate % of FVG already filled
- **Virgin Priority**: Virgin FVGs (never filled) are highest quality signals

### 3. Smart Money Flow Analysis
- **ACCUMULATION**: Price flat/down + volume rising + range contracting
- **DISTRIBUTION**: Price flat/up + volume rising + range contracting
- **MARKUP**: Price rising + volume confirming
- **MARKDOWN**: Price falling + volume confirming
- **Whale Detection**: Volume spike > 2 std dev from mean

### 4. Confluence Scoring (100 pts max)
- MTF Alignment: 20 pts
- Fresh OBs by TF (H4=15, H1=10, M15=5): 25 pts
- Virgin FVGs by TF (H1=15, H4=5): 20 pts
- CHOCH Confirmation: 15 pts
- Liquidity Sweep + Displacement: 15 pts
- Smart Money Flow: 10 pts
- Zone Bonus: 5 pts

### 5. Chart Generation (matplotlib)
- Dark theme (#1a1a2e background)
- Candlestick with OB/FVG zones overlay
- Entry/SL/TP horizontal lines with labels
- Liquidity levels as dotted lines
- Color scheme: green=bullish, red=bearish, yellow=liquidity

### 6. Step-by-Step Explanation
- Market Structure: D1/H4/H1/M15 alignment
- Entry Source: Which OB/FVG/CHOCH triggered
- Smart Money: Institutional activity detection
- Risk Analysis: R:R ratio, risk percentage
- Confidence Boosters: What supports the trade
- Warnings: What could go wrong

## Key Lessons

### What Makes Dozero.X Better (75/100 vs our initial 23/100)
1. **Virgin FVG detection** — FVGs that have never been tested
2. **CHOCH confirmation** — Change of Character on M15
3. **Multi-TF OB/FVG** — Separate detection per timeframe
4. **Better R:R** — Entry at OB mid, SL at OB low - buffer

### Improvements Made
- v1.0: Basic SMC (single TF, weak OB detection) → 23/100
- v2.0: Multi-TF OB/FVG + Smart Money Flow → 50/100
- v2.1: Separate per-TF detection + CHOCH → 50/100 (threshold 40)

### Trade-off: Threshold vs Signal Quality
- Threshold 50: Fewer signals, higher quality
- Threshold 40: More signals, moderate quality
- Current recommendation: 40 for monitoring, 50 for execution

## Chart Color Scheme (matplotlib compatible)
```python
colors = {
    'bg': '#1a1a2e',
    'candle_up': '#00ff88',
    'candle_down': '#ff4444',
    'ob_bullish': (0, 1, 0.53, 0.2),  # NOT rgba() string!
    'ob_bearish': (1, 0.27, 0.27, 0.2),
    'fvg_bullish': (0, 1, 0.53, 0.15),
    'fvg_bearish': (1, 0.27, 0.27, 0.15),
    'liquidity': (1, 1, 0, 0.5),
}
```
**PITFALL**: matplotlib does NOT accept CSS rgba() strings. Use tuple (r, g, b, a) with values 0-1.

## Telegram Output Format
Match Dozero.X style:
1. Header with emoji + pair + direction
2. Entry/SL/TP prices
3. Risk/Reward summary
4. Entry Sources (OB/FVG/CHOCH by timeframe)
5. Market Structure (D1/H4/H1/M15)
6. Reason (detailed explanation)
7. Confidence Score + Confluence list
8. Trade Status
