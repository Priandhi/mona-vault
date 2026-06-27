# Telegram Forum Topic Creation API

## Create Forum Topic

```bash
curl -X POST "https://api.telegram.org/bot{TOKEN}/createForumTopic" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "{CHAT_ID}",
    "name": "Topic Name",
    "icon_color": 13338331
  }'
```

## Response Format
```json
{
  "ok": true,
  "result": {
    "message_thread_id": 123,
    "name": "Topic Name",
    "icon_color": 13338331
  }
}
```

## Topic Icon Colors (Decimal)

| Color | Decimal | Hex | Use Case |
|-------|---------|-----|----------|
| Red | 13338331 | 0xCB5F4B | Alerts, Errors |
| Gold | 16766720 | 0xFFD700 | Airdrop, Rewards |
| Green | 7322014 | 0x6FB9F0 | Success, Mint |
| Blue | 4562184 | 0x4582C8 | General, Info |
| Orange | 16747520 | 0xFF8C00 | NFT, Warning |
| Purple | 8388736 | 0x800080 | Status, Cron |
| Teal | 2067277 | 0x1F9B4D | Wallet, Finance |
| Gray | 9498256 | 0x909090 | Logs, Debug |

## Standard Crypto Ops Topics

```python
CRYPTO_TOPICS = [
    {"name": "📝 Laporan Garapan", "icon_color": 13338331},  # Red
    {"name": "📣 List Airdrop", "icon_color": 16766720},     # Gold
    {"name": "⛏️ Live Minting", "icon_color": 7322014},      # Green
    {"name": "💎 Alpha", "icon_color": 4562184},              # Blue
    {"name": "⭐️ Nft Mint", "icon_color": 16747520},        # Orange
    {"name": "📊 Cron Status", "icon_color": 8388736},        # Purple
    {"name": "💸 Wallet", "icon_color": 2067277},             # Teal
    {"name": "📚 Logs", "icon_color": 9498256},               # Gray
]
```

## Send Message to Topic

```bash
curl -X POST "https://api.telegram.org/bot{TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "{CHAT_ID}",
    "message_thread_id": {TOPIC_ID},
    "text": "Your message here",
    "parse_mode": "HTML"
  }'
```

## Python Implementation

```python
import requests

class TelegramForumBot:
    def __init__(self, token):
        self.token = token
        self.api = f"https://api.telegram.org/bot{token}"
    
    def create_topic(self, chat_id, name, icon_color=0x6FB9F0):
        """Create new topic in forum group"""
        result = requests.post(f"{self.api}/createForumTopic", json={
            "chat_id": chat_id,
            "name": name,
            "icon_color": icon_color
        }).json()
        
        if result.get("ok"):
            return result["result"]["message_thread_id"]
        else:
            raise Exception(result.get("description"))
    
    def send_to_topic(self, chat_id, topic_id, message, parse_mode="HTML"):
        """Send message to specific topic"""
        result = requests.post(f"{self.api}/sendMessage", json={
            "chat_id": chat_id,
            "message_thread_id": topic_id,
            "text": message,
            "parse_mode": parse_mode
        }).json()
        
        if not result.get("ok"):
            raise Exception(result.get("description"))
        
        return result
    
    def create_crypto_ops_topics(self, chat_id):
        """Create standard crypto ops topics"""
        topics = [
            ("📝 Laporan Garapan", 13338331),
            ("📣 List Airdrop", 16766720),
            ("⛏️ Live Minting", 7322014),
            ("💎 Alpha", 4562184),
            ("⭐️ Nft Mint", 16747520),
            ("📊 Cron Status", 8388736),
            ("💸 Wallet", 2067277),
            ("📚 Logs", 9498256),
        ]
        
        created = []
        for name, color in topics:
            try:
                topic_id = self.create_topic(chat_id, name, color)
                created.append({"name": name, "id": topic_id})
                print(f"  ✅ {name} → ID: {topic_id}")
            except Exception as e:
                print(f"  ❌ {name} → {e}")
        
        return created

# Usage
bot = TelegramForumBot("YOUR_TOKEN")
topics = bot.create_crypto_ops_topics("-1001234567890")
```

## Setup Checklist

1. [ ] Create bot via @BotFather
2. [ ] Save token to `~/mona-workspace/vault/.telegram_bot` (chmod 600)
3. [ ] Create Telegram group
4. [ ] Enable Topics: Group → Edit → Topics → Enable
5. [ ] Add bot as admin with permissions:
   - [ ] Post Messages
   - [ ] Delete Messages
   - [ ] Manage Topics
6. [ ] Get chat_id (forward message to @userinfobot)
7. [ ] Create topics via API
8. [ ] Save topic IDs to `~/mona-workspace/vault/.telegram_topics.json`
9. [ ] Test message routing to each topic

## Troubleshooting

### "Not Found" Error
- Check bot token is correct
- Verify bot is admin in group
- Ensure chat_id format is correct (negative, starts with -100)

### "Bad Request: not enough rights"
- Bot needs Manage Topics permission
- Re-add bot as admin with all permissions

### Token Redaction
- Some VPS security systems redact tokens in output
- Use Python to read token from file programmatically
- Test with `curl` using environment variable

### Topics Not Showing
- Topics must be enabled in Group Settings first
- Group must be supergroup (convert if needed)
- Bot must have Manage Topics permission
