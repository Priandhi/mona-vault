# Binance Algo Order API — SL/TP Placement

## Problem

Standard `/fapi/v1/order` returns error **-4120** for these order types:
- `STOP_MARKET`
- `TAKE_PROFIT_MARKET`
- `STOP`
- `TRAILING_STOP_MARKET`

Error message: "Order type not supported for this endpoint. Please use the Algo Order API endpoints instead."

## Solution

Use `POST /fapi/v1/algoOrder` instead.

### Request Format

```python
import hmac, hashlib, time, requests
from urllib.parse import urlencode

def place_algo_sl(api_key, api_secret, symbol, side, trigger_price):
    """Place SL via Algo Order API."""
    params = {
        'algoType': 'CONDITIONAL',
        'symbol': symbol,
        'side': side,                    # BUY for SHORT close, SELL for LONG close
        'type': 'STOP_MARKET',
        'triggerPrice': str(trigger_price),
        'closePosition': 'true',         # Close entire position
        'workingType': 'MARK_PRICE',     # Use mark price, not last price
        'timeInForce': 'GTE_GTC',        # REQUIRED with closePosition
        'timestamp': str(int(time.time()*1000)),
    }
    # All values must be strings
    for k in params:
        params[k] = str(params[k])
    
    query = '&'.join(f'{k}={params[k]}' for k in sorted(params))
    sig = hmac.new(api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    
    r = requests.post(
        f'https://fapi.binance.com/fapi/v1/algoOrder?{query}&signature={sig}',
        headers={'X-MBX-APIKEY': api_key},
        timeout=10
    )
    return r.json()
```

### Success Response (200)

```json
{
    "algoId": 3000001775501555,
    "clientAlgoId": "P7bkmlAhsKLurMVta48qTp",
    "algoType": "CONDITIONAL",
    "orderType": "STOP_MARKET",
    "symbol": "SKYAIUSDT",
    "side": "BUY",
    "positionSide": "BOTH",
    "timeInForce": "GTE_GTC",
    "quantity": "0",
    "algoStatus": "NEW",
    "triggerPrice": "0.2850000",
    "closePosition": true,
    "reduceOnly": true
}
```

### Error Responses

- **-4130**: "An open stop or take profit order with GTE and closePosition in the direction is existing." → **Order already exists! This is NOT a failure.**
- **-4509**: "Time in Force (TIF) GTE can only be used with open positions." → Position was closed/flipped before order was placed.

## Key Facts

1. **Algo orders do NOT appear in `/fapi/v1/openOrders`** — they have a separate listing endpoint
2. **`closePosition: 'true'`** means the order closes the entire position regardless of quantity
3. **`timeInForce: 'GTE_GTC'`** is REQUIRED when using `closePosition`
4. **`workingType: 'MARK_PRICE'`** is safer than `CONTRACT_PRICE` (less likely to be manipulated)
5. **-4130 is SUCCESS** — it means protection already exists

## Verification Pattern

```python
async def _verify_sltp_for_all_positions(self):
    """Verify all positions have SL/TP. Place if missing."""
    if not self.execution:
        return  # Skip in paper mode
    
    real_positions = await self.execution.get_positions()
    for pos in real_positions:
        sym = pos['symbol']
        amt = float(pos['positionAmt'])
        if amt == 0:
            continue
        
        pos_data = self.position_monitor.positions.get(sym)
        if not pos_data:
            # Position on Binance but not in monitor — dangerous, close it
            close_side = 'SELL' if amt > 0 else 'BUY'
            await self.execution.market_order(sym, close_side, abs(amt))
            continue
        
        # Try to place SL (will return -4130 if already exists)
        sl_result = await self.execution.stop_market(sym, close_side, abs(amt), sl_price)
        if 'algoId' in sl_result:
            log.info(f"SL placed @ {sl_price}")
        elif sl_result.get('code') == -4130:
            log.debug(f"SL already exists")
        else:
            # SL FAILED — emergency close!
            log.error(f"SL FAILED: {sl_result} — EMERGENCY CLOSE")
            await self.execution.market_order(sym, close_side, abs(amt))
```

## Max Leverage Per Pair

Leverage limits vary by pair! Always check before entry:

```python
async def set_leverage_auto(self, symbol: str, desired: int) -> int:
    """Set leverage with auto-fallback to max supported."""
    result = await self.set_leverage(symbol, desired)
    if 'code' not in result:
        return desired
    
    # Try lower values
    for lev in [40, 35, 30, 25, 20, 15, 10, 5]:
        if lev >= desired:
            continue
        result = await self.set_leverage(symbol, lev)
        if 'code' not in result:
            return lev
    
    await self.set_leverage(symbol, 5)
    return 5
```

Known limits:
- BTCUSDT, ETHUSDT: 25x
- SKYAIUSDT: 10x
- HUSDT: 10x
- Most mid-cap: 20x
- Meme coins: 10-25x (varies)
