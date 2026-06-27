# Binance Futures Algo Order API

## Overview

As of 2025/2026, Binance moved ALL conditional order types (STOP_MARKET, TAKE_PROFIT_MARKET, STOP, TAKE_PROFIT, TRAILING_STOP_MARKET) from `POST /fapi/v1/order` to a new endpoint: `POST /fapi/v1/algoOrder`.

The old endpoint returns `-4120: Order type not supported for this endpoint. Please use the Algo Order API endpoints instead.` for ALL conditional types. LIMIT and MARKET orders still use `/fapi/v1/order`.

## Endpoint

```
POST /fapi/v1/algoOrder
```

## Required Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| algoType | ENUM | YES | Only `CONDITIONAL` supported |
| symbol | STRING | YES | Trading pair |
| side | ENUM | YES | `BUY` or `SELL` |
| type | ENUM | YES | `STOP_MARKET`, `TAKE_PROFIT_MARKET`, `STOP`, `TAKE_PROFIT`, `TRAILING_STOP_MARKET` |

## Optional Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| positionSide | ENUM | Default `BOTH` for One-way Mode |
| timeInForce | ENUM | `IOC`, `GTC`, `FOK`, `GTX` (default `GTC`) |
| quantity | DECIMAL | Cannot combine with `closePosition=true` |
| price | DECIMAL | Limit price (for STOP/TAKE_PROFIT types) |
| triggerPrice | DECIMAL | Price that triggers the order |
| workingType | ENUM | `MARK_PRICE` or `CONTRACT_PRICE` (default `CONTRACT_PRICE`) |
| closePosition | STRING | `true` for close-all (SELL closes LONG, BUY closes SHORT) |
| reduceOnly | STRING | `true` or `false`. Cannot combine with `closePosition=true` |
| priceProtect | STRING | `true` or `false`. Protects against mark/contract price divergence |
| callbackRate | DECIMAL | For TRAILING_STOP_MARKET only. Min 0.1, max 10 (1 = 1%) |
| activatePrice | DECIMAL | For TRAILING_STOP_MARKET only |
| clientAlgoId | STRING | Custom order ID |
| newOrderRespType | ENUM | `ACK`, `RESULT` (default `ACK`) |
| recvWindow | LONG | Max time diff in ms |
| timestamp | LONG | YES — milliseconds |

## Key Differences from Regular Orders

| Aspect | Regular (`/fapi/v1/order`) | Algo (`/fapi/v1/algoOrder`) |
|--------|--------------------------|----------------------------|
| Endpoint | `/fapi/v1/order` | `/fapi/v1/algoOrder` |
| Required param | — | `algoType=CONDITIONAL` |
| Trigger price param | `stopPrice` | `triggerPrice` |
| Response ID key | `orderId` | `algoId` |
| Response status key | `status` | `algoStatus` |
| Error key | `code` | `code` (same) |

## Implementation

```python
class ExecutionEngine:
    async def stop_market(self, symbol: str, side: str, qty: float, stop_price: float) -> dict:
        """Place stop market order via Algo Order API."""
        return await self._post('/fapi/v1/algoOrder', {
            'algoType': 'CONDITIONAL',
            'symbol': symbol, 'side': side, 'type': 'STOP_MARKET',
            'triggerPrice': str(stop_price),
            'closePosition': 'true', 'workingType': 'MARK_PRICE'
        })

    async def take_profit_market(self, symbol: str, side: str, qty: float, tp_price: float) -> dict:
        """Place take profit market order via Algo Order API."""
        return await self._post('/fapi/v1/algoOrder', {
            'algoType': 'CONDITIONAL',
            'symbol': symbol, 'side': side, 'type': 'TAKE_PROFIT_MARKET',
            'triggerPrice': str(tp_price),
            'closePosition': 'true', 'workingType': 'MARK_PRICE'
        })

    async def trailing_stop_market(self, symbol: str, side: str, qty: float, callback_rate: float) -> dict:
        """Place trailing stop market order via Algo Order API."""
        return await self._post('/fapi/v1/algoOrder', {
            'algoType': 'CONDITIONAL',
            'symbol': symbol, 'side': side, 'type': 'TRAILING_STOP_MARKET',
            'callbackRate': str(callback_rate),
            'reduceOnly': 'true', 'quantity': str(qty)
        })
```

## Successful Response

```json
{
    "algoId": 3000001768350200,
    "clientAlgoId": "ktrXsO2fDFHyynuJ20kCqD",
    "algoType": "CONDITIONAL",
    "orderType": "STOP_MARKET",
    "symbol": "ADAUSDT",
    "side": "SELL",
    "positionSide": "BOTH",
    "timeInForce": "GTE_GTC",
    "quantity": "0",
    "algoStatus": "NEW",
    "triggerPrice": "0.15440",
    "price": "0.00000",
    "closePosition": true,
    "priceProtect": false,
    "reduceOnly": true,
    "workingType": "MARK_PRICE",
    "createTime": 1780770255702,
    "updateTime": 1780770255702,
    "triggerTime": 0
}
```

