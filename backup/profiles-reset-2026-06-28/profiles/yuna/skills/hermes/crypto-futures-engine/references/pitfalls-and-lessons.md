# Pitfalls & Lessons Learned — Mona Futures Engine v2.0

## Critical Bugs Fixed

### 1. `closes` Variable Scope Bug (Fixed: 2026-06-08)
**Location:** `engine.py` scan_once() - High volatility filter section

**Problem:** `closes` variable used but not defined in scope.

**Fix:**
```python
# High volatility filter — skip pairs with ATR > 3%
klines_h1 = await self.data.binance_klines(symbol, '1h', 20)
if len(klines_h1) >= 15:
    from mona_futures_v2.risk import calculate_atr
    closes_h1 = [float(k[4]) for k in klines_h1]  # ← ADD THIS LINE
    atr = calculate_atr(klines_h1, 14)
    atr_pct = (atr / closes_h1[-1] * 100) if closes_h1 and closes_h1[-1] > 0 else 0  # ← USE closes_h1
```

## Signal Quality Issues

### 2. FearGreed Signal Domination
**Problem:** When market is in Extreme Fear (F&G < 15) or Extreme Greed (F&G > 85), FearGreed gives +90/-90 to ALL pairs, inflating composite scores by 4-5 points.

**Example:**
- F&G = 12 (Extreme Fear)
- All pairs get +90 from FearGreed
- Composite scores inflated across the board
- Engine becomes overly bullish on everything

**Solutions:**
1. Reduce FearGreed weight from 5 to 3
2. Cap max FearGreed contribution at 30 (not 90)
3. Only apply FearGreed when price is at key support/resistance

### 3. High-Volatility Meme Coins
**Problem:** Pairs like HYPE, DOGE, PEPE have ATR > 3% and unpredictable moves.

**Backtest Results (90 days):**
- HYPE: -17.31% PnL, PF 0.81, MaxDD 39.70% ❌
- SOL: +28.83% PnL, PF 2.05, MaxDD 7.80% ✅
- ETH: +22.01% PnL, PF 1.68, MaxDD 10.20% ✅
- BTC: +2.23% PnL, PF 1.11, MaxDD 8.17% ✅

**Solution:** Blacklist high-volatility pairs or reduce position size by 50%.

### 4. Single-TF SMC Limitation
**Problem:** Our engine uses single timeframe SMC analysis. Professional systems (Dozero.x) use multi-TF alignment (D1+H4+H1+M15) for higher probability entries.

**Performance Comparison:**
- Our Engine: 33% confidence, basic SMC
- Dozero.x: 75% confidence, multi-TF SMC

**Key Gaps:**
- Fresh OB/FVG detection (untested = high probability)
- Liquidity sweep detection (smart money entry)
- CHoCH confirmation (reversal signal)
- L/S ratio analysis (over-crowding detection)

**See:** `references/dozero-x-comparison.md` for full gap analysis and improvement roadmap.

## Configuration Issues

### 5. Model Management
**Problem:** MiMo v2.5 Pro (provider: mimo) should ALWAYS be the primary default model. Never accidentally change to Nemotron Ultra or other slow models during config edits.

**Config Location:** `~/.hermes/config.yaml`
```yaml
model:
  default: mimo-v2.5-pro
  provider: mimo
```

**Lesson:** Always verify model config after editing config.yaml. Slow models (Nemotron Ultra 550B) cause 150s+ response times on free tier.

## Scanner Self-Deadlock (Fixed: 2026-06-17, Dozero.X)

**Symptom:** Bot logs "All 200 pairs already signalled — nothing new to scan" for hours. 0 signals produced. 0 fresh pairs in scan universe. Position check shows balance but no activity.

