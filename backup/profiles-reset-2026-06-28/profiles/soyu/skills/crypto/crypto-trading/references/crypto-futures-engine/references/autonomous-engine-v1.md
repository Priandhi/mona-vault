# Autonomous Engine v1.0 — Silent Self-Learning Mode

Production architecture for fully autonomous, silent, self-learning crypto trading engine.

## Key Differences from Basic Auto-Trader

| Feature | Basic AutoTrader | Autonomous Engine v1.0 |
|---------|-----------------|----------------------|
| Notifications | Telegram alerts on every trade | Silent (log-only) |
| Learning | None | Tracks signal accuracy, auto-adjusts weights |
| Self-correction | None | Streak detection, pause on losses, dynamic sizing |
| Market analysis | Signal scores only | Regime detection, volatility, correlation |
| Position management | Fixed TP/SL | Dynamic trailing, partial close, MFE/MAE tracking |
| Trade journal | None | Records WHY each trade, analyzes outcomes |
| Position sync | None (forgets on restart) | Syncs from Binance on startup |

## Architecture

```
mona_autonomous.py (1700+ lines)
├── MarketIntelligence       — Regime detection (7 regimes), volatility, BTC correlation
├── DeepSignalAnalyzer       — Dynamic signal weights, time-decay, regime-specific boosting
├── AdaptiveRiskManager      — Streak detection, pause, dynamic sizing, auto-adjust SL/TP
├── TradeJournal             — Pre/post trade analysis, entry quality scoring, daily reports
├── PositionMonitor          — Silent 60s checks, trailing stops, partial TP, liq risk
├── AutonomousEngine         — Main loop, circuit breakers, correlation guard, evolution
└── CONSERVATIVE_CONFIG      — Hardcoded safety defaults (overridable by evolved config WITH caps)
```

## Startup Sequence (CRITICAL ORDER)

```python
class AutonomousEngine:
    def __init__(self, mode='live', interval=90):
        # 1. Load config + evolved config (with hard safety caps)
        # 2. Initialize modules (data, signals, risk, market_intel, journal, etc.)
        # 3. Initialize execution engine (Binance API)
        # 4. Initialize evolution engine
        # 5. SYNC EXISTING POSITIONS FROM BINANCE ← CRITICAL
        if mode == 'live':
            self._sync_existing_positions()  # See pitfall #66
        # 6. Log initialization
```

## Silent Mode

- NO StreamHandler — only FileHandler with auto-flush
- NO Telegram notifications for balance, PnL, entries
- All logging to `~/.hermes/logs/mona_autonomous.log`
- Trade journal to `~/.hermes/data/journal/`
- Evolution data to `~/.hermes/data/evolution/`
- Daily reports to `~/.hermes/data/reports/`

**User explicitly said:** "gausah notif alerts balance gua bisa liat manual di binance"
Translation: Don't send balance/PnL notifications. User checks Binance manually.

**Only notify on:** Emergency close (SL failed + position auto-closed). Everything else is silent.

## Main Loop Flow

```
Every 90 seconds:
  1. Daily reset (if midnight UTC)
  2. Update balance from Binance
  3. Check circuit breakers (drawdown, daily limit, reserve, cooldown, streak pause)
  4. Monitor existing positions (trailing stops, partial TP, liquidation risk)
  5. Check max positions guard (if 4 >= max 2 → monitoring only, skip scan)
  6. Scan 20 pairs for opportunities
     - Market intelligence per symbol (regime, volatility, BTC correlation)
     - Signal analysis with dynamic weights
     - Score must meet min_score AND min_signals
     - VPIN check (reject if > 0.7)
     - Correlation check (reject if > 0.85 with existing)
  7. Execute best opportunity (if found)
  8. Periodic evolution cycle (every 24h)
```

## Self-Learning Components

### DeepSignalAnalyzer
- Tracks per-signal accuracy over time (stored in `signal_performance.json`)
- Time-decay: recent trades weighted more (half-life = 1 week)
- Regime-specific weights: trend signals boosted in trending markets
- Dynamic range: 0.3x to 2.0x per signal weight

