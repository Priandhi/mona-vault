---
name: binance-futures-trading
description: "Binance Futures USDT-M trading via REST API — order placement, algo orders (SL/TP), position management, safety mechanisms, leverage auto-detect. Hard-won lessons from real-money trading."
triggers:
  - "binance futures"
  - "futures trading"
  - "stop loss placement"
  - "take profit"
  - "algo order"
  - "leverage"
  - "position management"
  - "fapi"
---

# Binance Futures Trading

## Critical: Algo Orders vs Regular Orders

Binance migrated STOP_MARKET, TAKE_PROFIT_MARKET, STOP, and TAKE_PROFIT order types to the **Algo Order API**. Placing them via `/fapi/v1/order` returns error **-4120**.

### Correct endpoint for SL/TP

```
POST /fapi/v1/algoOrder
```

**Required params:**
```python
{
    'algoType': 'CONDITIONAL',
    'symbol': 'BTCUSDT',
    'side': 'SELL',          # Opposite of position
    'type': 'STOP_MARKET',   # or TAKE_PROFIT_MARKET
    'triggerPrice': '50000', # Trigger price
    'closePosition': 'true', # Closes entire position
    'workingType': 'MARK_PRICE',
    'timeInForce': 'GTE_GTC',
}
```

**Response on success:**
```json
{
    "algoId": 3000001775501555,
    "algoStatus": "NEW",
    "symbol": "BTCUSDT",
    "side": "SELL",
    "orderType": "STOP_MARKET",
    "triggerPrice": "50000.0000000",
    "closePosition": true,
    ...
}
```

**Response if already exists:**
```json
{
    "code": -4130,
    "msg": "An open stop or take profit order with GTE and closePosition in the direction is existing."
}
```
This is NOT an error — it means SL/TP is already protected.

### PITFALL: Algo orders invisible in openOrders

`/fapi/v1/openOrders` only shows **regular orders**. Algo orders (SL/TP) are **NOT listed there**. To verify algo orders exist, you must track the `algoId` from placement response, or attempt to place a duplicate and check for -4130.

### Wrong endpoints (return -4120)

```
❌ POST /fapi/v1/order  with type=STOP_MARKET
❌ POST /fapi/v1/order  with type=TAKE_PROFIT_MARKET
❌ POST /fapi/v1/order  with type=STOP + stopPrice
❌ POST /fapi/v1/order  with type=TAKE_PROFIT + stopPrice
❌ POST /fapi/v1/order  with type=TRAILING_STOP_MARKET
```

All of these return: `"Order type not supported for this endpoint. Please use the Algo Order API endpoints instead."`

### Regular orders (still work on /fapi/v1/order)

```
✅ POST /fapi/v1/order  with type=MARKET
✅ POST /fapi/v1/order  with type=LIMIT
```

## Leverage Rule: ALWAYS USE MAX

**USER PREFERENCE (MANDATORY):** Always use the MAX leverage allowed per token. Never assume, never hardcode — always fetch from Binance.

**PITFALL:** `exchangeInfo` does NOT contain leverage info. There is no `leverageFilter` field. Use the **leverage bracket** endpoint instead:

```python
# ✅ CORRECT — fetch max leverage from leverage bracket
import hmac, time, hashlib, requests
from urllib.parse import urlencode

def get_max_leverage(symbol, api_key, api_secret):
    params = {'timestamp': int(time.time() * 1000)}
    qs = urlencode(params)
    sig = hmac.new(api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    headers = {'X-MBX-APIKEY': api_key}
    r = requests.get(f'https://fapi.binance.com/fapi/v1/leverageBracket?{qs}&signature={sig}', headers=headers)
    for item in r.json():
        if item.get('symbol') == symbol:
            return item['brackets'][0]['initialLeverage']  # First bracket = highest leverage
    return None

# Then set it
max_lev = get_max_leverage(symbol, API_KEY, API_SECRET)
requests.post(f'{BASE}/fapi/v1/leverage', params={'symbol': symbol, 'leverage': max_lev}, headers=headers)
```

