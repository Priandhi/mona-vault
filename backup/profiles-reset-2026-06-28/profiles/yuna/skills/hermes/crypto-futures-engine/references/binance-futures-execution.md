# Binance Futures Execution — Field Notes

Battle-tested patterns from PROJECT VIOLET v2 (Jun 2026) — YUNA's algo-based perpetual futures engine. All paths below reference the engine at `/home/ubuntu/project-violet/`.

## 1. The algo API pattern (LIMIT entry + pre-placed SL/TP)

**Problem:** `STOP_MARKET` / `TAKE_PROFIT_MARKET` with `reduceOnly=true` on `/fapi/v1/order` returns `HTTP 400: -4120 Order type not supported for this endpoint. Please use the Algo Order API endpoints instead.` AND requires a position to exist. You can't pre-place protective orders before entry fills.

**Solution:** Use the algo endpoint. It accepts orders WITHOUT an existing position — they sit as `algoStatus: NEW` and activate when both (a) a position exists and (b) the trigger price is hit.

```python
# Pre-place: 1 LIMIT entry + 1 SL + N TPs — all without position
POST /fapi/v1/algoOrder
{
  "algoType": "CONDITIONAL",     # ← the magic
  "type": "STOP_MARKET",          # or "TAKE_PROFIT_MARKET"
  "symbol": "BTCUSDT",
  "side": "SELL",                 # opposite of position side
  "quantity": 0.002,
  "triggerPrice": "58000",
  "workingType": "MARK_PRICE",    # or CONTRACT_PRICE
  "reduceOnly": "true",
}
# Returns: {"algoId": 1000000113387546, "algoStatus": "NEW", ...}
# Cancel:  DELETE /fapi/v1/algoOrder?algoId=1000000113387546
```

Probe endpoint availability with these candidate paths and look for the one whose GET returns 200 (not `-5000 Path not found`):
- `/fapi/v1/algoOrder` ← testnet/mainnet, the real one
- `/fapi/v1/order/algo` ← docs sometimes show this, often 404
- `/fapi/v1/algo/futures/newOrder` ← rare
- `/fapi/v1/conditional/order` ← 404

**One-way vs hedge mode:** If account is in one-way mode, OMIT `positionSide` from the algo payload. Specifying `LONG`/`SHORT` returns `-4061: Order's position side does not match user's setting`. The response will echo `"positionSide": "BOTH"` by default.

## 2. Quantity precision — the silent killer

**Symptom:** All order placements fail with `HTTP 400: -1111 Precision is over the maximum defined for this asset` even though the symbol exists and balance is fine.

**Root cause:** Each symbol has a `stepSize` filter (LOT_SIZE) that defines the valid qty increments. `round(qty, 6)` produces 6 decimal places; BTCUSDT stepSize is 0.0001 (4 decimals), SOLUSDT is 0.01 (2 decimals), SHIB1000USDT is 1 (0 decimals). Code that hardcodes round-to-6 will reject on most symbols.

**Fix:** Query `GET /fapi/v1/exchangeInfo` once, cache by symbol, then floor qty to step boundary.

```python
import math
from urllib.request import urlopen
import json

_CACHE = {}
def get_symbol_info(symbol):
    if symbol in _CACHE: return _CACHE[symbol]
    data = json.loads(urlopen('https://testnet.binancefuture.com/fapi/v1/exchangeInfo', timeout=10).read())
    for s in data['symbols']:
        if s['symbol'] == symbol:
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    info = {
                        'stepSize': float(f['stepSize']),
                        'minQty': float(f['minQty']),
                        'maxQty': float(f['maxQty']),
                    }
                    _CACHE[symbol] = info
                    return info

def round_qty(qty, step_size):
    if step_size <= 0: return qty
    precision = len(str(step_size).rstrip('0').split('.')[-1])
    return round(math.floor(qty / step_size) * step_size, precision)
```

Apply inside `place_order` BEFORE signing. Also floor prices to `tickSize` (2 decimals is usually safe for crypto).

## 3. Capturing the real API error