## Managing Algo Orders

### Query Open Algo Orders
```
GET /fapi/v1/algo/openOrders
```
Returns list of active algo orders with `algoId`, `symbol`, `orderType`, `triggerPrice`, etc.

**⚠️ KNOWN ISSUE (June 2026):** This endpoint consistently returns HTTP 404 regardless of signing method. It exists in official docs but is unreachable in production. **Workaround:** Use `-4130` error code as proxy — if placing SL returns -4130, an SL already exists. For position monitoring, cross-reference `/fapi/v2/account` positions with entry logs. Do NOT rely on this endpoint for SL/TP verification.

### Cancel Algo Order
```
DELETE /fapi/v1/algoOrder
```
Parameters: `symbol` (required), `algoId` (required)

### Cancel All Algo Open Orders
```
DELETE /fapi/v1/algo/allOpenOrders
```
Parameters: `symbol` (required)

## Trigger Conditions

- **STOP_MARKET SELL:** Triggers when price <= triggerPrice (for closing LONG)
- **STOP_MARKET BUY:** Triggers when price >= triggerPrice (for closing SHORT)
- **TAKE_PROFIT_MARKET SELL:** Triggers when price >= triggerPrice (for closing LONG)
- **TAKE_PROFIT_MARKET BUY:** Triggers when price <= triggerPrice (for closing SHORT)

## Pitfalls

1. **Cannot combine `closePosition` with `quantity`** — Use one or the other. For partial closes, use `quantity` + `reduceOnly=true`. For close-all, use `closePosition=true`.

2. **`workingType` default is `CONTRACT_PRICE`** — Recommend `MARK_PRICE` for SL/TP to avoid wick-induced premature triggers on low-liquidity pairs.

3. **Algo orders are NOT visible in regular order queries** — Use `/fapi/v1/algo/openOrders` instead of `/fapi/v1/openOrders`. Regular order endpoints won't show algo orders.

4. **Error detection** — Algo orders return `algoId` on success, not `orderId`. Update your success check:
   ```python
   # For market orders (regular):
   if 'orderId' not in result: return error
   
   # For algo orders:
   if 'algoId' not in result: return error
   ```

5. **Rate limits** — Algo orders have weight 0 on IP rate limit (generous), but still subject to order rate limits (10s/1min).

6. **Query endpoint BROKEN — use -4130 fallback** — As of June 2026, `GET /fapi/v1/algo/openOrders` returns HTTP 404 regardless of signing method. This is a Binance-side issue — the endpoint exists in docs but is unreachable. Use `-4130` error code as proxy: if placing SL returns -4130, an SL already exists. Cross-reference with `/fapi/v2/account` positions + entry logs.

7. **SL/TP verification pattern** — After placing SL/TP, ALWAYS check response for `algoId`. Log success/failure. If SL fails, the position is unprotected — alert Telegram immediately. This is defense-in-depth against signing bugs, endpoint changes, and API errors.

8. **-4130 = "Order already exists" (TREAT AS SUCCESS)** — Binance returns `{'code': -4130, 'msg': 'An open stop or take profit order with GTE and closePosition in the direction is existing.'}` when you try to place a `closePosition=true` algo order but one already exists for that symbol+side. This is NOT an error — the position IS protected. Treat as success. Common scenario: engine enters a position, previous SL for same symbol is still active from a prior trade, engine tries to place new SL → -4130 → should log "SL already exists" and continue, NOT trigger emergency close.

9. **`closePosition=true` = ONE order per symbol+side** — Binance enforces a limit: only ONE active `closePosition=true` algo order per symbol per direction. Attempting to place a second returns -4130. This means:
   - You CAN have 1 SL + 1 TP for the same position (SL=SELL closePosition, TP=SELL closePosition) — these are the SAME direction but Binance allows both SL and TP types simultaneously
   - You CANNOT have 2 SLs or 2 TPs for the same position
   - For multi-TP (TP1/TP2/TP3), use `quantity` with partial amounts instead of `closePosition=true`
   - Recommended: use `closePosition=true` for SL (full protection), single `closePosition=true` for TP (simplest)

10. **USUSDT = Algo Order ONLY + 10x max leverage** — USUSDT (Usual) on Binance Futures: max leverage is 10x (not 20x like most pairs). ALL conditional orders (SL/TP) MUST use `/fapi/v1/algoOrder` — `/fapi/v1/order` returns -4120 for USUSDT even for basic STOP_MARKET. This applies to ALL order types: STOP_MARKET, TAKE_PROFIT_MARKET, STOP, TAKE_PROFIT, TRAILING_STOP_MARKET. Only MARKET and LIMIT orders work on `/fapi/v1/order` for USUSDT.
