# Multi-Bot Pinning in Forum Groups

When multiple bots operate in the same Telegram forum group, each bot can only pin messages it sent. The Hermes `send_message` tool uses only the Mona bot — other bots require direct API calls.

## Send + Pin Pattern (Python)

```python
import os, requests

token = os.environ.get('TELEGRAM_BOT_TOKEN')
base = f"https://api.telegram.org/bot{token}"
chat_id = "-1003899936547"
thread_id = 947

# Send
r = requests.post(f"{base}/sendMessage", json={
    "chat_id": chat_id, "message_thread_id": thread_id,
    "text": "🌊 **DASHBOARD**\nhttps://xxx.lhr.life",
    "parse_mode": "Markdown"
})
msg_id = r.json()["result"]["message_id"]

# Pin with SAME bot token
r2 = requests.post(f"{base}/pinChatMessage", json={
    "chat_id": chat_id, "message_id": msg_id
})
```

**Common error:** "message to pin not found" = pinning with Bot B a message sent by Bot A. Always use SAME bot's token for send+pin.
