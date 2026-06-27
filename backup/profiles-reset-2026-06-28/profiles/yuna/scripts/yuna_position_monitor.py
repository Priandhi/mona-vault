#!/usr/bin/env python3
"""
YUNA — Position monitor cron wrapper.
Runs /home/ubuntu/project-violet/position_monitor.py to detect TP/SL events.

YUNA 2026-06-22
"""
import os
import subprocess
import sys
from pathlib import Path

os.environ["HOME"] = "/home/ubuntu"

ENV_FILE = Path.home() / ".hermes" / "profiles" / "yuna" / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() not in os.environ:
            os.environ[k.strip()] = v.strip()

PV_DIR = Path("/home/ubuntu/project-violet")
MONITOR = PV_DIR / "position_monitor.py"

try:
    result = subprocess.run(
        [sys.executable, str(MONITOR)],
        cwd=str(PV_DIR),
        capture_output=True,
        text=True,
        timeout=60,
    )
except Exception as e:
    print(f"❌ position_monitor.py error: {e}", file=sys.stderr)
    sys.exit(2)

stdout = (result.stdout or "").strip()
if stdout:
    print(stdout)
sys.exit(0)
