---
name: vps-agent-watchdog
description: "Self-healing cron-based watchdog for AI agent services running as systemd user units on a VPS. Auto-repairs broken Python venvs (uv pip install -e), auto-restarts crashed services, rotates logs, defensive-checks all paths. Triggers include: agent services crashing repeatedly after dep/Python changes, venv integrity loss, user asks for watchdog/auto-heal/self-healing, 'jangan eror terus', or any time the agent must survive dep churn unattended."
when_to_use:
  - "Agent's main systemd user services (hermes-gateway, mona-autonomous) keep crashing"
  - "After Python version swap, uv reinstall, or any dep change that might break the venv"
  - "After ANY system-level package update that could cascade (9router npm update, system Python pip, package upgrades via apt) — these can take down gateway services even when venv itself is fine"
  - "User asks for watchdog, auto-heal, self-heal, 'survive unattended'"
  - "Setting up an unattended VPS deployment that must auto-recover from venv breaks"
  - "Venv keeps getting wiped (uv auto-cleanup, `venv --clear`, symlink break)"
version: 1.0.0
---

# VPS Agent Watchdog — Self-Healing systemd Services

A defensive cron-based watchdog that keeps an AI agent's systemd user services alive across venv breakage, dependency churn, and silent crashes. Field-tested 2026-06-13 after a Python 3.12 swap cascade destroyed Mona's venv — the agent came back to life without user intervention after this was deployed.

## When to Use This Skill

**Symptoms that mean you need this:**
- Agent's main service (gateway, autonomous loop) keeps dying in `systemctl --user status` after dep changes
- `venv python -c "import httpx, openai"` fails with ModuleNotFoundError
- Crash loop: service starts → dies → restarts → dies, even with `Restart=always` in systemd
- User says "eror terus", "jangan eror", "auto-repair dong", "watchdog", "self-heal"
- Post-incident hardening after any Python/uv/dependency operation that touched the venv

**Scope:** VPS-based agents using **systemd user services** + **Python venv** + **uv**. NOT for PM2-managed stacks (use `pm2-process-health` instead) and NOT for in-process watchdogs (use `openclaw-superagent-framework` `watchdog.py`).

## The Pattern (3 Components)

### 1. Defensive Watchdog Script (≈60 lines, runs every 5 min)

The deployed template is at `templates/mona_watchdog.sh`. Core logic:

```bash
#!/bin/bash
set -u
export XDG_RUNTIME_DIR="/run/user/$(id -u)"   # CRITICAL — without this, systemctl --user fails from cron

LOG="$HOME/.hermes/logs/watchdog.log"
VENV_PYTHON="$HOME/.hermes/hermes-agent/venv/bin/python"
UV_BIN="$HOME/.local/bin/uv"
AGENT_DIR="$HOME/.hermes/hermes-agent"

# 1. Log rotation (>10MB → .1, frees disk)
# 2. Defensive checks: venv python exists+executable, uv exists, pyproject.toml exists
# 3. Venv integrity: $VENV_PYTHON -c "import httpx, openai" — if fails, uv pip install -e
# 4. Service loop: for svc in <agent-services>; do restart if not active
```

### 2. Cron Entry (every 5 min, idempotent install)

```bash
CRON_LINE="*/5 * * * * /home/ubuntu/.hermes/scripts/mona_watchdog.sh"
if ! crontab -l 2>/dev/null | grep -qF "mona_watchdog.sh"; then
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
fi
```

**Always check first to avoid duplicate entries on re-install.**

### 3. Required Pre-Conditions (BEFORE installing cron)

- `sudo loginctl enable-linger $USER` — **one-time, required**. Without it, `XDG_RUNTIME_DIR` export in cron is not enough; the user manager won't be running.
- Verify: `loginctl show-user $USER | grep Linger=yes` should show `Linger=yes`
- `~/.hermes/hermes-agent/venv/bin/python` must exist (path Claude-style agents use)
- `~/.local/bin/uv` must exist (uv binary)
- `~/.hermes/hermes-agent/pyproject.toml` must exist (editable install target)

## Gotchas (Field-Tested 2026-06-13)

1. **`systemctl --user` from cron needs BOTH linger AND `XDG_RUNTIME_DIR` export.** Exporting `XDG_RUNTIME_DIR` alone is not enough if `/run/user/<uid>` doesn't exist (no lingering = no user systemd manager running). Fix: `loginctl enable-linger $USER` once.

2. **Cron env is minimal.** No `PATH`, no session bus, no `/run/user/<uid>` by default. The script MUST export `XDG_RUNTIME_DIR` AND set all paths explicitly (no reliance on `$PATH`).

