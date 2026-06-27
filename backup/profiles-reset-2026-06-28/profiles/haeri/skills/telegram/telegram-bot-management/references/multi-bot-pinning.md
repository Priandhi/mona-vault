# Multi-Bot Pinning in Forum Groups

## Problem

When multiple bots operate in the same Telegram forum group, each bot can only pin messages it sent. The Hermes `send_message` tool uses only the Mona bot — other bots require direct API calls.

## Bot Token Map

| Bot | Use Case | Token Source |
|-----|----------|-------------|
| Mona (@Monaa_Ai_Bot) | Main AI companion | `~/.hermes/.env` → `TELEGRAM_BOT_TOKEN` |
| DinoCantik (@DinoCantik_Bot) | Meridian DLMM | `~/mona-workspace/meridian/.env` → `TELEGRAM_BOT_TOKEN` |
| Charon Sniper | Token sniper | `~/mona-workspace/charon-sniper/config.json` → `telegram.botToken` |

## Topic Map

| System | Topic ID | Bot |
|--------|----------|-----|
| Charon Sniper | 1309 | Mona (send_message) or Charon bot |
| Meridian DLMM | 947 | DinoCantik |
| Main chat | (none) | Mona |

## Send + Pin Pattern (bash)

```bash
# 1. Source the correct bot's .env
source ~/mona-workspace/meridian/.env 2>/dev/null

# 2. Send to specific topic
RESULT=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "-1003899936547",
    "message_thread_id": 947,
    "text": "🌊 **MERIDIAN DLMM DASHBOARD**\nhttps://xxx.lhr.life\n\nMonitoring + Pool Scanner",
    "parse_mode": "Markdown"
  }')

# 3. Extract message_id
MSG_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['message_id'])")

# 4. Pin with SAME bot token
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/pinChatMessage" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\":\"-1003899936547\",\"message_id\":${MSG_ID}}"
```

## Send + Pin Pattern (Python — preferred)

```python
import os, requests

# Load bot token
token = os.environ.get('TELEGRAM_BOT_TOKEN')
if not token:
    with open(os.path.expanduser('~/mona-workspace/meridian/.env')) as f:
        for line in f:
            if line.startswith('TELEGRAM_BOT_TOKEN='):
                token = line.strip().split('=', 1)[1]
                break

base = f"https://api.telegram.org/bot{token}"
chat_id = "-1003899936547"
thread_id = 947

# Send
r = requests.post(f"{base}/sendMessage", json={
    "chat_id": chat_id,
    "message_thread_id": thread_id,
    "text": "🌊 **DASHBOARD**\nhttps://xxx.lhr.life",
    "parse_mode": "Markdown"
})
msg_id = r.json()["result"]["message_id"]

# Pin
r2 = requests.post(f"{base}/pinChatMessage", json={
    "chat_id": chat_id,
    "message_id": msg_id
})
print("PINNED" if r2.json().get("ok") else f"FAIL: {r2.json()}")
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "message to pin not found" | Pinning with Bot B a message sent by Bot A | Use SAME bot's token for send+pin |
| "not enough rights to pin" | Bot not admin or missing Manage Topics | Promote bot to admin + enable Manage Topics |
| "Bad Request: message thread not found" | Wrong topic ID | Check topic ID with `getUpdates` or `getForumTopicIcon` |
| "Forbidden: bot is not a member" | Bot not in group | Add bot to group first |

## Verification

After send+pin, verify with:
```bash
# Check pinned message
curl -s "https://api.telegram.org/bot${TOKEN}/getChat" \
  -d '{"chat_id":"-1003899936547"}' | python3 -c "
import sys,json
d = json.load(sys.stdin)
pinned = d.get('result',{}).get('pinned_message',{})
print(f'Pinned: msg_id={pinned.get(\"message_id\")}, text={pinned.get(\"text\",\"\")[:50]}')
"
```
