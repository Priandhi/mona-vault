# Dozero.X — Session-Specific Lessons

Battle-tested gotchas from the YUNA dozero testnet bot (2026-06-16/17). For the
class-level futures engine pattern, see `SKILL.md`. This file captures bugs and
patterns that bit us in production.

## 1. Self-deadlock from unpruned blacklist files

`signalled.json` (or any "pairs-already-signalled" file) needs explicit cleanup
logic, or the bot will starve itself.

**Symptom:** Bot runs `*/30`, finds 0 fresh pairs to scan, log shows
"All 200 pairs already signalled — nothing new to scan". No signals for hours.

**Root cause:** Signalled set grows monotonically — pairs added on signal but
never removed after trade close. Combined with strike-cooldown, eventually
locks 100% of the universe.

**Fix:** At start of every `auto_scan()`, prune `signalled.json` to only keep
pairs that have an open position OR an open order:

```python
# Inside auto_scan() — after loading signalled
try:
    positions = conn.get_positions()
    active_pos_syms = {p['symbol'] for p in positions if abs(float(p['positionAmt', 0])) > 0}
    open_orders = conn.get_open_orders()
    active_order_syms = {o['symbol'] for o in open_orders}
    active_syms = active_pos_syms | active_order_syms
    stale_signalled = {s for s in signalled if s not in active_syms}
    if stale_signalled:
        signalled -= stale_signalled
        save_signalled(signalled)
        logger.info("Pruned %d stale signalled entries (no pos/order)", len(stale_signalled))
except Exception as e:
    logger.warning("Signalled prune failed: %s — proceeding", e)
```

**Lesson:** Any "blacklist with TTL" needs an auto-prune. Don't rely on
`tracked.json` per-pair cooldown alone — it has separate semantics (trade spam
prevention, not scan-universe lock).

## 2. `BinanceConnection.get_balance()` returns float, not dict

In `config/connection.py`, the `get_balance()` method returns the raw
`availableBalance` float. The matching `get_account_info()` returns a full
account dict.

**Symptom:** `agent_data.py` (or any consumer) does:
```python
bal = c.get_balance()
data['balance'] = round(float(bal.get('availableBalance', 0)), 2)
# AttributeError: 'float' object has no attribute 'get'
# → silent except → balance shows as 0
```

**Fix:** Use `get_balance()` for the number directly:
```python
bal = c.get_balance()
data['balance'] = round(float(bal) if bal else 0, 2)
```

If you need the full account dict, use `get_account_info()` and pull the field
yourself. Don't conflate them.

## 3. Notifier must distinguish FILLED vs LIMIT PLACED

**Hexa feedback (2026-06-17):** "harusnya kasih detail kalau limit order biar
gak salah paham" — the "✅ EXECUTED" label is ambiguous. A limit order being
placed in the book is NOT a position open. The notification should make this
obvious so the operator doesn't think a position is live when it isn't.

**Pattern:** Three explicit statuses:

```python
def send_execution(symbol, direction, entry, qty, sl, tp1, tp2, success,
                   order_id="", error="", filled=True, limit_price=0):
    if not success:
        status = "❌ FAILED"
    elif filled:
        status = "✅ FILLED"
    else:
        status = "⏳ LIMIT PLACED (waiting fill)"
    ...
    if filled:
        text += f"Entry: ${entry:.4f}\n"
    else:
        text += f"Signal entry: ${entry:.4f}\n"
        if limit_price:
            text += f"Limit price: ${limit_price:.4f}\n"
        text += f"⚠️ Posisi BELUM terbuka — nunggu market nyentuh limit\n"
```

**Executor contract:** Return both `filled` and `limit_price` from
`execute_trade()`:

```python
# In executor.execute_trade():
if not filled:
    result["filled"] = False
    result["limit_price"] = limit_price
    return result
# ... after fill detection ...
result["filled"] = True
```

**Default `filled=True` for backward compat** in the notifier signature, so
existing callers don't need to change.

## 4. Cron jobs calling external APIs need retry on transient HTTP codes

`yuna-soft-stop.py` cron got a 1-of-18+ transient `HTTP 408 Request Timeout`
from Binance testnet, fired a noisy failure alert.

**Pattern:** 3-attempt retry on 408/429/500/502/503/504 with 1s/2s backoff.
Non-retryable codes pass through immediately.

```python
def signed_get(b, p, q, k, s):
    last_err = None
    for attempt in range(3):
        try:
            q['timestamp'] = int(time.time()*1000); q['recvWindow'] = 5000
            qs = urlencode(q); sig = hmac.new(s.encode(), qs.encode(), hashlib.sha256).hexdigest()
            r = urllib.request.Request(f'{b}{p}?{qs}&signature={sig}', headers={'X-MBX-APIKEY': k})
            return json.loads(urllib.request.urlopen(r, timeout=10).read())
        except urllib.error.HTTPError as e:
            if e.code in (408, 429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise
    raise last_err
```

**Lesson:** Testnet APIs are flaky. Production alert noise is bad — retry
transient codes, alert on permanent failure only.

## 5. `Path.home()` expands nested under YUNA profile $HOME

YUNA profile's `$HOME = /home/ubuntu/.hermes/profiles/yuna/home/`. So
`Path.home() / "dozero" / "config" / ".testnet_keys"` in a YUNA-shell
Python process expands to:
`/home/ubuntu/.hermes/profiles/yuna/home/dozero/config/.testnet_keys` (wrong)

