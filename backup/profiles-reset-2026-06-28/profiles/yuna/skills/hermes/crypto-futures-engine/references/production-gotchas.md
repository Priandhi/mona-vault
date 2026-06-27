# Production Gotchas — Crypto Futures Bots

Field-tested pitfalls observed running live signal scanners + executors
(mainly Dozero.X pattern on Binance Futures). Each entry: symptom → root
cause → fix.

---

## 1. PM2 `cron_restart` + `restart_delay` trap → bot fires every 30s instead of every 30m

**Symptom.** You set `cron_restart: '*/30 * * * *'` (every 30 min), but
the bot runs every ~30 seconds. Scan universe hits 3-strike cooldown in
~1.5 hours instead of weeks. Self-deadlock.

**Root cause.** PM2's `restart_delay` (in **milliseconds**) overrides the
cron. The previous config had `restart_delay: 30000` (= 30s). PM2 spawned
the process, it exited fast, PM2 waited 30s, restarted. Infinite 30s
loop. The `cron_restart` was decoration — `restart_delay` is the actual
fire interval.

**Fix.**
```javascript
// ecosystem.config.js
{
  name: 'my-bot',
  cron_restart: '*/30 * * * *',
  autorestart: false,   // do not restart on exit
  restart_delay: 0,     // <-- ms, not minutes. Set 0 so cron controls
  max_restarts: 1,
  min_uptime: '30m',
}
```

**Verify.** After `pm2 start`, watch `pm2 logs` for 10+ minutes. If you
see 2+ fire cycles within 1 minute, the bug is back. Cron should fire
only at HH:00 and HH:30, not at 12:57.

---

## 2. Notifier "EXECUTED" is ambiguous → user thinks position is open when it's a limit order in the book

**Symptom.** Telegram notifier says `✅ EXECUTED — SYNUSDT  qty 965`.
User opens `/posisi` and sees 0 active positions. Confusion/frustration.

**Root cause.** The executor's `result["success"] = True` covers BOTH
"limit order placed in order book" AND "market order filled" AND "limit
order just got filled mid-poll". The notifier didn't distinguish.

**User feedback (first-class signal):** "harusnya kasih detail kalau
limit order biar gak salah paham" — Hexa. The skill must encode this.

**Fix.** Make the notifier status explicit:
- `✅ FILLED` — position is open, this is the actual entry price.
- `⏳ LIMIT PLACED (waiting fill)` — order in the book, NOT a position
  yet. Include the limit price separately from the signal entry.
- `❌ FAILED` — order rejected.

Implementation pattern:
```python
# executor.py
if not filled:
    result["success"] = True
    result["filled"] = False
    result["limit_price"] = limit_price
    return result
# ... on fill path:
result["success"] = True
result["filled"] = True

# notifier.py
def send_execution(*, filled, limit_price=0, **kw):
    if not kw['success']: status = "❌ FAILED"
    elif filled:          status = "✅ FILLED"
    else:                 status = "⏳ LIMIT PLACED (waiting fill)"
    # ... show "⚠️ Posisi BELUM terbuka — nunggu market nyentuh limit"
```

---

## 3. Signal scanner self-deadlock: `signalled.json` never cleaned up

**Symptom.** Bot scans 0 fresh pairs. Universe fully blocked.
Log: `All 200 pairs already signalled — nothing new to scan`. Happens
1-2 days after deploy even though 0 positions are open.

**Root cause.** Bot adds pair to `signalled.json` when it gives a signal
so it doesn't re-signal same pair. But no logic ever REMOVES a pair when
the trade closes (TP/SL/emergency/manual close). After 2-3 days, every
pair that ever gave a signal is permanently stuck.

**Compounding factor.** If strikes accumulate faster than 24h cooldown
(see #1), even non-signalled pairs get locked. Whole universe dead.

**Fix.** Auto-prune at the start of every scan cycle:
```python
# auto.py / auto_scan()
try:
    positions = conn.get_positions()
    open_pos = {p['symbol'] for p in positions if abs(float(p.get('positionAmt', 0))) > 0}
    open_ords = {o['symbol'] for o in conn.get_open_orders()}
    active = open_pos | open_ords
    stale = {s for s in signalled if s not in active}
    if stale:
        signalled -= stale
        save_signalled(signalled)
        logger.info("Pruned %d stale signalled entries (no pos/order)", len(stale))
except Exception as e:
    logger.warning("Signalled prune failed: %s — proceeding", e)  # never block scan
```

Wrap in try/except — never let the cleanup itself break the scan loop.

---

## 4. Tiered margin by grade ($75 B / $115 A) — design pattern

**Pattern.** When user gives a margin range like "75-115", map to grades:
```python
MARGIN_BY_GRADE = {"A": 115.0, "B": 75.0}  # in config/settings.py
```

Executor accepts `grade` param, defaults to "B":
```python
def _get_margin_per_trade(self, grade="B"):
    return MARGIN_BY_GRADE.get(grade.upper() if grade else "B",
                                MARGIN_BY_GRADE["B"])

def calculate_position_size(self, ..., grade="B"):
    margin = self._get_margin_per_trade(grade)
    # ...

def execute_trade(self, ..., grade="B"):
    pos = self.calculate_position_size(..., grade=grade)
```

Caller passes signal's grade:
```python
result = executor.execute_trade(..., grade=best.grade)
```

**Why this works.** Conviction-weighted capital. A-grade signals get
1.5× more capital, but risk profile is the same (same SL distance,
same leverage tier). Catches the user's intent without needing a new
config knob for each tweak.

---

## 5. References to undefined variables in log statements

**Symptom.** Bot logs `name 'X' is not defined` mid-execution. Trade
aborts.

**Common cause.** `executor.py:182` had:
```python
logger.info("...leverage=%d...", symbol, qty, max_lev, pos["margin"])
```
where `max_lev` was only defined in `calculate_position_size()` scope,
not in `execute_trade()` scope. Local variable is `leverage`.

**Fix.** Use the actual local variable. The bug is silent until a real
trade hits the log line — easy to miss in unit tests with mocked
connections.

**Prevention.** Always reference variables in their actual scope. When
refactoring `calculate_position_size()` to use `max_lev`, don't
copy-paste log statements into a different function that has `leverage`.

---

## 6. Soft-stop watchdog needs retry logic for transient HTTP errors

**Symptom.** Soft-stop cron (`*/5 * * * *`) reports `Script exited with
code 1` once a day. Log shows `urllib.error.HTTPError: HTTP Error 408:
Request Timeout` from Binance Testnet API.

**Root cause.** No retry on transient errors. A single 30-second
network blip fires a Telegram alert.

**Fix.** Wrap the signed request in retry with exponential backoff:
```python
def signed_get(b, p, q, k, s):
    for attempt in range(3):
        try:
            q['timestamp'] = int(time.time()*1000); q['recvWindow'] = 5000
            qs = urlencode(q); sig = hmac.new(s.encode(), qs.encode(), hashlib.sha256).hexdigest()
            r = urllib.request.Request(f'{b}{p}?{qs}&signature={sig}',
                                       headers={'X-MBX-APIKEY': k})
            return json.loads(urllib.request.urlopen(r, timeout=10).read())
        except urllib.error.HTTPError as e:
            if e.code in (408, 429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** attempt)  # 1s, 2s
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise
```

Only retry on truly transient codes. Don't retry 4xx (client error —
will fail again). After 3 attempts, let it raise so the cron can alert
on a real persistent problem.
