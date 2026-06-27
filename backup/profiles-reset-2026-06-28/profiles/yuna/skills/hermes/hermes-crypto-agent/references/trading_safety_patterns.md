# Trading Engine Safety Patterns

## Critical Rule: KILL ENGINE BEFORE FIXING

User is extremely sensitive about uncontrolled trades. If engine is being fixed/debugged:
1. **STOP engine completely** (kill process)
2. **Verify 0 positions** via Binance API
3. **Fix all bugs**
4. **Test in paper mode first**
5. **Only then restart in live mode**

User transferred ALL funds out ($55) when engine kept trading during a fix session.

## Safety Checks (must be in any trading engine)

### 1. Per-Pair Cooldown
```python
PAIR_COOLDOWN_SEC = 300  # 5 min between same-pair trades
last_trade = self._pair_last_trade.get(symbol, 0)
if time.time() - last_trade < PAIR_COOLDOWN_SEC:
    return  # Skip
```

### 2. Flip Prevention
```python
FLIP_COOLDOWN_SEC = 600  # 10 min before flipping LONG↔SHORT
last_dir = self._pair_last_direction.get(symbol)
if last_dir and last_dir[0] != side and time.time() - last_dir[1] < FLIP_COOLDOWN_SEC:
    return  # Block flip
```

### 3. Hourly Trade Limit
```python
MAX_HOURLY_TRADES = 4
hourly_trades = [t for t in self._hourly_trades if time.time() - t < 3600]
if len(hourly_trades) >= MAX_HOURLY_TRADES:
    return  # Rate limited
```

### 4. Max Positions
```python
if len(active_positions) >= max_simultaneous_positions:
    return  # Full
```

### 5. Minimum Balance
```python
if balance < 40.0:
    return  # Too low
```

### 6. SL/TP Verification (every monitoring cycle)
```python
async def _verify_sltp_for_all_positions(self):
    """Check all positions have SL/TP on Binance. Place if missing."""
    for pos in await self.execution.get_positions():
        if pos not in self.position_monitor.positions:
            # Orphan position — close immediately
            await close_position(pos)
            continue
        # Try to place SL/TP (idempotent — returns -4130 if exists)
        sl_result = await place_sl(pos)
        if not ('algoId' in sl_result or sl_result.get('code') == -4130):
            # SL failed — emergency close
            await close_position(pos)
```

### 7. Breakeven Update to Binance
When TP1 hits and local SL moves to breakeven, **also update the Binance algo order**:
```python
# After partial close:
new_sl = entry + atr * 0.1  # breakeven
result = await place_algo_order(symbol, close_side, 'STOP_MARKET', new_sl)
# Old SL is automatically replaced by new one
```

## Monitoring Loop Structure

```python
async def _monitor_positions(self):
    # 1. Verify SL/TP safety net (EVERY cycle)
    await self._verify_sltp_for_all_positions()
    
    # 2. Check prices
    prices = {sym: await get_price(sym) for sym in active_positions}
    
    # 3. Process actions (SL hit, TP hit, trailing)
    for action in check_positions(prices):
        if action == 'CLOSE_ALL':
            await close_position(symbol)
        elif action == 'CLOSE_PCT':
            await partial_close(symbol)
            # Update SL to breakeven on Binance
            await update_sl_on_binance(symbol, new_sl)
```
