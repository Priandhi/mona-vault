"""
Mona Squad — Cross-Agent Rule Engine (v3)
==========================================
SIMPLIFIED: Only active rules (YUNA↔SOYU).
Removed dead agent rules (YERIN, HAERI inactive).
Added timeout guard, file caching, rate limiting.

Data Sources:
  - Dozero signals:    ~/dozero/logs/signals.log
  - Charon positions:  ~/mona-workspace/charon-sniper/data/positions.json
  - Charon traded:     ~/mona-workspace/charon-sniper/data/traded.json

Active Rules:
  1. YUNA → SOYU : New trading signal → sniper check
  2. SOYU → YUNA : Token sniped → SMC analysis
"""

import json
import hashlib
import time
import sys
import signal
from pathlib import Path
from datetime import datetime

BASE = Path.home() / "mona-workspace" / "mona-squad"
sys.path.insert(0, str(BASE))

from squad import send_message, check_all_inboxes, sync_to_master_kanban

# ─── Timeout Guard ──────────────────────────────────────────────
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Orchestrator timed out (>25s)")

# ─── Data Source Paths ──────────────────────────────────────────
DOZERO_SIGNALS = Path.home() / "project-violet" / "data" / "signals.log"
CHARON_POSITIONS = Path.home() / "mona-workspace" / "charon-sniper" / "data" / "positions.json"
CHARON_TRADED = Path.home() / "mona-workspace" / "charon-sniper" / "data" / "traded.json"

# ─── State Tracking ─────────────────────────────────────────────
STATE_FILE = BASE / ".orchestrator_state.json"

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, ValueError):
            pass
    return {
        "last_signal_ts": 0,
        "seen_signals": [],
        "seen_charon_trades": [],
        "last_run_ts": 0,
    }

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def msg_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


# ─── Shared Data Cache ──────────────────────────────────────────
def read_signals():
    """Read Dozero signals.log, return lines with Grade."""
    if not DOZERO_SIGNALS.exists():
        return []
    content = DOZERO_SIGNALS.read_text().strip()
    if not content:
        return []
    return [l for l in content.split("\n") if "Grade" in l and "[" in l]

def read_charon_traded():
    """Read Charon traded.json, return list of mints."""
    if not CHARON_TRADED.exists():
        return []
    try:
        data = json.loads(CHARON_TRADED.read_text())
        if isinstance(data, dict):
            return data.get("traded", [])
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


# ─── RULE 1: YUNA → SOYU (Signal Alert) ─────────────────────────
def rule_yuna_to_soyu(state: dict) -> list:
    """New Dozero.X trading signal → alert SOYU for sniper check."""
    results = []
    lines = read_signals()
    if not lines:
        return results

    seen = state.get("seen_signals", [])

    # First run: mark ALL current signals as seen (no spam)
    if not seen:
        for line in lines:
            seen.append(msg_hash(line))
        state["seen_signals"] = seen
        return results

    for line in lines:
        h = msg_hash(line)
        if h in seen:
            continue

        try:
            parts = line.split("|")
            header = parts[0].strip() if parts else line
            symbol = header.split("]")[-1].strip().split()[0] if "]" in header else "UNKNOWN"

            send_message(
                "YUNA", "SOYU",
                f"Signal: {symbol}",
                f"Ada signal baru dari Dozero.X:\n\n{line}\n\n"
                f"Cek apakah token ini baru launch atau ada liquidity bagus "
                f"buat sniper entry.\n- YUNA",
                priority="high",
            )
            seen.append(h)
            results.append(f"YUNA→SOYU: {symbol} signal forwarded")
        except (ValueError, IndexError):
            continue

    # Cap dedup list at 200 entries
    state["seen_signals"] = seen[-100:] if len(seen) > 200 else seen
    return results


# ─── RULE 2: SOYU → YUNA (Token Sniped → SMC Analysis) ─────────
def rule_soyu_to_yuna(state: dict) -> list:
    """Charon snipes a new token → alert YUNA for SMC/technical analysis."""
    results = []
    traded = read_charon_traded()
    if not traded:
        return results

    seen = state.get("seen_charon_trades", [])
    new_trades = []

    # First run: mark ALL current trades as seen (no spam)
    if not seen:
        for item in traded[-50:]:
            mint = item if isinstance(item, str) else str(item)
            seen.append(msg_hash("soyu_trade_" + mint))
        state["seen_charon_trades"] = seen
        return results

    for item in traded[-10:]:
        mint = item if isinstance(item, str) else str(item)
        h = msg_hash("soyu_trade_" + mint)

        if h in seen:
            continue

        short_mint = mint[:8] + "..." + mint[-4:] if len(mint) > 16 else mint

        send_message(
            "SOYU", "YUNA",
            f"Sniped: {short_mint}",
            f"Charon baru snipe token:\n\n"
            f"Mint: {mint}\n\n"
            f"Tolong analisis SMC-nya — ada potensi swing atau langsung profit taking?\n"
            f"- SOYU",
            priority="high",
        )
        seen.append(h)
        new_trades.append(short_mint)

    if new_trades:
        results.append(f"SOYU→YUNA: {len(new_trades)} new trades forwarded")

    state["seen_charon_trades"] = seen[-200:] if len(seen) > 200 else seen
    return results


# ─── Orchestrator Main ──────────────────────────────────────────
def run_orchestrator():
    """Execute all cross-agent rules and return status."""
    # Set timeout guard — 25s max
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(25)

    try:
        state = load_state()

        # Rate limit: max once every 60s
        now = time.time()
        last_run = state.get("last_run_ts", 0)
        if now - last_run < 60:
            return {"rules_run": 0, "actions": 0, "results": ["Skipped (rate limit)"], "unread": 0}

        all_results = []

        # Only active rules: YUNA↔SOYU
        rules = [
            ("YUNA→SOYU", rule_yuna_to_soyu),
            ("SOYU→YUNA", rule_soyu_to_yuna),
        ]

        for name, rule_fn in rules:
            try:
                results = rule_fn(state)
                if results:
                    all_results.extend(results)
            except Exception as e:
                all_results.append(f"ERROR {name}: {e}")

        # Check inboxes (lightweight)
        try:
            inbox_status = check_all_inboxes()
            total_unread = sum(v["unread"] for v in inbox_status.values())
        except Exception:
            total_unread = 0

        # Sync master kanban
        try:
            sync_to_master_kanban()
        except Exception:
            pass

        # Save state
        state["last_run_ts"] = now
        save_state(state)

        # Output for cron (silent when nothing happened)
        if all_results:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Orchestrator ran {len(rules)} rules:")
            for r in all_results:
                print(f"  -> {r}")

        return {
            "rules_run": len(rules),
            "actions": len(all_results),
            "results": all_results,
            "unread": total_unread,
        }

    except TimeoutError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ORCHESTRATOR TIMEOUT — killed after 25s")
        return {"rules_run": 0, "actions": 0, "results": ["TIMEOUT"], "unread": 0}
    finally:
        signal.alarm(0)  # Disable alarm


if __name__ == "__main__":
    result = run_orchestrator()
