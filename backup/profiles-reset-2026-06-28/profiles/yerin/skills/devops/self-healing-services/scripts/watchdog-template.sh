#!/bin/bash
# Watchdog Template — auto-repair venv + auto-restart services via cron
# Copy to ~/.hermes/scripts/<name>_watchdog.sh, customize the variables, chmod +x, install cron.
# Verified working 2026-06-13. Required: linger enabled, XDG_RUNTIME_DIR, hardened service files.
set -u

# ======= CUSTOMIZE THESE =======
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
LOG="$HOME/.hermes/logs/watchdog.log"
LOG_MAX_BYTES=10485760  # 10MB
VENV_PYTHON="$HOME/.hermes/hermes-agent/venv/bin/python"
UV_BIN="$HOME/.local/bin/uv"
AGENT_DIR="$HOME/.hermes/hermes-agent"
SERVICES=(hermes-gateway mona-autonomous)
CRITICAL_IMPORTS=(httpx openai aiohttp)
# =================================

TS() { date '+%Y-%m-%d %H:%M:%S'; }
mkdir -p "$(dirname "$LOG")"

# Log rotation
[ -f "$LOG" ] && {
    SIZE=$(stat -c%s "$LOG" 2>/dev/null || echo 0)
    if [ "$SIZE" -gt "$LOG_MAX_BYTES" ]; then
        mv "$LOG" "${LOG}.1"
        : > "$LOG"
        echo "[$(TS)] log rotated (was ${SIZE}B)" >> "$LOG"
    fi
}

# Defensive checks (fail fast with log)
[ ! -f "$VENV_PYTHON" ] && { echo "[$(TS)] ERR: venv python missing: $VENV_PYTHON" >> "$LOG"; exit 1; }
[ ! -x "$VENV_PYTHON" ] && { echo "[$(TS)] ERR: venv python not executable" >> "$LOG"; exit 1; }
[ ! -f "$UV_BIN" ] && { echo "[$(TS)] ERR: uv missing: $UV_BIN" >> "$LOG"; exit 1; }
[ ! -f "$AGENT_DIR/pyproject.toml" ] && { echo "[$(TS)] ERR: pyproject.toml missing" >> "$LOG"; exit 1; }

# Venv integrity test + auto-repair
IMPORT_TEST=$(printf 'import %s' "${CRITICAL_IMPORTS[0]}" 2>/dev/null; for m in "${CRITICAL_IMPORTS[@]:1}"; do printf ', %s' "$m"; done)
if ! "$VENV_PYTHON" -c "import $IMPORT_TEST" 2>/dev/null; then
    echo "[$(TS)] venv broken (imports failed: $IMPORT_TEST), auto-repair..." >> "$LOG"
    if VIRTUAL_ENV="$AGENT_DIR/venv" "$UV_BIN" pip install -e "$AGENT_DIR" >> "$LOG" 2>&1; then
        echo "[$(TS)] auto-repair OK" >> "$LOG"
    else
        echo "[$(TS)] auto-repair FAILED — manual intervention needed" >> "$LOG"
    fi
fi

# Service health + auto-restart
for svc in "${SERVICES[@]}"; do
    if ! systemctl --user is-active --quiet "${svc}.service" 2>/dev/null; then
        echo "[$(TS)] ${svc} down, restarting..." >> "$LOG"
        if systemctl --user restart "${svc}.service" >> "$LOG" 2>&1; then
            echo "[$(TS)] ${svc} restarted OK" >> "$LOG"
        else
            echo "[$(TS)] ${svc} restart FAILED (exit $?)" >> "$LOG"
        fi
    fi
done
