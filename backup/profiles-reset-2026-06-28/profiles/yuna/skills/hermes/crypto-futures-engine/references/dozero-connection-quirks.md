# Dozero Connection API — Return Type Quirks

The dozero wrapper at `/home/ubuntu/dozero/config/connection.py` does NOT mirror Binance's
raw API responses uniformly. Documented here so any aggregator script (`agent_data.py`,
`send_pnl.py`, downstream bots) can call the right methods without trial-and-error.

## `BinanceConnection` — what each method actually returns

| Method | Return type | Shape | Source |
|---|---|---|---|
| `get_balance()` | **`float`** | `4272.42` (already extracted) | `/fapi/v2/account` → `availableBalance` |
| `get_positions()` | `list[dict]` | raw `/fapi/v2/positionRisk` items | `/fapi/v2/positionRisk` |
| `get_open_orders()` | `list[dict]` | raw `/fapi/v1/openOrders` items | `/fapi/v1/openOrders` |
| `market_order(...)` | `dict` | order response with `orderId`, `status` | `/fapi/v1/order` |
| `algo_order(...)` | `dict` | algo order response with `algoId`, `algoStatus` | `/fapi/v1/algoOrder` |
| `get_algo_orders(symbol)` | `list[dict]` | raw algo order items | `/fapi/v1/algoOrder` (testnet returns 400 — broken) |

**Gotcha:** `get_balance()` is the ONLY method that pre-extracts a scalar. Everything else
returns the raw dict. If you write code that assumes uniform "dict → `.get(key)`" access, you
will silently get `AttributeError → 0` for balance (the wrapper catches it).

## Reference implementation: `get_yuna()` in `agent_data.py`

```python
def get_yuna():
    from config.connection import BinanceConnection
    c = BinanceConnection()
    positions = c.get_positions()                       # list[dict]
    active = [p for p in positions if abs(float(p.get('positionAmt', 0))) > 0]
    data = {'agent': 'YUNA', 'active': [], 'total_pnl': 0.0, 'total_margin': 0.0}
    for p in active:
        amt = float(p['positionAmt'])
        entry = float(p.get('entryPrice', 0))
        mark = float(p.get('markPrice', 0))
        pnl = float(p.get('unRealizedProfit', 0))
        lev = float(p.get('leverage', 1)) or 1
        margin = abs(amt * mark) / lev
        data['active'].append({
            'symbol': p['symbol'].replace('USDT', ''),
            'direction': 'LONG' if amt > 0 else 'SHORT',
            'entry': round(entry, 8),
            'mark': round(mark, 8),
            'pnl': round(pnl, 2),
            'margin': round(margin, 2),
            'roe': round(pnl / margin * 100, 2) if margin > 0 else 0.0,
            'size': abs(amt),
            'leverage': round(lev),
        })
        data['total_pnl'] += pnl
        data['total_margin'] += margin
    # Get balance (get_balance returns float, not dict)
    try:
        bal = c.get_balance()
        data['balance'] = round(float(bal) if bal else 0, 2)
    except Exception:
        data['balance'] = 0
    return data
```

**Key field reference per position dict:**

| Field | Type | Notes |
|---|---|---|
| `symbol` | str | e.g. `BTCUSDT` (suffix NOT stripped in raw API; strip in display layer) |
| `positionAmt` | str (numeric) | signed; positive = LONG, negative = SHORT |
| `entryPrice` | str (numeric) | avg entry across the position |
| `markPrice` | str (numeric) | current mark (used for uPnL) |
| `unRealizedProfit` | str (numeric) | uPnL in USDT |
| `leverage` | str (numeric) | current leverage — NOT max, but the position's current setting |
| `initialMargin` | str (numeric) | margin posted for the position (notional / leverage) |

## Environment: how `BinanceConnection` finds keys

```python
# From config/connection.py:_load_keys()
mainnet_file = Path.home() / "dozero" / "config" / ".mainnet_keys"
testnet_file = Path.home() / "dozero" / "config" / ".testnet_keys"
```

**Both files MUST exist relative to `Path.home()`.** The real keys are at
`/home/ubuntu/dozero/config/.{testnet,mainnet}_keys`. From the YUNA profile,
`Path.home()` resolves to the nested path
`/home/ubuntu/.hermes/profiles/yuna/home/dozero/config/` — which does NOT exist.
So calling any `BinanceConnection()` method from a YUNA shell fails with:

```
No valid API keys file found
API error [401] -2014: API-key format invalid.
```

**Fix:** prefix `HOME=/home/ubuntu` on every dozero script invocation from YUNA:
```bash
HOME=/home/ubuntu python3 /home/ubuntu/dozero/send_pnl.py yuna
```

This is the same root cause as the cron-script-nested-path bug
(pitfall #45 in `binance-futures-trading` skill). The fix is identical:
`$HOME` from a YUNA shell is the trap; explicit `HOME=` is the workaround.

## Testnet API gaps (2026-06-16 snapshot)

These endpoints DO NOT WORK on testnet — keep a list so future agents don't loop:

| Endpoint | Testnet | Mainnet | Impact |
|---|---|---|---|
| `GET /fapi/v1/algoOrder` | 400 | OK | Cannot list open SL/TP |
| `GET /fapi/v1/openAlgoOrder` | 404 | OK | Same as above |
| `GET /fapi/v1/allOpenOrders` | 404 | OK | Cannot list across symbols |
| `DELETE /fapi/v1/algoOrder` | 400 | OK | Cannot cancel phantom SL/TP slots |
| `POST /fapi/v1/algoOrder` | -4045 (after limit) | -4045 (recoverable) | Per-symbol stop-order cap |

If you hit -4045 on testnet, the only path is `close_losers` (market reduceOnly).
Do NOT loop on SL placement.

## Versioning note

These quirks were confirmed on 2026-06-16 against dozero commit
pre-`agent_data.py` get_balance fix. If `connection.py` is refactored to return
dict consistently, this file should be updated.