3. **`<<'EOF'` (quoted heredoc) writes LITERAL text — variables expand at SCRIPT RUNTIME, not at heredoc write.** `<< EOF` (unquoted) expands variables at WRITE time. When reviewing or writing heredocs, distinguish carefully. (Field lesson 2026-06-13: I once flagged a correct script as broken on this exact issue — don't make the same mistake.)

4. **Don't `rm` log files held by processes — use `> file` to truncate.** Keeps the file descriptor valid, frees blocks. Same for the watchdog log when rotating.

5. **The `reboot` keyword in shell commands can trigger the Hermes hardline blocklist**, even when the command is only `grep`ing for it. When verifying the cron entry was installed, use `grep -F "mona_watchdog.sh"` (literal match) or `grep -E "watchdog|cron"` — avoid `reboot` as a grep token.

6. **Always test the script with a manual dry run before installing cron.** Run `~/.hermes/scripts/mona_watchdog.sh` once. If state is healthy: exit 0 + no log entries = good. If it logs errors, fix paths before adding to cron.

7. **Watchdog should be SILENT when healthy.** If it logs on every cron tick, it's noise. Only log on action taken or error found.

8. **`RestartSec=5` + `StartLimitIntervalSec=0`** (the typical hermes-gateway setup) means systemd restart is gentle but unthrottled. The cron watchdog is a SAFETY NET, not a replacement — systemd `Restart=always` handles most crashes within seconds. Watchdog catches the cases systemd can't (broken venv, missing module, dep version mismatch).

9. **Defensive checks should EXIT with a logged reason, not silently skip.** If the venv python is missing, log "ERROR: venv python missing" and exit 1. Don't fall through and try to "repair" something that doesn't exist.

## Verification Sequence

Run after install:

```bash
# 1. Script exists + executable
ls -la ~/.hermes/scripts/mona_watchdog.sh

# 2. Syntax check
bash -n ~/.hermes/scripts/mona_watchdog.sh && echo "syntax OK"

# 3. Dry run (state should be healthy, exit 0, no log)
~/.hermes/scripts/mona_watchdog.sh; echo "exit=$?"

# 4. Cron entry exists
crontab -l | grep -F "mona_watchdog.sh"

# 5. Linger enabled
loginctl show-user $USER | grep "Linger=yes"

# 6. Simulated failure (recommended)
systemctl --user stop hermes-gateway.service
~/.hermes/scripts/mona_watchdog.sh
systemctl --user is-active hermes-gateway.service   # should be "active"
cat ~/.hermes/logs/watchdog.log                      # should show "restarted OK"
systemctl --user start hermes-gateway.service        # in case the test left it down
```

## Integration with Other Skills

- **`self-healing-services`** — Owns the venv check (`scripts/startup_check.py`) and the service file audit checklist. The watchdog's venv integrity test is a SUBSET of what startup_check does — for new stacks, **defer to startup_check rather than duplicating the check.** The watchdog should: (a) detect that a service is down, (b) run `startup_check.py --service <svc> --quiet`, (c) if it FAILS, attempt `uv pip install -e $AGENT_DIR` repair, (d) restart the service. This separates "is the substrate OK?" (startup_check) from "is the process running?" (watchdog). Layered cleanly, no logic duplication.
- **`pm2-process-health`**: Different scope (PM2-managed services, not systemd). Use that for PM2 stacks; use this for systemd.
- **`openclaw-superagent-framework` `watchdog.py`**: In-process watchdog (pgrep + auto-restart from inside the agent process). Use that for runtime crash detection; use this for OS-level dep/venv failures.
- **`mona-enhanced-monitoring`**: Watchdog complements but doesn't replace observability — the watchdog handles venv/dep; monitoring handles API/provider health.

## Field Validation

- **2026-06-13 19:15** — First real catch. See `references/2026-06-13-19-15-first-real-catch.md`. Watchdog auto-recovered `hermes-gateway` after a 9router npm update cascade. ROI validated: 60 lines of bash caught a cascade that would have required user intervention.

## Pitfalls

- **Do NOT install the cron entry without `loginctl enable-linger` first.** `systemctl --user` calls will fail silently in cron. Verify linger BEFORE adding the cron line.
- **Do NOT use the watchdog to restart services that AREN'T agent-owned** (postgres, nginx, etc.). Keep scope tight — only restart what the watchdog has defensive knowledge of.
- **Do NOT set cron interval < 5 minutes.** `uv pip install` can take 30+ seconds; tight intervals cause pile-up.
- **Do NOT trust systemd `Restart=always` alone** for venv-related issues. systemd restarts the failing process, not the broken venv. The watchdog's value is the venv check + repair.
- **Do NOT add `--force` to `uv pip install`.** If repair fails repeatedly, surface to user — don't loop forever.
- **Do NOT add Telegram notification for every cron tick.** Only on actual repair/restart events. Alert fatigue kills attention.
