# Mona SMC Master v2.1 — Multi-TF OB/FVG Detection Engine

**Status:** Built 2026-06-08, tested on FFUSDT
**Script:** `~/.hermes/scripts/mona_smc_master_v21.py`
**Base Engine:** `~/.hermes/scripts/dozero_smc_engine.py`

## Architecture

```
mona_smc_master_v21.py
├── MonaSMCMasterV21 (extends MonaSMCMaster)
│   ├── full_analysis() — Multi-TF OB/FVG detection pipeline
│   ├── detect_order_blocks() — OB with strength rating
│   ├── detect_enhanced_fvgs() — FVG with quality scoring
│   ├── analyze_smart_money_flow() — Smart Money detection
│   ├── get_ls_ratio() — L/S ratio analysis
│   ├── generate_explanation() — Step-by-step breakdown
│   └── format_telegram() — Professional Telegram output
└── Data Classes
    ├── OrderBlock — high, low, mid, is_bullish, strength, volume, displacement_strength, index, tested, fresh
    ├── EnhancedFVG — high, low, mid, is_bullish, quality, size_pct, volume_at_creation, index, filled_pct
    ├── SmartMoneyAnalysis — flow, strength, evidence, institutional_activity, whale_accumulation
    ├── ChartAnnotation — order_blocks, fvgs, liquidity_levels, structure_breaks, current_price, entry_zone, stop_loss, take_profits
    ├── StepByStepExplanation — market_structure, smart_money_activity, entry_reasoning, risk_analysis, confidence_boosters, warnings
    └── MonaSetup — All fields from SMCSetup + enhanced fields
```

## Key Features

### 1. Multi-TF OB/FVG Detection
Detects OB/FVG on EACH timeframe separately, then combines:
- D1: Major structure
- H4: Primary OB/FVG
- H1: Execution OB/FVG
- M15: Precision OB/FVG

### 2. Order Block Strength Rating
```python
class OBStrength(Enum):
    WEAK = "weak"           # Tested multiple times
    MEDIUM = "medium"       # Tested once
    STRONG = "strong"       # Untested (fresh)
    INSTITUTIONAL = "inst"  # High volume + displacement
```

### 3. FVG Quality Scoring
```python
class FVGQuality(Enum):
    TESTED = "tested"           # Already filled
    PARTIAL = "partial"         # Partially filled
    VIRGIN = "virgin"           # Never filled
    VIRGIN_HIGH_VOL = "virgin_hv"  # Never filled + high volume
```

### 4. Smart Money Flow Analysis
```python
class SmartMoneyFlow(Enum):
    ACCUMULATION = "accumulation"      # Buying quietly
    DISTRIBUTION = "distribution"      # Selling quietly
    MARKUP = "markup"                  # Price rising (public buying)
    MARKDOWN = "markdown"              # Price falling (public selling)
    NEUTRAL = "neutral"
```

### 5. Step-by-Step Explanation
Generates detailed explanation of why entry at this level:
- Market Structure Analysis
- Smart Money Activity
- Entry Reasoning (OB/FVG/Liquidity)
- Risk Analysis
- Confidence Boosters
- Warnings

## Confluence Scoring (v2.1)

| Factor | Points |
|--------|--------|
| MTF fully aligned (all 4 TFs agree) | 20 |
| H4 Fresh OB | 15 |
| H1 Fresh OB | 10 |
| M15 Fresh OB | 5 |
| H1 Virgin FVG | 15 |
| H4 Virgin FVG | 5 |
| M15 CHOCH confirmation | 15 |
| Liquidity sweep + displacement | 15 |
| Liquidity sweep only | 8 |
| Displacement only | 8 |
| Smart Money: ACCUMULATION/DISTRIBUTION | 10 |
| Whale activity | 5 |
| Correct zone (discount for long, premium for short) | 5 |

**Threshold:** 50+ (configurable)

## Usage

```python
from mona_smc_master_v21 import MonaSMCMasterV21

engine = MonaSMCMasterV21({'confluence_threshold': 50})

# Full analysis
setup = await engine.full_analysis('FFUSDT', data_collector)

if setup:
    # Telegram output
    print(engine.format_telegram(setup))
    
    # Access setup data
    print(f"Entry: ${setup.entry_price:.6f}")
    print(f"SL: ${setup.stop_loss:.6f}")
    print(f"TP1: ${setup.tp1:.6f}")
    print(f"Confidence: {setup.confluence_score}/100 ({setup.confidence})")
    
    # Access enhanced data
    print(f"Fresh OBs: {setup.fresh_ob_count}")
    print(f"Virgin FVGs: {setup.virgin_fvg_count}")
    print(f"Smart Money: {setup.smart_money.flow.value}")
    print(f"L/S Ratio: {setup.ls_ratio}")
```

## Known Issues

### 1. Virgin FVG Detection
**Problem:** All FVGs are marked as "tested" — 0 virgin FVGs found
**Root Cause:** `filled_pct` calculation may be too aggressive
**Debug:** Check `detect_enhanced_fvgs()` logic for partial fill detection

### 2. CHoCH Detection
**Problem:** M15 CHoCH not detected even when present
**Root Cause:** M15 swing detection may not find enough swing points
**Debug:** Check `find_swing_points()` with M15 data

### 3. Entry Calculation
**Problem:** Entry using OB mid instead of optimal entry
**Root Cause:** No FVG/OB confluence for entry optimization
**Fix:** Use FVG low (for long) or OB high (for short) as entry

## Integration with Main Engine

To integrate with `mona_futures_v2/engine.py`:

```python
from mona_smc_master_v21 import MonaSMCMasterV21

class MonaFuturesEngine:
    def __init__(self, config):
        # ... existing init ...
        self.smc_engine = MonaSMCMasterV21({'confluence_threshold': 50})
    
    async def scan_once(self, symbols=None):
        for symbol in symbols:
            # ... existing analysis ...
            
            # Run SMC analysis
            smc_setup = await self.smc_engine.full_analysis(symbol, self.data)
            if smc_setup:
                analysis['smc_setup'] = smc_setup
                analysis['smc_score'] = smc_setup.confluence_score
                analysis['smc_direction'] = smc_setup.direction
```

## Testing

```bash
# Test on specific pair
python3 mona_smc_master_v21.py

# Test with debug output
python3 << 'PYEOF'
import asyncio
from mona_smc_master_v21 import MonaSMCMasterV21
from mona_futures_v2.data import DataCollector

async def test():
    data = DataCollector()
    engine = MonaSMCMasterV21({'confluence_threshold': 0})  # No threshold
    
    setup = await engine.full_analysis('FFUSDT', data)
    if setup:
        print(engine.format_telegram(setup))
    
    await data.close()

asyncio.run(test())
PYEOF
```

## Performance Results

### FFUSDT Analysis (2026-06-08)
```
Entry: $0.094365
SL: $0.093325
TP1: $0.095405
TP2: $0.096446
R:R: 1:2.0
Confidence: 50/100 (MEDIUM)
Fresh OBs: 6 (H4+H1+M15)
Virgin FVGs: 0
Smart Money: neutral
MTF Alignment: D1=bullish, H4=bearish, H1=bullish, M15=neutral
```

### Comparison with Dozero.x
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

## Next Steps

1. **Debug FVG detection** — Check `filled_pct` calculation
2. **Debug CHoCH detection** — Verify M15 swing point detection
3. **Improve entry calculation** — Use FVG/OB confluence
4. **Add L/S ratio integration** — Connect to Binance API
5. **Add chart generation** — Visual SMC analysis
6. **Deploy to production** — Integrate with main engine
