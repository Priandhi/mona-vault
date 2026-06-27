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
| -4045 | **Reach max stop order limit** | Reduce SL/TP order count per symbol — see SL/TP Limit section below |
| -2021 | Order would immediately trigger | Widen SL/TP price or skip — see SL Retry Logic section below |

## 🚨 SL/TP Order Limit & Emergency Close (CRITICAL — Hexa post-mortem 2026-06-16)

**Problem:** On 2026-06-16, Dozero.X placed SL + TP1 + TP2 + TP3 + Main TP (5 stop orders per symbol). All FAILED with `-4045: Reach max stop order limit`. Result: 3 positions (BANK/INX/AR) ran unprotected, hit -256% / -110% / -85% ROE.

**Key fact:** Binance testnet has very low per-symbol stop order limits (~2-3). Mainnet has higher but still capped (usually 10-20 per symbol). New symbols often have even lower limits.

### Rules

1. **Place 1 SL + 1 Main TP only.** Use TP2 (2R) as Main TP target — conservative, fewer orders.
2. **If SL fails after 3 attempts → EMERGENCY CLOSE position via market order.** Unprotected position = worse than small loss.
3. **Min SL distance 2%** — tight SLs (1-2%) get triggered in 1-2 candles of micro-cap volatility.
4. **Leverage cap by price tier** — micro-caps < $0.10 → 10x max, $0.10-$1 → 15x, $1-$10 → 25x, $10+ → 50x.
5. **Min price $0.05** — dust tokens have wide spreads + manipulation risk.
6. **Max margin $5 per trade** — even with high leverage, this caps absolute loss.

### SL Retry Logic

```python
sl_placed = False
for attempt in range(3):
    sl_order = algo_order(symbol, side, trigger_price=sl_price,
                          order_type="STOP_MARKET", close_position=True)
    if not sl_order.get("_error"):
        sl_placed = True
        break
    if sl_order.get("code") == -4130:
        sl_placed = True  # Already exists = protected
        break
    if sl_order.get("code") == -2021:
        # Widen SL by 1.5x (cap at 8% from entry)
        sl_price = entry * (1 - pct_to_sl * (1.5 ** (attempt + 1)))
        if abs(sl_price - entry) / entry > 0.08:
            break  # Too wide, will emergency close
    # else: try again with new price

if not sl_placed:
    # EMERGENCY: market close the position
    market_order(symbol, close_side, qty, reduce_only=True)
    return  # abort trade
```

### Leverage Tier Table (Dozero implementation, transferable)

| Price Tier | Price Range | Max Leverage | Examples |
|---|---|---|---|
| high | ≥ $10 | 50x | BTC, ETH, SOL, BNB |
| mid | ≥ $1 | 25x | LINK, AVAX, NEAR |
| low | ≥ $0.10 | 15x | ADA, XRP, DOGE |
| dust | < $0.10 | REJECTED | BANK, INX, AR-style micro-caps |

### Real Numbers from 2026-06-16

Without filters:
- BANKUSDT LONG @ 0.0432, SL 0.0424 (1.85%), lev 50x → max loss potential 92% margin
- INXUSDT LONG @ 0.0083, SL 0.0082 (1.20%), lev 50x → max loss potential 60% margin
- All 3 SL/TP placements failed (-4045 spam) → floating loss grew uncontrollably

With new filters:
- BANK (1.85% SL, $0.04) → REJECTED ✅
- INX (1.2% SL, $0.008) → REJECTED ✅
- AR (1.23% SL, $2.12) → REJECTED ✅
- BTC (3% SL, $100k) → PASSED ✅ (high tier 50x)
- ADA (3% SL, $0.50) → PASSED ✅ (low tier 15x)

### Files Updated (Dozero implementation reference)

- `config/settings.py` — added LEVERAGE_TIERS, MIN_PRICE_USD, MIN_SL_DISTANCE_PCT, MAX_SL_DISTANCE_PCT, MIN_VOLUME_USDT ($2M)
- `engine/risk.py` — `build_trade_plan()` with 3 new filter checks + `_get_leverage_cap_for_price()` helper
- `engine/executor.py` — 1 SL + 1 Main TP only, SL retry with widen, `_emergency_close()` for SL failure
- `config/connection.py` — added `market_order()` for emergency close
- `engine/core.py` — pass `current_price` to `build_trade_plan()` for tier filter

