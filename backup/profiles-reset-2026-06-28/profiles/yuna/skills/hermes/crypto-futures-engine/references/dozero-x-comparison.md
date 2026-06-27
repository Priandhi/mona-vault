# Dozero.x vs Our Engine — Gap Analysis

## Overview
Dozero.x is a professional SMC-based trading system that significantly outperforms our basic signal engine. This document captures the gaps and improvement roadmap.

## Performance Comparison

| Metric | Our Engine | Dozero.x |
|--------|-----------|----------|
| Confidence Score | 33% | 75% |
| SMC Integration | Basic (single TF) | Multi-TF (D1+H4+H1+M15) |
| Fresh OB Detection | ❌ Missing | ✅ Implemented |
| FVG Detection | ❌ Missing | ✅ Implemented |
| Liquidity Sweep | ❌ Missing | ✅ Implemented |
| CHoCH Confirmation | ❌ Missing | ✅ Implemented |
| L/S Ratio Analysis | ❌ Missing | ✅ Implemented |

## Key Gaps Identified

### 1. Multi-Timeframe SMC Alignment
**Our Engine:** Single timeframe analysis
**Dozero.x:** D1 + H4 + H1 + M15 alignment for high-probability entries

**Improvement:**
```python
# Add multi-TF bias detection
async def get_mtf_bias(self, symbol: str) -> Dict:
    klines_d = await self.data.binance_klines(symbol, '1d', 30)
    klines_h4 = await self.data.binance_klines(symbol, '4h', 50)
    klines_h1 = await self.data.binance_klines(symbol, '1h', 100)
    klines_m15 = await self.data.binance_klines(symbol, '15m', 50)
    
    biases = {
        'daily': self._detect_bias(klines_d),
        'h4': self._detect_bias(klines_h4),
        'h1': self._detect_bias(klines_h1),
        'm15': self._detect_bias(klines_m15),
    }
    return biases
```

### 2. Fresh Order Block + FVG Detection
**Our Engine:** Basic OB detection
**Dozero.x:** Fresh OB + FVG (untested = high probability)

**Key Insight:** Fresh OB/FVG = price hasn't returned to test it yet = higher probability of reaction

**Improvement:**
```python
def detect_fresh_ob(self, klines: List, lookback: int = 20) -> List:
    """Detect untested Order Blocks."""
    obs = []
    for i in range(len(klines) - lookback, len(klines)):
        ob = self._identify_ob(klines, i)
        if ob and not self._is_tested(ob, klines[i+1:]):
            ob['fresh'] = True
            obs.append(ob)
    return obs

def detect_fresh_fvg(self, klines: List, lookback: int = 20) -> List:
    """Detect untested Fair Value Gaps."""
    fvgs = []
    for i in range(2, len(klines) - lookback):
        fvg = self._identify_fvg(klines, i)
        if fvg and not self._is_filled(fvg, klines[i+1:]):
            fvg['fresh'] = True
            fvgs.append(fvg)
    return fvgs
```

### 3. Liquidity Sweep Detection
**Our Engine:** ❌ Missing
**Dozero.x:** Detects when smart money sweeps liquidity

**Key Insight:** Liquidity sweep = price breaks key level to trigger stop losses → reversal likely

**Improvement:**
```python
def detect_liquidity_sweep(self, klines: List, lookback: int = 50) -> bool:
    """Detect if sell-side/buy-side liquidity was swept."""
    recent_lows = [k['low'] for k in klines[-lookback:]]
    recent_highs = [k['high'] for k in klines[-lookback:]]
    
    # Check if current candle swept below recent lows
    current_low = klines[-1]['low']
    support_level = min(recent_lows[:-1])
    
    if current_low < support_level and klines[-1]['close'] > support_level:
        return True  # Sell-side liquidity swept
    return False
```

### 4. CHoCH (Change of Character) Confirmation
**Our Engine:** ❌ Missing
**Dozero.x:** CHoCH = first break against trend = reversal signal

**Key Insight:** CHoCH is more powerful than BOS (Break of Structure) — indicates trend reversal

**Improvement:**
```python
def detect_choch(self, klines: List, trend: str) -> bool:
    """Detect Change of Character (reversal signal)."""
    if trend == 'bullish':
        # CHoCH bearish: break below previous higher low
        prev_hl = self._find_previous_higher_low(klines)
        if klines[-1]['close'] < prev_hl:
            return True
    elif trend == 'bearish':
        # CHoCH bullish: break above previous lower high
        prev_lh = self._find_previous_lower_high(klines)
        if klines[-1]['close'] > prev_lh:
            return True
    return False
```

### 5. Long/Short Ratio Analysis
**Our Engine:** ❌ Missing
**Dozero.x:** L/S ratio for over-crowding detection

**Key Insight:** Over-crowded side = squeeze potential (e.g., 61.8% short = squeeze candidate)

