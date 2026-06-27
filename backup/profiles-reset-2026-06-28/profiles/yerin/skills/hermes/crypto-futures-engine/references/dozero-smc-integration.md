# DOZERO.X SMC Engine — Integration with Autonomous Engine

**Status:** Integrated June 2026 into `mona_autonomous.py` v2.0
**Script:** `~/.hermes/scripts/dozero_smc_engine.py` (pure Python, no external deps)

## What it adds to the signal engine

The DOZERO.X SMC Engine provides **Smart Money Concepts** analysis on top of the existing 12 signal generators. It adds institutional-grade structure analysis:

| Component | What it does |
|-----------|-------------|
| Multi-Timeframe | Daily bias → H4 structure → H1 execution → M15 precision |
| Virgin FVG | Detects fresh Fair Value Gaps (untouched by price) |
| Liquidity Sweep | Identifies when price swept liquidity pools |
| BOS/CHOCH | Break of Structure (continuation) / Change of Character (reversal) |
| Premium/Discount | Long in discount zone, short in premium zone |
| Smart Entry | Limit order placement based on retracement strength |
| Confluence Scoring | 0-100 score combining all SMC factors |

## Confluence scoring (100 max)

| Factor | Points |
|--------|--------|
| MTF fully aligned (all 4 TFs agree) | 25 |
| Virgin FVG present | 20 |
| Liquidity sweep + displacement | 20 |
| BOS confirmed | 15 (CHOCH = 12) |
| Correct premium/discount zone | 10 (wrong zone = -5) |
| Accumulation/distribution detected | 10 |

Threshold: **75+ = elite setups only**

## Integration in mona_autonomous.py

1. `_evaluate_symbol()` fetches H1, H4, Daily klines via `data.binance_klines()`
2. `_get_bias()` determines MTF bias from recent swing structure
3. `smc_engine.full_analysis()` runs complete SMC pipeline
4. SMC confluence × 0.3 = bonus added to signal score (max +30 points)
5. If SMC direction conflicts with signal direction → SKIP (safety)
6. If SMC setup found → uses structural SL/TP (FVG-based) instead of ATR-based

## Key classes

```python
from dozero_smc_engine import DozeroSMCEngine, Bias as SMCBias, SMCSetup

engine = DozeroSMCEngine({
    'confluence_threshold': 75,
    'swing_lookback': 5,
    'displacement_atr_mult': 1.5,
    'fvg_min_atr_mult': 0.5,
})

setup = engine.full_analysis("BTCUSDT", ohlcv_data, mtf_biases)
if setup:
    print(f"Score: {setup.confluence_score}, Entry: {setup.entry_price}, SL: {setup.stop_loss}")
```

## Full Market Scanner

When user asks to scan the market, use `references/full-market-scanner.md` for the complete workflow. Script: `~/.hermes/scripts/scan_market_full.py`. Scans 550+ USDT pairs in ~2-3 minutes, ranks by DOZERO.X SMC confluence score.

## Pitfalls

- **Pure Python, no numpy** — uses list comprehensions and manual math. Safe for any Python 3.x.
- **Swing detection needs clean data** — random/noisy data returns 0 swings. Real market data works.
- **MTF bias is simplified** — compares last 5 vs previous 5 candle averages, not full swing analysis.
- **Confluence can go negative** if wrong premium/discount zone (-5 penalty).
- **WASM captcha for Galxe** — NOT related to this module, but same session. See `hermes-crypto-agent` skill for Galxe WASM bypass.
- **Volume conviction is NOT in the SMC engine** — The SMC engine analyzes structure (FVG, BOS, sweeps) but does NOT check volume. A BOS on low volume (< 0.3x 20-period average) is a fakeout trap. Always check H1 volume ratio before entering, even if SMC score is 75+.
- **Orderbook is NOT in the SMC engine** — Bid/ask ratio < 0.5 means sellers dominate. This can invalidate a bullish SMC setup. Add `GET /fapi/v1/depth?limit=20` as a pre-entry check.
- **Full scan typical results:** 550+ pairs scanned → 0-2 elite (75+), 5-10 strong (60-74), 20-30 good (50-59). If you get 0 elite, that's NORMAL — it means the market is ranging or lacks structure. Wait for trending conditions.
- **SMC score 67 is NOT "close enough" to 75** — The 8-point gap represents missing structural components (usually MTF alignment or volume confirmation). Entering at 67 and hoping it works is gambling, not trading. Real session evidence: entered USUSDT at 67, found bearish orderbook + dying volume, closed immediately for -$0.02 loss.
