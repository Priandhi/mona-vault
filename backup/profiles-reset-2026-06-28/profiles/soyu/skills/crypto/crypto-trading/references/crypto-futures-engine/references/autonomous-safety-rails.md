# Autonomous Trading Engine — Safety Rails

## Why This Exists

Engine went berserk: flip LONG↔SHORT in seconds, SL/TP not on Binance (algo orders ≠ /openOrders), user closed all + transferred funds out. Root causes:
1. No pair cooldown
2. No flip prevention
3. Breakeven logic updated local state only, not Binance
4. No SL/TP verification after placement
5. Max leverage assumed same for all pairs

## The 9 Safety Rails

### 1. Per-Pair Cooldown (300s)
```python
self._pair_last_trade: Dict[str, float] = {}  # {symbol: timestamp}

# In _execute_trade:
last_trade = self._pair_last_trade.get(symbol, 0)
if time.time() - last_trade < 300:
    return  # Skip — too soon
```

### 2. Flip Prevention (600s)
```python
self._pair_last_direction: Dict[str, Tuple[str, float]] = {}  # {symbol: (side, ts)}

# In _execute_trade:
last_dir = self._pair_last_direction.get(symbol)
if last_dir:
    last_side, last_ts = last_dir
    if last_side != side and time.time() - last_ts < 600:
        return  # Block flip
```

### 3. Hourly Trade Limit (4/hour)
```python
self._hourly_trades: List[float] = []

# In _check_circuit_breakers:
now = time.time()
self._hourly_trades = [t for t in self._hourly_trades if now - t < 3600]
if len(self._hourly_trades) >= 4:
    return False, "Hourly limit"
```

### 4. Max Positions (2)
```python
active_count = len(self.position_monitor.get_active_symbols())
if active_count >= self.config['max_simultaneous_positions']:
    return  # Max reached
```

### 5. Minimum Balance ($40)
```python
if self._live_balance < 40.0:
    return  # Too low to trade safely
```

### 6. Balance Refresh
```python
# Before each trade, fetch real balance:
real_bal = await self.execution.get_balance()
if real_bal > 0:
    self._live_balance = real_bal
```

### 7. SL/TP Verification (Every Cycle)
```python
async def _verify_sltp_for_all_positions(self):
    """Called every monitoring cycle."""
    real_positions = await self.execution.get_positions()
    for pos in real_positions:
        sym = pos['symbol']
        pos_data = self.position_monitor.positions.get(sym)
        if not pos_data:
            # Position exists but not tracked — close it
            await self.execution.market_order(sym, close_side, abs(amt))
            continue
        
        # Try to place SL (returns -4130 if exists)
        sl_result = await self.execution.stop_market(sym, close_side, amt, sl_price)
        if 'algoId' in sl_result:
            pass  # Placed
        elif sl_result.get('code') == -4130:
            pass  # Already exists
        else:
            # FAILED — emergency close
            await self.execution.market_order(sym, close_side, abs(amt))
```

### 8. Breakeven Update to Binance
```python
# After partial close (TP1 hit), update SL on Binance:
if pos_data.get('trailing_active'):
    new_sl = pos_data.get('sl')
    if new_sl:
        result = await self.execution.stop_market(symbol, close_side, 0, new_sl)
        if 'algoId' in result:
            log.info(f"BREAKEVEN SL UPDATED @ {new_sl}")
```

### 9. Emergency Close
```python
# If SL placement fails:
sl_result = await self.execution.stop_market(symbol, close_side, qty, sl_price)
if 'algoId' not in sl_result and sl_result.get('code') != -4130:
    # SL FAILED — close position immediately
    await self.execution.market_order(symbol, close_side, qty)
    return
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

## Paper Mode Safety

All execution-dependent code must check for paper mode:
```python
if not self.execution:
    return  # Skip in paper mode
```

This applies to: SL/TP verification, breakeven update, limit entry, position close.