```python
# ❌ WRONG — exchangeInfo has no leverage data
exchange = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo").json()
for sym_info in exchange['symbols']:
    if sym_info['symbol'] == symbol:
        max_lev = int(sym_info['leverageFilter']['maxLeverage'])  # KeyError!
```

**Actual max leverages (from leverageBracket):**
- BTCUSDT → 125x
- ETHUSDT → 100x
- CAKEUSDT → 75x (NOT 10x!)
- SOLUSDT → 50x
- Most altcoins → 25-75x

**Margin is ALWAYS $5 per trade** (unless user specifies otherwise).
**Position sizing formula:** `qty = (margin × max_leverage) / entry_price`

> See `references/leverage-bracket-api.md` for full endpoint docs and response format.

## Position Verification After Entry

**ALWAYS verify** position exists on Binance after placing market order. Don't trust the order response alone.

```python
# After market_order()
await asyncio.sleep(1)
positions = await execution.get_positions()
real_qty = sum(float(p['positionAmt']) for p in positions if p['symbol'] == symbol)
if abs(real_qty) < abs(expected_qty) * 0.5:
    # Position not confirmed — handle error
    log.error(f"ENTRY VERIFY FAILED: expected {expected_qty} but got {real_qty}")
```

## Safety Mechanisms (MANDATORY for autonomous trading)

### 1. Per-pair cooldown
Minimum 5 minutes between trades on the same pair. Prevents rapid flipping.

### 2. Flip prevention
Minimum 10 minutes before reversing direction (LONG→SHORT or vice versa) on the same pair.

### 3. Hourly trade limit
Max 4 trades per hour across all pairs. Prevents overtrading.

### 4. Max simultaneous positions
Typically 2-3. Check before opening new positions.

### 5. Minimum balance check
Don't trade if balance < $40 (or appropriate threshold). Refresh balance from Binance API before each trade.

### 6. SL/TP verification loop
Every monitoring cycle, verify all open positions have SL/TP algo orders. If missing, place them. If placement fails, emergency-close the position.

### 7. Emergency close
If SL placement fails after entry, immediately close the position with a market order. An unprotected position is worse than a small loss.

### 8. Daily loss limit
Track cumulative daily PnL. Pause trading if daily loss exceeds threshold (e.g., $3 on $55 balance).

## Binance API Keys Location

**Keys are stored in `~/mona-workspace/vault/.binance_keys`** (NOT in `.env`).

Format:
```
API_KEY=AdnUH7...DvcE
API_SECRET=w8GG6m...CxfB
```

Load them like:
```python
from pathlib import Path
keys_file = Path.home() / 'mona-workspace' / 'vault' / '.binance_keys'
keys = {}
for line in keys_file.read_text().strip().split('\n'):
    if '=' in line:
        k, v = line.split('=', 1)
        keys[k.strip()] = v.strip()
API_KEY = keys['API_KEY']
API_SECRET = keys['API_SECRET']
```

**Pitfall:** Do NOT look for Binance keys in `~/.hermes/.env` — they are not there. User got frustrated when agent kept saying "no API keys found" ("lu udah ku kasih apikey jirr"). Always check vault first.

## Signing Requests

```python
import hmac, hashlib, time
from urllib.parse import urlencode

def signed_request(params, secret):
    params['timestamp'] = str(int(time.time() * 1000))
    # All values must be strings
    for k in params:
        params[k] = str(params[k])
    query = '&'.join(f'{k}={params[k]}' for k in sorted(params))
    sig = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    params['signature'] = sig
    return params
```

## Common Error Codes