`urllib.error.HTTPError` is the wrong tool for "log the response body". The body lives in `e.read()`, not `str(e)`. Logging `str(e)` gives you `HTTP Error 400: Bad Request` — useless. The actual error code and message (e.g. `-1111: Precision is over the maximum defined for this asset`) are in the body.

```python
from urllib.error import HTTPError
try:
    resp = urlopen(req, timeout=10)
    return json.loads(resp.read())
except HTTPError as e:
    body = e.read().decode('utf-8', errors='ignore')  # ← THIS
    logger.error(f"Binance API error [{method} {path}]: {e} | body: {body}")
    return {"_error": True, "_body": body, "_status": e.code}
```

Critical for debugging testnet/mainnet divergence: Binance returns the same 400 for `-4046 No need to change margin type` (safe, ignore) and `-1111 Precision` (real bug). Without the body you can't tell them apart.

## 4. Cron telegram dedup — the spam fix

**Symptom:** YUNA cron `*/5 * * * *` scans 50 pairs and the user gets a Telegram message every 5 min containing every signal that passed filter. After 1 hour: 12+ spammy messages. User: "kok kamu spam yuna?"

**Fix pattern:** Make the Telegram send conditional on a specific marker in the execution report, not on "any signal exists".

```python
# WRONG: send whenever there's any signal
if signals_found:
    telegram_send(format_signals(signals_found))

# RIGHT: send only when LIMIT ENTRY actually placed
if any("LIMIT ENTRY PLACED" in e for e in executions):
    telegram_send("\n\n".join(executions))
```

Add a dedup check too — skip auto-execute if a pending LIMIT entry already exists for the symbol. Otherwise the same pair tries to enter every 5 min.

## 5. Filter tuning 3-axis (signal-side, not execution-side)

When user says "filter terlalu ketat, kasih sinyal lebih" but "jangan terlalu rendah" — they're asking for the middle of three knobs. Don't collapse them into one:

| Knob | Range | Effect of relaxing |
|---|---|---|
| `SOFT_WAJIB` | True/False | Failures reduce score (don't block) — biggest unlock |
| `MIN_WAJIB_REQUIRED` | 1–3 | Number of WAJIB that must pass (e.g. 2 of 3) |
| `EXECUTE_MIN_SCORE` | 3–9 | Minimum score to send to execution (4 = include WEAK) |

PV sweet spot: SOFT=True, MIN_WAJIB=2, EXECUTE_MIN_SCORE=4. Relaxed enough for tuning-mode data flow, strict enough to not fill with junk.

## 6. Margin type "no need to change" is fine

`POST /fapi/v1/marginType` returns 400 with `{"code":-4046,"msg":"No need to change margin type."}` when the margin type is already correct. This is **expected** on every re-set. Wrap it:

```python
def set_margin_type(symbol, margin_type="CROSSED"):
    try:
        resp = _signed_request("POST", "/fapi/v1/marginType", {"symbol": symbol, "marginType": margin_type})
        # -4046 "No need to change" is a 400, treat as success
        if resp and resp.get("code") == 200:
            return True
        if isinstance(resp, dict) and "-4046" in resp.get("_body", ""):
            return True
        return True  # default to True — never block on this
    except Exception:
        return True
```

## 7. Testnet quirks worth knowing

- **595 symbols** are TRADING on testnet. Many are testnet-only (GWEIUSDT, USUSDT, SIRENUSDT, 1000000BOBUSDT). They have non-zero volume and pass general filters — the algo doesn't care if a pair is testnet-specific, but it WILL fail to find order history for some of them.
- `/futures/data/openInterestHist` returns empty body on many testnet symbols. Non-fatal; signals still produce. Don't log it as a hard error.
- Initial testnet balance: 5000 USDT. Funding doesn't happen on testnet. Liquidations are simulated.
- `/fapi/v2/positionRisk` sometimes returns `positionAmt: 0.0` for symbols that just got filled. The fill IS real (check `executedQty: 0.0010` in the order), but the position endpoint has a brief lag. Don't use position-only to confirm fills.