The real keys are at `/home/ubuntu/dozero/config/.testnet_keys`. Same for
`notifier.py` looking for `.hermes/profiles/yuna/.env` — gets the nested path.

**Symptom:** 401 invalid API key, "No YUNA bot token found", etc. — but only
when running from the yuna profile shell. PM2 processes that have explicit
`HOME=/home/ubuntu` in their env work fine.

**Workarounds (in priority order):**
1. PM2 `env.HOME = /home/ubuntu` (preferred — keeps dozero as standalone project)
2. `os.path.expanduser('~/.hermes/profiles/yuna/.env')` — still nested
3. Set `HOME=/home/ubuntu` prefix when running dozero scripts from yuna shell:
   `HOME=/home/ubuntu python3 /home/ubuntu/dozero/agent_data.py yuna`
4. Long-term: refactor dozero scripts to use absolute paths in `config/`
   (e.g. `Path('/home/ubuntu/dozero/config/.testnet_keys')`)

**Long-term fix:** YUNA profile should not be the active profile when running
dozero tooling. Or, refactor dozero config to read from a fixed absolute path
ignoring `$HOME` entirely.

## 6. Margin tiered by signal grade

YUNA 2026-06-17: Hexa wanted margin $75-$115 range, mapped to Grade B ($75)
and Grade A ($115) respectively. Margin grows with conviction.

```python
# config/settings.py
MARGIN_BY_GRADE = {
    "A": 115.0,   # score >= 80
    "B":  75.0,   # score 70-79
    # C/D filtered at MINIMUM_TRADE_SCORE
}

# engine/executor.py
def _get_margin_per_trade(self, grade: str = "B") -> float:
    from config.settings import MARGIN_BY_GRADE
    return MARGIN_BY_GRADE.get(grade.upper() if grade else "B", MARGIN_BY_GRADE["B"])

def calculate_position_size(self, symbol, entry, sl, leverage=None, grade: str = "B"):
    margin = self._get_margin_per_trade(grade)
    # ... rest unchanged

def execute_trade(self, ..., grade: str = "B"):
    pos = self.calculate_position_size(symbol, entry, sl, leverage=leverage, grade=grade)
    # ... rest unchanged

# auto.py — pass grade from signal
executor.execute_trade(..., grade=best.grade)
```

**Risk calc note:** `notional = margin * leverage` scales 23x from old $5 max
(A-grade $115 × 50x = $5,750 notional). Make sure account balance supports
`notional ≤ balance * leverage * 0.85` cap (already in code).

## 7. `max_lev` undefined in `execute_trade()` log statement

**Bug:** `executor.py:182` (pre-2026-06-17):
```python
logger.info("[%s] Position: qty=%f, leverage=%d, margin=$%.2f",
            symbol, qty, max_lev, pos["margin"])
```
`max_lev` is only defined inside `calculate_position_size()`, not
`execute_trade()`. The log statement threw `NameError: name 'max_lev' is not
defined` on every trade execution.

**Fix:** Use the local `leverage` variable from the `execute_trade` scope:
```python
logger.info("[%s] Position: qty=%f, leverage=%d, margin=$%.2f",
            symbol, qty, leverage, pos["margin"])
```

## 8. Soft-stop monitor needs explicit mainnet vs testnet handling

Testnet Binance Futures does NOT support the algo order endpoints
(`/fapi/v1/algoOrder/openOrder` returns 404). This means SL/TP algo orders
can be placed but cannot be queried back.

**Workaround for testnet safety net:** `yuna_soft_stop.py` cron (every 5 min)
checks all positions, computes `uPnL / margin`, and market-closes anything
below -5%. Mainnet has higher stop order limits, so algo SL/TP works there
natively.

**When to deploy soft-stop:** Always on testnet. Optional on mainnet if your
SL algo order placement is reliable. Keep it anyway as a belt-and-suspenders.

## 9. Testnet algo SL/TP order placement silently fails

The executor places algo orders for SL/TP after limit fill. On testnet, the
algo order placement 404s. The position is open without protection. Soft-stop
cron is the only safety net.

**Detection:** Check `dozero-error.log` for algo 404s. Don't trust
"Trade tracked" log as proof of SL placement.

## 10. PM2 "Process not found" during waiting state is cosmetic

When `dozero-auto` is in `waiting` status (between cron ticks), `pm2 restart`
returns `[ERROR] Process 7 not found`. The process IS there, just in waiting
state. Use `pm2 jlist` to verify `status: online` after restart, not the
restart output.

```bash
# Wrong: trust the restart output
pm2 restart 7
# [PM2][ERROR] Process 7 not found  ← cosmetic

# Right: verify status after restart
pm2 jlist | python3 -c "import json, sys; d=json.load(sys.stdin); [print(p['pm2_env']['status'], p['name']) for p in d if p['name']=='dozero-auto']"
# online dozero-auto  ← that's the truth
```

## 11. Default profile Telegram bot token vs profile-specific

`notifier.py` does `Path.home() / ".hermes" / "profiles" / "yuna" / ".env"`
to find the YUNA bot token. In YUNA shell, this expands to the nested path.
In PM2 with `HOME=/home/ubuntu`, this works.

**For scripts that need to send from non-PM2 context:** Hardcode the YUNA
profile home path:
```python
env_file = Path("/home/ubuntu/.hermes/profiles/yuna/.env")
```

Or set `YUNA_HOME` env var and read that. Either way, don't rely on
`Path.home()` when the active profile's HOME is the wrong root.
