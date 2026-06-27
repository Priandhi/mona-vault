# Telegram Bot Token — Where It Lives & How to Fix

## Token Locations (ALL must match)

| Location | Config Key | File |
|----------|-----------|------|
| Environment | `TELEGRAM_BOT_TOKEN` | `~/.hermes/.env` |
| Main config | `telegram.bot_token` | `~/.hermes/config.yaml` |
| Profile config | `telegram.token` | `~/.hermes/profiles/<name>/config.yaml` |

**NOTE:** Different key names! Main config = `bot_token`, profile config = `token`.

## Token Precedence (from gateway/config.py:1346)

```python
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")  # .env wins
if telegram_token:
    telegram_config.token = telegram_token
```

The gateway reads `TELEGRAM_BOT_TOKEN` env var FIRST. Config.yaml fields are fallback.

## Symptom: "InvalidToken: Unauthorized"

Gateway log shows:
```
telegram.error.InvalidToken: The token `8993907472:***` was rejected by the server.
```

## Diagnosis Steps

### 0. FIRST: Check if env var is loaded (systemd issue)
This is the #1 cause of "InvalidToken" when the token IS valid. Systemd user services don't auto-load `.env`.
```bash
PID=$(pgrep -f "hermes.*gateway" | head -1)
cat /proc/$PID/environ 2>/dev/null | tr '\0' '\n' | grep TELEGRAM_BOT_TOKEN
```
**If EMPTY:** The service file is missing `EnvironmentFile`. See `references/systemd-gateway-management.md` for fix. This is MORE COMMON than an actual bad token.

### 1. Verify token is valid (from the VPS itself)
```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@VPS 'python3 -c "
import urllib.request, json
token = open(\"/tmp/bot_token.txt\").read().strip()
url = f\"https://api.telegram.org/bot{token}/getMe\"
try:
    r = urllib.request.urlopen(url)
    data = json.loads(r.read())
    print(\"OK:\", data[\"result\"][\"username\"])
except Exception as e:
    print(\"ERROR:\", e)
"'
```

### 2. Check all 3 locations
```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@VPS 'python3 -c "
import yaml
# Main config
with open(\"/home/ubuntu/.hermes/config.yaml\") as f:
    c1 = yaml.safe_load(f)
t1 = c1.get(\"telegram\",{}).get(\"bot_token\",\"\")
print(f\"main config bot_token: len={len(t1)}\")

# Profile config
with open(\"/home/ubuntu/.hermes/profiles/hyejin/config.yaml\") as f:
    c2 = yaml.safe_load(f)
t2 = c2.get(\"telegram\",{}).get(\"token\",\"\")
print(f\"profile config token: len={len(t2)}\")
"'
```

### 3. Check .env for duplicates/broken lines
```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@VPS 'grep -n TELEGRAM_BOT_TOKEN ~/.hermes/.env'
```

**Common .env problems:**
- Multiple entries (first wins, even if empty)
- Merged with comment: `TELEGRAM_BOT_TOKEN=*** TELEGRAM_ALLOWED_USERS=...` (115+ chars)
- Empty value: `TELEGRAM_BOT_TOKEN=`

### 4. Check what gateway actually loaded
```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@VPS 'tail -20 ~/.hermes/profiles/<name>/logs/gateway.log'
```

## Fix: Update Token Safely

### Step 1: Write token to temp file
```python
# On local machine
token = "8993907472:AAHqrg1D2u-pi9LtpBdQ_JsJrROPfBgsaE0"
with open("/tmp/bot_token.txt", "w") as f:
    f.write(token)
```

### Step 2: SCP to remote VPS
```bash
scp -i ~/.ssh/id_ed25519 /tmp/bot_token.txt ubuntu@VPS:/tmp/bot_token.txt
```

### Step 3: Fix all 3 locations with Python script
```python
# fix_telegram_token.py — run on remote VPS
import yaml

token = open("/tmp/bot_token.txt").read().strip()

# Fix .env (replace first TELEGRAM_BOT_TOKEN line, remove duplicates)
lines = []
found = False
with open("/home/ubuntu/.hermes/.env") as f:
    for line in f:
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            if not found:
                lines.append(f"TELEGRAM_BOT_TOKEN={token}\n")
                found = True
            # skip duplicate lines
        else:
            lines.append(line)
with open("/home/ubuntu/.hermes/.env", "w") as f:
    f.writelines(lines)

# Fix main config.yaml
with open("/home/ubuntu/.hermes/config.yaml") as f:
    c = yaml.safe_load(f)
c["telegram"]["bot_token"] = token
with open("/home/ubuntu/.hermes/config.yaml", "w") as f:
    yaml.dump(c, f, default_flow_style=False, sort_keys=False)

# Fix profile config.yaml
with open("/home/ubuntu/.hermes/profiles/hyejin/config.yaml") as f:
    c = yaml.safe_load(f)
c["telegram"]["token"] = token
with open("/home/ubuntu/.hermes/profiles/hyejin/config.yaml", "w") as f:
    yaml.dump(c, f, default_flow_style=False, sort_keys=False)

print(f"All 3 locations updated, token len={len(token)}")
```

### Step 4: Restart gateway
```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@VPS '~/.hermes/hermes-agent/venv/bin/hermes gateway restart --profile <name>'
```

### Step 5: Verify in logs
```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@VPS 'tail -10 ~/.hermes/profiles/<name>/logs/gateway.log'
```

Look for: `[Telegram] Connected to Telegram` or bot username in startup logs.

## Pitfalls

- **sed breaks .env lines** — `sed -i 's|TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=*** ~//.hermes/.env` can merge with the next line if the value contains special chars. ALWAYS use Python script for .env edits.
- **yaml.dump changes config format** — When using python yaml to update config.yaml, `yaml.dump()` may reorder keys, change quoting, or convert types. This is usually harmless for hermes but can break `custom_providers` if it converts list→dict. For simple token updates, `yaml.dump` is safe.
- **Token masked in logs** — hermes redacts tokens in log output (`8993907472:***`). You can't see the actual token in logs. Verify by testing against Telegram API directly.
- **Gateway reconnection watcher** — After failed token, gateway starts a "reconnection watcher" that retries periodically. If you fix the token, it may auto-reconnect without explicit restart (but restart is more reliable).
