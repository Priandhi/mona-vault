#!/bin/bash
# Mona Safety Check — Rule 4: warn before self-destructive actions.
# Detects dangerous patterns in the command, blocks unless confirmed.
#
# Usage:
#   safety_check.sh --why "explanation" -- COMMAND ARGS...
#   safety_check.sh --why "explanation" --confirm -- COMMAND ARGS...   # skip prompt
#   safety_check.sh --check "systemctl restart hermes-gateway"         # classify only
#   safety_check.sh --list                                              # list patterns
#
# Exit codes:
#   0  allowed (or non-dangerous)
#   10 dangerous, user aborted
#   11 dangerous, --confirm required (non-interactive)
#   12 pattern matched but unknown risk (forces prompt)
#   20 internal error
#
# Pattern format: REGEX###CATEGORY###RISK###EXPLANATION  (use ###, not |, to avoid regex conflicts)
# Logs to ~/.hermes/logs/safety_check.log

set -u

LOG="$HOME/.hermes/logs/safety_check.log"
mkdir -p "$(dirname "$LOG")"
TS() { date '+%Y-%m-%dT%H:%M:%S%z'; }
log_event() { echo "[$(TS)] [$1] $2" >> "$LOG"; }

# ======= EXTEND THIS FOR YOUR STACK =======
PATTERNS=(
    # SELF-SEVER: kills the connection that the agent depends on
    'systemctl[[:space:]]+--user[[:space:]]+(restart|stop|kill)[[:space:]]+(hermes-gateway|mona-autonomous)\.service###SELF_SEVER###HIGH###This will kill the gateway or autonomous service. You may go offline.'
    'systemctl[[:space:]]+(restart|stop|reload)[[:space:]]+hermes-gateway###SELF_SEVER###HIGH###Restarting hermes-gateway severs all platform connections (Telegram/Discord/etc).'
    'pkill[[:space:]]+-f[[:space:]]+(hermes|autonomous|9router)###SELF_SEVER###HIGH###Killing these processes will sever agent connection.'
    'kill[[:space:]]+(-9|-SIGKILL|-TERM)[[:space:]]+[0-9]+.*(hermes|autonomous|9router)###SELF_SEVER###HIGH###Signal to critical process.'

    # TUNNEL disruption
    'cloudflared[[:space:]]+(tunnel|.*)[[:space:]]+.*kill###TUNNEL###HIGH###Stops the public tunnel. Remote URLs go down.'
    'systemctl[[:space:]]+--user[[:space:]]+(restart|stop)[[:space:]]+cf-tunnel###TUNNEL###HIGH###Stops CF tunnel service. Public URLs go down.'

    # GLOBAL PACKAGE INSTALL (observed cascade on 9router update Jun13)
    'npm[[:space:]]+install[[:space:]]+-g[[:space:]]+9router###NPM_GLOBAL###MEDIUM###9router global update can cascade-kill gateway. Watchdog recovers but expect ~30s downtime.'
    'npm[[:space:]]+install[[:space:]]+-g[[:space:]]+###NPM_GLOBAL###MEDIUM###Global npm install can affect running services via resource spikes.'

    # PYTHON VENV DAMAGE
    'python[0-9.]*[[:space:]]+-m[[:space:]]+venv[[:space:]]+--clear###PYTHON_VENV###HIGH###Wipes an existing venv. Confirm the right path (NEVER use /home/ubuntu/.hermes/*/venv).'
    'rm[[:space:]]+-rf.*\.hermes/(hermes-agent|venv-mona)###FILESYSTEM###CRITICAL###Deletes agent venv or source. Will break everything.'
    'rm[[:space:]]+-rf.*/(hermes-gateway|mona-autonomous)\.service###FILESYSTEM###HIGH###Deletes a service file. Service cannot start.'

    # SYSTEM
    '(shutdown|poweroff|reboot)[[:space:]]###SYSTEM###CRITICAL###Will shut down or restart the system.'
    'init[[:space:]]+[0-6]###SYSTEM###CRITICAL###System runlevel change.'

    # IRREVERSIBLE DATA
    'dd[[:space:]]+.*of=/dev/###DISK###CRITICAL###Writes raw data to a device. Cannot be undone.'
    'mkfs\.###DISK###CRITICAL###Formats a filesystem. Destroys data.'
    '>[[:space:]]*/dev/sd###TRUNCATE###CRITICAL###Truncates a block device.'
)