**Root cause:** The scanner maintains a `signalled.json` blacklist (pairs that already gave a signal, don't re-scan to avoid duplicate orders). **No cleanup logic after trade close** — once a pair enters signalled.json, it stays there forever. Combined with `STRIKE_LIMIT=3` (3 no-signal scans → 24h cooldown), the bot self-deadlocks:

```
signalled.json: 53 pairs (all from past trades, no current position)
no_signal.json: 210 pairs, 206 with 3 strikes (24h cooldown)
Scan universe: 200 pairs
  → 44 in signalled (lock)
  → 156 in strike-cooldown (lock)
  → 0 fresh pairs
Bot: "All 200 pairs already signalled" → return
```

**Two bugs in this loop:**

1. **signalled.json never pruned** — pairs that gave signals yesterday block fresh scans today, even after position is closed.
2. **Strike counter never resets on partial success** — even if SOME pairs in a batch give signals, the rest get strikes. After 3 cycles of "no signal from THIS pair", locked for 24h.

**Fix (YUNA Dozero):**
```python
# At start of auto_scan, prune signalled.json to only pairs with active pos/order
try:
    positions = conn.get_positions()
    active_pos_syms = {p['symbol'] for p in positions if abs(float(p.get('positionAmt', 0))) > 0}
    open_orders = conn.get_open_orders()
    active_order_syms = {o['symbol'] for o in open_orders}
    active_syms = active_pos_syms | active_order_syms
    stale_signalled = {s for s in signalled if s not in active_syms}
    if stale_signalled:
        signalled -= stale_signalled
        save_signalled(signalled)
        logger.info("Pruned %d stale signalled entries (no pos/order)", len(stale_signalled))
except Exception as e:
    logger.warning("Signalled prune failed: %s — proceeding", e)
```

**Lesson:** Any blacklist that grows monotonically (signalled, no_signal, cooldown) MUST be cleaned at the start of each scan cycle, using the CURRENT position/order state as ground truth. The blacklist is a cache, not a permanent log. Also consider:

- If your scan universe is fixed (e.g. `MAX_SCAN_PAIRS=200`) and your blacklist grows over time, you'll always deadlock. Either expand the universe or shrink the blacklist TTL.
- Add a periodic "all clear" — e.g. if no fresh pairs for N hours, force-reset no_signal.json and try again with looser thresholds.

## New Pitfalls Discovered (2026-06-08)

### 6. Mona SMC Master v2.1 — Virgin FVG Detection Issue
**Problem:** All FVGs are marked as "tested" — 0 virgin FVGs found in FFUSDT analysis
**Root Cause:** `filled_pct` calculation in `detect_enhanced_fvgs()` may be too aggressive
**Debug Steps:**
1. Check if `future_highs` and `future_lows` arrays are correct
2. Verify `filled_pct` calculation logic
3. Check if FVG detection is finding the right gaps

**Fix Location:** `mona_smc_master_v21.py` → `detect_enhanced_fvgs()` method

### 7. Mona SMC Master v2.1 — CHoCH Detection Issue
**Problem:** M15 CHoCH not detected even when present in market structure
**Root Cause:** M15 swing detection may not find enough swing points (needs minimum 4)
**Debug Steps:**
1. Check `find_swing_points()` with M15 data
2. Verify swing detection lookback period
3. Check if M15 data has enough candles (50+)

**Fix Location:** `dozero_smc_engine.py` → `find_swing_points()` method

### 8. Mona SMC Master v2.1 — Entry Calculation Issue
**Problem:** Entry using OB mid instead of optimal entry (FVG/OB confluence)
**Root Cause:** No FVG/OB confluence for entry optimization
**Fix:** Use FVG low (for long) or OB high (for short) as entry when available

**Fix Location:** `mona_smc_master_v21.py` → `full_analysis()` method

## Best Practices

### Signal Weight Recommendations
```python
# Current (problematic)
weight_fear_greed: float = 5  # Still too dominant when F&G is extreme

# Recommended
weight_fear_greed: float = 3  # Reduce to 3
weight_fresh_ob: float = 15  # Fresh Order Block (new)
weight_fresh_fvg: float = 12  # Fresh Fair Value Gap (new)
weight_liquidity_sweep: float = 10  # Liquidity sweep (new)
weight_choch: float = 12  # Change of Character (new)
weight_ls_ratio: float = 8  # Long/Short ratio (new)
```

### Backtest Validation Checklist
- [ ] Run backtest on 90+ days of data
- [ ] Test on multiple pairs (BTC, ETH, SOL, alts)
- [ ] Check profit factor > 1.5 for profitable pairs
- [ ] Verify max drawdown < 15%
- [ ] Compare win rate before/after improvements
- [ ] Test with fresh OB/FVG entries only
- [ ] Verify CHoCH detection accuracy
- [ ] Check L/S ratio signal quality
