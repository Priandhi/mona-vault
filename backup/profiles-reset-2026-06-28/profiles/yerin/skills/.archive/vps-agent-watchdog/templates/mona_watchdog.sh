#!/bin/bash
# Mona Watchdog — auto-repair venv + restart services
# Deployed 2026-06-13 after Python swap cascade. Runs every 5 min via cron.
# See vps-agent-watchdog skill for full context and gotchas.
set -u

export XDG_RUNTIME_DIR="/run/user/$(id -u)"

LOG="$HOME/.hermes/logs/watchdog.log"
LOG_MAX_BYTES=10485760  # 10MB
VENV_PYTHON="$HOME/.hermes/hermes-agent/venv/bin/python"
UV_BIN="$HOME/.local/bin/uv"
AGENT_DIR="$HOME/.hermes/hermes-agent"
TS() { date '+%Y-%m-%d %H:%M:%S'; }

# Rotate log if too big (keep last rotated as .1)
[ -f "$LOG" ] && {
    SIZE=$(stat -c%s "$LOG" 2>/dev/null || echo 0)
    if [ "$SIZE" -gt "$LOG_MAX_BYTES" ]; then
        mv "$LOG" "${LOG}.1"
        : > "$LOG"
        echo "[$(TS)] watchdog log rotated (was ${SIZE} bytes)" >> "$LOG"
    fi
}

# Defensive checks — exit early with logged reason if env is wrong
[ ! -f "$VENV_PYTHON" ] && echo "[$(TS)] ERROR: venv python missing at $VENV_PYTHON" >> "$LOG" && exit 1
[ ! -x "$VENV_PYTHON" ] && echo "[$(TS)] ERROR: venv python not executable: $VENV_PYTHON" >> "$LOG" && exit 1
[ ! -f "$UV_BIN" ] && echo "[$(TS)] ERROR: uv missing at $UV_BIN" >> "$LOG" && exit 1
[ ! -f "$AGENT_DIR/pyproject.toml" ] && echo "[$(TS)] ERROR: pyproject.toml missing at $AGENT_DIR" >> "$LOG" && exit 1

# Venv integrity test — repair if broken
if ! "$VENV_PYTHON" -c "import httpx, openai" 2>/dev/null; then
    echo "[$(TS)] venv broken (httpx/openai import failed), auto-repair..." >> "$LOG"
    if VIRTUAL_ENV="$AGENT_DIR/venv" "$UV_BIN" pip install -e "$AGENT_DIR" >> "$LOG" 2>&1; then
        echo "[$(TS)] auto-repair OK" >> "$LOG"
    else
        echo "[$(TS)] auto-repair FAILED — manual intervention needed" >> "$LOG"
    fi
fi

# Service health check + auto-restart
for svc in hermes-gateway mona-autonomous; do
    if ! systemctl --user is-active --quiet "${svc}.service" 2>/dev/null; then
        echo "[$(TS)] ${svc} down, restarting..." >> "$LOG"
        if systemctl --user restart "${svc}.service" >> "$LOG" 2>&1; then
            echo "[$(TS)] ${svc} restarted OK" >> "$LOG"
        else
            echo "[$(TS)] ${svc} restart FAILED (exit $?)" >> "$LOG"
        fi
    fi
done
