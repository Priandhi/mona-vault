# Mona Autonomous Engine v2.0 + DOZERO.X (June 2026)

**Location:** `~/.hermes/scripts/mona_autonomous.py` (1,900+ lines)
**SMC Module:** `~/.hermes/scripts/dozero_smc_engine.py` (pure Python, no deps)
**Log:** `~/.hermes/logs/mona_autonomous.log`
**Data:** `~/.hermes/data/evolution/`, `~/.hermes/data/journal/`, `~/.hermes/data/reports/`

## v2.0 Changes (DOZERO.X SMC Integration)

See `references/dozero-smc-integration.md` for full details. Key additions:
- Multi-timeframe analysis (Daily→H4→H1→M15)
- Virgin FVG detection, liquidity sweep, BOS/CHOCH structural breaks
- Premium/Discount zone enforcement
- Confluence scoring (75+ threshold for elite setups)
- SMC bonus up to +30 added to signal score
- Structural SL/TP (replaces ATR-based when SMC setup found)
- Direction conflict protection (SMC vs signal = SKIP)

## Architecture

8 classes, fully async, silent operation (no Telegram notifications):

### 1. MarketIntelligence
- Market regime detection (7 regimes): STRONG_TREND_UP, WEAK_TREND_UP, RANGING, WEAK_TREND_DOWN, STRONG_TREND_DOWN, HIGH_VOLATILITY, BREAKOUT
- Volatility regime: LOW, NORMAL, HIGH, EXTREME (ATR ratio vs 20-period average)
- Multi-timeframe trend strength (0-100 score)
- Volume profile: spike/declining/climax detection
- BTC correlation: Pearson on 20-period returns
- Regime tradeability check: blocks trades against trend in STRONG regimes

### 2. DeepSignalAnalyzer
- Per-signal accuracy tracking with time-decay (1-week half-life)
- Dynamic weight recalculation (0.3x–2.0x range)
- Regime-specific signal boosting (trend signals in trending, contrarian in ranging)
- Weighted composite scoring
- Signal snapshot storage for post-trade analysis

### 3. AdaptiveRiskManager
- Streak detection: 3 consecutive losses → 50% size reduction + 10pt score threshold increase
- 5 consecutive losses → pause trading for 2 hours
- Gradual restoration on wins
- Dynamic leverage by score/volatility/trend
- Drawdown-based position sizing
- Auto-adjust SL/TP based on historical hit rates
- Persistent state across restarts

### 4. TradeJournal
- Pre-trade entry recording (signals, scores, reasoning)
- Post-trade exit recording (MFE/MAE, PnL, hold time)
- Entry quality scoring (0-100)
- Win/loss pattern recognition (regimes, symbols, scores)
- Daily summary generation → `~/.hermes/data/reports/`

### 5. PositionMonitor
- Silent 60s checks
- MFE/MAE tracking per position
- Dynamic trailing stop: breakeven at 1R profit, trail at 0.5 ATR after 2R
- Partial TP: 25% at TP1, 25% at TP2, 50% trailing
- Liquidation risk detection

### 6. DozeroSMCEngine (v2.0)
- Full Smart Money Concepts analysis pipeline
- Swing point detection (N-bar lookback)
- Fair Value Gap detection (virgin = untouched)
- Liquidity level clustering and sweep detection
- BOS (Break of Structure) and CHOCH (Change of Character)
- Displacement detection (impulsive candles > 1.5x ATR)
- Premium/Discount zone classification
- Multi-timeframe bias alignment
- Accumulation/Distribution detection
- Confluence scoring (0-100) with configurable threshold
- Smart entry calculation (retracement-based FVG entry)
- Structural SL + 1:1, 1:2, 1:3, 1:4 TP calculation
- Telegram output formatting

### 7. AutonomousEngine (updated)
- Main loop: 90s scan interval, 20-pair scanning
- Circuit breakers: max 4 trades/day, max 2 positions, 25% reserve, 5% drawdown, 7% emergency
- Correlation guard (0.85 threshold)
- Spread check (max 0.3%)
- VPIN check (max 0.7)
- Daily reset with report generation
- 24h evolution cycles

## Conservative Config (default for small accounts)

