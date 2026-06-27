# YUNA Dozero Session Notes — 2026-06-17

Specific implementation patterns captured from the YUNA dozero testnet trading bot. Complements the class-level `crypto-futures-engine` skill with concrete code patterns and gotchas discovered while running a real Binance testnet deployment.

## Notifier FILLED vs LIMIT PLACED

Hexa feedback (2026-06-17): The previous notifier used `✅ EXECUTED` for any successful order placement. He got confused when a SYNUSDT limit order was "executed" but no position was open yet — the order was just sitting in the order book waiting to fill. He asked: "harusnya kasih detail kalau limit order biar gak salah paham".

**Rule:** Distinguish 3 states with unambiguous labels: `✅ FILLED` (position open), `⏳ LIMIT PLACED (waiting fill)` (order in book), `❌ FAILED` (rejected). See `crypto-futures-engine` SKILL.md for the pattern.

**YUNA dozero notifier code (`/home/ubuntu/dozero/notifier.py`):**

```python
def send_execution(symbol, direction, entry, qty, sl, tp1, tp2, success,
                   order_id="", error="", filled=True, limit_price=0):
    if not success:
        status = "❌ FAILED"
    elif filled:
        status = "✅ FILLED"
    else:
        status = "⏳ LIMIT PLACED (waiting fill)"
    text = f"{status} — {symbol}\n" + "━" * 20 + "\n"
    text += f"Direction: {direction}\n"
    if filled:
        text += f"Entry: ${entry:.4f}\n"
    else:
        text += f"Signal entry: ${entry:.4f}\n"
        if limit_price:
            text += f"Limit price: ${limit_price:.4f}\n"
        text += f"⚠️ Posisi BELUM terbuka — nunggu market nyentuh limit\n"
    text += f"Qty: {qty:.4f}\n"
    text += f"SL: ${sl:.4f}\n"
    text += f"TP1: ${tp1:.4f} | TP2: ${tp2:.4f}\n"
    if order_id:
        text += f"Order ID: {order_id}\n"
    if error:
        text += f"Error: {error}\n"
    return _send(text, TOPIC_SIGNAL)
```

## ROI-Based TP System [DEPRECATED 2026-06-17 16:14 — see "TP System Evolution" below]

⚠️ **Replaced by R:R-based TP.** Kept for historical reference only. Use TP_RR_MULTIPLIERS instead of TP_ROI. See "TP System Evolution: ROI → R:R-Based" section below for why this was replaced.

**Settings (`/home/ubuntu/dozero/config/settings.py`):**

```python
TP_ROI = [1.0, 2.0, 3.0]        # 100% / 200% / 300% of margin
TP_QTY_PCTS = [0.3, 0.3, 0.4]   # 30% / 30% / 40% qty split
```

**Executor (`/home/ubuntu/dozero/engine/executor.py`):**

```python
# YUNA 2026-06-17: ROI-based TP. Use TP_ROI[1]=2.0 (200%) as Main TP.
from config.settings import TP_ROI
tp_main_pct = TP_ROI[1] / leverage  # TP2 = 200% margin
main_tp_price = actual_entry * (1 + tp_main_pct) if direction == "LONG" else actual_entry * (1 - tp_main_pct)
```

**Reconcile (`/home/ubuntu/dozero/auto.py`):**

```python
lev = int(p.get("leverage", 1)) or 1
main_tp_pct = TP_PCTS[1] / lev
main_tp_price = entry * (1 + main_tp_pct) if direction == "LONG" else entry * (1 - main_tp_pct)
# Log all 3 levels for visibility
logger.info("[%s] TP levels: TP1=%.4f (+%.2f%%), TP2=%.4f (+%.2f%%, MAIN), TP3=%.4f (+%.2f%%)",
            symbol, tp1_price, TP_PCTS[0]/lev*100,
            main_tp_price, TP_PCTS[1]/lev*100,
            tp3_price, TP_PCTS[2]/lev*100)
```

## Margin Tiered by Grade

YUNA dozero (2026-06-17): `MARGIN_BY_GRADE = {"A": 115.0, "B": 75.0}`. Margin flows through executor:

