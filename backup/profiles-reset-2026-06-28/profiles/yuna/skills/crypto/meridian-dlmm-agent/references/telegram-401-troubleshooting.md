# Telegram 401 Unauthorized — Troubleshooting

## Symptoms

- PM2 logs show repeated `sendChatAction 401` and `sendMessage 401` errors
- Bot appears "online" in PM2 — process does NOT crash or error
- ALL notifications silently lost (deploy, close, OOR, cycle reports)
- LLM agent loop continues working — only Telegram output is broken

## Root Cause

The `TELEGRAM_BOT_TOKEN` in `.env` is invalid, expired, or revoked. Common scenarios:
- Token was revoked via @BotFather (`/revokentoken`)
- Bot was deleted and recreated (old token invalidated)
- Token was corrupted during `.env` edit

## Detection

```bash
# Check for 401 errors in PM2 logs
grep "401" ~/.pm2/logs/meridian-out-*.log | tail -5

# Expected output if broken:
# [TELEGRAM_ERROR] sendChatAction 401: {"ok":false,"error_code":401,"description":"Unauthorized"}
# [TELEGRAM_ERROR] sendMessage 401: {"ok":false,"error_code":401,"description":"Unauthorized"}
```

**PITFALL:** PM2 status shows "online" even when every Telegram call fails. Always check logs for 401, not just PM2 status.

## Fix

1. Get new token from @BotFather: `/newbot` or `/revokentoken` then `/newtoken`
2. Update `TELEGRAM_BOT_TOKEN` in `~/mona-workspace/meridian/.env`
3. Delete and recreate PM2 process (NOT just restart — env vars are cached):
   ```bash
   pm2 delete meridian && pm2 start ecosystem.config.cjs
   ```
4. Verify: `pm2 logs meridian --lines 10 --nostream` — should show bot polling started, no 401

## Verification Script

```python
import httpx, os

# Read token from .env
token = None
with open(os.path.expanduser('~/mona-workspace/meridian/.env')) as f:
    for line in f:
        if line.startswith('TELEGRAM_BOT_TOKEN='):
            token = line.split('=', 1)[1].strip()
            break

if not token:
    print("ERROR: No TELEGRAM_BOT_TOKEN found in .env")
    exit(1)

# Test token validity
resp = httpx.get(f'https://api.telegram.org/bot{token}/getMe', timeout=10)
data = resp.json()
if data.get('ok'):
    print(f"✅ Token valid — bot: @{data['result']['username']}")
else:
    print(f"❌ Token invalid — {data.get('description', 'unknown error')}")
```

## Related Pitfalls

- **PM2 env caching:** `pm2 restart` does NOT reload `.env`. Even `pm2 restart --update-env` can fail. Must use `pm2 delete && pm2 start ecosystem.config.cjs`. Verified Jun11: changed token in `.env`, ran `pm2 restart --update-env`, but `/proc/PID/environ` still showed OLD token. Only `pm2 delete && pm2 start` loaded the new token.
- **`--update-env` is unreliable:** PM2's `--update-env` flag re-reads env from ecosystem.config.cjs but may NOT re-read `.env` (which is loaded by dotenv at app startup, not by PM2). Since Telegram token is in `.env` (not ecosystem.config.cjs), `--update-env` doesn't help. Always delete+start.
- **Shared bot token:** If Meridian shares a token with Hermes (Mona), revoking the token breaks BOTH bots. Always create a dedicated bot for Meridian.
- **Silent failure:** Unlike 402/429 errors which cause retries, 401 on Telegram calls is a silent failure — the agent continues working but no notifications are delivered.
