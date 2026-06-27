# Telegram Status Report Delivery

## Chat ID Mapping

| Purpose | Chat ID | Type | Notes |
|---|---|---|---|
| User DM (HOME_CHANNEL) | `1492210461` | user | Default delivery target, NOT for forum topics |
| Supergroup (forum) | `-1003899936547` | supergroup | Use this for topic-based delivery |
| Auto-heal topic | thread_id `1309` | forum topic | PM2 health reports |
| Charon sniper topic | thread_id `1309` | forum topic | DRY RUN status reports |

## Quick Bash Extraction (for curl commands)

When you need the token for a quick `curl` call (not worth spinning up Python):

```bash
# Extract from .env (NEVER source the .env — it has malformed lines)
BOT_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" ~/.hermes/.env | tail -1 | cut -d= -f2-)
CHAT_ID="-1003899936547"  # supergroup, NOT from TELEGRAM_HOME_CHANNEL

curl -s "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -d chat_id="${CHAT_ID}" \
  -d message_thread_id=1309 \
  -d text="Status: OK"
```

**PITFALL:** `TELEGRAM_HOME_CHANNEL` in `.env` is the user DM ID (`1492210461`). Always hardcode the supergroup ID (`-1003899936547`) for forum delivery. The `.env` has NO `TELEGRAM_CHAT_ID` for the supergroup.

**PITFALL:** Use `tail -1` not `head -1` — `.env` may have duplicate `TELEGRAM_BOT_TOKEN=` lines. Last one wins.

## Token Sources (in order of reliability)

1. **Vault (base64-encoded):** `~/mona-workspace/vault/.telegram_bot`
   - Content: base64-encoded `{bot_id}:{secret}`
   - Must decode: `base64.b64decode(content).decode().strip()`
   - This is the @Monaa_Ai_Bot token

2. **`.env` (plaintext, may be redacted):** `~/.hermes/.env`
   - `TELEGRAM_BOT_TOKEN=8389764935:***`
   - Hermes security.redact_secrets may mask it in output

3. **Multiple tokens exist:** `.env` may have duplicate `TELEGRAM_BOT_TOKEN=` lines.
   - The LAST one wins.
   - Check with: `grep TELEGRAM_BOT_TOKEN ~/.hermes/.env | grep -v '^#'`

## Sending Pattern (Python)

```python
import base64, requests, os

# Read and decode vault token
with open(os.path.expanduser("~/mona-workspace/vault/.telegram_bot")) as f:
    token = base64.b64decode(f.read().strip()).decode().strip()

api = f"https://api.telegram.org/bot{token}"

# Send to forum topic
resp = requests.post(f"{api}/sendMessage", json={
    "chat_id": -1003899936547,       # supergroup, NOT user DM
    "message_thread_id": 1309,       # forum topic
    "text": "<b>Status OK</b>",
    "parse_mode": "HTML",
    "disable_web_page_preview": True
})

result = resp.json()
# result["ok"] == True means success
# "Not Found" error usually means wrong chat_id (DM instead of supergroup)
```

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `Bad Request: chat not found` | Using user DM ID instead of supergroup ID | Use `-1003899936547` |
| `Not Found` | Token doesn't have access to the group | Check bot is admin in the group |
| `Unauthorized` | Wrong or expired token | Check vault token, verify with getMe |
| `Bad Request: message thread not found` | Topic ID doesn't exist | Check topic exists, bot has Manage Topics permission |

## Verification Command

```bash
# Quick token + access check
python3 -c "
import base64, requests, os
with open(os.path.expanduser('~/mona-workspace/vault/.telegram_bot')) as f:
    token = base64.b64decode(f.read().strip()).decode().strip()
r = requests.get(f'https://api.telegram.org/bot{token}/getMe').json()
print(f'Bot: @{r[\"result\"][\"username\"]}' if r.get('ok') else f'Error: {r.get(\"description\")}')
"
```
