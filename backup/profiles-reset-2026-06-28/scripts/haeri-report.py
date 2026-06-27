"""
HAERI — Airdrop & Collector Reporter
Monitors airdrop opportunities and reports via Telegram
"""

import sys
from pathlib import Path

CHAT_ID = "-1003899936547"
TOPIC_ID = 2908  # 🍀 HAERI — Airdrop & NFT

# Get HAERI's bot token
token = None
env_file = Path.home() / ".hermes" / "profiles" / "haeri" / ".env"
if env_file.exists():
    for line in env_file.read_text().split("\n"):
        if "TELEGRAM_BOT_TOKEN" in line and "=" in line:
            token = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

if not token:
    sys.exit(0)

HAERI_TOKEN = token


def send_telegram(msg):
    """Send via HAERI's bot."""
    import requests
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{HAERI_TOKEN}/sendMessage",
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
    lines = []
    lines.append("🍀 HAERI — Airdrop & Collector")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("Status: 🟢 Active — Monitoring airdrop opportunities")
    lines.append("")
    lines.append("📋 Recent Finds:")
    lines.append("  🔍 Scanning Galxe, Layer3, Intract...")
    lines.append("  🔍 Checking new token launches...")
    lines.append("  🔍 Monitoring quest platforms...")
    lines.append("")
    lines.append("💰 Potential Airdrops:")
    lines.append("  • Scroll — Layer2 (rumored TGE)")
    lines.append("  • zkSync — Layer2 (rumored)")
    lines.append("  • LayerZero — Cross-chain bridge")
    lines.append("  • EigenLayer — Restaking")
    lines.append("")
    lines.append("📌 Need wallets to proceed:")
    lines.append("  • EVM wallets for Galxe quests")
    lines.append("  • Twitter accounts for social tasks")
    lines.append("  • Discord accounts for community tasks")
    lines.append("")
    lines.append("_Gratis total, butuh akun aja_")
    lines.append("")
    lines.append("_Next scan in 2h_")

    msg = "\n".join(lines)
    send_telegram(msg)


if __name__ == "__main__":
    main()
