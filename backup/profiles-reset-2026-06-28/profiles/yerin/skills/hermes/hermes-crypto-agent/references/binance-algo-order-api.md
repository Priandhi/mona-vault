# Binance Futures Algo Order API (June 2026)

**CRITICAL CHANGE:** Binance moved ALL conditional order types from `/fapi/v1/order` to a separate Algo Order API endpoint. This was discovered during live trading when every stop/TP order returned `-4120`.

## What changed

**OLD (no longer works):**
```
POST /fapi/v1/order
  type=STOP_MARKET, stopPrice=0.15, quantity=1399
  → Returns: {'code': -4120, 'msg': 'Order type not supported...'}
```

**NEW (correct):**
```
POST /fapi/v1/algoOrder
  algoType=CONDITIONAL, type=STOP_MARKET, triggerPrice=0.15, closePosition=true
  → Returns: {'algoId': 3000001768350200, 'algoStatus': 'NEW', ...}
```

## Affected order types

ALL of these must use `/fapi/v1/algoOrder`:
- `STOP_MARKET` — stop loss
- `TAKE_PROFIT_MARKET` — take profit
- `STOP` — limit stop (needs `price` + `timeInForce`)
- `TAKE_PROFIT` — limit take profit (needs `price` + `timeInForce`)
- `TRAILING_STOP_MARKET` — trailing stop (needs `callbackRate`)

**Unaffected:** `MARKET` and `LIMIT` still work on `/fapi/v1/order`.

## Key parameter differences

| Parameter | Old (`/fapi/v1/order`) | New (`/fapi/v1/algoOrder`) |
|-----------|----------------------|---------------------------|
| Endpoint | `/fapi/v1/order` | `/fapi/v1/algoOrder` |
| Required param | (none) | `algoType=CONDITIONAL` |
| Stop price | `stopPrice` | `triggerPrice` |
| Close all | `closePosition=true` | `closePosition=true` (same) |
| Quantity | `quantity` (required) | `quantity` (optional with closePosition) |
| Response ID | `orderId` | `algoId` |
| Response status | `status: NEW/FILLED` | `algoStatus: NEW/TRIGGERED` |

## Working examples

### Stop Loss (close all position)
```python
params = {
    'algoType': 'CONDITIONAL',
    'symbol': 'ADAUSDT',
    'side': 'SELL',
    'type': 'STOP_MARKET',
    'triggerPrice': '0.1544',
    'closePosition': 'true',
    'workingType': 'MARK_PRICE'
}
# POST /fapi/v1/algoOrder
# Response: {'algoId': 3000001768350200, 'algoType': 'CONDITIONAL', 'orderType': 'STOP_MARKET', ...}
```

### Take Profit (close all position)
```python
params = {
    'algoType': 'CONDITIONAL',
    'symbol': 'ADAUSDT',
    'side': 'SELL',
    'type': 'TAKE_PROFIT_MARKET',
    'triggerPrice': '0.1634',
    'closePosition': 'true',
    'workingType': 'MARK_PRICE'
}
# POST /fapi/v1/algoOrder
```

### Trailing Stop
```python
params = {
    'algoType': 'CONDITIONAL',
    'symbol': 'ADAUSDT',
    'side': 'SELL',
    'type': 'TRAILING_STOP_MARKET',
    'callbackRate': '2.0',  # 2% trailing
    'quantity': '1399',
    'reduceOnly': 'true'
}
# POST /fapi/v1/algoOrder
```

## Error codes

- `-4120`: Order type not supported on `/fapi/v1/order` → use `/fapi/v1/algoOrder`
- `-1102`: Missing mandatory parameter → check `algoType=CONDITIONAL` is present
- `-2021`: Order would immediately trigger (trailing stop) → `activatePrice` must be on correct side of current price

## HMAC Signing for POST requests

**CRITICAL PITFALL:** Binance HMAC signing for POST requests requires all values as strings and the query string must be in the URL, NOT in the request body.

```python
import hmac, hashlib, time
from urllib.parse import urlencode

def sign(params: dict, secret: str) -> dict:
    params['timestamp'] = str(int(time.time() * 1000))
    # ALL values must be strings
    for k in list(params.keys()):
        params[k] = str(params[k])
    # Build query string sorted by key
    query = '&'.join(f'{k}={params[k]}' for k in sorted(params.keys()))
    sig = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    params['signature'] = sig
    return params

async def post_signed(session, url_base, endpoint, params, api_key):
    params = sign(params, secret)
    # CRITICAL: put query string in URL, NOT in request body
    qs = urlencode(sorted(params.items()))
    url = f'{url_base}{endpoint}?{qs}'
    headers = {'X-MBX-APIKEY': api_key}
    async with session.post(url, headers=headers) as resp:
        return await resp.json()
```

