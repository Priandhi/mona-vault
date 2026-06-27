# Binance Futures API — Algo Orders (Critical Reference)

## The Problem

As of 2026, `STOP_MARKET`, `TAKE_PROFIT_MARKET`, `STOP`, `TAKE_PROFIT`, and `TRAILING_STOP_MARKET` order types are **NO LONGER supported** on `/fapi/v1/order`. They return error `-4120`:

```
"Order type not supported for this endpoint. Please use the Algo Order API endpoints instead."
```

## The Solution

Use `/fapi/v1/algoOrder` with `algoType=CONDITIONAL`:

```python
import hmac, hashlib, time, requests
from urllib.parse import urlencode

def algo_order(api_key, api_secret, symbol, side, order_type, trigger_price):
    """Place SL/TP via Algo Order API."""
    params = {
        'algoType': 'CONDITIONAL',
        'symbol': symbol,
        'side': side,
        'type': order_type,  # 'STOP_MARKET' or 'TAKE_PROFIT_MARKET'
        'triggerPrice': str(trigger_price),
        'closePosition': 'true',
        'workingType': 'MARK_PRICE',
        'timeInForce': 'GTE_GTC',  # REQUIRED for algo orders
        'timestamp': str(int(time.time()*1000)),
    }
    for k in list(params.keys()):
        params[k] = str(params[k])
    query = '&'.join(f'{k}={params[k]}' for k in sorted(params.keys()))
    sig = hmac.new(api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    url = f'https://fapi.binance.com/fapi/v1/algoOrder?{query}&signature={sig}'
    r = requests.post(url, headers={'X-MBX-APIKEY': api_key}, timeout=10)
    return r.json()

# Example: Place SL for SHORT position
result = algo_order(
    api_key, api_secret,
    symbol='BTCUSDT',
    side='BUY',           # Opposite of position side
    order_type='STOP_MARKET',
    trigger_price='65000',
)
# Success: {'algoId': 3000001775506778, 'algoStatus': 'NEW', ...}
# Failure: {'code': -4130, 'msg': 'An open stop or take profit order...is existing.'}
```

## Key Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `algoType` | `CONDITIONAL` | Required for all conditional orders |
| `timeInForce` | `GTE_GTC` | **REQUIRED** — omitting causes error -4509 |
| `closePosition` | `true` | Closes entire position (ignores quantity) |
| `workingType` | `MARK_PRICE` | Trigger on mark price (safer) |
| `reduceOnly` | `true` | Optional, but recommended with quantity |

## Error Codes

| Code | Meaning | Fix |
|------|---------|-----|
| `-4120` | Order type not supported on `/fapi/v1/order` | Use `/fapi/v1/algoOrder` |
| `-4130` | SL/TP already exists for this direction | Normal — skip or cancel old one first |
| `-4509` | `timeInForce` GTE requires open positions | Add `timeInForce: 'GTE_GTC'` |
| `-2022` | ReduceOnly order rejected | Use `closePosition: 'true'` instead |

## Important: Algo Orders Don't Appear in openOrders

`/fapi/v1/openOrders` only shows **regular** orders. Algo orders are separate.

To verify algo orders exist:
- Check the POST response for `algoId` (success indicator)
- Error `-4130` means "already exists" (also a success indicator)
- There's no public endpoint to list algo orders — trust the POST response

## SL/TP Verification Pattern

```python
async def verify_sltp_exists(symbol, side, sl_price, tp_price):
    """Verify SL/TP exists by trying to place them."""
    sl_result = await place_algo_order(symbol, side, 'STOP_MARKET', sl_price)
    tp_result = await place_algo_order(symbol, side, 'TAKE_PROFIT_MARKET', tp_price)
    
    sl_ok = 'algoId' in sl_result or sl_result.get('code') == -4130
    tp_ok = 'algoId' in tp_result or tp_result.get('code') == -4130
    
    if not sl_ok:
        # SL failed — EMERGENCY CLOSE position
        await close_position(symbol)
    if not tp_ok:
        # TP failed — SL still active, acceptable
        log.warning(f"TP not placed for {symbol}")
```

## Leverage Auto-Detect

Different pairs have different max leverage. Always fetch before setting:

```python
# Fetch exchange info
info = requests.get('https://fapi.binance.com/fapi/v1/exchangeInfo').json()
for sym_info in info['symbols']:
    if sym_info['symbol'] == symbol:
        max_leverage = int(sym_info['leverageFilter']['maxLeverage'])
        break

# Try desired leverage, fallback to max
result = await set_leverage(symbol, desired_lev)
if 'code' in result:
    result = await set_leverage(symbol, max_leverage)
```
