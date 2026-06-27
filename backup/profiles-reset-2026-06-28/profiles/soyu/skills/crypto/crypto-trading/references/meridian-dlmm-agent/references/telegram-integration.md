# Telegram Integration for Meridian

## Separate Bot Setup (Recommended)

### Step-by-step
1. Chat [@BotFather](https://t.me/BotFather) → `/newbot`
2. Name: `Meridian Agent` (or similar)
3. Username: `meridian_agent_bot` (must end with `bot`)
4. Save the token
5. Add bot to group as admin with **Manage Topics** permission
6. Send any message to the bot (DM) to register chat ID
7. Update Meridian `.env`:
```env
TELEGRAM_BOT_TOKEN=<new_bot_token>
TELEGRAM_CHAT_ID=-1003899936547
TELEGRAM_ALLOWED_USER_IDS=1492210461
```
8. Restart: `pm2 delete meridian && pm2 start ecosystem.config.cjs`

### Verification
```python
import httpx
resp = httpx.get(f'https://api.telegram.org/bot{token}/getMe')
print(resp.json())  # Should show bot info
```

## Forum Topic Support

### Setup
1. Add `TELEGRAM_MESSAGE_THREAD_ID=<topic_id>` to `.env`
2. Modify `telegram.js`:
```javascript
// After chatId declaration:
const THREAD_ID = process.env.TELEGRAM_MESSAGE_THREAD_ID || null;

// In postTelegram:
body: JSON.stringify({
  chat_id: chatId,
  ...(THREAD_ID ? { message_thread_id: Number(THREAD_ID) } : {}),
  ...body
}),
```

### Topic ID
- Group: `-1003899936547`
- Meridian topic: `947`

## Shared Bot Token with Hermes

When sharing a bot token with Hermes (Mona), only ONE can poll:

### Solution: TELEGRAM_NO_POLL
```env
# In Meridian .env:
TELEGRAM_NO_POLL=true
```

### Modify telegram.js
```javascript
export function startPolling(onMessage) {
  if (!TOKEN) return;
  if (process.env.TELEGRAM_NO_POLL === "true") {
    log("telegram", "Polling disabled — Hermes handles incoming messages");
    return;
  }
  _polling = true;
  poll(onMessage);
  registerCommands();
  log("telegram", "Bot polling started");
}
```

### Limitations
- Meridian can't handle `/positions`, `/close`, `/set` commands
- All commands must go through Mona
- Notifications still work (send-only)

## Bot Commands

Meridian registers these commands automatically:
- `/positions` — List open positions with progress bar
- `/close <n>` — Close position by index
- `/set <n> <note>` — Set note on position

## Notifications

Meridian sends notifications for:
- Deploy: pair, amount, position, tx hash
- Close: pair, PnL
- Swap: token → SOL after close
- OOR: position out of range alert
- Cycle reports: screening/management results

## Testing

```python
import httpx, base64, os

# Read bot token
vault_path = os.path.expanduser('~/mona-workspace/vault/.telegram_bot')
with open(vault_path) as f:
    token = base64.b64decode(f.read().strip()).decode()

# Send test message
url = f'https://api.telegram.org/bot{token}/sendMessage'
payload = {
    'chat_id': '-1003899936547',
    'message_thread_id': 947,
    'text': '✅ Test message',
    'parse_mode': 'HTML'
}
resp = httpx.post(url, json=payload, timeout=10)
print(resp.json())
```
