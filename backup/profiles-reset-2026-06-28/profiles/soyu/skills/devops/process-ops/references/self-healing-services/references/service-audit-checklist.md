# Service File Audit Checklist — Walkthrough

Detailed step-by-step audit of the Mona stack service files, with the specific bugs found on 2026-06-13 and the fixes applied. Use this as a template when reviewing any systemd --user service.

## Step 1: Inventory existing services

```bash
ls -la ~/.config/systemd/user/*.service
# Output: hermes-gateway.service, mona-autonomous.service
```

## Step 2: For each service, dump full state

```bash
systemctl --user show <service>.service | grep -E "ExecStart|WorkingDirectory|Environment|Restart=|RestartSec=|StartLimit|MemoryMax|CPUQuota|TimeoutStop"
```

## Step 3: Apply the audit checklist

For EACH field, run the corresponding check:

### 3.1 `After=` and `Wants=` dependencies

```bash
# For each dep in After=/Wants=, verify it exists
for dep in $(grep -E "^(After|Wants)=" service-file | sed 's/.*=//' | tr ' ' '\n' | grep '\.service$'); do
    if [ -f ~/.config/systemd/user/"$dep" ]; then
        echo "OK: $dep exists"
    else
        echo "BUG: $dep referenced in After= but DOES NOT EXIST"
    fi
done
```

**Bug found (mona-autonomous.service, Jun13):** `After=mona-bot.service` — `mona-bot.service` did NOT exist. systemd warned at boot but proceeded. Service ran, dep was silently missing. **Fix:** Change to `After=network-online.target` + `Wants=network-online.target`.

### 3.2 `StartLimitIntervalSec` + `StartLimitBurst`

```bash
systemctl --user show service | grep StartLimit
```

**What to look for:**
- `StartLimitIntervalUSec=0` = NO throttling. Bad. Service can crash-loop forever.
- `StartLimitIntervalUSec=10s` + `StartLimitBurst=5` = systemd default. Allows 5 in 10s, then service enters failed state.
- Recommended for production: `StartLimitIntervalSec=60` + `StartLimitBurst=5` (5 in 60s = 1 crash per 12s average before failure). Gives time for transient issues to recover.

**Bug found (hermes-gateway.service, Jun13):** `StartLimitIntervalSec=0` (NO throttling) + `Restart=always` + `RestartSec=5` = if a bug caused 1 crash per 5s, service would restart 720x/hour forever. **Fix:**
```ini
StartLimitIntervalSec=60
StartLimitBurst=5
# StartLimitAction: default (none) — service enters failed state after burst. Watchdog won't help, manual intervention needed.
```

**PITFALL:** `StartLimitAction=fail` is NOT a valid value. Valid: `none`, `reboot`, `reboot-force`, `reboot-immediate`, `poweroff`, `poweroff-force`, `poweroff-immediate`, `exit`, `exit-force`. `none` is default and correct.

### 3.3 `Environment=PATH`

Default systemd --user PATH = `/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin`. uv, nvm, pyenv, any `~/.local/bin` install won't be found.

```bash
systemctl --user show service | grep "Environment=PATH"
```

**Required for services that use:**
- `uv` (Python package manager) → needs `~/.local/bin` in PATH
- `node` via nvm → needs `nvm.sh` source or versioned path
- `pip install --user` → `~/.local/bin`
- Any venv-installed CLI → `~/.hermes/hermes-agent/venv/bin`

**Bug found (mona-autonomous.service, Jun13):** NO `Environment=PATH` set. uv not reachable. Likely contributor to the `ModuleNotFoundError: aiohttp` event at 18:33:52. **Fix:**
```ini
Environment="PATH=/home/ubuntu/.hermes/hermes-agent/venv/bin:/home/ubuntu/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
```

### 3.4 `Environment=VIRTUAL_ENV` and `HERMES_HOME`

```bash
systemctl --user show service | grep -E "VIRTUAL_ENV|HERMES_HOME"
```