### Detailed Post-Mortem & Test Suite

- **Full reproduction recipe + tier table + Dozero file diffs:** `references/sl-tp-order-limit.md`
- **Re-runnable verification test suite** (40+ assertions, covers config + filters + incident signals): `scripts/sl_tp_filter_test.py`
  ```bash
  python3 scripts/sl_tp_filter_test.py          # Run anywhere
  python3 scripts/sl_tp_filter_test.py --verbose  # Show passing tests too
  ```
  Run after ANY change to `config/settings.py`, `engine/risk.py`, or `engine/executor.py` to catch regressions.
- **Dozero connection API return-type quirks** (`BinanceConnection.get_balance()` returns float, `get_positions()` returns raw list, `Path.home()` key-loading trap): `references/dozero-connection-quirks.md`

## 🚑 Emergency Recovery: Unprotected Positions (Hexa 2026-06-16)

**Different scenario than the SL/TP design above.** The rules above prevent NEW unprotected positions. This section covers recovery when you discover EXISTING positions are unprotected (e.g. after a bug, after restart, after a failed batch).

**Diagnostic: count `-4045` errors in logs.**
```bash
grep -c "Reach max stop order limit" /home/ubuntu/dozero/logs/auto.log
# 0   = clean
# > 0 = at least one SL/TP placement failed historically
```

**Try to place a fresh SL on each unprotected position (script in `scripts/emergency_sl_placement.py`).** It will fail with `-4045` if the per-symbol limit is exhausted.

### Why you cannot recover by retrying on testnet

Testnet has severe endpoint gaps. The following endpoints all return errors that make recovery impossible:

| Endpoint | Testnet response | Effect |
|---|---|---|
| `GET /fapi/v1/algoOrder` (list open algo orders) | `400` | Cannot see existing algo orders |
| `GET /fapi/v1/openAlgoOrder` | `404` | Endpoint does not exist |
| `GET /fapi/v1/allOpenOrders` | `404` | Cannot list across symbols |
| `DELETE /fapi/v1/algoOrder` (cancel algo) | `400` | Cannot cancel phantom orders |
| `POST /fapi/v1/algoOrder` (place new SL) | `-4045` | Per-symbol limit exhausted |

**Bottom line:** once `-4045` fires for a symbol on testnet, you cannot query, cancel, or add orders for that symbol. The slot is "phantom-locked" until the position is closed (and even then, it sometimes persists — log shows `-4045` after position close too).

### Recovery procedure

1. **Snapshot current positions** via `/fapi/v2/positionRisk`.
2. **Classify each by uPnL:**
   - **Winners (`uPnL > 0`)** — leave alone, hope for continued profit.
   - **Losers (`uPnL < 0`)** — close via market order with `reduceOnly: true`.
3. **Accept the realized loss.** Testnet doesn't auto-liquidate, so floating loss can grow to -256% ROE. In mainnet those would already be MC. Realized loss is a controlled outcome.
4. **Restart with the new SL/TP design** (1 SL + 1 Main TP only). New positions will not hit the limit.

```python
# Pseudocode for emergency_close_losers()
positions = api.position_risk()
for p in positions:
    if abs(float(p['positionAmt'])) == 0: continue
    upnl = float(p['unRealizedProfit'])
    if upnl >= 0:
        continue  # keep winners
    side = 'SELL' if float(p['positionAmt']) > 0 else 'BUY'
    qty = abs(float(p['positionAmt']))
    api.market_order(symbol=p['symbol'], side=side, quantity=qty, reduce_only=True)
```

**Reference script:** `scripts/emergency_sl_placement.py` (tries SL first, falls back to losers-close pattern if all SL fail). `scripts/close_losers.py` (skip-SL, just close losers).

### Pitfall: don't waste cycles retrying SL on testnet