| Code | Meaning | Fix |
|------|---------|-----|
| -4120 | Order type not supported on this endpoint | Use `/fapi/v1/algoOrder` for SL/TP |
| -4130 | Duplicate SL/TP exists | Not an error — position is protected |
| -4028 | ReduceOnly order rejected | Position already closed or direction wrong |
| -2022 | ReduceOnly Order rejected | Same as above |
| -4509 | TIF GTE needs open positions | Position may have been closed/flipped |

## Async Rounding (CRITICAL)

`_round_qty` and `_round_price` MUST be async. Using `urllib.request` (sync) inside an async event loop **blocks the entire loop** while waiting for Binance API. This causes timeouts and missed entries.

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

**Cache step/tick sizes** — they rarely change. Fetch once per symbol, store in dict.

## Breakeven SL After TP1

When TP1 hits, move SL to entry + small buffer (0.1 ATR). This locks profit and removes risk:

```python
if hit_tp1:
    # Move SL to breakeven
    breakeven_atr = atr * 0.1
    if pos.side == 'LONG':
        new_sl = max(pos.sl_price, pos.entry_price + breakeven_atr)
    else:
        new_sl = min(pos.sl_price, pos.entry_price - breakeven_atr)
    pos.sl_price = new_sl
```

## Retry Logic for Order Placement

SL/TP placement can fail transiently (network, rate limit). Retry 3x with exponential backoff:

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
```

## Limit Order Entry (avoid slippage)

User preference: "limit order jangan nabrak" — ALWAYS use limit orders for entry, NOT market orders.

**CRITICAL: NEVER place limit at/near market price!** A limit order at market price fills instantly like a market order but charges TAKER fee (0.04%) instead of MAKER fee (0.02%). This costs 2× the fee for zero benefit.

```python
# ❌ WRONG — limit at market = instant taker fill with taker fee
entry_price = await exec_eng._round_price(symbol, price)

# ✅ CORRECT — offset limit from market to get MAKER fee
# Method 1: Fixed ATR offset (best for volatile pairs)
offset = atr * 0.003  # 0.3% of ATR below market for LONG
if side == 'LONG':
    entry_price = await exec_eng._round_price(symbol, price - offset)
else:
    entry_price = await exec_eng._round_price(symbol, price + offset)

# Method 2: Orderbook-based (best for tight spreads)
book = await data.get_orderbook(symbol, 5)
if side == 'LONG':
    best_bid = float(book['bids'][0][0])
    entry_price = await exec_eng._round_price(symbol, best_bid)
else:
    best_ask = float(book['asks'][0][0])
    entry_price = await exec_eng._round_price(symbol, best_ask)

result = await exec_eng.limit_order(symbol, 'BUY', qty, entry_price)
```

**If limit doesn't fill within 60s, cancel it.** Don't chase — wait for next scan cycle.

**PITFALL: SL/TP placement AFTER limit order fill.** Unlike market orders (instant fill), limit orders may not fill immediately. Algo Order API for SL/TP requires an OPEN POSITION. Flow:

1. Place limit order → returns `status: 'NEW'` (pending)
2. Wait / poll `get_positions()` until position appears
3. THEN place SL/TP via algo orders

```python
# After limit order placed
entry_result = await exec_eng.limit_order(symbol, side, qty, entry_price)
# Poll for fill
for _ in range(30):  # 30 attempts, 2s each = 60s max
    positions = await exec_eng.get_positions()
    filled = any(p['symbol'] == symbol for p in positions)
    if filled:
        break
    await asyncio.sleep(2)
# NOW place SL/TP
if filled:
    sl_result = await exec_eng.stop_market(symbol, close_side, qty, sl)
    tp_result = await exec_eng.take_profit_market(symbol, close_side, qty, tp1)
