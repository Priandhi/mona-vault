#!/usr/bin/env bash
# Quick PM2 status table — one-line per process, key fields only
# Usage: bash pm2-status-table.sh [process-name-filter]
#
# Output columns: name | status | restarts | unstable | pid | memory
# Exit code 0 = all online, 1 = any non-online

FILTER="${1:-}"

pm2 jlist 2>/dev/null | python3 -c "
import sys, json

data = json.load(sys.stdin)
filter_name = '$FILTER'.strip()

any_bad = False
for p in data:
    name = p['name']
    if filter_name and filter_name not in name:
        continue
    env = p.get('pm2_env', {})
    mon = p.get('monit', {})
    status = env.get('status', '?')
    restarts = env.get('restart_time', 0)
    unstable = env.get('unstable_restarts', 0)
    pid = p.get('pid', '?')
    mem_mb = round(mon.get('memory', 0) / 1024 / 1024, 1)

    flag = ''
    if status == 'errored':
        flag = ' 🔴'
        any_bad = True
    elif status == 'stopped':
        flag = ' ⛔'
        any_bad = True
    elif unstable > 0:
        flag = ' ⚠️'
        any_bad = True
    elif restarts > 5:
        flag = ' ⚡'

    print(f'{name:30s} | {status:10s} | restarts={restarts:4d} | unstable={unstable:2d} | pid={str(pid):>7s} | mem={mem_mb:>7.1f}MB{flag}')

sys.exit(1 if any_bad else 0)
"
