# Futures Engine v2.0 Code Fixes (June 2026)

## Config Issues Fixed

### Duplicate `max_daily_trades` (config.py)
**Problem:** `max_daily_trades` defined TWICE — line 58 as 5, line 82 as 4 (overwrites first).
**Fix:** Remove the duplicate at line 82. Keep value at 5.

### Missing Safety Rail Configs
Add these to `FuturesConfig` dataclass:
```python
# Safety Rails (MANDATORY per skill spec)
per_pair_cooldown_sec: int = 300       # 5 min cooldown per pair
flip_cooldown_sec: int = 600           # 10 min before reversing direction
max_hourly_trades: int = 4             # Max 4 trades per hour
sl_tp_verify_interval_sec: int = 60    # Verify SL/TP every 60s
emergency_close_on_sl_fail: bool = True
daily_loss_limit_pct: float = 0.07     # 7% daily loss → stop all
min_balance_to_trade: float = 40.0     # Minimum $40 balance
```

## RiskEngine Fixes (risk.py)

### Async Rounding (CRITICAL)
`_round_qty()` and `_round_price()` were SYNCHRONOUS — used `urllib.request.urlopen()` in async context = blocks event loop.

**Fix:** Convert to `async def` with `aiohttp` + caching:
```python
async def _round_qty(self, symbol: str, qty: float) -> float:
    if not hasattr(self, '_step_cache'):
        self._step_cache = {}
    # Check cache first, then hardcoded dict, then API
    step = self._step_cache.get(symbol) or step_sizes.get(symbol)
    if step is None:
        # Fetch async from /fapi/v1/exchangeInfo
        async with self.session.get(url) as resp:
            # ... extract stepSize, cache it
    return max(round(qty / step) * step, step)
```

### Safety Rails on RiskEngine
Add `_check_safety_rails(symbol, side) -> Tuple[bool, str]` and `record_trade(symbol, side)`:
```python
def _check_safety_rails(self, symbol: str, side: str) -> Tuple[bool, str]:
    now = time.time()
    # 1. Per-pair cooldown
    # 2. Flip prevention (direction reversal cooldown)
    # 3. Hourly trade limit
    # 4. Min balance check
    return True, 'OK'

def record_trade(self, symbol: str, side: str):
    self._pair_last_trade[symbol] = time.time()
    self._pair_last_side[symbol] = side
    self._hourly_trades.append(time.time())
```

### Breakeven SL After TP1
When TP1 hits, move SL to entry + 0.1*ATR to lock profit:
```python
if hit_tp1:
    breakeven_atr = atr * 0.1 if atr > 0 else current_price * 0.001
    if pos.side == 'LONG':
        pos.sl_price = max(pos.sl_price, pos.entry_price + breakeven_atr)
    else:
        pos.sl_price = min(pos.sl_price, pos.entry_price - breakeven_atr)
```

### Retry Logic for SL/TP Orders
```python
async def _retry_order(self, coro_fn, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        result = await coro_fn(*args, **kwargs)
        if 'algoId' in result or 'orderId' in result:
            return result
        if result.get('code') in (-4130, -4028):
            return result  # Already exists = protected
        await asyncio.sleep((attempt + 1) * 1.5)
    return result
```

### Nested Class Bug (Patch Tool)
The patch tool can create nested classes when inserting into a class body:
```python
class RiskEngine:
    class RiskEngine:  # BUG: nested!
```
**Fix:** Use Python script to replace the broken block, not the patch tool for complex class insertions.

## AutoTrader Fixes (mona_futures_auto.py)

### Balance Sync
```python
async def _sync_balance(self):
    """Sync live balance from Binance API."""
    balance = await self.execution.get_balance()
    if balance > 0:
        self._live_balance = balance
        self.risk.balance = balance
        if balance > self.risk.peak_balance:
            self.risk.peak_balance = balance
```

### Position Reconciliation
```python
async def _reconcile_positions(self):
    """Reconcile local state with Binance positions on startup."""
    positions = await self.execution.get_positions()
    for p in positions:
        sym = p.get('symbol', '')
        amt = float(p.get('positionAmt', 0))
        # Log existing positions for awareness
```

### Safety Rail Integration
Call `self.risk._check_safety_rails(symbol, side)` BEFORE each entry attempt.
Call `self.risk.record_trade(symbol, side)` AFTER successful entry.

## Data Layer Fixes (data.py)

### DXY Fallback
Yahoo Finance frequently returns 429 for DXY. Add CoinGecko fallback:
```python
if not data or not data.get('chart', {}).get('result'):
    if symbol == 'DXY':
        cg_data = await self._get('https://api.coingecko.com/api/v3/simple/price', ...)
        return {'price': cg_data['tether']['usd'], 'change_pct': ...}
```