If `emergency_sl_placement.py` returns `0 placed | 10 failed` with all `-4045`, the only path forward is closing losers. Telling the user "SL gagal semua" and offering the close-losers option is the correct response. Do NOT loop, do NOT try creative workarounds — the testnet API simply does not support recovery.

### Mainnet caveat

Mainnet has the same `-4045` error but DOES support cancel via `DELETE /fapi/v1/algoOrder` with `algoId`. If mainnet shows `-4045`, the recovery path is:
1. List open algo orders via `GET /fapi/v1/openAlgoOrder` (works on mainnet)
2. Cancel redundant/old ones with `algoId`
3. Place fresh SL on unprotected positions

So `-4045` on mainnet is recoverable; on testnet it is not.

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

## Telegram Report Format (PROJECT VIOLET) — HEXA PREFERENCE

**MANDATORY for Hexa:** When sending PNL / position snapshots to Telegram, use the exact layout below. This was corrected 3+ times in session — do NOT improvise the format.

**Top-level structure:**
```
📊 PROJECT VIOLET — POSISI & PNL
🕒 2026-06-16 14:35 WIB

━━━ BTCUSDT ━━━
Pair    : BTCUSDT
Side    : LONG
Size    : 0.0030 BTC
Entry   : 105,250.50
Mark    : 105,418.20
Lev     : 50x
Margin  : $6.32
PnL     : +$0.50 🟢
ROI     : +7.91%

━━━ ETHUSDT ━━━
...

━━━━━━
💰 TOTAL PnL  : +$3.42 🟢
📊 TOTAL ROI  : +2.18%
💼 Wallet     : $4,272.42 USDT
🎯 Margin used: $12.64 (0.3%)
```

**Rules:**
- **Title:** `📊 PROJECT VIOLET — POSISI & PNL` (always uppercase, always this name — project was renamed from Dozero 2026-06-16)
- **Time:** `🕒 YYYY-MM-DD HH:MM WIB` immediately after title
- **Per-symbol header:** `━━━ SYMBOL ━━━` (3 box-drawing char each side, NOT `===`, NOT `<b>`, NOT markdown `##`)
- **Field labels:** exactly `Pair / Side / Size / Entry / Mark / Lev / Margin / PnL / ROI` — spelled this way, with 1 space after the colon
- **Field alignment:** spaces, not tabs. Labels are left-aligned, values follow. Readability over width.
- **Emoji inline on PnL/ROI values only:** `+$0.50 🟢` or `-$25.75 🔴`
- **Summary footer:** `━━━━━━` (6 box-drawing chars) then summary fields with `💰 / 📊 / 💼 / 🎯` emojis
- **NO markdown:** no `**bold**`, no `<b>`, no `<pre>`, no `##` headers. Telegram's `parse_mode=""` is REQUIRED.
- **Project name in title:** always "PROJECT VIOLET" (never "Dozero", "Dozero.X", "DOZERO", or "dozero" — internal codename is deprecated for user-facing output)

**Reusable script:** `scripts/yuna_format.py` — `format_for_telegram(snapshots: list) -> str` returns the exact string above. Just import + call. This is the approved path — do NOT hand-format in agent reply.

**PITFALL: User explicitly rejected these formats:**
- ❌ Markdown bold `**Entry:** $1.2484` — renders as literal asterisks
- ❌ HTML `<b>Entry</b>` — looks messy, user: "knp pake html"
- ❌ `<pre>code blocks</pre>` — too wide, "gak enak diliat"
- ❌ Simple 3-field version (Entry/Mark/PnL only) — "kurang detail"
- ❌ JSON dumps — "jelek banget tampilannya"

The rich per-symbol block with full fields is the GOLD STANDARD. Lock it in.

## Soft-Stop Monitor (CRITICAL — backup when SL/TP fails)

**When:** SL/TP algo order placement is structurally impossible (testnet `-4045` lock, exchange outage, repeated `-2021` rejections). Positions sit unprotected and testnet does NOT auto-liquidate, so floating loss can grow to -256% ROE.

