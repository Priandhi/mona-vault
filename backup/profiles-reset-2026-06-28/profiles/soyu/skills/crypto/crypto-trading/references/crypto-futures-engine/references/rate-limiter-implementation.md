# Rate Limiter for Binance API — Production Implementation

## Problem
Scanning 528+ pairs with individual API calls per symbol triggers Binance IP ban within 1 cycle (~90 seconds). Ban lasts ~90 minutes. Binance returns HTTP 418 (not 429) with `{'code': -1003, 'msg': 'Way too many requests; IP(xxx) banned until TIMESTAMP'}`.

## Solution: RateLimiter Class in DataCollector

Add to `data.py` BEFORE the `DataCollector` class:

```python
class RateLimiter:
    """Rate limiter: max N requests per window. Blocks if exceeded."""
    def __init__(self, max_requests: int = 50, window_sec: int = 60):
        self.max_requests = max_requests
        self.window_sec = window_sec
        self._timestamps: list = []

    async def acquire(self):
        """Wait until a request slot is available."""
        now = time.time()
        self._timestamps = [t for t in self._timestamps if now - t < self.window_sec]
        if len(self._timestamps) >= self.max_requests:
            wait_time = self.window_sec - (now - self._timestamps[0]) + 0.1
            if wait_time > 0:
                log.info(f"Rate limit: waiting {wait_time:.1f}s ({len(self._timestamps)}/{self.max_requests})")
                await asyncio.sleep(wait_time)
        self._timestamps.append(time.time())
```

In `DataCollector.__init__`:
```python
self.rate_limiter = RateLimiter(max_requests=50, window_sec=60)  # 50 req/min
```

In `DataCollector._get()`:
```python
async def _get(self, url, params=None, cache_key='', ttl=120):  # ttl 120s not 60s
    await self._ensure_session()
    now = time.time()
    if cache_key and cache_key in self._cache:
        if now - self._cache_ts.get(cache_key, 0) < ttl:
            return self._cache[cache_key]
    # Rate limit: wait if needed
    await self.rate_limiter.acquire()
    try:
        async with self.session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                if cache_key:
                    self._cache[cache_key] = data
                    self._cache_ts[cache_key] = now
                return data
            elif resp.status == 418:
                log.warning(f"IP BANNED (418): {url}")
                if cache_key:
                    self._cache[cache_key] = {}
                    self._cache_ts[cache_key] = now + 300  # Cache empty 5 min
                return {}
            elif resp.status == 429:
                log.warning(f"Rate limited (429): {url}")
                await asyncio.sleep(10)
                return {}
            return {}
    except Exception as e:
        log.warning(f"GET {url} failed: {e}")
        return {}
```

## Symbol Count Cap

In `_fetch_all_usdt_symbols()`:
```python
filtered = [s for s in symbols if vol_map.get(s, 0) > 500000]
filtered.sort(key=lambda s: vol_map.get(s, 0), reverse=True)
filtered = filtered[:30]  # Top 30 only — avoid IP ban
```

## Scan Interval

Default interval for autonomous engines scanning >100 symbols: 300 seconds (5 min).
For top-30 only: 120-300 seconds is safe with rate limiter.

## Alert Discipline

Telegram alerts ONLY on:
1. Trade OPENED (new position)
2. Trade CLOSED (position exited)

NO periodic status updates, NO balance reports, NO scan summaries.
After ALL positions close: one line max ("All closed, wallet $X").

Implementation in `_execute_trade()`:
```python
send_telegram_alert(
    f"🟢 <b>TRADE OPENED</b>\n"
    f"Pair: <b>{symbol}</b>\n"
    f"Side: <b>{side}</b>\n"
    f"Entry: <code>{price:.4f}</code>\n"
    f"SL: <code>{sl_price:.4f}</code>\n"
    f"TP1: <code>{tp1_price:.4f}</code>\n"
    f"Leverage: {leverage}x\n"
    f"Score: {score:.1f}\n"
    f"Regime: {regime.value}"
)
```

Implementation in `_close_position()`:
```python
icon = "✅" if pnl_pct > 0 else "❌"
send_telegram_alert(
    f"{icon} <b>TRADE CLOSED</b>\n"
    f"Pair: <b>{symbol}</b>\n"
    f"Exit: <code>{exit_type}</code>\n"
    f"PnL: <b>{pnl_pct:+.2f}%</b>\n"
    f"Score: {pos_data.get('score', 0):.1f}"
)
```

## API Call Budget Per Cycle

With rate limiter + top 30 + 300s interval:
- exchangeInfo: 1 call (cached 24h)
- ticker/24hr: 1 call (cached 5 min)
- Per symbol: ~3-5 calls (klines 1h, 15m, price, aggtrades) × 30 symbols = 90-150 calls
- But with 120s cache TTL, many are cache hits
- Effective: ~30-50 new API calls per cycle = ~10-17 calls/min (well under 50/min limit)

## Auto-Start on IP Unban Pattern

When IP gets banned, set up a cron job to check every 5 minutes and auto-start the engine:

```python
# auto_start_engine.py
def check_ip_status():
    """Check if IP is still banned by making a signed request."""
    params = {'timestamp': int(time.time() * 1000)}
    qs = urllib.parse.urlencode(params)
    sig = hmac.new(api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.binance.com/fapi/v2/account?{qs}&signature={sig}"
    req = urllib.request.Request(url, headers={'X-MBX-APIKEY': api_key})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        return True, float(data.get('totalWalletBalance', 0))
    except urllib.error.HTTPError as e:
        return False, 0
    except:
        return False, 0

# Don't start if already running
if is_engine_running():
    exit(0)
ok, balance = check_ip_status()
if ok:
    start_engine()
```

Set as cron: `schedule='every 5m'`, `no_agent=True`, `script='auto_start_engine.py'`.

## Breakeven Stop After TP1

When TP1 partial close triggers, move SL to breakeven immediately:

```python
if hit_tp1:
    pos['partial_closes'] = 1
    actions.append({'action': 'CLOSE_PCT', 'pct': 0.25, 'reason': 'TP1'})
    # Breakeven: move SL to entry + small buffer
    if side == 'LONG':
        pos['sl'] = max(pos['sl'], entry + pos['atr'] * 0.1)
    else:
        pos['sl'] = min(pos['sl'], entry - pos['atr'] * 0.1)
    pos['trailing_active'] = True
```

## Retry Order Placement

All SL/TP placements should use retry with exponential backoff:

```python
async def _retry_order(coro_func, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            result = await coro_func(*args, **kwargs)
            if 'algoId' in result or 'orderId' in result:
                return result
            if result.get('code') == -4130:
                return result
        except Exception as e:
            log.warning(f"Order attempt {attempt+1}/{max_retries}: {e}")
        if attempt < max_retries - 1:
            await asyncio.sleep(1 * (attempt + 1))
    return {'error': 'max retries exceeded'}
```
