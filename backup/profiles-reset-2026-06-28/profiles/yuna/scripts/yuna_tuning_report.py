#!/usr/bin/env python3
"""
YUNA — Tuning report cron wrapper.
Runs /home/ubuntu/project-violet/tuning_report.py and forwards to Telegram.

YUNA 2026-06-22
"""
import os
import subprocess
import sys
from pathlib import Path

os.environ["HOME"] = "/home/ubuntu"

# Load YUNA env vars
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
REPORT = PV_DIR / "tuning_report.py"

DAYS = sys.argv[1] if len(sys.argv) > 1 else "1"

# Run report
try:
    result = subprocess.run(
        [sys.executable, str(REPORT), "--days", DAYS, "--send-telegram"],
        cwd=str(PV_DIR),
        capture_output=True,
        text=True,
        timeout=60,
    )
except Exception as e:
    print(f"❌ tuning_report.py error: {e}", file=sys.stderr)
    sys.exit(2)

stdout = (result.stdout or "").strip()
stderr = (result.stderr or "").strip()

if stdout:
    print(stdout)
    sys.exit(0)
else:
    if stderr:
        print(f"stderr: {stderr}", file=sys.stderr)
    print("❌ No output from tuning_report.py", file=sys.stderr)
    sys.exit(3)
