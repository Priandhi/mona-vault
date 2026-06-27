# Binance Futures Execution Patterns

## Order Execution Flow

```python
async def execute_full_trade(self, symbol, side, leverage, qty, sl, tp1, tp2, tp3, tp1_pct, tp2_pct):
    results = {}
    
    # 1. Set leverage (must be done before order)
    results['leverage'] = await self.set_leverage(symbol, leverage)
    
    # 2. Round qty to valid step size
    qty = self._round_qty(symbol, qty)
    
    # 3. Place market order
    entry_side = 'BUY' if side == 'LONG' else 'SELL'
    close_side = 'SELL' if side == 'LONG' else 'BUY'
    results['entry'] = await self.market_order(symbol, entry_side, qty)
    
    # 4. CRITICAL: Check for orderId (success), NOT 'error' key
    if 'orderId' not in results['entry']:
        error_code = results['entry'].get('code', 'unknown')
        error_msg = results['entry'].get('msg', 'Unknown error')
        results['error'] = f'Binance error {error_code}: {error_msg}'
        return results
    
    # 5. Place SL via Algo Order API — ALWAYS verify!
    results['sl'] = await self.stop_market(symbol, close_side, qty, sl)
    if 'algoId' in results['sl']:
        log.info(f'✅ SL placed: {symbol} @ {sl} (algoId={results["sl"]["algoId"]})')
    else:
        log.error(f'❌ SL FAILED: {symbol} @ {sl} → {results["sl"]}')
    
    # 6. Place TPs via Algo Order API with closePosition=true
    results['tp1'] = await self.take_profit_market(symbol, close_side, 0, tp1)
    if 'algoId' in results['tp1']:
        log.info(f'✅ TP1 placed: {symbol} @ {tp1} (algoId={results["tp1"]["algoId"]})')
    else:
        log.error(f'❌ TP1 FAILED: {symbol} @ {tp1} → {results["tp1"]}')
    
    results['tp2'] = await self.take_profit_market(symbol, close_side, 0, tp2)
    if 'algoId' in results['tp2']:
        log.info(f'✅ TP2 placed: {symbol} @ {tp2} (algoId={results["tp2"]["algoId"]})')
    else:
        log.error(f'❌ TP2 FAILED: {symbol} @ {tp2} → {results["tp2"]}')
    
    results['tp3'] = await self.take_profit_market(symbol, close_side, 0, tp3)
    if 'algoId' in results['tp3']:
        log.info(f'✅ TP3 placed: {symbol} @ {tp3} (algoId={results["tp3"]["algoId"]})')
    else:
        log.error(f'❌ TP3 FAILED: {symbol} @ {tp3} → {results["tp3"]}')
    
    return results
```

## Binance Error Response Format

**Success response:**
```json
{
    "orderId": 12345678,
    "symbol": "LINKUSDT",
    "status": "FILLED",
    "clientOrderId": "abc123",
    "price": "0",
    "avgPrice": "7.310",
    "origQty": "42.80",
    "executedQty": "42.80",
    "cumQty": "42.80",
    "cumQuote": "312.87",
    "timeInForce": "GTC",
    "type": "MARKET",
    "side": "BUY",
    "stopPrice": "0",
    "workingType": "CONTRACT_PRICE",
    "selfTradePreventionMode": "NONE",
    "updateTime": 1717725225951
}
```

**Error response:**
```json
{
    "code": -1102,
    "msg": "Mandatory parameter 'quantity' was not sent, was empty/null, or malformed."
}
```

