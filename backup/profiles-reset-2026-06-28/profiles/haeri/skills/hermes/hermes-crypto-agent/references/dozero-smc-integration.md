# DOZERO.X SMC Engine — Integration Reference

**Status:** Integrated into Mona Autonomous Engine v2.0 (June 2026)
**Script:** `~/.hermes/scripts/dozero_smc_engine.py` (pure Python, no deps)
**Integration:** `~/.hermes/scripts/mona_autonomous.py` (lines with `smc_engine`)

## What it adds to Mona Engine

| Feature | Before (v1.0) | After (v2.0 + DOZERO.X) |
|---------|---------------|--------------------------|
| Timeframe analysis | Single TF (H1) | Multi-TF: Daily→H4→H1→M15 |
| Entry zones | EMA crossover | Virgin FVG (untouched Fair Value Gaps) |
| Structure | Threshold score | BOS/CHOCH structural breaks |
| Liquidity | None | Sweep detection + displacement |
| Direction bias | Signal consensus | Premium/Discount zones |
| Entry | Market order | Smart Entry (retracement-based) |
| SL/TP | ATR-based fixed | Structural SL + 1:1/1:2/1:3/1:4 TPs |
| Scoring | 0-100 signals | Signals + SMC confluence (up to +30 bonus) |

## Confluence scoring breakdown (100 max)

- MTF Alignment: 25 points (all 4 TFs agree = 25, mostly aligned = 15, partial = 8)
- Virgin FVG present: 20 points (touched FVG = 5 only)
- Liquidity sweep + displacement: 20 points (either alone = 10)
- BOS/CHOCH confirmed: 15 points (BOS=15, CHOCH=12)
- Premium/Discount correct: 10 points (wrong zone = -5 penalty)
- Accumulation/Distribution: 10 points

Threshold: **75+ = elite setups only** (configurable)

## How integration works in mona_autonomous.py

1. `_evaluate_symbol()` fetches H1, H4, Daily klines via `data.binance_klines()`
2. `_get_bias()` determines MTF bias from swing structure (HH/HL = bullish, LH/LL = bearish)
3. `smc_engine.full_analysis()` runs complete SMC pipeline
4. SMC confluence score × 0.3 = bonus added to signal score (max +30)
5. If SMC direction conflicts with signal direction → SKIP (safety)
6. If SMC setup found → uses structural SL/TP instead of ATR-based
7. Journal records full DOZERO.X reasoning (confidence, score, zone)

## Standalone SMC scan workflow (for existing positions)

When user asks "scan ulang posisi" or "cek sinyal masih valid", run DOZERO.X analysis on each open position independently:

1. Fetch position list from Binance (`/fapi/v2/positionRisk`)
2. For each active position, fetch klines on 4 timeframes (15m, 1h, 4h, 1d)
3. Run standalone SMC analysis per position:
   - `find_swings()` → swing highs/lows on each TF
   - `detect_fvg()` → Fair Value Gaps
   - `is_virgin_fvg()` → check if FVG untouched
   - `detect_bos_choch()` → structural breaks
   - `detect_liquidity_sweep()` → stop hunts
   - `detect_displacement()` → momentum candles
   - `get_market_structure()` → uptrend/downtrend/ranging
   - `calc_premium_discount()` → premium/discount/equilibrium zone
4. Score each position on 6 confluence dimensions (same breakdown as above)
5. Verdict: ≥75 = ✅ STRONG (hold), 50-74 = ⚠️ MODERATE (watch), 30-49 = 🟡 WEAK (partial close), <30 = 🔴 INVALID (consider close)
6. CHOCH against position = immediate close recommendation

**Script template:** `/home/ubuntu/.hermes/scripts/close_all_positions.py` has the full standalone scan + close pattern (API key loading, signing, position fetch, kline fetch, analysis, scoring).

## MTF bias determination

