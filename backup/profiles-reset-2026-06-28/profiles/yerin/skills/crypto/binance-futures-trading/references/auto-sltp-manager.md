# Auto SL/TP Manager for Binance Futures

## Problem

When placing LIMIT orders, SL/TP cannot be placed immediately because there's no open position yet. The Algo Order API requires an existing position.

## Solution

A background process that:
1. Monitors all open limit orders
2. When a limit order fills, automatically places SL/TP
3. Also checks for unprotected positions (no SL/TP) and protects them

## Implementation

```python
class MonaAutoSLTP:
    async def run(self):
        while True:
            try:
                positions = await self.get_positions()
                orders = await self.get_open_orders()
                stop_orders = [o for o in orders if o['type'] in ('STOP_MARKET', 'TAKE_PROFIT_MARKET')]

                for pos in positions:
                    sym = pos['symbol']
                    amt = float(pos['positionAmt'])
                    if amt == 0:
                        continue

                    has_sl = any(o['symbol'] == sym and o['type'] == 'STOP_MARKET' for o in stop_orders)
                    has_tp = any(o['symbol'] == sym and o['type'] == 'TAKE_PROFIT_MARKET' for o in stop_orders)

                    if has_sl and has_tp:
                        continue

                    entry = float(pos['entryPrice'])
                    qty = abs(amt)
                    direction = 'LONG' if amt > 0 else 'SHORT'

                    # Place SL/TP
                    if not has_sl:
                        sl_price = entry * 0.97 if direction == 'LONG' else entry * 1.03
                        await self.place_sl(sym, 'SELL' if direction == 'LONG' else 'BUY', sl_price, qty)

                    if not has_tp:
                        tp_price = entry * 1.03 if direction == 'LONG' else entry * 0.97
                        await self.place_tp(sym, 'SELL' if direction == 'LONG' else 'BUY', tp_price, qty)

                await asyncio.sleep(10)
            except Exception as e:
                log.error(f"Error: {e}")
                await asyncio.sleep(15)
```

## Key Points

1. **Run as background process** — not a cron job, needs to be always-on
2. **Check every 10 seconds** — fast enough to catch fills quickly
3. **SL at -3%, TP at +3%** — default values, can be customized per signal
4. **Also check unprotected positions** — catches positions that lost their SL/TP

## Deployment

```bash
# Run in background
python3 mona_auto_sltp.py &

# Or as a systemd service
# Or as a cron job that runs every minute (less ideal)
```

## Files

- `mona_auto_sltp.py` — Main auto SL/TP manager

## State File Race Condition (CRITICAL — learned 2026-06-08)

**Problem:** When the manager is killed (SIGTERM), its signal handler calls `save_state()`. If in-memory `monitored_orders` is empty (e.g., manager just restarted and hasn't loaded the file yet), it overwrites the state file with `{}`, erasing all registered orders.

**Sequence that causes data loss:**
1. Write orders to `sl_tp_monitor.json`
2. Kill old manager → signal handler fires → saves empty `{}` to file
3. New manager starts → reads empty file → 0 orders loaded

**Fix in signal handler:**
```python
def signal_handler(sig, frame):
    if monitored_orders:  # DON'T overwrite with empty dict
        save_state()
    sys.exit(0)
```

**Safe restart sequence:**
```bash
pkill -f auto_sl_tp_manager
sleep 2  # wait for clean shutdown (old process writes empty)
python3 -c "...write orders to sl_tp_monitor.json..."  # write AFTER kill
python3 scripts/auto_sl_tp_manager.py &  # start new (reads non-empty file)
```