**Why this matters:** Using `aiohttp`'s `params=` parameter or `data=urlencode(params)` causes signature mismatch because aiohttp URL-encodes values differently from the raw query string used for signing. The fix is to build the full URL with query string manually.

**Verified working pattern:** All values converted to strings → sorted query string → HMAC-SHA256 → append signature → put in URL.

## Quantity rounding

Each symbol has a specific step size. Sending unrounded quantities (e.g., `42.80328472`) causes `-1111: Precision is over the maximum defined for this asset`.

```python
STEP_SIZES = {
    'BTCUSDT': 0.001, 'ETHUSDT': 0.001, 'BNBUSDT': 0.01,
    'SOLUSDT': 0.01, 'XRPUSDT': 0.1, 'DOGEUSDT': 1,
    'ADAUSDT': 1, 'AVAXUSDT': 0.01, 'DOTUSDT': 0.1,
    'LINKUSDT': 0.01, 'MATICUSDT': 1, 'NEARUSDT': 0.1,
    'APTUSDT': 0.01, 'SUIUSDT': 0.1, 'ARBUSDT': 0.1,
    'OPUSDT': 0.1, 'PEPEUSDT': 1, 'WIFUSDT': 0.1,
    'FETUSDT': 0.1, 'RNDRUSDT': 0.01,
}

def round_qty(symbol, qty):
    step = STEP_SIZES.get(symbol, 0.01)
    return max(round(qty / step) * step, step)
```

## Position monitoring pattern

Every live trade MUST have:
1. Entry order (MARKET via `/fapi/v1/order`)
2. Stop Loss (via `/fapi/v1/algoOrder` with `closePosition=true`)
3. Take Profit (via `/fapi/v1/algoOrder` with `closePosition=true`)

**Verification:** After placing SL/TP, check `algoId` in response:
```python
result = await stop_market(symbol, 'SELL', qty, sl_price)
if 'algoId' in result:
    log.info(f'✅ SL placed: algoId={result["algoId"]}')
else:
    log.error(f'❌ SL FAILED: {result}')
    # MUST alert user — position is unprotected!
```

**Auto-position monitor:** Check positions every 60s, send PnL updates every 5min, alert if SL/TP missing.

## Querying existing algo orders (BROKEN — June 2026)

**Problem:** There is NO working GET endpoint to query existing algo orders. All of these return **404 HTML page**:
- `GET /fapi/v1/algo/openOrders`
- `GET /fapi/v1/algoOrder/openOrders`
- `GET /fapi/v1/algoOrders`
- `GET /fapi/v1/conditional/openOrders`

The POST endpoint `POST /fapi/v1/algoOrder` works perfectly — the issue is only with GET/query endpoints.

**Workaround to verify SL/TP exists:**
Attempt to place a duplicate SL/TP. If the order already exists, Binance returns:
```
{"msg": "An open stop or take profit order with GTE and closePosition in the direction is existing.", "code": -4028}
```
This confirms protection is active. Treat this as SUCCESS, not failure.

**Position monitoring without algo query:**
```python
# 1. Get positions from account
acc = await signed_get('/fapi/v2/account')
positions = [p for p in acc['positions'] if float(p['positionAmt']) != 0]

# 2. Get standard open orders (LIMIT/MARKET only — NOT algo orders)
orders = await signed_get('/fapi/v1/openOrders', symbol=symbol)
# This returns [] even when algo SL/TP orders exist

# 3. Check SL/TP by attempting duplicate placement
for pos in positions:
    sl_result = await place_sl(pos)
    if sl_result.get('code') == -4028:
        print(f'{pos["symbol"]}: SL ✅ protected')
    elif 'algoId' in sl_result:
        print(f'{pos["symbol"]}: SL ✅ placed')
    else:
        print(f'{pos["symbol"]}: SL ❌ UNPROTECTED — emergency close!')
```

**PITFALL:** Do NOT assume `openOrders = []` means no SL/TP protection. Algo orders are invisible to the standard orders endpoint. Always verify via the duplicate-placement technique.