If `ExecStart` uses a venv, set `VIRTUAL_ENV` env var. If scripts read `HERMES_HOME`, set it explicitly.

**Bug found (mona-autonomous.service, Jun13):** Neither set. Scripts may have read empty env vars and silently failed. **Fix:**
```ini
Environment="VIRTUAL_ENV=/home/ubuntu/.hermes/hermes-agent/venv"
Environment="HERMES_HOME=/home/ubuntu/.hermes"
```

### 3.5 `ExecStart` binary and venv path

```bash
# Extract ExecStart
systemctl --user show service | grep "^ExecStart="
# Verify path exists
PY=$(echo "<ExecStart output>" | grep -oP "path=\K[^ ]+")
[ -x "$PY" ] && echo "OK: $PY exists and executable" || echo "BUG: $PY missing"

# Also: venv consistency between ExecStart and Environment
EXEC_VENV=$(echo "$PY" | sed 's|/bin/python.*||')
ENV_VENV=$(systemctl --user show service | grep VIRTUAL_ENV | sed 's/.*=//;s/"//g')
[ "$EXEC_VENV" = "$ENV_VENV" ] && echo "OK: venv paths match" || echo "BUG: venv mismatch ($EXEC_VENV vs $ENV_VENV)"
```

### 3.6 `TimeoutStopSec`

```bash
systemctl --user show service | grep TimeoutStop
```

If missing or =90s default, the service can be killed mid-operation during shutdown. Add explicit value:
```ini
TimeoutStopSec=30  # for fast services
TimeoutStopSec=90  # for services that need drain time
```

### 3.7 `WorkingDirectory`

```bash
# Verify the path exists
WD=$(systemctl --user show service | grep "WorkingDirectory=" | head -1 | sed 's/.*=//')
[ -d "$WD" ] && echo "OK" || echo "BUG: $WD does not exist"
```

If the script uses relative paths, this MUST point to where relative files are.

## Step 4: Apply fixes (atomic, no restart)

```bash
# 1. Backup
mkdir -p ~/.hermes/backups/services-$(date +%Y%m%d)
cp ~/.config/systemd/user/<service>.service ~/.hermes/backups/services-$(date +%Y%m%d)/

# 2. Patch (use patch tool with mode=replace, NOT sed -i)

# 3. Apply
systemctl --user daemon-reload

# 4. Verify NO service was accidentally restarted
systemctl --user is-active <service>.service
# Must still be "active" (or "running"). NOT "failed" or "inactive".

# 5. Verify new policy is loaded
systemctl --user show <service>.service | grep <new field>
```

## Step 5: Diffs for the Mona fix (Jun13)

```diff
# hermes-gateway.service
-StartLimitIntervalSec=0
+StartLimitIntervalSec=60
+StartLimitBurst=5
+# StartLimitAction: default (none) — after 5 restarts in 60s, service enters failed state.
```

```diff
# mona-autonomous.service
-After=network.target mona-bot.service
-Wants=network.target
+After=network-online.target
+Wants=network-online.target

-Environment=PYTHONUNBUFFERED=1
+Environment="PYTHONUNBUFFERED=1"
+Environment="PATH=/home/ubuntu/.hermes/hermes-agent/venv/bin:/home/ubuntu/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
+Environment="VIRTUAL_ENV=/home/ubuntu/.hermes/hermes-agent/venv"
+Environment="HERMES_HOME=/home/ubuntu/.hermes"
+TimeoutStopSec=30
```

## Post-audit verification (Mona stack, Jun13)

```bash
# Both services still active
systemctl --user is-active hermes-gateway.service    # active
systemctl --user is-active mona-autonomous.service   # active

# New policy applied
systemctl --user show hermes-gateway.service | grep StartLimit
# StartLimitIntervalUSec=1min
# StartLimitBurst=5
# StartLimitAction=none
```

No restart needed. Changes take effect on next service crash (or manual `systemctl --user restart`).
