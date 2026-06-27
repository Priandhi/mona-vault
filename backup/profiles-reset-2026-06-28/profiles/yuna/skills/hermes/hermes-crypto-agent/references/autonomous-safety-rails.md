# Autonomous Trading Safety Rails

8 mandatory safety mechanisms for any autonomous trading engine. Built from real-money losses (June 2026).

## The 8 Safety Rails

### 1. Per-Pair Cooldown (5 min)
Minimum 5 minutes between trades on the same pair. Prevents rapid re-entry after close.

```python
self._pair_last_trade: Dict[str, float] = {}  # {symbol: timestamp}
self.PAIR_COOLDOWN_SEC = 300

# In _execute_trade():
now = time.time()
last = self._pair_last_trade.get(symbol, 0)
if now - last < self.PAIR_COOLDOWN_SEC:
    return  # Skip
```

### 2. Flip Prevention (10 min)
Minimum 10 minutes before reversing direction (LONG→SHORT or vice versa) on the same pair.

```python
self._pair_last_direction: Dict[str, Tuple[str, float]] = {}  # {symbol: (side, timestamp)}
self.FLIP_COOLDOWN_SEC = 600

last_dir = self._pair_last_direction.get(symbol)
if last_dir:
    last_side, last_ts = last_dir
    if last_side != side and now - last_ts < self.FLIP_COOLDOWN_SEC:
        return  # Block flip
```

### 3. Hourly Trade Limit (max 4/hour)
Track timestamps of all trades, prune older than 1 hour.

```python
self._hourly_trades: List[float] = []
self.MAX_HOURLY_TRADES = 4

self._hourly_trades = [t for t in self._hourly_trades if now - t < 3600]
if len(self._hourly_trades) >= self.MAX_HOURLY_TRADES:
    return False, f"Hourly limit"
```

### 4. Max Simultaneous Positions (2-3)
Check active positions before opening new ones.

```python
active_count = len(self.position_monitor.get_active_symbols())
if active_count >= self.config['max_simultaneous_positions']:
    return  # Max positions reached
```

### 5. Minimum Balance Check ($40+)
Refresh balance from Binance API before each trade. Don't trade if below threshold.

```python
real_bal = await self.execution.get_balance()
if real_bal > 0:
    self._live_balance = real_bal
if self._live_balance < 40.0:
    return  # Balance too low
```

### 6. SL/TP Verification Loop
Every monitoring cycle, verify ALL open positions have SL/TP algo orders. Place if missing.

```python
async def _verify_sltp_for_all_positions(self):
    real_positions = await self.execution.get_positions()
    for pos in real_positions:
        sym = pos['symbol']
        pos_data = self.position_monitor.positions.get(sym)
        if not pos_data:
            # Position on Binance but not in monitor — emergency close
            await self.execution.market_order(sym, close_side, abs(amt))
            continue
        
        # Try to place SL (will get -4130 if already exists)
        sl_result = await self.execution.stop_market(sym, close_side, abs(amt), sl_price)
        if 'algoId' in sl_result:
            log.info(f"SL confirmed")
        elif sl_result.get('code') == -4130:
            pass  # Already exists, OK
        else:
            # SL FAILED — emergency close
            await self.execution.market_order(sym, close_side, abs(amt))
```

### 7. Emergency Close
If SL placement fails after entry, immediately close the position. An unprotected position is worse than a small loss.

```python
sl_result = await self.execution.stop_market(symbol, close_side, qty, sl_price)
if 'algoId' not in sl_result and sl_result.get('code') != -4130:
    log.error(f"SL FAILED: EMERGENCY CLOSE")
    await self.execution.market_order(symbol, close_side, qty)
    return
```

### 8. Daily Loss Limit ($3)
Track cumulative daily PnL. Pause trading if exceeded.

```python
self._daily_pnl = 0.0
self._daily_reset_time = self._next_midnight_utc()

# In circuit breaker check:
if self._daily_pnl <= -3.0:
    return False, f"Daily loss limit hit: ${self._daily_pnl:.2f}"
```

## Update Tracking After Trade

```python
# After successful entry:
self._daily_trades += 1
self._last_trade_time = time.time()
self._pair_last_trade[symbol] = time.time()
self._pair_last_direction[symbol] = (side, time.time())
self._hourly_trades.append(time.time())
```

## What Happened Without These Rails

- Engine flipped LONG→SHORT on BTWUSDT in seconds
- Opened 3 positions simultaneously with no SL/TP
- Lost $55.65 (entire balance) in rapid overtrading
- User had to manually transfer funds out to stop the engine

## Key Lesson

"User said: 'gua sendiri karena lu terus open posisi'" — The engine was entering trades faster than the user could monitor. Without cooldowns, the engine treats every signal as an entry opportunity, even on the same pair seconds after closing.