```python
# settings.py
MARGIN_BY_GRADE = {
    "A": 115.0,   # score >= 80 (high conviction)
    "B":  75.0,   # score 70-79 (moderate)
}

# engine/executor.py
def _get_margin_per_trade(self, grade: str = "B") -> float:
    from config.settings import MARGIN_BY_GRADE
    return MARGIN_BY_GRADE.get(grade.upper() if grade else "B", MARGIN_BY_GRADE["B"])

def calculate_position_size(self, symbol, entry, sl, leverage=None, grade="B"):
    if leverage is None:
        leverage = self.conn.get_max_leverage(symbol)
    margin = self._get_margin_per_trade(grade)
    # ...

def execute_trade(self, symbol, direction, entry, sl, tp1, tp2, tp3, grade="B"):
    pos = self.calculate_position_size(symbol, entry, sl, leverage=leverage, grade=grade)
    # ...

# auto.py — pass grade from best signal
result = executor.execute_trade(
    symbol=best.symbol, direction=best.direction,
    entry=best.entry_price, sl=best.stop_loss,
    tp1=best.take_profit_1, tp2=best.take_profit_2, tp3=best.take_profit_3,
    grade=best.grade,   # <-- new
)
```

## PM2 Cron `restart_delay` Pitfall

YUNA dozero (2026-06-17): Original PM2 process had `restart_delay: 30000` (30 sec) + `cron_restart: '*/30 * * * *'`. PM2 spawned the script every 30 seconds instead of every 30 minutes — `restart_delay` overrode the cron. Bot hit strike-cooldown within 1-2 hours and self-deadlocked.

**Fix (preferred — recommended over ecosystem config):** Use `auto_loop.py` wrapper (see "PM2 Crash-Restart Loop: ACTUAL Fix is auto_loop.py Wrapper" above). Process stays alive, sleeps between cycles, no PM2 cron needed. Solved the 17-restart-in-30-seconds crash loop cleanly.

```js
// /home/ubuntu/.hermes/profiles/yuna/home/.pm2/ecosystem-dozero.config.js
module.exports = {
  apps: [{
    name: 'dozero-auto',
    script: '/home/ubuntu/dozero/auto.py',
    interpreter: 'python3',
    cwd: '/home/ubuntu/dozero',
    cron_restart: '*/30 * * * *',
    autorestart: false,
    restart_delay: 0,
    max_restarts: 1,
    min_uptime: '30m',
    exec_mode: 'fork',
    env: { DOZERO_ENV: 'testnet' },
  }],
};
```

## Hexa YUNA Spec (2026-06-17 16:14, FINAL — current state)

**Do NOT re-apply older values without explicit confirmation.** This is the current spec — use it as the default for YUNA dozero:

```python
# config/settings.py
DEFAULT_LEVERAGE = 20                # Mathematically safe w/ 4% SL
MARGIN_PER_TRADE_USD = 90.0          # Middle of $75-115 range
MARGIN_MIN_USD = 75.0
MARGIN_MAX_USD = 115.0
SL_DISTANCE_PCT = 0.04               # 4% SL
MAX_SL_DISTANCE_PCT = 0.05           # 5% max (20x liq floor)
MIN_RR = 1.5                         # 1:1.5 R:R minimum
TP_RR_MULTIPLIERS = [1.0, 2.0, 3.0]  # R:R-based, not ROI-based
LEVERAGE_USE_TIER_CAP = False        # Use DEFAULT_LEVERAGE directly
MIN_PRICE_USD = 0.05
MIN_VOLUME_USDT = 2_000_000
MINIMUM_TRADE_SCORE = 70             # Grade B minimum
```

**Hexa spec evolution (same day, two passes):**
- 2026-06-17 morning: Hexa wanted Binance max leverage (50-75x), 6% SL, 100/200/300% ROI TPs
- 2026-06-17 16:14 (FINAL): 20x leverage, 4% SL, 1:1/1:2/1:3 R:R TPs, $90 margin, mandatory liq validation
- **Reasoning:** Realized that 75x with any SL > 1.3% triggers liquidation. 20x is the highest leverage where a 4% SL still has a safety buffer.

**Lesson for future sessions:** When user gives a specific spec, apply it directly. If user later overrides (like Hexa did here from "Binance max" → 20x), update immediately. Don't keep applying the older default. The "PM2 Cron restart_delay Pitfall" fix previously documented as ecosystem config was a band-aid — the auto_loop.py wrapper is the real fix.

## Auto-Prune signalled.json Pattern

YUNA dozero had a self-deadlock bug: `signalled.json` accumulated pair names that had received signals, but was never cleaned up after the trade closed. Combined with the PM2 cron bug, this caused 53 pairs to be stuck in signalled forever, blocking fresh scans.

