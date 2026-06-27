# Safety Rails, SMC Integration & Advanced Patterns

## Safety Rails Implementation (Mandatory)

Every production engine MUST implement these 8 safety rails:

```python
@dataclass
class SafetyRailConfig:
    per_pair_cooldown_sec: int = 300       # 5 min per pair
    flip_cooldown_sec: int = 600           # 10 min before reversing
    max_hourly_trades: int = 4
    max_daily_trades: int = 5
    min_balance_to_trade: float = 40.0
    emergency_drawdown_pct: float = 0.07   # 7% → stop all
    max_drawdown_pct: float = 0.05         # 5% → pause
    cooldown_after_loss_sec: int = 600     # 10 min after SL

class SafetyRails:
    def __init__(self):
        self._pair_last_trade: Dict[str, float] = {}
        self._pair_last_side: Dict[str, str] = {}
        self._hourly_trades: List[float] = []

    def check(self, symbol: str, side: str, balance: float) -> Tuple[bool, str]:
        now = time.time()
        # Per-pair cooldown
        last = self._pair_last_trade.get(symbol, 0)
        if now - last < self.config.per_pair_cooldown_sec:
            return False, f'Per-pair cooldown: {self.config.per_pair_cooldown_sec - (now - last):.0f}s'
        # Flip prevention
        last_side = self._pair_last_side.get(symbol)
        if last_side and last_side != side:
            if now - last < self.config.flip_cooldown_sec:
                return False, f'Flip cooldown: {self.config.flip_cooldown_sec - (now - last):.0f}s'
        # Hourly limit
        self._hourly_trades = [t for t in self._hourly_trades if t > now - 3600]
        if len(self._hourly_trades) >= self.config.max_hourly_trades:
            return False, f'Max hourly trades ({self.config.max_hourly_trades}) reached'
        # Min balance
        if balance < self.config.min_balance_to_trade:
            return False, f'Balance ${balance:.2f} < min ${self.config.min_balance_to_trade}'
        return True, 'OK'
```

## DOZERO.X SMC Integration

Smart Money Concepts (SMC) adds 6 confluence factors to the standard signal engine:

| Factor | Points | Description |
|--------|--------|-------------|
| MTF Alignment | 25 | Daily+H4+H1+M15 all same direction |
| Virgin FVG | 20 | Fresh Fair Value Gap (never touched) |
| Liquidity Sweep + Displacement | 20 | Sweep + strong candle |
| BOS/CHOCH | 15 | Break of Structure / Change of Character |
| Premium/Discount | 10 | Buy in discount, sell in premium |
| Accumulation | 10 | Smart money accumulation detected |

**Elite setup = 75+ confluence score.** Integration pattern:

```python
# In signals.py
from dozero_smc_engine import DozeroSMCEngine, Bias as SMCBias

async def smc_confluence(self, symbol: str) -> SignalResult:
    klines = await self.data.binance_klines(symbol, '1h', 100)
    ohlcv = {
        'open': [float(k[1]) for k in klines],
        'high': [float(k[2]) for k in klines],
        'low': [float(k[3]) for k in klines],
        'close': [float(k[4]) for k in klines],
        'volume': [float(k[5]) for k in klines],
    }
    # Get MTF biases from multiple timeframes
    mtf_biases = {
        'daily': get_bias(await self.data.binance_klines(symbol, '1d', 30)),
        'h4': get_bias(await self.data.binance_klines(symbol, '4h', 50)),
        'h1': get_bias(klines),
        'm15': get_bias(await self.data.binance_klines(symbol, '15m', 50)),
    }
    smc = DozeroSMCEngine({'confluence_threshold': 50})
    setup = smc.full_analysis(symbol, ohlcv, mtf_biases)
    # Convert to signal score
    score = setup.confluence_score if setup.direction == SMCBias.BULLISH else -setup.confluence_score
    return SignalResult('SMC', signal, score, ...)
```

**Add to gather() with weight_smc=15 in config.**

## DXY Fallback

Yahoo Finance often returns 429 for DXY. Add CoinGecko fallback:

```python
async def yahoo_quote(self, symbol: str) -> dict:
    data = await self._get(f'{YAHOO_FINANCE}/{yahoo_sym}', ...)
    if not data or not data.get('chart', {}).get('result'):
        if symbol == 'DXY':
            # Fallback to CoinGecko
            cg = await self._get('https://api.coingecko.com/api/v3/simple/price',
                                {'ids': 'tether', 'vs_currencies': 'usd'}, ttl=300)
            return {'price': cg.get('tether', {}).get('usd', 100), 'change_pct': 0}
    return data
```

## Breakeven SL After TP1

When TP1 hits, move SL to entry + small buffer (0.1 ATR). This locks profit and removes risk:

```python
if hit_tp1:
    breakeven_atr = atr * 0.1
    if pos.side == 'LONG':
        new_sl = max(pos.sl_price, pos.entry_price + breakeven_atr)
    else:
        new_sl = min(pos.sl_price, pos.entry_price - breakeven_atr)
    pos.sl_price = new_sl
```

## Retry Logic for Order Placement

SL/TP placement can fail transiently. Retry 3x with exponential backoff:

```python
async def _retry_order(self, coro_fn, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        result = await coro_fn(*args, **kwargs)
        if 'algoId' in result or 'orderId' in result:
            return result
        if result.get('code') == -4130:  # Already exists = protected
            return result
        if attempt < max_retries - 1:
            await asyncio.sleep((attempt + 1) * 1.5)
    return result
```

## Position Reconciliation on Startup

When engine restarts, it doesn't know about existing positions. Always reconcile:

```python
async def _reconcile_positions(self):
    positions = await self.execution.get_positions()
    if positions:
        log.info(f"Reconciling {len(positions)} open positions from Binance")
        for p in positions:
            sym = p.get('symbol', '')
            amt = float(p.get('positionAmt', 0))
            if amt != 0:
                log.info(f"  {sym}: {'LONG' if amt > 0 else 'SHORT'} {abs(amt)}")
```

## Auto Balance Sync

Never use hardcoded balance. Sync from Binance before each trade cycle:

```python
async def _sync_balance(self):
    balance = await self.execution.get_balance()
    if balance > 0:
        self._live_balance = balance
        self.risk.balance = balance
        if balance > self.risk.peak_balance:
            self.risk.peak_balance = balance
```

## Async Rounding (CRITICAL)

`_round_qty` and `_round_price` MUST be async. Using `urllib.request` (sync) inside an async event loop **blocks the entire loop** while waiting for Binance API.

```python
# ❌ WRONG — blocks event loop
def _round_qty(self, symbol, qty):
    resp = urllib.request.urlopen(url, timeout=5)  # BLOCKS!

# ✅ CORRECT — async with caching
async def _round_qty(self, symbol, qty):
    if not hasattr(self, '_step_cache'):
        self._step_cache = {}
    step = self._step_cache.get(symbol) or STEP_SIZES.get(symbol)
    if step is None:
        async with self.session.get(url) as resp:
            data = await resp.json()
            step = float(data['stepSize'])
            self._step_cache[symbol] = step
    return round(qty / step) * step
```

## Config Pitfall: Duplicate Fields

Python dataclasses silently overwrite duplicate field definitions. If you define `max_daily_trades` twice, the second value wins. **Always grep for duplicates before committing.**
