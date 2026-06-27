"""
YERIN — Mining Status Reporter
Reports CPU/GPU mining status via Telegram
"""

import subprocess
import sys
from pathlib import Path

CHAT_ID = "-1003899936547"
TOPIC_ID = 2907  # ⛏️ YERIN — Mining Ops

# Get YERIN's bot token
token = None
env_file = Path.home() / ".hermes" / "profiles" / "yerin" / ".env"
if env_file.exists():
    for line in env_file.read_text().split("\n"):
        if "TELEGRAM_BOT_TOKEN" in line and "=" in line:
            token = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

if not token:
    sys.exit(0)

YERIN_TOKEN = token


def check_mining_processes():
    """Check if any mining processes are running."""
    try:
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.split("\n")
        mining_keywords = ["xmrig", "juno", "randomx", "miner", "ccminer", "gominer"]
        found = []
        for line in lines:
            for kw in mining_keywords:
                if kw in line.lower():
                    found.append(line.strip())
        return found
    except Exception:
        return []


def check_pm2_mining():
    """Check PM2 for mining processes."""
    try:
        result = subprocess.run(
            ["pm2", "jlist"], capture_output=True, text=True, timeout=5
        )
        import json
        processes = json.loads(result.stdout)
        mining_procs = []
        for p in processes:
            name = p.get("name", "").lower()
            if any(kw in name for kw in ["mining", "xmrig", "juno", "yerin"]):
                status = p.get("pm2_env", {}).get("status", "unknown")
                mining_procs.append({"name": p["name"], "status": status})
        return mining_procs
    except Exception:
        return []


def get_cpu_info():
    """Get CPU load info."""
    try:
        load = subprocess.run(
            ["uptime"], capture_output=True, text=True, timeout=3
        ).stdout.strip()
        cpu = subprocess.run(
            ["nproc"], capture_output=True, text=True, timeout=3
        ).stdout.strip()
        return {"cores": cpu, "load": load}
    except Exception:
        return {"cores": "?", "load": "unknown"}


def send_telegram(msg):
    """Send via YERIN's bot."""
    import requests
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{YERIN_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "message_thread_id": TOPIC_ID,
                "text": msg,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
        return resp.json().get("ok", False)
    except Exception:
        return False


def main():
    mining_procs = check_mining_processes()
    pm2_procs = check_pm2_mining()
    cpu = get_cpu_info()

    lines = []
    lines.append("⛏️ YERIN — Mining Status")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    if mining_procs or pm2_procs:
        lines.append(f"CPU Cores: {cpu['cores']}")
        lines.append(f"Load: {cpu['load']}")
        lines.append("")
        lines.append(f"Active Miners: {len(mining_procs) + len(pm2_procs)}")
        for p in mining_procs:
            lines.append(f"  🔸 {p[:80]}...")
        for p in pm2_procs:
            lines.append(f"  🔸 {p['name']} ({p['status']})")
    else:
        lines.append("Status: 💤 Idle")
        lines.append("CPU Cores: {cpu['cores']}")
        lines.append("")
        lines.append("Belum ada mining process aktif.")
        lines.append("Siap setup: RandomX / Juno Cash / CPU mining")
        lines.append("")
        lines.append("_Gratis, pake CPU doang_")

    lines.append("")
    lines.append("_Next check in 1h_")

    msg = "\n".join(lines)
    send_telegram(msg)


if __name__ == "__main__":
    main()
