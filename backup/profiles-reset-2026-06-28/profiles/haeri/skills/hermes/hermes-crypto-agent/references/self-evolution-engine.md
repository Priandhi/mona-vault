# Self-Evolution Engine v1.0 (Trade Outcome Learning)

**Distinct from Sprint 5 Self-Evolving Agent** — that one evaluates tasks and learns from user feedback. This one specifically learns from TRADE OUTCOMES to improve trading parameters automatically.

**Script:** `~/.hermes/scripts/mona_evolution.py`
**Data dir:** `~/.hermes/data/evolution/`

## Architecture

4 components:

### 1. TradeTracker
Records completed trades with full context:
```python
trade_data = {
    'symbol': 'BTCUSDT', 'side': 'LONG',
    'entry_price': 65000, 'exit_price': 66500,
    'exit_type': 'TP1',  # TP1/TP2/TP3/SL/MANUAL/TIMEOUT
    'pnl_usd': 5.5, 'pnl_pct': 2.3,
    'leverage': 35, 'size_usdt': 100,
    'hold_time_min': 45,
    'entry_time': '...', 'exit_time': '...',
    'signals': {  # FULL signal snapshot at entry
        'oi_divergence': 0.8, 'funding_rate': -0.01,
        'cvd': 1500, 'taker_volume': 0.65,
        'structure': 'bullish', 'composite_score': 72,
        'regime': 'TRENDING_UP',
    },
    'market_conditions': {'btc_trend': 'up', 'fear_greed': 65},
}
```

Auto-classifies: WIN (pnl>0), LOSS (pnl<0), BREAKEVEN (pnl=0).

### 2. SignalAnalyzer
Tracks per-signal accuracy. After N trades, knows:
- `oi_divergence`: 65% win rate (best signal)
- `funding_rate`: 45% win rate (reduce weight)
- Per-symbol: BTC 60% win, LINK 20% win (blacklist)
- Per-regime: TRENDING_UP 70%, RANGING 30%
- Per-hour: 08:00 UTC 65%, 14:00 UTC 35%

### 3. EvolutionEngine
Auto-adjusts based on analysis:
- **Signal weights:** Boost >60% accuracy, reduce <40%
- **Risk params:** Win rate >60% → increase size to 6%. <40% → decrease to 3%
- **Leverage:** Win rate >60% + small max loss → 40x default. Poor performance → 20x
- **Symbol blacklist:** 3+ consecutive losses → auto-blacklist
- **Time filter:** Best/worst trading hours identified

### 4. Lessons Memory
Stores significant events:
- BIG_LOSS (>3%): "Avoid X when score < Y"
- SYMBOL_LOSE_STREAK (3+): "Blacklist X temporarily"
- BIG_WIN (>5%): "Repeat setup: X with score Y in regime Z"

## Integration with Futures Engine

Connected in `mona_futures_auto.py`:
1. **Entry:** Signals stored in position dict via `signals=analysis` param
2. **Exit:** `_alert_exit()` records trade to evolution tracker
3. **Daily:** Midnight WIB → evolution cycle runs → report sent to Topic 387
4. **Balance guard:** Before entry, checks available balance >= 20% reserve

## CLI

```bash
python3 mona_evolution.py --report   # Human-readable report
python3 mona_evolution.py --evolve   # Run evolution cycle, output JSON
python3 mona_evolution.py --stats    # Raw stats JSON
python3 mona_evolution.py --record trade.json  # Manual record
```

## Minimum Data Requirements

- Needs 10+ trades before making adjustments (prevents overfitting on small samples)
- Signal accuracy needs 5+ samples per signal type
- Symbol blacklist needs 3+ trades per symbol

## Data Files

- `trades.json` — Full trade history (list of dicts)
- `signal_performance.json` — Per-signal, per-symbol, per-regime, per-hour stats
- `lessons.json` — Extracted lessons from significant trades
- `evolved_config.json` — Last evolution cycle output
- `performance_log.json` — Historical snapshots for trend analysis

## Pitfalls

- **Signals must be stored at ENTRY time.** If signals aren't passed to `open_position()`, evolution can't learn which signals predicted correctly. Always pass `signals=analysis` when opening positions.
- **Exit price calculation from pnl_pct is approximate.** `exit_price = entry * (1 + pnl_pct/100)` — good enough for learning but not for exact PnL reconciliation.
- **Evolution runs every 24h, not every trade.** Prevents over-adjustment from single outcomes. Manual trigger via `--evolve` for testing.
- **Evolved config CAN override conservative defaults (June 2026).** The `AutoAdjuster` writes to `evolved_config.json` which the autonomous engine reads on startup. If the evolution engine runs with aggressive settings (5% risk, 30x leverage), the next engine restart picks those up. **Fix:** Add hard caps in `_apply_evolved_config()`:
  ```python
  self.config['risk_per_trade_pct'] = min(0.03, risk.get('position_size_pct', 0.03))  # Never >3%
  self.config['leverage_base'] = min(20, lev.get('default', 20))  # Never >20x
  self.config['leverage_max'] = min(30, lev.get('max', 30))  # Never >30x
  ```
  Also verify after restart: `tail -5 ~/.hermes/logs/mona_autonomous.log` should show correct risk/lev values.
- **Evolution cycle runs immediately on first engine start.** Because `_last_evolution` is initialized to 0, the first `_loop_iteration` always triggers an evolution cycle. This is fine for fresh starts but means the engine takes ~10s extra on first iteration.