**Pattern:** install a cron-based Python monitor that:
1. Polls `/fapi/v2/positionRisk` every 5 minutes
2. Calculates `uPnL / margin` ratio for each open position
3. If ratio < -5% (configurable), closes that position via market reduceOnly
4. Sends a single Telegram alert with what was closed
5. Silent when healthy (no spam)

**Cron registration (no_agent=true):**
```python
# cronjob payload
{
  "name": "yuna-soft-stop",
  "schedule": "*/5 * * * *",     # every 5 min
  "no_agent": true,                # script-only, no LLM
  "script": "yuna_soft_stop.py"    # under scripts/
}
```

**Script structure (`scripts/yuna_soft_stop.py`):**
```python
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path.home() / '.hermes' / 'profiles' / 'yuna' / 'scripts'))
from execution import BinanceFutures  # shared client
from telegram import send_message

THRESHOLD = -0.05  # -5% of margin

async def main():
    client = BinanceFutures()
    positions = await client.get_positions()
    closed = []
    for p in positions:
        amt = float(p['positionAmt'])
        if amt == 0: continue
        margin = float(p['initialMargin'])
        upnl = float(p['unRealizedProfit'])
        if margin == 0: continue
        ratio = upnl / margin
        if ratio < THRESHOLD:
            side = 'SELL' if amt > 0 else 'BUY'
            qty = abs(amt)
            result = await client.market_order(
                symbol=p['symbol'], side=side, quantity=qty, reduce_only=True
            )
            closed.append({
                'symbol': p['symbol'],
                'side': 'LONG' if amt > 0 else 'SHORT',
                'upnl': upnl,
                'ratio': ratio,
                'orderId': result.get('orderId')
            })
    if closed:
        msg = "🚨 SOFT-STOP triggered:\n"
        for c in closed:
            msg += f"  {c['symbol']} {c['side']} closed | uPnL ${c['upnl']:.2f} ({c['ratio']*100:.1f}%)\n"
        send_message(msg)
    # Else: silent. Healthy.
```

**Reusable script:** `scripts/yuna_soft_stop.py` (full implementation, just point at your API keys).

**Installation path warning (YUNA profile):** See pitfall #45. The script MUST live at `/home/ubuntu/.hermes/profiles/yuna/scripts/yuna_soft_stop.py` (absolute path). If you used `~` in a `cp` from a YUNA shell, the file landed at the nested path and cron returns "Script not found" forever. Use absolute paths for installation. Verify with `ls -la /home/ubuntu/.hermes/profiles/yuna/scripts/yuna_soft_stop.py` after install.

**When to install soft-stop:**
- Testnet always (no auto-liquidation) — should be permanent fixture
- Mainnet only as belt-and-suspenders (Binance LIQ handles it, but -5% loss cap is stricter than LIQ)
- During any SL/TP bug investigation

