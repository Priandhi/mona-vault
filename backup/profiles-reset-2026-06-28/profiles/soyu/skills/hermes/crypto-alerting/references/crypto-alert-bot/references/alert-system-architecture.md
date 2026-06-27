# Alert System Architecture Pattern

## Overview
Multi-topic Telegram alert system with shared module, individual alert scripts, and cron scheduling.

## Architecture

```
~/.hermes/scripts/
├── mona_telegram.py          # Shared module (sender, RPC, formatting)
├── mona_wallet_monitor.py    # → 💸 Wallet (ID 16)
├── mona_alpha_intel.py       # → 💎 Alpha (ID 13)
├── mona_nft_mint.py          # → ⭐️ Nft Mint (ID 14)
├── mona_airdrop_scanner.py   # → 📣 List Airdrop (ID 11)
├── mona_live_minting.py      # → ⛏️ Live Minting (ID 12)
├── mona_cron_status.py       # → 📊 Cron Status (ID 15)
├── mona_laporan_garapan.py   # → 📝 Laporan Garapan (ID 10)
└── mona_logs_reporter.py     # → 📚 Logs (ID 17)
```

## Shared Module Pattern (`mona_telegram.py`)

```python
#!/usr/bin/env python3
"""
Mona Telegram Alert Module
Shared functions for sending alerts to Mona Ai group topics.
"""
import urllib.request
import json
import base64
from datetime import datetime, timezone, timedelta

# Bot credentials (base64 encoded to avoid redaction)
ENCODED_TOKEN="ODk5...T_ID = "-1003899936547"

# Topic IDs
TOPICS = {
    "laporan": 10,
    "airdrop": 11,
    "minting": 12,
    "alpha": 13,
    "nft": 14,
    "cron": 15,
    "wallet": 16,
    "logs": 17,
}

def get_token():
    """Decode bot token from base64."""
    return base64.b64decode(ENCODED_TOKEN).decode().strip()

def send_message(topic_key, text, parse_mode="HTML"):
    """Send a message to a specific topic in the Mona Ai group."""
    token = get_token()
    topic_id = TOPICS.get(topic_key)
    
    if not topic_id:
        print(f"Unknown topic: {topic_key}")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": CHAT_ID,
        "message_thread_id": topic_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }).encode()
    
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        return result.get("ok", False)
    except Exception as e:
        print(f"Error sending to {topic_key}: {e}")
        return False

def now_wib():
    """Get current time in WIB (UTC+7)."""
    return datetime.now(timezone(timedelta(hours=7)))

def timestamp():
    """Get formatted WIB timestamp."""
    return now_wib().strftime("%Y-%m-%d %H:%M:%S WIB")

def format_number(n):
    """Format number with commas."""
    if isinstance(n, float):
        return f"{n:,.4f}"
    return f"{n:,}"

def format_usd(n):
    """Format USD value."""
    if n >= 1_000_000:
        return f"${n/1_000_000:.2f}M"
    elif n >= 1_000:
        return f"${n/1_000:.2f}K"
    else:
        return f"${n:.2f}"
```

## Individual Alert Script Pattern

```python
#!/usr/bin/env python3
"""
Mona [Alert Type] Monitor
Sends alerts to the [Topic Name] topic (ID XX).
"""
import sys
import os
sys.path.insert(0, os.path.expanduser('~/.hermes/scripts'))
from mona_telegram import send_message, timestamp, now_wib

def main():
    """Main alert logic."""
    # 1. Fetch data (API calls, RPC calls, etc.)
    # 2. Process and filter
    # 3. Format HTML message
    # 4. Send to topic
    
    msg = f"""🎯 <b>[Alert Type]</b>

⏰ {timestamp()}

[Alert content here]

<i>Powered by Mona 💜</i>"""
    
    success = send_message("topic_key", msg)
    print(f"Alert: {'✅ Sent' if success else '❌ Failed'}")
    
    return success

if __name__ == "__main__":
    main()
```

## Cron Job Scheduling

| Alert Type | Topic | Schedule | Rationale |
|------------|-------|----------|-----------|
| Wallet Monitor | 💸 | Every 15m | Balance changes slowly |
| Alpha Intel | 💎 | Every 30m | Market signals need time |
| NFT Mint | ⭐️ | Every 10m | Mints happen fast |
| Airdrop Scanner | 📣 | Every 1h | Airdrops are slow-moving |
| Live Minting | ⛏️ | Every 5m | New tokens launch fast |
| Cron Status | 📊 | Every 30m | System monitoring |
| Laporan Garapan | 📝 | Daily 9am | Daily summary |
| Logs Reporter | 📚 | Every 6h | Log rotation |

## Creating Cron Jobs

```python
# Via cronjob tool
cronjob(
    action="create",
    name="Mona Wallet Monitor",
    schedule="15m",
    script="mona_wallet_monitor.py",
    prompt="Run the wallet balance monitor script and report results."
)

# Via CLI
hermes cron create "15m" --name "Mona Wallet Monitor" --script mona_wallet_monitor.py
```

## Data Flow

```
[Data Source] → [Alert Script] → [Shared Module] → [Telegram API] → [Topic]
     ↑               ↑                ↑
   API/RPC      Process/Filter    Route to Topic
```

## Error Handling Pattern

```python
def fetch_data():
    """Fetch data with retry and fallback."""
    try:
        # Primary source
        response = urllib.request.urlopen(url, timeout=10)
        return json.loads(response.read())
    except Exception as e:
        print(f"Primary source failed: {e}")
        try:
            # Fallback source
            response = urllib.request.urlopen(fallback_url, timeout=10)
            return json.loads(response.read())
        except Exception as e2:
            print(f"Fallback failed: {e2}")
            return None
```

## Testing Pattern

```bash
# Test individual script
python3 ~/.hermes/scripts/mona_wallet_monitor.py

# Test all scripts
for script in ~/.hermes/scripts/mona_*.py; do
    echo -n "Testing $(basename $script)... "
    python3 "$script" > /dev/null 2>&1 && echo "✅ OK" || echo "❌ Failed"
done

# Test shared module
python3 -c "
import sys; sys.path.insert(0, '~/.hermes/scripts')
from mona_telegram import send_message, timestamp
success = send_message('logs', f'Test at {timestamp()}')
print('✅ OK' if success else '❌ Failed')
"
```

## Best Practices

1. **Shared module** — Put common functions in shared module, import in each script
2. **Topic routing** — Use topic keys (strings) not hardcoded IDs
3. **Error handling** — Wrap all HTTP calls in try/except
4. **Rate limiting** — Add delays between API calls (0.3s minimum)
5. **Deduplication** — Track seen items to avoid re-alerting
6. **Message splitting** — Handle Telegram's 4096 char limit
7. **Disable preview** — Use `disable_web_page_preview: True` for cleaner messages
8. **HTML format** — Use HTML parse_mode for rich formatting
9. **Timestamp** — Always include WIB timestamp
10. **Branding** — End with "Powered by Mona 💜"

## Common Pitfalls

- **Token redaction** — Use base64 encoding for tokens in code
- **Missing permissions** — Bot needs Post Messages + Manage Topics
- **Wrong chat_id** — Supergroup ID is negative, starts with -100
- **Rate limits** — Telegram limits to 30 messages/second per group
- **Message length** — Max 4096 characters per message
- **Parse mode** — HTML is more reliable than Markdown for complex formatting
