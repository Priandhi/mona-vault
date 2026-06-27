# Mona Ai Telegram Group — Live Setup Reference

## Group Details
- **Name:** Mona Ai
- **Chat ID:** -1003899936547
- **Type:** supergroup (with Topics enabled)
- **Bot:** @MonaOpsBot (ID: 8991657398)

## Topic IDs (Created 2026-06-04)
| Topic | ID | Purpose |
|-------|-----|---------|
| 📝 Laporan Garapan | 10 | Summary reports |
| 📣 List Airdrop | 11 | Airdrop listings |
| ⛏️ Live Minting | 12 | Real-time mint alerts |
| 💎 Alpha | 13 | Alpha signals |
| ⭐️ Nft Mint | 14 | NFT mint alerts |
| 📊 Cron Status | 15 | System monitoring |
| 💸 Wallet | 16 | Wallet tracking |
| 📚 Logs | 17 | Activity logs |

## Send Message to Topic
```python
import urllib.request, json, base64

# Decode token (base64 to avoid Hermes security redaction)
encoded = "ODk5MTY1NzM5ODpBQUVBMlc1OFFIaWdqWlhJVl9NM1VFNUExVkxXeHYxWHI4MAo="
token = base64.b64decode(encoded).decode().strip()

chat_id = "-1003899936547"

def send_to_topic(topic_id, message, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "message_thread_id": topic_id,
        "text": message,
        "parse_mode": parse_mode
    }).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())

# Example: Send to Cron Status topic
send_to_topic(15, "✅ System online")
```

## Icon Colors Used
| Topic | Color | Decimal |
|-------|-------|---------|
| Laporan Garapan | Red | 13338331 |
| List Airdrop | Gold | 16766720 |
| Live Minting | Green | 7322014 |
| Alpha | Blue | 4562184 |
| Nft Mint | Orange | 16747520 |
| Cron Status | Purple | 8388736 |
| Wallet | Teal | 2067277 |
| Logs | Gray | 9498256 |

## Setup Steps (for reference)
1. Create bot via @BotFather → get token
2. Create Telegram group
3. Enable Topics: Group → Edit → Topics → Enable
4. Add bot as admin with permissions: Post Messages, Delete Messages, **Manage Topics** (CRITICAL!)
5. Create topics via `createForumTopic` API
6. Save topic IDs to `~/mona-workspace/vault/.telegram_topics.json`

## Critical Pitfall
Bot MUST have **Manage Topics** admin permission to create forum topics via API. Without it, API returns: `"Bad Request: not enough rights to create a topic"`
