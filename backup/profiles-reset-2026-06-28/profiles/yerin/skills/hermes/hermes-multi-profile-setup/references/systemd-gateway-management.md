# Systemd Gateway Management for Hermes Profiles

## Problem: Systemd User Service Doesn't Load `.env`

When `hermes gateway install` creates a systemd user service, it does NOT add an `EnvironmentFile` directive. This means environment variables from `~/.hermes/.env` (like `TELEGRAM_BOT_TOKEN`) are **not available** to the gateway process.

**Symptom:** Token is valid (curl/python test works), config has correct token, but gateway fails with `InvalidToken: Unauthorized`.

## Diagnosis

### 1. Check if env vars are in the running process
```bash
# Get PID of running hermes
PID=$(pgrep -f "hermes.*gateway" | head -1)

# Check if TELEGRAM_BOT_TOKEN is in environment
cat /proc/$PID/environ 2>/dev/null | tr '\0' '\n' | grep TELEGRAM
# EMPTY = env var not loaded (problem!)
# Shows value = env var loaded (check token value)
```

### 2. Check systemd service file
```bash
cat ~/.config/systemd/user/hermes-gateway-<name>.service
```

Look for `EnvironmentFile=` under `[Service]`. If missing, that's the problem.

### 3. Check gateway logs
```bash
journalctl --user -u hermes-gateway-<name> -n 30 --no-pager
# Or for profile-specific:
tail -20 ~/.hermes/profiles/<name>/logs/gateway.log
```

## Fix: Add EnvironmentFile to Service

### Option A: Edit service file directly
```bash
# Stop service
systemctl --user stop hermes-gateway-<name>

# Add EnvironmentFile after [Service] line
sed -i '/^\[Service\]/a EnvironmentFile=-/home/ubuntu/.hermes/.env' \
  ~/.config/systemd/user/hermes-gateway-<name>.service

# Reload and restart
systemctl --user daemon-reload
systemctl --user start hermes-gateway-<name>
```

### Option B: Python script (safer for remote VPS)
```python
# fix_systemd_env.py
import re

path = "/home/ubuntu/.config/systemd/user/hermes-gateway-hyejin.service"
with open(path) as f:
    content = f.read()

# Add EnvironmentFile after [Service] if not already present
if "EnvironmentFile" not in content:
    content = content.replace(
        "[Service]\n",
        "[Service]\nEnvironmentFile=-/home/ubuntu/.hermes/.env\n"
    )
    with open(path, "w") as f:
        f.write(content)
    print("Added EnvironmentFile directive")
else:
    print("EnvironmentFile already present")
```

### Option C: Alternative — embed token in service file
If `.env` loading is problematic, embed the token directly:
```bash
# Get token
TOKEN=$(cat /tmp/bot_token.txt)

# Add to service file
sed -i "/^Environment=\"HERMES_HOME/a Environment=\"TELEGRAM_BOT_TOKEN=$TOKEN\"" \
  ~/.config/systemd/user/hermes-gateway-<name>.service

systemctl --user daemon-reload
systemctl --user restart hermes-gateway-<name>
```

## Service File Anatomy

```ini
[Unit]
Description=Hermes Agent Gateway - Messaging Platform Integration
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
EnvironmentFile=-/home/ubuntu/.hermes/.env    # ← ADD THIS LINE
Type=simple
ExecStart=/home/ubuntu/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main --profile hyejin gateway run
WorkingDirectory=/home/ubuntu/.hermes/profiles/hyejin
Environment="PATH=/home/ubuntu/.hermes/hermes-agent/venv/bin:..."
Environment="VIRTUAL_ENV=/home/ubuntu/.hermes/hermes-agent/venv"
Environment="HERMES_HOME=/home/ubuntu/.hermes/profiles/hyejin"
Restart=always
RestartSec=5
RestartForceExitStatus=75
KillMode=mixed
KillSignal=SIGTERM
ExecReload=/bin/kill -USR1 $MAINPID
TimeoutStopSec=210
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

## Common Pitfalls

### `.env` inline comments break systemd parser
systemd's `EnvironmentFile` does NOT support inline comments.

**WRONG:**
```
TELEGRAM_HOME_CHANNEL=1492210461    # Default chat for cron delivery
```

**RIGHT:**
```
# Default chat for cron delivery
TELEGRAM_HOME_CHANNEL=1492210461
```

If `.env` has inline comments, systemd silently skips those lines OR parses the comment as part of the value.

### Duplicate `.env` entries
First entry wins, even if empty:
```
TELEGRAM_BOT_TOKEN=           # ← EMPTY, but wins!
TELEGRAM_BOT_TOKEN=realtoken  # ← IGNORED
```

Always clean duplicates:
```bash
# Remove empty/duplicate TELEGRAM_BOT_TOKEN, keep only non-empty
awk '!seen[$0]++ || !/TELEGRAM_BOT_TOKEN/' ~/.hermes/.env > /tmp/.env.clean
mv /tmp/.env.clean ~/.hermes/.env
```

### `EnvironmentFile=-` prefix
The `-` prefix means "don't fail if file doesn't exist". Without it, systemd refuses to start the service if the file is missing. Always use `-` prefix.

### Service file gets overwritten
`hermes gateway install` or `hermes gateway restart` may regenerate the service file, removing your `EnvironmentFile` addition. After adding it, verify it persists after restart:
```bash
systemctl --user restart hermes-gateway-<name>
grep EnvironmentFile ~/.config/systemd/user/hermes-gateway-<name>.service
```

## Verification Checklist

After fixing, verify ALL of these:
```bash
# 1. Service file has EnvironmentFile
grep EnvironmentFile ~/.config/systemd/user/hermes-gateway-<name>.service

# 2. Process has TELEGRAM_BOT_TOKEN
cat /proc/$(pgrep -f hermes | head -1)/environ | tr '\0' '\n' | grep TELEGRAM

# 3. Gateway connected to Telegram
journalctl --user -u hermes-gateway-<name> --since "1 min ago" | grep -i "connected\|telegram"

# 4. Bot responds to messages
# Send a test message to the bot on Telegram
```