Fix: auto-prune at start of each scan cycle, removing pairs that have no open position and no open order.

```python
# auto.py — at start of auto_scan()
try:
    positions = conn.get_positions()
    active_pos_syms = {p['symbol'] for p in positions if abs(float(p.get('positionAmt', 0))) > 0}
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

## Soft-Stop Cron

YUNA soft-stop cron (id `f4fc8ce3a405`) runs every 5 min, monitoring uPnL of open positions. If `uPnL/margin < -5%`, auto-closes via market reduceOnly. Critical safety net since testnet SL algo orders have a 1-per-symbol limit. Script at `/home/ubuntu/.hermes/profiles/yuna/scripts/yuna_soft_stop.py`.

## YUNA Profile $HOME Path Issue

YUNA profile's `$HOME = /home/ubuntu/.hermes/profiles/yuna/home/`. So `~` in shell commands expands to that nested path. Use absolute paths or `HOME=/home/ubuntu` prefix. Cron `script:` field resolves to the real path `/home/ubuntu/.hermes/profiles/yuna/scripts/`, not the HOME-nested one.

## YUNA Bot "Self-Deadlock" Failure Mode

Three combined bugs caused total scan deadlocks in the YUNA dozero testnet:

1. **signalled.json never cleaned** — pairs stuck after trade close
2. **PM2 cron restart_delay = 30s** — bot fires every 30 sec instead of 30 min
3. **strike-cooldown accumulates** — pairs with 3 no-signals locked for 24h

Result: 200/200 scan universe locked, "All 200 pairs already signalled — nothing new to scan" log spam. Diagnose by checking:
- `pm2 jlist` → `restart_delay` and `autorestart` values
- `cat data/signalled.json` → should be empty or near-empty
- `cat data/no_signal.json` → count of `scans >= 3` should be small

## Soft-Stop HTTP Timeout Resilience

The `yuna_soft_stop.py` script hit `urllib.error.HTTPError: HTTP Error 408: Request Timeout` on a 1-of-18 run. Added retry logic:

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
            last_err = e
            if e.code in (408, 429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** attempt)  # 1s, 2s backoff
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise
    raise last_err
```

Testnet APIs are flaky — any direct-API call script should have retry logic for 408/429/5xx.

## TP System Evolution: ROI → R:R-Based (2026-06-17 16:14)

**Lesson:** Hexa was confused by `TP_ROI = [1.0, 2.0, 3.0]` (100% / 200% / 300% of margin). He said: *"Tapi ke tinggian kayak nya kalau TP 1-3 nya segitu 🤣 tapi aku bingung ngatur sistem nya gimana"*. The math varied wildly with leverage (1.33% price move at 75x vs 30% at 10x) and felt non-intuitive.

**Fix:** Switch to R:R-based TP. TP price = entry ± (sl_distance × multiplier). Always guarantees a fixed R:R ratio at each level, regardless of leverage. This is the industry standard and much easier to reason about.

**Why R:R is better than ROI for TP design:**
- ROI = leverage-dependent (1.33% at 75x vs 30% at 10x) — confusing
- R:R = always expressed as "1:1, 1:2, 1:3 of SL" — language anyone understands
- Auto-adjusts to whatever SL the signal provides (signal-agnostic)
- Aligns with trading literature and risk management theory

**Settings (current — Hexa spec):**

```python
# YUNA 2026-06-17: R:R-based TP (Hexa bingung dengan ROI-based 100/200/300%)
# TP1/TP2/TP3 = SL distance × multiplier. Cleaner, guarantees positive R:R.
# TP1 = 1:1, TP2 = 1:2 (main exit), TP3 = 1:3
TP_RR_MULTIPLIERS = [1.0, 2.0, 3.0]   # R:R for each TP level
TP_QTY_PCTS = [0.30, 0.30, 0.40]      # 30% / 30% / 40% qty split per TP
# Backward-compat aliases
TP_ROI = TP_RR_MULTIPLIERS  # legacy: treated as R:R multiplier when sl_distance is known
```

**Executor (current):**

```python
# YUNA 2026-06-17: R:R-based TP. TP2 = SL distance × 2 (1:2 R:R) = Main TP.
# TP price = entry × (1 + sl_distance_pct × TP_RR_MULTIPLIERS[i])
from config.settings import TP_RR_MULTIPLIERS
sl_distance_pct = abs(entry - sl) / entry if entry > 0 else 0.02
main_tp_pct = sl_distance_pct * TP_RR_MULTIPLIERS[1]  # TP2 = 1:2 R:R
main_tp_price = actual_entry * (1 + main_tp_pct) if direction == "LONG" else actual_entry * (1 - main_tp_pct)
```

