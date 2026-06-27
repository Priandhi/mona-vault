# Self-Evolution Engine — Trading Parameter Optimization

## Overview
Learns from trade outcomes and auto-adjusts trading parameters. Tracks signal accuracy, symbol performance, time-of-day patterns, and stores lessons from wins/losses.

## Architecture
```
~/.hermes/data/evolution/
├── trades.json              # All recorded trade outcomes
├── signal_performance.json  # Per-signal accuracy stats
├── lessons.json             # Extracted patterns (big wins/losses, streaks)
├── evolved_config.json      # Latest evolved parameters
└── performance_log.json     # Historical snapshots for trend analysis
```

## Components

### TradeTracker
Records every closed trade with full context:
```python
{
    'symbol': 'BTCUSDT', 'side': 'LONG',
    'entry_price': 65000, 'exit_price': 66500,
    'exit_type': 'TP1',  # TP1/TP2/TP3/SL/MANUAL/TIMEOUT
    'pnl_usd': 5.50, 'pnl_pct': 2.3,
    'leverage': 35, 'size_usdt': 100,
    'signals': {  # From engine's analysis dict
        'oi_divergence': 0.8, 'funding_rate': -0.01,
        'cvd': 1500, 'taker_volume': 0.65,
        'composite_score': 72, 'regime': 'TRENDING_UP',
    }
}
```

### SignalAnalyzer
Measures accuracy per signal type. Needs 5+ samples per signal.
- Signal with >65% win rate → BOOST weight by 1.3x
- Signal with 55-65% → KEEP
- Signal with 40-55% → REDUCE by 0.7x
- Signal with <40% → MINIMIZE by 0.3x

### Symbol Blacklist
Auto-blacklist symbols with <30% win rate after 3+ trades.

### Time-of-Day Analysis
Track which hours (WIB) produce best results. Avoid trading during historically bad hours.

### Evolution Cycle (runs every 24h)
1. Calculate signal accuracy adjustments
2. Adjust risk params based on overall win rate:
   - Win rate ≥60% + profit factor ≥1.5 → position_size_pct = 6%
   - Win rate 45-60% → keep at 5%
   - Win rate <45% → reduce to 3%
3. Optimize leverage:
   - Win rate ≥60% + small max loss → default 40x
   - Win rate 45-60% → default 30x
   - Win rate <45% → default 20x
4. Update symbol blacklist
5. Generate evolution report → Telegram

## Integration with Futures Engine

### In AutoTrader.__init__:
```python
from mona_evolution import EvolutionEngine
self.evolution = EvolutionEngine()
self._last_evolution = 0
```

### In PaperTrader.open_position (store signals):
```python
entry = {
    ...
    'signals': signals or {},  # Store full analysis for evolution
}
```

### In _alert_exit (record outcome):
```python
trade_data = {
    'symbol': pos.get('symbol'),
    'side': pos.get('side'),
    'entry_price': pos.get('entry_price'),
    'exit_type': exit_action.get('reason'),
    'pnl_usd': exit_action.get('pnl'),
    'pnl_pct': exit_action.get('pnl_pct'),
    'signals': pos.get('signals', {}),
}
self.evolution.tracker.record_trade(trade_data)

# Run evolution every 24h
if time.time() - self._last_evolution > 86400:
    adjustments = self.evolution.evolve()
    self._last_evolution = time.time()
```

### In monitor_loop (daily report):
```python
# At midnight reset:
if today != last_reset:
    report = self.evolution.get_evolution_report()
    self._send_telegram(report)
```

## CLI Usage
```bash
python3 mona_evolution.py --report    # Generate evolution report
python3 mona_evolution.py --evolve    # Run evolution cycle
python3 mona_evolution.py --stats     # Show trade stats
python3 mona_evolution.py --record trade.json  # Record a trade
```

## Key Insight
The evolution engine needs SIGNAL DATA stored with each trade. If the engine just records "BTC won +2%", it can't learn WHICH signals predicted that win. Always store the full `analysis` dict as `signals` in the position entry.