### AdaptiveRiskManager
- Streak detection: 3 consecutive losses → reduce size 50% + raise min_score
- 5 consecutive losses → pause trading for 2 hours
- 2 consecutive wins → gradually restore size
- Dynamic leverage: reduce in high vol, increase in strong trends
- Drawdown-based sizing: smaller positions when in drawdown
- Auto-adjust SL: widen if too many SL hits, tighten if too few

### TradeJournal
- Records pre-trade analysis (signals, scores, reasoning)
- Records post-trade analysis (MFE/MAE, what went right/wrong)
- Entry quality scoring (0-100)
- Pattern recognition: identify recurring win/loss patterns
- Daily summary generation

## Circuit Breakers (Conservative Mode)

```python
CONSERVATIVE_CONFIG = {
    'min_score': 50,           # Only strong signals
    'min_signals': 4,          # Need 4 signals agreeing
    'max_positions': 2,        # Max 2 concurrent
    'balance_reserve_pct': 0.25,  # 25% always free
    'risk_per_trade_pct': 0.03,   # 3% per trade
    'leverage_base': 20,       # 20x base
    'leverage_max': 30,        # 30x max
    'max_drawdown_pct': 0.05,  # 5% pause
    'emergency_drawdown_pct': 0.07,  # 7% stop all
    'max_daily_trades': 4,
    'cooldown_after_loss_sec': 600,  # 10 min
    'consecutive_loss_pause_threshold': 5,
    'consecutive_loss_pause_sec': 7200,  # 2 hours
}
```

## Mandatory Safety Rails

**Before going live, ALL of these must be implemented.** See `references/autonomous-safety-rails.md` for full implementation:

1. Per-pair cooldown (5 min)
2. Flip prevention (10 min before LONG↔SHORT)
3. Hourly trade limit (max 4/hour)
4. Minimum balance check ($40+)
5. Max positions guard
6. SL/TP verification cycle (every monitoring loop)
7. Breakeven update to Binance (not just local)
8. Emergency close on SL failure

**User lesson:** "fix semua lah bos autonomus kok kayak gitu" — when user says fix everything, STOP engine → fix ALL → verify paper mode → restart live. Never fix incrementally.

## Pitfalls Specific to Autonomous Mode

1. **Never use `asyncio.get_event_loop().run_until_complete()` inside async context** — Use synchronous `requests` for startup sync.
2. **Never set synced TP values to 0** — Engine thinks TP is hit → mass partial close (see pitfall #66).
3. **Never let evolved config exceed safety caps** — Always enforce hard limits (see pitfall #67).
4. **Always use FlushingFileHandler** — Otherwise logs appear missing (see pitfall #68).
5. **Set balance reserve minimum to $1.0** — $5.0 is too restrictive for micro-accounts (see pitfall #69).
6. **Sync ALL position fields** — Missing fields cause KeyError crashes: `atr`, `tp1`, `tp2`, `tp1_hit`, `tp2_hit`, `trailing_active`, `trailing_sl`, `partial_closes`, `last_check`. Add all these with safe defaults when syncing.
7. **Add INFO-level scan summary logging** — In silent mode (no StreamHandler), all scan evaluation happens at DEBUG level. This makes the engine appear stuck — the log shows initialization, then silence. Add an INFO-level summary after each scan cycle: `Scan: {N} pairs → BEST: {symbol} score={score}` or `Scan: {N} pairs → No opportunities (positions: {M})`. Also log when max positions guard blocks scanning: `Max positions (4/2) — monitoring only`. Without these, you can't distinguish a hung engine from one that's running but finding no trades.
8. **Stale position state file = phantom positions (CRITICAL)** — The PositionMonitor persists positions to `~/.hermes/data/evolution/position_monitor_state.json`. When positions are closed externally (user closes on Binance app, or SL/TP triggers), the state file is NOT updated. On engine restart, stale positions load → engine thinks max positions reached → refuses to scan. **Fix:** During `_sync_existing_positions()`, after fetching positions from Binance, remove any entries in `self.position_monitor.positions` that are NOT in the Binance response:
    ```python
    stale = [s for s in self.position_monitor.positions if s not in binance_syms]
    for s in stale:
        log.info(f"Removing stale position: {s} (no longer on Binance)")
        del self.position_monitor.positions[s]
    ```
    **Symptom:** Log shows `Synced 0 existing positions from Binance` but then `Max positions (4/2) — monitoring only`. The "4" comes from the stale state file, not from Binance.