**Test matrix (SL 4% default, 20x leverage):**

| SL | Lev | Liq risk | TP1 (1:1) | TP2 (1:2, main) | TP3 (1:3) |
|----|-----|----------|-----------|-----------------|-----------|
| 4% | 20x | -80% ROI | +4% = +80% ROI | +8% = +160% ROI | +12% = +240% ROI |
| 2% | 75x | -150% ROI | +2% = +150% ROI | +4% = +300% ROI | +6% = +450% ROI |
| 6% | 15x | -90% ROI | +6% = +90% ROI | +12% = +180% ROI | +18% = +270% ROI |

R:R is always fixed (1:1 / 1:2 / 1:3 of SL), only the absolute ROI varies with leverage. Hexa can now reason "I want 1:2 R:R" without doing leverage math.

## Liquidation Validation (Mandatory Pre-Trade Check)

**Lesson (2026-06-17 16:14):** Hexa specified the leverage/SL safety rule explicitly:

| Lev | Liq distance | Max safe SL (80% buffer) |
|-----|--------------|--------------------------|
| 20x | ~5% | 4.0% ✅ |
| 25x | ~4% | 3.2% ❌ (SL 4% too wide) |
| 30x | ~3.3% | 2.7% ❌ |
| 50x | ~2% | 1.6% ❌ |
| 75x | ~1.3% | 1.1% ❌ |

**Function (`/home/ubuntu/dozero/engine/executor.py`):**

```python
def validate_leverage_sl(leverage: int, sl_pct: float) -> bool:
    """YUNA 2026-06-17: Liquidation safety check (Hexa spec).
    Liquidation distance ≈ 1/leverage (isolated, no fees).
    80% safety buffer = SL must be < 0.8 × liq_distance.
    Raises ValueError if SL is too wide for the leverage.
    """
    if leverage <= 0:
        raise ValueError(f"Invalid leverage: {leverage}")
    liq_distance = (1.0 / leverage) * 0.8   # 80% safety buffer
    if sl_pct >= liq_distance:
        raise ValueError(
            f"DITOLAK: SL {sl_pct*100:.1f}% tidak aman untuk {leverage}x leverage. "
            f"Max SL yang aman: {liq_distance*100:.1f}%"
        )
    return True
```

**Call before place order (`executor.py` execute_trade):**

```python
# 0.5. 🛡️ Liquidation safety check (YUNA 2026-06-17: Hexa spec)
from config.settings import SL_DISTANCE_PCT as _SL_PCT, DEFAULT_LEVERAGE as _DEF_LEV
validate_leverage_sl(_DEF_LEV, _SL_PCT)
logger.info("[%s] ✅ Liquidation check passed: %dx lev + %.0f%% SL = safe",
            symbol, _DEF_LEV, _SL_PCT * 100)
```

**Rule of thumb for any leverage tier:**
- Leverage N → liquidation at 1/N price move (isolated, no fees)
- SL must be < 0.8/N to have a safety buffer
- E.g. 20x → SL < 4%, 50x → SL < 1.6%, 75x → SL < 1.1%

**This applies to ANY leveraged trading setup**, not just YUNA dozero. Pattern is reusable for Bybit, OKX, dYdX, Hyperliquid, etc.

## Position Sizing: Margin-Based (Hexa Spec) vs Risk-Based

**Lesson (2026-06-17 16:14):** Hexa explicitly preferred **margin-based** sizing over risk-based, after I default-implemented risk-based. His reasoning: "Hexa mau fix margin $75-115" — he wants predictable $90 margin per trade regardless of SL distance.

**Margin-based (Hexa spec, YUNA dozero):**

```python
def calculate_position_size(self, symbol, entry, sl, leverage=None, grade="B"):
    """Calculate position size (YUNA 2026-06-17: margin-based, Hexa spec).
    Formula: notional = margin × leverage, qty = notional / entry.
    Position sizing is NOT risk-based — margin cap is the hard limit.
    """
    from config.settings import DEFAULT_LEVERAGE, MARGIN_PER_TRADE_USD
    if leverage is None:
        leverage = DEFAULT_LEVERAGE
    margin = MARGIN_PER_TRADE_USD  # fixed $90 (range $75-115)
    max_lev = leverage
    notional = margin * max_lev  # $90 × 20x = $1,800
    # Cap at 85% of balance × leverage as safety buffer
    balance = self.conn.get_balance()
    max_notional = balance * max_lev * 0.85
    notional = min(notional, max_notional)
    qty = notional / entry
    qty = self._round_qty(symbol, qty)
    risk_pct = abs(entry - sl) / entry if entry > 0 else 0
    risk_amount = margin * risk_pct * max_lev
    return {"quantity": qty, "leverage": max_lev, "notional": notional,
            "margin": margin, "risk_amount": risk_amount, "risk_pct": risk_pct * 100}
```

