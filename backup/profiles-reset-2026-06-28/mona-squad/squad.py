"""
Mona Squad — Multi-Agent Communication System
==============================================
Agents can send messages to each other, request help,
and coordinate tasks via shared kanban boards.

Agents:
  MONA 🧠 — Architect / Orchestrator
  YUNA 💹 — Trading Strategist (Dozero.X, Binance Futures)
  SOYU 🎯 — Sniper (Charon, token launches)
  YERIN ⛏️ — Miner (RandomX, Juno Cash, GPU mining)
  HAERI 🍀 — Collector (Airdrops, NFTs, Galxe)
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

BASE_DIR = Path.home() / "mona-workspace" / "mona-squad"
INBOX_DIR = BASE_DIR / "inbox"
LOG_FILE = BASE_DIR / "messages" / "message-log.md"

AGENTS = {
    "MONA": "🧠 Mona — The Architect",
    "YUNA": "💹 YUNA — The Strategist (Trading)",
    "SOYU": "🎯 SOYU — The Phantom (Sniper)",
    "YERIN": "⛏️ YERIN — The Grinder (Mining)",
    "HAERI": "🍀 HAERI — The Collector (Airdrop/NFT)",
}

KANBAN_FILES = {
    "MONA": Path.home() / "obsidian-vault" / "06-KANBAN" / "master-kanban.md",
    "YUNA": Path.home() / "obsidian-vault" / "06-KANBAN" / "yuna-trading.md",
    "SOYU": Path.home() / "obsidian-vault" / "06-KANBAN" / "soyu-sniper.md",
    "YERIN": Path.home() / "obsidian-vault" / "06-KANBAN" / "yerin-mining.md",
    "HAERI": Path.home() / "obsidian-vault" / "06-KANBAN" / "haeri-airdrop.md",
}


def send_message(from_agent: str, to_agent: str, subject: str, body: str,
                 priority: str = "normal", task_id: str = "") -> bool:
    """
    Send a message from one agent to another.
    Message is written to the recipient's inbox.
    """
    from_agent = from_agent.upper()
    to_agent = to_agent.upper()
    
    if from_agent not in AGENTS:
        print(f"❌ Unknown sender: {from_agent}")
        return False
    if to_agent not in AGENTS:
        print(f"❌ Unknown recipient: {to_agent}")
        return False
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg_id = f"msg_{int(time.time())}"
    
    # Format message
    priority_icon = {"high": "🔴", "normal": "🟡", "low": "🟢"}
    p_icon = priority_icon.get(priority, "🟡")
    
    msg = f"""
### {p_icon} [{timestamp}] — {AGENTS[from_agent]} → {AGENTS[to_agent]}

**Subject:** {subject}
**Priority:** {priority.upper()}
**Message ID:** `{msg_id}`

{body}

---
*To reply: use `send_message(from="{to_agent}", to="{from_agent}", ...)`*
"""

    # Write to inbox
    inbox_file = INBOX_DIR / f"{to_agent.lower()}.md"
    current = inbox_file.read_text()
    
    # Insert after header
    if "___" in current:
        current += msg + "\n"
    else:
        current += msg + "\n"
    
    inbox_file.write_text(current)
    print(f"✅ Message sent: {from_agent} → {to_agent}: {subject}")
    return True


def read_inbox(agent: str, clear: bool = False) -> str:
    """Read messages in an agent's inbox."""
    agent = agent.upper()
    inbox_file = INBOX_DIR / f"{agent.lower()}.md"
    if not inbox_file.exists():
        return f"No inbox found for {agent}"
    
    content = inbox_file.read_text()
    if clear:
        # Reset inbox (keep header)
        inbox_file.write_text(f"# 📥 Inbox — {AGENTS[agent]}\n\n_Pesan dari agent lain akan muncul di sini._\n")
    
    return content


