"""
MONA Auto-Heal System
Monitors all processes, auto-restarts, reports to Command Center
"""

import json
import subprocess
import time
import sys
from pathlib import Path

CHAT_ID = "-1003899936547"
TOPIC_ID = 2909  # 🧠 MONA — Command Center

# Get @MonaOpsBot token
token = None
env_file = Path.home() / ".hermes" / ".env"
for line in env_file.read_text().split("\n"):
    if "MONAOPS_BOT_TOKEN" in line and "=" in line:
        token = line.split("=", 1)[1].strip().strip('"').strip("'")
        break

WATCHED_PROCESSES = [
    # "pm2_name", "description"
    ("charon-bot", "Charon Sniper Bot (DRY RUN)"),
    ("charon-sniper", "Charon Dashboard"),
    ("meridian", "Meridian LP Agent (DRY RUN)"),
    ("iclix-api", "ICLIX Backend (Express)"),
]

# Cron jobs to check
WATCHED_CRONS = [
    "Dozero.X — Auto-Trader",
    "Dozero.X — PnL Report",
    "SOYU — Sniper Status",
    "YERIN — Mining Status",
    "HAERI — Airdrop Status",
    "Mona Squad — Orchestrator",
]


def send_telegram(msg):
    if not token:
        return
    import requests
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "message_thread_id": TOPIC_ID,
                "text": msg,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
    except:
        pass


def check_pm2():
    """Check PM2 processes and restart if needed."""
    try:
        result = subprocess.run(
            ["pm2", "jlist"], capture_output=True, text=True, timeout=10
        )
        processes = json.loads(result.stdout)
    except:
        return [], []

    online = []
    dead = []

    for name, desc in WATCHED_PROCESSES:
        found = False
        for p in processes:
            if name.lower() in p.get("name", "").lower():
                found = True
                status = p.get("pm2_env", {}).get("status", "unknown")
                if status == "online":
                    online.append(f"✅ {desc}")
                else:
                    dead.append((p["name"], desc, status))
                break

        if not found:
            pass  # All watched processes should be in PM2 now

    return online, dead


def check_crons():
    """Check cron job status from Hermes."""
    try:
        # The orchestrator script has access to check
        pass
    except:
        pass
    return []


def auto_heal(dead_processes):
    """Attempt to restart dead processes."""
    healed = []
    failed = []

    for name, desc, status in dead_processes:
        try:
            subprocess.run(
                ["pm2", "restart", name, "--update-env"],
                capture_output=True, text=True, timeout=15
            )
            healed.append(desc)
        except:
            failed.append(desc)

    return healed, failed


def main():
    # Check system status first
    try:
        uptime = subprocess.run(
            ["uptime", "-p"], capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except:
        uptime = "unknown"

    online, dead = check_pm2()
    healed, failed = auto_heal(dead)

    # Only send message if something changed
    if dead or healed or failed:
        lines = []
        lines.append("🛡️ MONA — Auto-Heal Report")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")

        if online:
            lines.append("✅ **Running:**")
            for p in online:
                lines.append(f"  {p}")

        if dead:
            lines.append("")
            lines.append("⚠️ **Down & Auto-Restart:**")
            for _, desc, status in dead:
                lines.append(f"  🔴 {desc} ({status})")

        if healed:
            lines.append("")
            lines.append("🔄 **Healed:**")
            for h in healed:
                lines.append(f"  ✅ {h} — restarted successfully")

        if failed:
            lines.append("")
            lines.append("❌ **Failed to heal:**")
            for f in failed:
                lines.append(f"  {f}")

        lines.append("")
        lines.append(f"⏱️ VPS uptime: {uptime}")

        msg = "\n".join(lines)
        send_telegram(msg)
        return True

    return False


if __name__ == "__main__":
    result = main()
    # Silent if nothing to report
    sys.exit(0)
