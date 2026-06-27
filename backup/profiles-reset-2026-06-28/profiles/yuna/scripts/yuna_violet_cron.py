#!/usr/bin/env python3
"""
YUNA — PROJECT VIOLET cron wrapper
Runs /home/ubuntu/project-violet/run_cron.py and forwards output to Telegram via YUNA bot.

Cron spec (no_agent):
   - exit 0 with output → cron delivers to topic 2905
   - exit 0 silent      → no signal this cycle, no Telegram spam
   - exit non-zero      → cron error alert

YUNA 2026-06-22
"""
import os
import sys
import subprocess
from pathlib import Path

# Set HOME so Path.home() inside PV resolves correctly
os.environ["HOME"] = "/home/ubuntu"

PV_DIR = Path("/home/ubuntu/project-violet")
RUN_CRON = PV_DIR / "run_cron.py"

# Load YUNA env vars (Binance keys + bot token)
ENV_FILE = Path.home() / ".hermes" / "profiles" / "yuna" / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() not in os.environ:
            os.environ[k.strip()] = v.strip()

# Run PV run_cron.py
try:
    result = subprocess.run(
        [sys.executable, str(RUN_CRON)],
        cwd=str(PV_DIR),
        capture_output=True,
        text=True,
        timeout=300,  # 5 min max
    )
except subprocess.TimeoutExpired:
    print("❌ PV run_cron.py TIMEOUT (5 min)", file=sys.stderr)
    sys.exit(2)
except Exception as e:
    print(f"❌ PV run_cron.py error: {e}", file=sys.stderr)
    sys.exit(3)

# Forward stdout (signal alerts already formatted in Bab 15.2)
stdout = (result.stdout or "").strip()
stderr = (result.stderr or "").strip()

if stdout:
    # PV detected a signal → cron auto-delivers stdout to Telegram
    print(stdout)
    if stderr:
        print("\n[stderr]\n" + stderr, file=sys.stderr)
    sys.exit(0)
else:
    # No signal this cycle — silent (no Telegram spam)
    # Log stderr to journal for debugging if any
    if stderr:
        # Write to local debug log only
        debug_log = PV_DIR / "logs" / "cron-stderr.log"
        debug_log.parent.mkdir(parents=True, exist_ok=True)
        with debug_log.open("a") as f:
            from datetime import datetime
            f.write(f"\n=== {datetime.utcnow().isoformat()}Z ===\n{stderr}\n")
    sys.exit(0)