def add_kanban_task(agent: str, section: str, task: str) -> bool:
    """Add a task to an agent's kanban board."""
    agent = agent.upper()
    kb_file = KANBAN_FILES.get(agent)
    if not kb_file or not kb_file.exists():
        print(f"❌ Kanban not found for {agent}")
        return False
    
    valid_sections = ["BACKLOG", "IN PROGRESS", "PENDING REVIEW", "DONE"]
    if section not in valid_sections:
        print(f"❌ Invalid section: {section}. Use: {valid_sections}")
        return False
    
    content = kb_file.read_text()
    marker = f"## {section}"
    task_line = f"- [ ] {task}\n"
    
    if marker in content:
        content = content.replace(marker, f"{marker}\n{task_line}", 1)
        kb_file.write_text(content)
        print(f"✅ Task added to {agent}'s {section}: {task}")
        return True
    else:
        print(f"❌ Section {section} not found in {agent}'s kanban")
        return False


def move_kanban_task(agent: str, task_text: str, from_section: str, to_section: str) -> bool:
    """Move a task between kanban sections."""
    agent = agent.upper()
    kb_file = KANBAN_FILES.get(agent)
    if not kb_file or not kb_file.exists():
        return False
    
    content = kb_file.read_text()
    
    # Find and update the task
    old_marker = f"- [ ] {task_text}"
    new_marker = f"- [ ] {task_text}"  # Same format but in new section
    
    # Remove from old section
    lines = content.split("\n")
    new_lines = []
    found = False
    in_old_section = False
    in_new_section = False
    
    for line in lines:
        if line.strip().startswith(f"## {from_section}"):
            in_old_section = True
            new_lines.append(line)
            continue
        if line.strip().startswith(f"## {to_section}"):
            in_new_section = True
            in_old_section = False
            new_lines.append(line)
            new_lines.append(old_marker)
            found = True
            continue
        if in_old_section and line.strip().startswith("- [") and task_text in line:
            # Skip this line (removing from old section)
            continue
        if line.strip().startswith("## ") and line.strip()[2:].strip() not in (from_section, to_section):
            in_old_section = False
            in_new_section = False
        
        new_lines.append(line)
    
    if found:
        kb_file.write_text("\n".join(new_lines))
        print(f"✅ Task moved: {task_text} ({from_section} → {to_section})")
        return True
    else:
        print(f"⚠️ Task not found: {task_text}")
        return False


def check_all_inboxes() -> dict:
    """Check all agent inboxes for new messages. Returns summary."""
    summary = {}
    for agent in AGENTS:
        inbox_file = INBOX_DIR / f"{agent.lower()}.md"
        if inbox_file.exists():
            content = inbox_file.read_text()
            msg_count = content.count("### 🟡") + content.count("### 🔴") + content.count("### 🟢")
            unread = msg_count
            summary[agent] = {"name": AGENTS[agent], "unread": unread}
        else:
            summary[agent] = {"name": AGENTS[agent], "unread": 0}
    return summary


def format_squad_status() -> str:
    """Format squad status for display."""
    summary = check_all_inboxes()
    lines = ["🧠 MONA SQUAD — Status Report", "━━━━━━━━━━━━━━━━━━━", ""]
    
    for agent, info in summary.items():
        inbox_icon = "📬" if info["unread"] > 0 else "📭"
        lines.append(f"{inbox_icon} {info['name']} — {info['unread']} pesan")
    
    lines.append("")
    lines.append(f"🕐 Last check: {datetime.now().strftime('%H:%M:%S')}")
    
    return "\n".join(lines)


def sync_to_master_kanban():
    """Sync all agent tasks to master kanban."""
    master_file = KANBAN_FILES["MONA"]
    if not master_file.exists():
        return
    
    content = master_file.read_text()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Update last update date
    for line in content.split("\n"):
        if "Last Update" in line:
            content = content.replace(line, f"> Last Update: {today}")
            break
    
    master_file.write_text(content)


if __name__ == "__main__":
    # Test: print squad status
    print(format_squad_status())
    print()
    
    # Example: send test message from MONA to YUNA
    # send_message("MONA", "YUNA", "Koordinasi Strategy", "Ada signal SMC, monitor terus ya.")