**Tradeoff vs risk-based:**
- Margin-based: $X margin × Y leverage = fixed notional. SL variance → risk variance.
- Risk-based: $X risk / SL distance = variable notional. SL variance → constant risk.
- For small accounts with fixed budgets, margin-based is simpler and more predictable.
- For professional risk management, risk-based is superior (consistent dollar risk per trade).

**YUNA decision:** Hexa explicitly chose margin-based for predictability. This is a USER preference for this bot — not a system-wide rule. Future sessions should ask before switching to risk-based.

## PM2 Crash-Restart Loop: ACTUAL Fix is auto_loop.py Wrapper

**Update to the "PM2 Cron restart_delay Pitfall" section below:** The ecosystem config with `autorestart: false` was the previous recommendation, but in practice the cleanest fix is a Python loop wrapper that keeps the process alive between cycles.

**Reasoning:** PM2's autorestart and cron_restart are both flaky for long-cycle interval scripts. The auto-restart of a one-shot script + cron_restart = race condition + delayed spawn. A self-contained loop wrapper is more predictable.

**`/home/ubuntu/dozero/auto_loop.py`:**

```python
#!/usr/bin/env python3
"""Loop wrapper. PM2 runs THIS (not auto.py) so the process stays alive.
YUNA 2026-06-17: 30 min cycle, not 30s crash-restart bug."""
import sys, time, signal, logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from auto import auto_scan

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(),
              logging.FileHandler(Path(__file__).parent / "logs" / "auto_loop.log")],
)
logger = logging.getLogger("dozero.loop")

CYCLE_SECONDS = 1800  # 30 minutes between scans (Hexa spec)

def _shutdown(signum, frame):
    logger.info("Received signal %s — shutting down", signum)
    sys.exit(0)

signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)

def main():
    logger.info("━━━ DOZERO LOOP STARTED — cycle=%ds ━━━", CYCLE_SECONDS)
    while True:
        try:
            logger.info("━━━ SCAN CYCLE START ━━━")
            auto_scan(execute=True)
            logger.info("━━━ SCAN CYCLE END — sleeping %ds ━━━", CYCLE_SECONDS)
        except Exception as e:
            logger.exception("Scan cycle error: %s", e)
        time.sleep(CYCLE_SECONDS)

if __name__ == "__main__":
    main()
```

**PM2 start command:**

```bash
pm2 delete dozero-auto
pm2 start /home/ubuntu/dozero/auto_loop.py --name dozero-auto --cwd /home/ubuntu/dozero --interpreter python3
```

**Pattern applies to any interval-based bot:** If a script is meant to fire periodically (cron-like), use a loop wrapper instead of one-shot + PM2 cron. It's more reliable, easier to debug, and gives you a single process to monitor.

## ROI-Based TP System (DEPRECATED — kept for reference)

⚠️ **Deprecated 2026-06-17 16:14:** Replaced by R:R-based TP. Kept here for reference only. Do NOT use in new code — use R:R-based instead.

YUNA dozero (2026-06-17) used `TP_ROI = [1.0, 2.0, 3.0]` meaning 100% / 200% / 300% of margin. See "TP System Evolution: ROI → R:R-Based" above for why this was replaced.

**Settings (DEPRECATED):**

```python
TP_ROI = [1.0, 2.0, 3.0]        # 100% / 200% / 300% of margin
TP_QTY_PCTS = [0.3, 0.3, 0.4]   # 30% / 30% / 40% qty split
```

**Executor (DEPRECATED):**

```python
# YUNA 2026-06-17: ROI-based TP. Use TP_ROI[1]=2.0 (200%) as Main TP.
from config.settings import TP_ROI
tp_main_pct = TP_ROI[1] / leverage  # TP2 = 200% margin
main_tp_price = actual_entry * (1 + tp_main_pct) if direction == "LONG" else actual_entry * (1 - tp_main_pct)
```