**Common error codes:**
- `-1102`: Missing/malformed parameter
- `-1111`: Precision over maximum (qty not rounded to stepSize)
- `-2019`: Margin insufficient
- `-4003`: Quantity less than minimum
- `-4028`: Leverage too high for symbol
- `-4120`: Order type not supported on this endpoint — use `/fapi/v1/algoOrder` for conditional orders (pitfall #50)
- `-4164`: Notional too small — **minimum varies by pair** (not always $5). Known minimums: BTC=$100, ETH/LINK=$20, BNB/ADA/SOL/DOGE=$5. Fetch from `exchangeInfo` → `MIN_NOTIONAL` filter. Small accounts with multiple positions may hit this when available margin shrinks.
- `-1003`: IP banned (too many requests)

## Step Size Reference

Each pair has a `stepSize` that quantity must be rounded to. Common values:

| Pair | Step Size | Min Qty | Example |
|------|-----------|---------|---------|
| BTCUSDT | 0.001 | 0.001 | 0.123 ✓, 0.1234 ✗ |
| ETHUSDT | 0.001 | 0.001 | 1.234 ✓, 1.2345 ✗ |
| SOLUSDT | 0.01 | 0.01 | 10.50 ✓, 10.505 ✗ |
| LINKUSDT | 0.01 | 0.01 | 42.80 ✓, 42.803 ✗ |
| DOGEUSDT | 1 | 1 | 1000 ✓, 1000.5 ✗ |
| ADAUSDT | 1 | 1 | 500 ✓, 500.5 ✗ |
| XRPUSDT | 0.1 | 0.1 | 100.0 ✓, 100.05 ✗ |
| WIFUSDT | 0.1 | 0.1 | 100.0 ✓, 100.05 ✗ |
| PEPEUSDT | 1 | 1 | 1000 ✓, 1000.5 ✗ |

**Dynamic lookup for unknown symbols:**
```python
async def get_step_size(self, symbol: str) -> float:
    """Fetch stepSize from exchange info."""
    url = 'https://fapi.binance.com/fapi/v1/exchangeInfo'
    async with self.session.get(url) as resp:
        data = await resp.json()
        for s in data.get('symbols', []):
            if s['symbol'] == symbol:
                for f in s['filters']:
                    if f['filterType'] == 'LOT_SIZE':
                        return float(f['stepSize'])
    return 0.01  # default fallback
```

## Caller Error Handling Pattern

```python
result = await self.execution.execute_full_trade(
    symbol=symbol, side=side, leverage=leverage,
    qty=qty, sl=sl, tp1=tp1, tp2=tp2, tp3=tp3,
    tp1_pct=self.config.tp1_close_pct,
    tp2_pct=self.config.tp2_close_pct
)
if 'error' not in result:
    self.daily_trades += 1
    self.last_trade_time = time.time()
    self._alert_entry_live(symbol, side, price, size_usdt, leverage, analysis)
    log.info(f"🔴 Live {side} {symbol} @ ${price:,.2f} | Size: ${size_usdt:.2f} | Lev: {leverage}x")
else:
    log.error(f"❌ Trade FAILED {side} {symbol}: {result.get('error', result)}")
    # DON'T increment daily_trades or set cooldown on failure
```

## HMAC Signing for POST Requests (CRITICAL)

GET requests work with basic aiohttp `params=` signing. POST requests fail with `-1022: Signature for this request is not valid` because aiohttp's `params=` URL-encodes values differently from the raw query string used for HMAC signing.

**Root cause:** `aiohttp.ClientSession.post(url, params=params)` and `aiohttp.ClientSession.post(url, data=urlencode(params))` both apply URL encoding that diverges from the signing query string.

**Correct implementation:**

```python
class ExecutionEngine:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self._hmac = __import__('hmac')
        self._hashlib = __import__('hashlib')

    def _sign(self, params: dict) -> dict:
        """Sign params — ALL values must be strings for consistent encoding."""
        params['timestamp'] = str(int(time.time() * 1000))
        # Convert all values to strings — mixed types cause encoding mismatch
        for k in list(params.keys()):
            params[k] = str(params[k])
        # Build query string deterministically
        query = '&'.join(f'{k}={params[k]}' for k in sorted(params.keys()))
        sig = self._hmac.new(
            self.api_secret.encode(), query.encode(), self._hashlib.sha256
        ).hexdigest()
        params['signature'] = sig
        return params

    async def _post(self, endpoint: str, params: dict) -> dict:
        """POST with signed params in query string (not body)."""
        if not self.has_keys:
            return {'error': 'No API keys'}
        await self._ensure_session()
        params = self._sign(params)
        # Build query string manually to match signature exactly
        from urllib.parse import urlencode
        query_string = urlencode(sorted(params.items()))
        url = f'https://fapi.binance.com{endpoint}?{query_string}'
        try:
            # CRITICAL: Do NOT use params= or data= — they re-encode values
            async with self.session.post(url) as resp:
                return await resp.json()
        except Exception as e:
            return {'error': str(e)}
```

**Why GET works but POST doesn't:**
- GET: `session.get(url, params=params)` — aiohttp encodes params into URL query string
- POST: `session.post(url, params=params)` — same encoding, but for some reason the encoding diverges from the signing query string (possibly related to Content-Type header or body encoding)
- POST with `data=urlencode(params)` — body encoding also diverges
- **Solution:** Build the full URL with query string manually, then `session.post(url)` with no params/data

**Verification script:**
```python
import hmac, hashlib, time, aiohttp, asyncio
from urllib.parse import urlencode

# Test signing consistency
params = {'symbol': 'ADAUSDT', 'side': 'BUY', 'type': 'MARKET', 'quantity': '1.0'}
params['timestamp'] = str(int(time.time() * 1000))
for k in list(params.keys()): params[k] = str(params[k])
query1 = '&'.join(f'{k}={params[k]}' for k in sorted(params.keys()))
query2 = urlencode(sorted(params.items()))
assert query1 == query2, f"Mismatch: {query1} vs {query2}"

# Test actual API call (expect -4164 notional = signing works)
sig = hmac.new(b'SECRET', query1.encode(), hashlib.sha256).hexdigest()
params['signature'] = sig
qs = urlencode(sorted(params.items()))
url = f'https://fapi.binance.com/fapi/v1/order?{qs}'
headers = {'X-MBX-APIKEY': 'KEY'}
async with aiohttp.ClientSession(headers=headers) as s:
    async with s.post(url) as r:
        print(await r.json())
        # Expected: {'code': -4164, 'msg': "Order's notional must be no smaller than 5"}
        # NOT: {'code': -1022, 'msg': 'Signature for this request is not valid.'}
```

## Silent Failure Detection

If the engine logs "Live LONG/SHORT" but:
- Balance unchanged
- No position on Binance
- No trade in trade history

Then check:
1. Is `'error' not in result` always True? → Fix pitfall #46
2. Is qty properly rounded? → Fix pitfall #51
3. Is `_alert_entry_live` method defined? → Fix pitfall #44
4. Is IP banned? → Check for `code: -1003` in response
5. Are SL/TP algo orders placed? → Check for `algoId` in response (pitfall #52)

## Position Monitor Pattern

Run a SEPARATE process that checks all open positions every 60s and verifies SL/TP algo orders exist:

```python
async def monitor_loop():
    while True:
        positions = await get_positions()
        algo_orders = await get_algo_orders()
        
        for p in positions:
            symbol = p['symbol']
            sl_count = sum(1 for o in algo_orders 
                          if o['symbol'] == symbol and o['orderType'] == 'STOP_MARKET')
            tp_count = sum(1 for o in algo_orders 
                          if o['symbol'] == symbol and o['orderType'] == 'TAKE_PROFIT_MARKET')
            
            if sl_count == 0 or tp_count == 0:
                missing = []
                if sl_count == 0: missing.append('SL')
                if tp_count == 0: missing.append('TP')
                send_telegram(f'⚠️ WARNING: {symbol} missing {" + ".join(missing)}!')
        
        await asyncio.sleep(60)
```

This catches:
- SL/TP cancelled by Binance (liquidation, auto-deleverage)
- Engine crashes between entry and SL/TP placement
- User manually closes SL/TP via Binance app

## Emergency Close Pattern (SL Failure)

When SL placement fails (NOT -4130), the position must be closed immediately:

```python
# STEP 2: SL (MANDATORY)
results['sl'] = await self.stop_market(symbol, close_side, qty, sl)

if 'algoId' in results['sl']:
    # New SL placed — SUCCESS
    log.info(f'✅ SL placed: {symbol} @ {sl} (algoId={results["sl"]["algoId"]})')
elif results['sl'].get('code') == -4130:
    # SL already exists for this symbol+direction — STILL PROTECTED
    log.info(f'✅ SL already exists for {symbol} (protected)')
else:
    # REAL failure — EMERGENCY CLOSE
    log.error(f'🚨 SL FAILED for {symbol}! EMERGENCY CLOSING!')
    emergency = await self.market_order(symbol, close_side, qty)
    results['emergency_close'] = emergency
    results['error'] = f'SL placement failed ({results["sl"]}), position emergency-closed'
    return results
```

**CRITICAL:** -4130 is NOT a failure. It means "an open stop or take profit order already exists" — the position IS protected. Treating -4130 as failure triggers unnecessary emergency closes that lose money via market spread + fees. Real production bug: 3 positions emergency-closed in one session because -4130 was treated as SL failure.

## Caller Pattern with Emergency Close

```python
result = await self.execution.execute_full_trade(...)
if 'error' not in result:
    # Success — SL/TP confirmed
    self.daily_trades += 1
    self.last_trade_time = time.time()
    self._alert_entry_live(symbol, side, price, size_usdt, leverage, analysis)
elif 'emergency_close' in result:
    # SL failed — position auto-closed, alert user
    msg = f'🚨 EMERGENCY CLOSE — {symbol}\nEntry placed but SL FAILED!\nPosition auto-closed to prevent liquidation.\n\n⚠️ {result.get("error", "Unknown")}'
    self._send_telegram(msg)
    log.error(f'🚨 EMERGENCY CLOSE {side} {symbol}: {result.get("error")}')
else:
    # Entry failed — no position opened
    log.error(f'❌ Trade FAILED {side} {symbol}: {result.get("error", result)}')
```
