# Auto SL/TP Manager

## Problem

When placing LIMIT orders, SL/TP cannot be placed immediately because there's no open position yet. The Algo Order API requires an existing position.

## Solution

A background process that:
1. Monitors all open limit orders via `/fapi/v1/order` (check status)
2. When a limit order fills (status=FILLED), automatically places SL/TP via Algo Order API
3. Also checks for unprotected positions and protects them
4. Emergency closes position if SL placement fails

## Implementation (auto_sl_tp_manager.py)

```python
import hmac, time, hashlib, requests, json
from urllib.parse import urlencode
from pathlib import Path

# Load keys from vault
vault = Path.home() / 'mona-workspace' / 'vault'
keys = {}
for line in (vault / '.binance_keys').read_text().strip().splitlines():
    if '=' in line:
        k, v = line.split('=', 1)
        keys[k.strip()] = v.strip()

API_KEY = keys.get('API_KEY', '')
API_SECRET = keys.get('API_SECRET', '')
BASE = 'https://fapi.binance.com'

monitored_orders = {}  # {symbol: {order_id, side, sl, tp1, leverage, qty}}

def signed_params(params):
    params['timestamp'] = int(time.time() * 1000)
    qs = urlencode(params)
    sig = hmac.new(API_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    return qs + '&signature=' + sig

def check_order_filled(symbol, order_id):
    params = {'symbol': symbol, 'orderId': order_id}
    r = requests.get(f'{BASE}/fapi/v1/order?{signed_params(params)}', headers={'X-MBX-APIKEY': API_KEY})
    return r.json().get('status') == 'FILLED'

def place_algo_order(symbol, side, order_type, trigger_price):
    params = {
        'symbol': symbol, 'side': side, 'type': order_type,
        'algoType': 'CONDITIONAL', 'triggerPrice': str(trigger_price),
        'closePosition': 'true', 'workingType': 'MARK_PRICE',
        'timeInForce': 'GTE_GTC',
    }
    r = requests.post(f'{BASE}/fapi/v1/algoOrder?{signed_params(params)}', headers={'X-MBX-APIKEY': API_KEY})
    return r.json()

def monitor_loop():
    while True:
        for symbol in list(monitored_orders.keys()):
            info = monitored_orders[symbol]
            if check_order_filled(symbol, info['order_id']):
                # Place SL
                close_side = 'SELL' if info['side'] == 'BUY' else 'BUY'
                sl_result = place_algo_order(symbol, close_side, 'STOP_MARKET', info['sl'])
                tp_result = place_algo_order(symbol, close_side, 'TAKE_PROFIT_MARKET', info['tp1'])
                
                # Emergency close if SL failed
                if 'algoId' not in sl_result and sl_result.get('code') != -4130:
                    requests.post(f'{BASE}/fapi/v1/order?{signed_params({"symbol": symbol, "side": close_side, "type": "MARKET", "quantity": info['qty'], "reduceOnly": "true"})}', headers={'X-MBX-APIKEY': API_KEY})
                
                del monitored_orders[symbol]
        time.sleep(5)
```

## Key Points

1. **Run as background process** — not a cron job, needs to be always-on
2. **Check every 5 seconds** — fast enough to catch fills quickly
3. **Use Algo Order API** — `/fapi/v1/algoOrder` for SL/TP, NOT `/fapi/v1/order`
4. **-4130 = already protected** — not an error, means SL/TP already exists
5. **Emergency close** — if SL placement fails, immediately market close the position
6. **Persist state** — save `monitored_orders` to JSON file, reload on startup

## State File

Save to `~/.hermes/data/sl_tp_monitor.json`:
```json
{
  "CAKEUSDT": {
    "order_id": 5282079793,
    "side": "BUY",
    "sl": 1.1909,
    "tp1": 1.3059,
    "leverage": 75,
    "qty": 300,
    "added_at": 1780882324.0
  }
}
```

## Critical: State File Race Condition

**Problem:** When the manager is killed (SIGTERM), its signal handler calls `save_state()`. If the in-memory `monitored_orders` dict is empty (e.g., manager just restarted), it overwrites the state file with `{}`, erasing all registered orders.

**Sequence that causes data loss:**
1. Write 3 orders to `sl_tp_monitor.json`
2. Kill old manager → signal handler fires → saves empty `{}` to file
3. New manager starts → reads empty file → 0 orders loaded

**Fix:** Only save state if there are orders:

```python
def signal_handler(sig, frame):
    if monitored_orders:  # DON'T overwrite with empty dict
        save_state()
    sys.exit(0)
```

**Safe restart sequence:**
```bash
pkill -f auto_sl_tp_manager
sleep 2  # wait for clean shutdown
python3 -c "...write orders to file..."  # write AFTER kill
python3 scripts/auto_sl_tp_manager.py &  # start new
```

## Deployment

```bash
# Run in background via Hermes terminal
terminal(command="python3 scripts/auto_sl_tp_manager.py", background=True, notify_on_complete=True)

# Or as a cron job that runs every minute (less ideal)
```

## Files

- `auto_sl_tp_manager.py` — Main auto SL/TP manager (in ~/.hermes/scripts/)
- State: `~/.hermes/data/sl_tp_monitor.json`
- Logs: `~/.hermes/logs/auto_sl_tp.log`