```python
def _get_bias(klines):
    # Compare last 5 candles vs previous 5 candles
    mid_h = avg(highs[-5:])
    prev_h = avg(highs[-10:-5])
    mid_l = avg(lows[-5:])
    prev_l = avg(lows[-10:-5])
    if mid_h > prev_h and mid_l > prev_l: return BULLISH
    if mid_h < prev_h and mid_l < prev_l: return BEARISH
    return NEUTRAL
```

## Classes

- `DozeroSMCEngine` — main engine class
- `SMCSetup` — complete setup dataclass (entry, SL, TP1-4, RR, zone, confluence, reasons)
- `Bias` — BULLISH/BEARISH/NEUTRAL
- `FVG` — Fair Value Gap (high, low, mid, is_bullish, virgin)
- `LiquidityLevel` — liquidity pool (price, is_high, strength, swept)
- `StructureBreak` — BOS or CHOCH event
- `Displacement` — impulsive displacement (direction, strength as ATR multiple)

## Config options

```python
DozeroSMCEngine({
    'confluence_threshold': 75,     # Min score to pass
    'swing_lookback': 5,            # N-bar lookback for swing points
    'displacement_atr_mult': 1.5,   # Min ATR multiple for displacement
    'fvg_min_atr_mult': 0.5,       # Min ATR multiple for FVG gap
    'liquidity_cluster_dist': 0.001 # 0.1% price cluster threshold
})
```

## Live operational notes (verified June 2026)

- **Engine stays in "monitoring only" when positions maxed out.** With 3+ open positions and max_positions=2, the engine skips scanning entirely. SMC analysis only runs when `_evaluate_symbol()` is called (i.e. when there are open slots). This is correct behavior — don't restart the engine trying to "fix" it.
- **Liquidation risk warnings fire every 90s** for positions near their liq price. These are WARNING-level, not errors. The engine monitors but doesn't auto-close unless SL is hit.
- **SL/TP must be set separately via Algo Order API** — the engine places market entries but DOES NOT automatically place SL/TP orders. After engine opens a position, immediately set SL/TP using `/fapi/v1/algoOrder` with `algoType=CONDITIONAL` and `triggerPrice`. See `references/binance-algo-order-api.md`.
- **DOZERO.X + signal direction conflict = SKIP.** If SMC says LONG but signal composite says SHORT, the position is skipped entirely. This is intentional safety — never override this.

## Pitfalls

- **Swing detection with random/noisy data returns 0 swings.** The N-bar lookback requires strict higher-high/lower-low. Real market data works; random test data doesn't. Don't be alarmed by 0 swings in unit tests.
- **FVG detection works independently of swing detection.** FVGs are detected from 3-candle patterns, not swing structure. You can have FVGs even when no swings are found.
- **MTF bias from `_get_bias()` is simplified.** It compares recent vs previous 5-candle averages, not full swing structure. For production, consider upgrading to proper swing-based MTF analysis.
- **Confluence score can go negative** if price is in wrong premium/discount zone (-5 penalty). Minimum practical score is around 40-50 even with weak signals.
- **CRITICAL: Position state file caching bug (discovered June 2026).** `position_monitor_state.json` (`~/.hermes/data/evolution/position_monitor_state.json`) stores positions to disk on every `_save_state()` call. On engine restart, `_load_json()` restores these cached positions BEFORE Binance sync runs. If positions were closed externally (manually, by SL/TP, or by another script), the engine still thinks they exist. **Symptom:** Engine shows "Synced 0 existing positions" but then "Max positions (4/2) — monitoring only". **Fix applied (June 2026):** After Binance sync loop, compare `self.position_monitor.positions.keys()` with `binance_syms` set — any stale symbols get `del` with log message "Removing stale position: {sym} (no longer on Binance)". **Manual emergency fix:** `echo '{"positions": {}}' > ~/.hermes/data/evolution/position_monitor_state.json` then kill + restart engine. **Root cause:** The sync code only ADDS/UPDATES positions from Binance but never REMOVES positions that disappeared. The fix adds a stale-cleanup pass after the sync loop.