```python
CONSERVATIVE_CONFIG = {
    'min_score': 50,           # Minimum signal score to enter
    'min_signals': 4,          # Minimum agreeing signals
    'max_positions': 2,        # Max simultaneous positions
    'balance_reserve_pct': 0.25,  # 25% always protected
    'risk_per_trade_pct': 0.03,   # 3% risk per trade
    'leverage_base': 20,       # Base leverage
    'leverage_min': 15,        # Dynamic minimum
    'leverage_max': 30,        # Dynamic maximum
    'sl_atr_mult': 1.0,       # SL = entry ± ATR * 1.0
    'tp1_close_pct': 0.25,    # Close 25% at TP1
    'tp2_close_pct': 0.25,    # Close 25% at TP2
    'max_drawdown_pct': 0.05,  # 5% max drawdown
    'emergency_drawdown_pct': 0.07,  # 7% emergency halt
    'max_daily_trades': 4,
    'cooldown_after_loss_sec': 600,  # 10min cooldown
    'consecutive_loss_pause_threshold': 5,  # Pause after 5 losses
    'consecutive_loss_pause_sec': 7200,     # 2 hour pause
    'max_spread_pct': 0.003,  # Max 0.3% spread
    'evolution_interval_sec': 86400,  # 24h evolution cycle
}
```

## Hard Caps (NEVER overridden by evolution)

Evolved config adjustments are capped to protect the user's money:
- Risk per trade: max 3% (never increase beyond this)
- Base leverage: max 20x
- Max leverage: max 30x
- SL ATR multiplier: 0.8–2.0 range

## Running

```bash
cd ~/.hermes/scripts
python3 -u mona_autonomous.py --mode live --interval 90 --silent
```

## Pitfalls

- **Evolved config can override conservative defaults.** The evolution engine writes to `evolved_config.json` which gets applied on startup. If the evolution engine was previously running with aggressive settings, the evolved config may have 5% risk and 30x leverage. Always verify after restart: `tail -5 ~/.hermes/logs/mona_autonomous.log` should show `risk=0.03, lev=20`.
- **Available balance threshold too high.** Original code had `available < $5.0` minimum. For $54 balance with 25% reserve, available is ~$2.26 — always below $5. Changed to `available < $1.0`. Adjust based on actual balance.
- **Max positions guard from internal state.** `position_monitor.get_active_symbols()` returns positions tracked by THIS engine instance. If engine restarts, it loses track of existing Binance positions. The engine may try to open new positions while 4 are already open on Binance. Fix: on startup, query `/fapi/v2/account` and sync existing positions to the position monitor.
- **CRITICAL: Position sync sentinel values.** When syncing existing Binance positions to the internal position monitor on startup, you MUST set sentinel values to prevent the PositionMonitor from triggering auto-close/partial-close on positions it didn't open. Without this, TP1/TP2 default to 0, and the monitor thinks all TPs are "hit" (price > 0), triggering immediate 50% partial close of ALL positions. Required sentinel values for synced positions:
  ```python
  'tp1': entry * 999, 'tp2': entry * 999,  # Never trigger
  'tp1_hit': True, 'tp2_hit': True,         # Already "hit" = skip
  'partial_closes': 2,                       # Mark as fully closed out
  'trailing_active': False, 'trailing_sl': 0,
  'sl': 0, 'tp': 0, 'mfe': 0, 'mae': 0,
  'atr': entry * 0.01,                       # Placeholder ATR
  'last_check': time.time(),
  ```
  ALSO: set `leverage` from Binance position data (`int(float(p.get('leverage', 20)))`). Sync method uses synchronous `requests` (not `aiohttp`) because `__init__` runs before the async event loop starts.
- **aiohttp unclosed sessions.** The engine creates multiple `aiohttp.ClientSession` instances that don't get properly closed. This causes `Unclosed client session` warnings on exit. Fix: use a single shared session or add `__del__` cleanup.
- **`logging.basicConfig()` module conflict.** If you import `mona_futures_v2.risk` which also calls `basicConfig`, handlers get duplicated or overridden. Each script should use `logging.getLogger('UniqueName')` and configure handlers explicitly.
- **Engine DOES NOT auto-set SL/TP orders.** The engine places market entries via `ExecutionEngine.market_order()` but does NOT place SL/TP algo orders. After the engine opens a position, you MUST manually set SL/TP using `/fapi/v1/algoOrder` with `algoType=CONDITIONAL` and `triggerPrice`. Without this, positions are unprotected. See `references/binance-algo-order-api.md` for the correct API pattern.
- **DOZERO.X SMC only runs during active scanning.** When `max_positions` is reached, the engine enters "monitoring only" mode and skips `_evaluate_symbol()` entirely. SMC analysis doesn't run until a position closes and frees a slot. This is by design — don't restart the engine to "fix" it.