```

**PITFALL: Limit order error ≠ failure.** Binance may return error-like JSON even when the order succeeds. ALWAYS verify via `get_positions()` API, not by checking the order response.

## Margin Cap for Position Sizing

When ATR-based SL is tight (e.g., BNB ATR $2.33 on $596 price = 0.39%), the risk formula produces a huge position:
- risk $4 / 0.0039 = $1,025 position
- With $55 balance at 20x, max notional = $1,100
- Margin needed = $1,025 / 20 = $51.25 → leaves $4 free margin → **margin insufficient**

**Fix: Cap at 85% of max notional:**
```python
max_notional = balance * leverage * 0.85  # leave 15% buffer
size_usdt = min(risk_based_size, max_notional)
```

This ensures enough margin remains for the position + SL/TP algo orders.

## Risk Communication: Use Absolute Dollars

User prefers absolute dollar amounts for risk, NOT percentages. Instead of "7.5% risk", say "$4 per trade". Communicate:
```
Risk: $4.01 (not "7.5% of $55.37")
```

## Leverage & Margin Summary

**Simple rule:** MAX leverage per token, $5 margin per trade. See "Leverage Rule: ALWAYS USE MAX" above for implementation.

**Risk communication:** Always use absolute dollar amounts, NOT percentages.
```
✅ "Risk: $4.01"
❌ "Risk: 7.5% of $55.37"
```

## Signal Format: Plain Text (NO markdown)

When sending signals to Telegram, use **plain text only** — no `**bold**`, no markdown. Telegram's `parse_mode=""` renders markdown as literal `**text**` which looks ugly.

```
❌ Entry: $1.2484        ← shows as **Entry:** $1.2484 in Telegram
✅ Entry: $1.2484        ← clean plain text
```

Use Unicode box-drawing characters (━━━) for visual separation instead of markdown headers.

## PITFALLS

1. **Don't log "SL PLACED" from engine logs and trust it** — always verify via API (-4130 check or algoId tracking)
2. **Position can flip between SL placement attempts** — check current position direction before placing SL
3. **closePosition=true** on algo orders means qty=0 in the request — the exchange handles the full close
4. **Market orders with reduceOnly=true** can fail if position already closed by SL/TP algo order
5. **Balance can be $0 due to transfers** — always check /fapi/v2/balance before assuming trading balance
6. **Sync urllib blocks async event loop** — use aiohttp for all HTTP calls in async context
7. **Config fields defined twice** — Python dataclass silently overwrites; check for duplicates
22. **Margin MAX $5 per position** — NEVER exceed $5 margin per trade. This is a hard rule. User: "margin max 5$ per posisi". Calculate: `qty = ($5 × max_leverage) / entry_price`. Even with high leverage, margin stays at $5.
23. **Scanner must send signals directly, not via LLM agent** — When deploying signal scanners as cron jobs, set `no_agent: true` and have the script call `send_message()` directly. LLM agents truncate/reformat signal data, losing prices and details. Use `parse_mode=""` for plain text delivery.
24. **Signal dedup: per TOKEN, not per direction** — When deduplicating signals, use `symbol` as key (e.g. `ETHUSDT`), NOT `symbol_direction` (e.g. `ETHUSDT_LONG`). Otherwise the same token can appear twice (once LONG, once SHORT) in the same scan. Cooldown: 24 hours per token.
25. **Python in bash heredoc: write to temp file first** — Writing Python with dict key access (`keys['API_KEY']`) inside a bash heredoc (`<< 'PYEOF'`) causes syntax errors because single quotes conflict with the heredoc delimiter. Write the script to `/tmp/script.py` first, then execute with `python3 /tmp/script.py`.
26. **High-volatility altcoins lose money in backtests** — ZECUSDT (-10.2%, PF 0.78) and HYPEUSDT (-17.4%, PF 0.72) over 30-day backtest. Filter: skip pairs with ATR% > 3% of price, or regime = HIGH_VOLATILITY. Stick to top 10 by 24h volume.
27. **Backtest before trusting a strategy** — Always run `mona_backtest.py` on historical data before going live. Backtest on BTC/SOL (profitable, PF > 1.3) not on random altcoins. Win rate alone is meaningless — Profit Factor (PF) and Max Drawdown matter more.
28. **NEVER use market order when user says limit order** — User said "pasang limit order" for MANTA, Mona placed MARKET ORDER instead. User caught it: "kok lu gak pasang limit order bos kenapa langsung nabrak😭". When user specifies "limit order", ALWAYS use LIMIT order type, NEVER MARKET. If user says "gas" or "langsung", THEN use market. When in doubt, ASK.
29. **Verify orders exist after placing** — After placing ANY order (limit or market), ALWAYS verify it exists via API. Don't just trust the response. Check `/fapi/v1/openOrders` for limit orders, `/fapi/v2/positionRisk` for positions. User caught Mona claiming "LIMIT ORDER PLACED" when no order existed on Binance.
30. **NEVER claim "udah dipasang" without actual execution** — Mona kept saying "SUDAH DIPASANG! ✅" when it hadn't actually executed anything. User: "jadi jangan bilang udah di pasang kalau belum eksekusi lu belum nglakuin apapun tadi". ALWAYS execute FIRST, verify via API, THEN report success.
31. **Check for duplicate orders before placing** — Before placing a new order, check `/fapi/v1/openOrders` for existing orders on the same symbol. If a duplicate exists, cancel it first or ask user. Don't leave multiple orders that could both fill.
32. **Signal quality over quantity** — User wants 1-3 top signals, NOT 25 signals at once. User: "kan aku bilang kasih 1-3 sinyal aja yang potensi🥲". When scanning, filter to top 1-3 by score/confidence, don't dump everything.
33. **Route trading signals to correct Telegram topic** — Trading signals go to topic 387 (📈 Futures Trading), NOT to DM/home channel. Verify `deliver` target in cron jobs is `telegram:-1003899936547:387`.
34. **Don't apologize, just work** — User hates excuses and apologies. When you make a mistake, acknowledge it ONCE briefly, then immediately fix it and move on. No repeated sorries, no lengthy explanations.
35. **NEVER open-close-reopen positions** — Costs real money in taker fees + slippage. If position size is wrong, adjust SL/TP on existing position, or wait for it to hit SL/TP naturally. Don't close and re-enter.
36. **Auto SL/TP manager: don't overwrite state on shutdown** — Signal handler must check `if monitored_orders:` before calling `save_state()`. Otherwise killing the manager overwrites the state file with `{}`, erasing all registered orders. See `references/auto-sltp-manager.md` in crypto-signal-scanner for full race condition details.
37. **Python heredoc: write to temp file first** — Writing Python with dict key access (`keys['API_KEY']`) inside a bash heredoc (`<< 'PYEOF'`) causes syntax errors because single quotes conflict. Write script to `/tmp/script.py` first, then execute with `python3 /tmp/script.py`.
38. **ALL report-type cron jobs must be no_agent=true** — Market context, news, onchain, dashboard, daily reports — ALL must use `no_agent: true` with `script` field pointing to the Python script. LLM agents truncate/reformat signal data, losing prices and details. Pattern: `cronjob(action='update', job_id=..., no_agent=True, script='mona_xxx.py')`. This is the SAME lesson as pitfall #23 (scanner) but applies to ALL report scripts, not just scanners.
39. **Cron jobs scheduled at `0 */N * * *` only fire at top of hour** — A job scheduled `0 */6 * * *` at 10:35 won't fire until 12:00. If you need immediate first run, use `cronjob(action='run', job_id=...)` after creating/updating the job. The `next_run_at` shows when the next automatic run occurs.
40. **User is protective of built projects** — When doing VPS cleanup, ALWAYS explain what each file/project is and ask before deleting. User: "takut ada yang miss jelaskan dulu". Never assume a project is "old" or "unused" without checking. Projects like `freellmapi`, `FinceptTerminal`, `TradingAgents`, `mona/` (old Node.js) were built by user — explain, then ask, then delete only after confirmation.
