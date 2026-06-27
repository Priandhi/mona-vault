# PM2 Auto-Heal Workflow

Recovery procedure when PM2 processes are down or crashing.

## Quick Health Check

```bash
# Check all processes at once
pm2 jlist 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
for p in data:
    print(f\"{p['name']:30s} status={p['pm2_env']['status']:10s} restarts={p['pm2_env']['restart_time']}\")
"

# If empty output → all processes are DOWN, need full restart
```

## Full Recovery Sequence

When PM2 list is empty or processes keep crashing:

1. **Check error logs FIRST** — don't blindly restart a broken config:
   ```bash
   tail -30 ~/.pm2/logs/charon-sniper-error.log
   tail -30 ~/.pm2/logs/meridian-error-0.log
   tail -20 ~/.pm2/logs/charon-dashboard-error-1.log
   ```

2. **Fix code issues** before restarting (restart loop = wasted CPU + log spam)

3. **Restart from ecosystem configs** (order matters — main process before dashboard):
   ```bash
   cd ~/mona-workspace/charon-sniper && pm2 start ecosystem.config.cjs
   cd ~/mona-workspace/meridian && pm2 start ecosystem.config.cjs
   cd ~/mona-workspace/charon-dashboard && pm2 start ecosystem.config.cjs
   cd ~/mona-workspace/meridian-dashboard && pm2 start ecosystem.config.cjs
   ```

4. **Verify stability** (wait 5s, check restarts=0):
   ```bash
   sleep 5 && pm2 jlist | python3 -c "import sys,json; [print(f\"{p['name']} restarts={p['pm2_env']['restart_time']}\") for p in json.load(sys.stdin)]"
   ```

5. **Check dashboard HTTP**:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3457  # meridian-dashboard
   curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3458  # charon-dashboard
   ```

6. **Save process list** (critical — enables pm2 resurrect on reboot):
   ```bash
   pm2 save
   ```

7. **Report to Telegram** topic 1309 via `mona_telegram.send_message(1309, msg)`

## Common Error Patterns

### `__dirname is not defined in ES module scope`
- **Cause**: package.json has `"type": "module"` but code uses bare `__dirname`
- **Fix**: Add `const __dirname = path.dirname(fileURLToPath(import.meta.url));` at top of file
- **Status**: Already fixed in charon-sniper modules (token-filter.js uses `path.resolve()` instead)

### `trades.filter is not a function`
- **Cause**: `loadJSON()` returns object `{ trades: [] }` but code calls `.filter()` on the object instead of `.trades`
- **Fix**: Use `trades.trades.filter()` not `trades.filter()`
- **Impact**: Dashboard runtime error on certain endpoints, non-blocking for sniper

### Punycode deprecation warning
- **Cause**: Node.js built-in `punycode` module deprecated
- **Impact**: Cosmetic warning only, no functional impact
- **Action**: Ignore

## PM2 Ecosystem Config Locations

| Process | Config Path |
|---------|-------------|
| charon-sniper + dashboard | `~/mona-workspace/charon-sniper/ecosystem.config.cjs` |
| meridian | `~/mona-workspace/meridian/ecosystem.config.cjs` |
| meridian-dashboard | `~/mona-workspace/meridian-dashboard/ecosystem.config.cjs` |

## Tunnel Check

After restart, verify SSH tunnels for external dashboard access:
```bash
ps aux | grep -i "localhost.run\|ssh.*-R\|tunnel" | grep -v grep
```

If no tunnel found → dashboards are local-only. Report this in the Telegram message.