**When to REMOVE soft-stop:** never on testnet, only on mainnet if you want Binance's natural liquidation to take over.

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
41. **Testnet `-4045` is unrecoverable via API** — When `Reach max stop order limit` fires on testnet, you cannot query (`/fapi/v1/algoOrder` 400, `/fapi/v1/openAlgoOrder` 404), cannot cancel (`DELETE /fapi/v1/algoOrder` 400), and cannot add new algo orders. The slot is phantom-locked. **Recovery path on testnet:** close the unprotected position via market reduceOnly. **On mainnet** the same error IS recoverable (cancel via algoId). Do not waste time on testnet retry loops. See "Emergency Recovery: Unprotected Positions" section above.
42. **Use `.py` script files, NOT `python3 -c "..."` for non-trivial logic** — User: "knapa pake python3 -c mulu, knp ga sekalian buat file .py sekalian biar bisa dipake lagi". Inline `python3 -c` blocks waste context tokens (the whole command echoes in output), cannot be re-run, and are easy to typo. Rule of thumb: if the script is more than 5 lines OR will be run more than once, write it to `~/.hermes/profiles/yuna/scripts/<name>.py` and execute it. Inline `python3 -c` is only OK for true one-liner probes (test connectivity, fetch a single value).
43. **Don't regenerate PNL from agent knowledge — call the existing entry point** — When user sends `/pnl`, `/status`, "pnl", "posisi", or "snapshot", the canonical response is `python3 /home/ubuntu/dozero/send_pnl.py yuna`. Do NOT fetch positions yourself, do NOT format by hand, do NOT use `get_positions()` + hand-format. The script handles its own dedup, layout, and Telegram delivery using the approved `telegram-trading-reports` format. Agent answers based on its own API calls are always slightly out of date by the time they're typed.
44. **Soft-stop install = permanent on testnet** — Testnet does not auto-liquidate. Once a position is opened, without SL/TP or a soft-stop monitor, floating loss grows unbounded. Install `yuna_soft_stop.py` cron BEFORE deploying the scanner, not after the first -100% ROE position. Threshold -5% is conservative; tighten to -3% if max margin is $5 and DD budget is $1.
45. **YUNA profile `$HOME` is nested** — In the YUNA Hermes profile, `$HOME` is set to `/home/ubuntu/.hermes/profiles/yuna/home/`. This means `~` in shell commands and `Path.home()` / `os.path.expanduser("~")` in Python resolve to that nested path. Concrete failures:
    - `cp foo ~/.hermes/profiles/yuna/scripts/` lands at `/home/ubuntu/.hermes/profiles/yuna/home/.hermes/profiles/yuna/scripts/foo` (NOT the real `scripts/` dir).
    - `Path.home() / "dozero" / "config" / ".testnet_keys"` resolves to `/home/ubuntu/.hermes/profiles/yuna/home/dozero/config/.testnet_keys` — does not exist, so `BinanceConnection._load_keys()` fails with "No valid API keys file found".
    - **Rule:** always use absolute paths inside the YUNA profile, and prefix `HOME=/home/ubuntu` when calling dozero scripts (`HOME=/home/ubuntu python3 /home/ubuntu/dozero/send_pnl.py yuna`). The default profile does not have this problem.
46. **Cron `script:` field is a bare filename** — `cronjob(action='create', script='yuna_soft_stop.py')` resolves the script under `/home/ubuntu/.hermes/profiles/yuna/scripts/` (the REAL one, not the HOME-nested one). So:
    - The file MUST live at `/home/ubuntu/.hermes/profiles/yuna/scripts/<name>.py` exactly.
    - If you used `cp foo ~/.hermes/profiles/yuna/scripts/` from a YUNA shell, the file landed at the nested path → cron fails with "Script not found" forever.
    - **Rule:** use `cp foo /home/ubuntu/.hermes/profiles/yuna/scripts/` (absolute). Verify with `ls -la /home/ubuntu/.hermes/profiles/yuna/scripts/<name>.py` after install.
47. **Dozero `BinanceConnection.get_balance()` returns `float`, not `dict`** — Unlike Binance's raw `/fapi/v2/account` response (dict with `availableBalance` key), the dozero wrapper in `/home/ubuntu/dozero/config/connection.py` returns a plain float (already extracted). Calling `bal.get('availableBalance', 0)` on it raises `AttributeError`. **Correct usage in any aggregator script (e.g. `agent_data.py`):**
    ```python
    bal = c.get_balance()
    data['balance'] = round(float(bal) if bal else 0, 2)
    ```
    Same shape applies to `get_positions()`: it returns the raw list from `/fapi/v2/positionRisk` (list of dicts with `symbol`, `positionAmt`, `entryPrice`, `markPrice`, `unRealizedProfit`, `leverage`), so `p.get('positionAmt')` and friends work as expected. The asymmetry is only in `get_balance()`.
48. **YUNA profile `.env` lookup is fragile** — `send_pnl.py` resolves bot token via `os.path.expanduser(f'~/.hermes/profiles/{profile_name}/.env')`. From a YUNA shell this expands to the wrong nested path. The script has a fallback to `~/.hermes/.env` which usually saves it, but if you ever see "ERROR: No bot token found", the cause is `$HOME` not the missing key. Workaround: prefix `HOME=/home/ubuntu` (same fix as pitfall #45).