SAFE_PATTERNS=(
    '^ls[[:space:]]' '^cat[[:space:]]' '^echo[[:space:]]' '^grep[[:space:]]'
    '^find[[:space:]]' '^ps[[:space:]]'
    '^systemctl[[:space:]]+--user[[:space:]]+(is-active|show|status)[[:space:]]'
    '^journalctl[[:space:]]' '^tail[[:space:]]' '^head[[:space:]]'
    '^which[[:space:]]' '^curl[[:space:]]+(--max-time|-s|-L|-I)' '^stat[[:space:]]'
)
# ==========================================

# ---------- classify ----------
classify() {
    local cmd="$1"
    for p in "${SAFE_PATTERNS[@]}"; do
        if [[ "$cmd" =~ $p ]]; then
            echo "SAFE|LOW|read-only or known-safe command"
            return 0
        fi
    done
    for entry in "${PATTERNS[@]}"; do
        local pat="${entry%%###*}"
        local rest="${entry#*###}"
        local cat="${rest%%###*}"
        rest="${rest#*###}"
        local risk="${rest%%###*}"
        local expl="${rest#*###}"
        if [[ "$cmd" =~ $pat ]]; then
            echo "$cat|$risk|$expl"
            return 0
        fi
    done
    echo "UNKNOWN|UNKNOWN|no pattern matched — treat as risky"
    return 0
}

prompt_confirm() {
    local cat="$1" risk="$2" expl="$3" cmd="$4"
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "WARNING: MONA SAFETY CHECK — $cat ($risk)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Command : $cmd"
    echo "Reason  : $expl"
    echo
    if [ -t 0 ]; then
        echo -n "Proceed? [y/N] (10s timeout): "
        local ans
        if read -t 10 -r ans; then
            [[ "$ans" =~ ^[Yy](es)?$ ]]
            return $?
        else
            echo "(timeout, defaulting to NO)"
            return 1
        fi
    else
        echo "(non-interactive — re-run with --confirm, or pipe 'yes')"
        return 2
    fi
}

# ---------- main ----------
WHY=""
CONFIRM=0
CHECK_ONLY=0
LIST=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --why) WHY="$2"; shift 2 ;;
        --confirm) CONFIRM=1; shift ;;
        --check) CHECK_ONLY=1; shift; break ;;
        --list) LIST=1; shift ;;
        --) shift; break ;;
        -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
        *) break ;;
    esac
done

if [ "$LIST" -eq 1 ]; then
    echo "DANGEROUS PATTERNS:"
    for entry in "${PATTERNS[@]}"; do
        pat="${entry%%###*}"; rest="${entry#*###}"; cat="${rest%%###*}"
        rest="${rest#*###}"; risk="${rest%%###*}"; expl="${rest#*###}"
        printf "  %-14s %-7s  %s\n" "$cat" "$risk" "$expl"
    done
    echo
    echo "SAFE PATTERNS:"
    for p in "${SAFE_PATTERNS[@]}"; do printf "  %s\n" "$p"; done
    exit 0
fi

if [ $# -eq 0 ]; then
    echo "usage: safety_check.sh --why 'reason' [--confirm] -- COMMAND [ARGS...]" >&2
    echo "       safety_check.sh --check 'COMMAND'" >&2
    echo "       safety_check.sh --list" >&2
    exit 20
fi

CMD="$*"
if [ "$CHECK_ONLY" -eq 1 ]; then
    classify "$CMD"
    exit 0
fi

CLASSIFY_OUT=$(classify "$CMD")
IFS='|' read -r CAT RISK EXPL <<< "$CLASSIFY_OUT"

if [ "$CAT" = "SAFE" ]; then
    log_event "ALLOW" "cmd=\"$CMD\" why=\"$WHY\""
    exec "$@"
fi

log_event "BLOCK" "cat=$CAT risk=$RISK cmd=\"$CMD\" why=\"$WHY\""

if [ "$CONFIRM" -eq 0 ]; then
    if prompt_confirm "$CAT" "$RISK" "$EXPL" "$CMD"; then
        log_event "ALLOW_AFTER_PROMPT" "cat=$CAT cmd=\"$CMD\" why=\"$WHY\""
        echo "user confirmed — proceeding"
        exec "$@"
    else
        log_event "DENY" "cat=$CAT cmd=\"$CMD\" why=\"$WHY\""
        echo "BLOCKED. Use --confirm to skip prompt next time."
        exit 10
    fi
else
    log_event "ALLOW_CONFIRM" "cat=$CAT cmd=\"$CMD\" why=\"$WHY\""
    echo "WARNING: --confirm flag set, proceeding without prompt: $CMD"
    exec "$@"
fi
