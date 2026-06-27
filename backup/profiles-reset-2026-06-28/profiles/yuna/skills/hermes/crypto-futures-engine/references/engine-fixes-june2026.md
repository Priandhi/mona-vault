# Engine Code Fixes Reference (June 2026)

Applied to `mona_futures_v2/` — Binance Futures USDT-M engine.

## Files Modified
- `config.py` — Removed duplicate `max_daily_trades`, added 7 safety rail configs
- `risk.py` — Async rounding, safety rails, breakeven SL, retry logic
- `mona_futures_auto.py` — Balance sync, position reconciliation, safety rail integration
- `data.py` — DXY fallback to CoinGecko

## Safety Rail Configs (add to FuturesConfig)
```python
per_pair_cooldown_sec: int = 300
flip_cooldown_sec: int = 600
max_hourly_trades: int = 4
sl_tp_verify_interval_sec: int = 60
emergency_close_on_sl_fail: bool = True
daily_loss_limit_pct: float = 0.07
min_balance_to_trade: float = 40.0
```

## RiskEngine Safety Rails
```python
def _check_safety_rails(self, symbol: str, side: str) -> Tuple[bool, str]:
    now = time.time()
    # Per-pair cooldown
    last_trade = self._pair_last_trade.get(symbol, 0)
    if now - last_trade < self.config.per_pair_cooldown_sec:
        return False, f'Cooldown: {remaining:.0f}s'
    # Flip prevention
    last_side = self._pair_last_side.get(symbol)
    if last_side and last_side != side:
        if now - last_trade < self.config.flip_cooldown_sec:
            return False, f'Flip cooldown: {remaining:.0f}s'
    # Hourly limit
    self._hourly_trades = [t for t in self._hourly_trades if t > now - 3600]
    if len(self._hourly_trades) >= self.config.max_hourly_trades:
        return False, f'Max hourly trades reached'
    # Min balance
    if self.balance < self.config.min_balance_to_trade:
        return False, f'Balance too low'
    return True, 'OK'
```

## Breakeven SL After TP1
```python
if hit_tp1:
    breakeven_atr = atr * 0.1 if atr > 0 else current_price * 0.001
    if pos.side == 'LONG':
        pos.sl_price = max(pos.sl_price, pos.entry_price + breakeven_atr)
    else:
        pos.sl_price = min(pos.sl_price, pos.entry_price - breakeven_atr)
```

## Retry Logic
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