**Improvement:**
```python
async def get_ls_ratio(self, symbol: str) -> Dict:
    """Get Long/Short ratio from Binance."""
    url = 'https://fapi.binance.com/futures/data/globalLongShortAccountRatio'
    params = {'symbol': symbol, 'period': '1h', 'limit': 1}
    async with self.session.get(url, params=params) as resp:
        data = await resp.json()
        if data:
            return {
                'long_pct': float(data[0]['longAccount']) * 100,
                'short_pct': float(data[0]['shortAccount']) * 100,
                'ratio': float(data[0]['longShortRatio']),
            }
    return {}
```

## Signal Weight Adjustments (Post-Dozero.x Analysis)

### Current Weights (Problematic)
```python
weight_fear_greed: float = 5  # Still too dominant when F&G is extreme
```

### Recommended Weights
```python
# Reduce FearGreed influence
weight_fear_greed: float = 3  # Was 5, reduce to 3

# Add new SMC weights
weight_fresh_ob: float = 15  # Fresh Order Block
weight_fresh_fvg: float = 12  # Fresh Fair Value Gap
weight_liquidity_sweep: float = 10  # Liquidity sweep
weight_choch: float = 12  # Change of Character
weight_ls_ratio: float = 8  # Long/Short ratio
```

## Known Issues

### FearGreed Domination
**Problem:** When market is in Extreme Fear (F&G < 15), FearGreed gives +90 to ALL pairs, inflating scores.

**Example:**
- F&G = 12 (Extreme Fear)
- All pairs get +90 from FearGreed
- Composite scores inflated by ~4-5 points

**Solution:**
1. Reduce FearGreed weight from 5 to 3
2. Add cap: max FearGreed contribution = 30 (not 90)
3. Only apply FearGreed when price is at key support/resistance

### High-Volatility Pairs
**Problem:** Meme coins (HYPE, DOGE, PEPE) have high ATR% and unpredictable moves.

**Backtest Results:**
- HYPE: -17.31% PnL, PF 0.81, MaxDD 39.70%
- SOL: +28.83% PnL, PF 2.05, MaxDD 7.80%

**Solution:** Blacklist high-volatility pairs or reduce position size by 50%.

## ✅ RESOLVED: Mona SMC Master v2.1 (Built: 2026-06-08)

**Status:** Built and tested — `~/.hermes/scripts/mona_smc_master_v21.py`

### What was built:
1. **Multi-TF OB/FVG Detection** — Detects OB/FVG on EACH timeframe (D1, H4, H1, M15) separately
2. **Fresh OB Strength Rating** — WEAK/MEDIUM/STRONG/INSTITUTIONAL based on test count and displacement
3. **FVG Quality Scoring** — TESTED/PARTIAL/VIRGIN/VIRGIN_HIGH_VOL
4. **Smart Money Flow Analysis** — ACCUMULATION/DISTRIBUTION/MARKUP/MARKDOWN detection
5. **CHOCH Confirmation** — M15 precision entry confirmation
6. **Step-by-Step Explanation** — "Kenapa entry di sini" breakdown
7. **Telegram Output** — Professional format matching Dozero.x

### Performance Comparison (After v2.1):
```
                | Mona v2.1  | Dozero.x
----------------|------------|----------
Confidence      | 50/100     | 75/100
Fresh OB        | 6 (H4+H1+M15)| 3 (H4+H1)
Virgin FVG      | ❌         | ✅ H1
CHoCH           | ❌         | ✅ M15
R:R             | 1:2        | 1:4
Entry           | $0.094365  | $0.092895
SL              | $0.093325  | $0.089153
```

### Remaining Gaps:
1. **Virgin FVG Detection** — Our engine finds 0 virgin FVGs, Dozero.x finds 1
2. **CHoCH Detection** — Our engine doesn't detect CHoCH on M15
3. **R:R Ratio** — Our engine has 1:2, Dozero.x has 1:4

### Root Cause Analysis:
- **Virgin FVG Issue:** All FVGs are marked as "tested" — detection logic may be too aggressive
- **CHoCH Issue:** M15 swing detection may not be finding enough swing points
- **R:R Issue:** Entry calculation using OB mid instead of optimal entry

### Next Steps:
1. Debug FVG detection — check if `filled_pct` calculation is correct
2. Debug CHoCH detection — verify M15 swing point detection
3. Improve entry calculation — use FVG/OB confluence for optimal entry

## Improvement Roadmap

### Phase 1: Multi-TF SMC (Priority: HIGH)
- [ ] Add multi-timeframe bias detection
- [ ] Implement fresh OB detection
- [ ] Implement fresh FVG detection

### Phase 2: Smart Money Detection (Priority: HIGH)
- [ ] Liquidity sweep detection
- [ ] CHoCH confirmation
- [ ] Displacement candle detection

### Phase 3: Sentiment Enhancement (Priority: MEDIUM)
- [ ] L/S ratio integration
- [ ] FearGreed weight reduction
- [ ] FearGreed cap implementation

### Phase 4: Risk Management (Priority: MEDIUM)
- [ ] High-volatility pair blacklist
- [ ] Dynamic position sizing by confidence
- [ ] Multi-pair correlation check

## Testing Checklist

- [ ] Backtest with multi-TF SMC signals
- [ ] Compare win rate before/after improvements
- [ ] Test with fresh OB/FVG entries only
- [ ] Verify CHoCH detection accuracy
- [ ] Check L/S ratio signal quality
