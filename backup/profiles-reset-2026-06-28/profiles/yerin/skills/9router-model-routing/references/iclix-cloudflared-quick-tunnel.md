# ICLIX Cloudflared Quick-Tunnel PM2 Restoration

**Scope:** Restoring the ICLIX + 9Router `trycloudflare.com` quick-tunnel pair on Mona VPS after cloudflared processes die (VM restart, OOM, manual kill, etc.). Not for named-tunnel setups with `~/.cloudflared/config.yml` + cert.pem — those need a different procedure.

## When to use this

- `pm2 list` shows only `iclix-api` and `tunnel-url-watcher` (no `cf-tunnel-*`)
- `urls.json` at `/tmp/tunnel-watchdog/urls.json` is missing or stale
- Both `prague-runner-cyber-volumes.trycloudflare.com` (or whatever the old iclix URL was) and the 9router trycloudflare URL are returning HTTP 000
- `ps aux | grep cloudflared` shows no PIDs (or shows PIDs you can't kill as the `ubuntu` user)

## The infrastructure (the thing being restored)

The intended setup is a **PM2 ecosystem** at `/home/ubuntu/.local/bin/tunnel-ecosystem.config.js` with 3 apps:
- `cf-tunnel-9router` — `cloudflared tunnel --url http://localhost:20128 --no-autoupdate`
- `cf-tunnel-iclix` — `cloudflared tunnel --url http://localhost:3000 --no-autoupdate`
- `tunnel-url-watcher` — `python3 /home/ubuntu/.local/bin/tunnel-url-watcher.py` (parses PM2-merged logs at `/tmp/tunnel-watchdog/{9router,iclix}.err.log`, writes `/tmp/tunnel-watchdog/urls.json`, sends TG notif on URL change)

PM2 logs go to `/home/ubuntu/.pm2/logs/cf-tunnel-{name}-{out,error}.log` (because `merge_logs: true`).

**Do NOT run `tunnel-watchdog.sh start` from `/home/ubuntu/.local/bin/`** — that script conflicts with PM2 (it spawns bare cloudflared with no PM2 ownership, and you end up with duplicate tunnels + the script's own URL extraction fighting the watcher).

## The two non-obvious pitfalls (the things that bit us)

### Pitfall 1: `cloudflared` runs as `root`

PM2 launches the cloudflared children as `root`, not as the `ubuntu` user. This means:
- A bare `kill <pid>` from a normal `ubuntu` shell returns **"Operation not permitted"** with no further hint
- You must use `sudo kill -9 <pid>` or `sudo pkill -f "cloudflared tunnel --url"`
- If a previous `tunnel-watchdog.sh start` left orphaned cloudflared PIDs owned by root, **do not try to kill them from PM2's ecosystem** — PM2 will refuse to take over the port and you'll be stuck with zombies. Kill the orphans first, then re-apply the ecosystem.

### Pitfall 2: the URL is **random** every restart

`trycloudflare.com` quick tunnels get a fresh random subdomain on every cloudflared launch. The old URL (`prague-runner-cyber-volumes.trycloudflare.com`, `washing-grade-hint-appreciation.trycloudflare.com`, etc.) **will not come back** — `urls.json` will be overwritten with a new random URL within ~25-30 seconds of restart.

**Implication:** any hardcoded URL (bookmark, Telegram pinned message, frontend env var, marketing material) becomes dead the next time the tunnel restarts. Always read the current URL from `urls.json` or the TG notification the watcher sends.

## The restoration procedure (verified Jun 13 2026)

```bash
# 1. Kill orphaned root-owned cloudflared processes (sudo required)
sudo pkill -f "cloudflared tunnel --url" 2>/dev/null
sleep 2
ps aux | grep cloudflared | grep -v grep   # should be empty

# 2. Clean stale state in /tmp/tunnel-watchdog/
rm -f /tmp/tunnel-watchdog/*.pid /tmp/tunnel-watchdog/*.log \
      /tmp/tunnel-watchdog/urls.json /tmp/tunnel-watchdog/watcher.state.json

# 3. Apply the PM2 ecosystem
cd /home/ubuntu/.local/bin
pm2 start tunnel-ecosystem.config.js
# Expected: cf-tunnel-9router, cf-tunnel-iclix, tunnel-url-watcher all start

# 4. Wait ~25 seconds for cloudflared to print the new trycloudflare URL
sleep 25

# 5. Verify the watcher picked it up
cat /tmp/tunnel-watchdog/urls.json
# Should now show:
# {
#   "9router": "https://<random>.trycloudflare.com",
#   "iclix":   "https://<random>.trycloudflare.com",
#   "updated": "2026-06-13T..."
# }

# 6. Verify HTTP 200 on both
ICLIX_URL=$(python3 -c "import json; print(json.load(open('/tmp/tunnel-watchdog/urls.json'))['iclix'])")
NINER_URL=$(python3 -c "import json; print(json.load(open('/tmp/tunnel-watchdog/urls.json'))['9router'])")
curl -s -o /dev/null -w "iclix: HTTP %{http_code}\n" "$ICLIX_URL/"
curl -s -o /dev/null -w "9router: HTTP %{http_code}\n" "$NINER_URL/"

# 7. Sanity-check that iclix-api is talking to TMDB
curl -s "$ICLIX_URL/api/trending" | head -c 200
# Should be JSON, not HTML
```

**Expected wait time:** 5s for cloudflared to print the URL to its log, then another 8s for the watcher's poll cycle to pick it up. Total ~15-25s.

## Diagnosing "tunnel shows online but URL returns HTTP 000"

If `pm2 list` says `cf-tunnel-iclix` is `online` but `curl <urls.json iclix>` returns `HTTP 000` (connection failed/timeout), the cloudflared child process is alive but the QUIC connection to Cloudflare edge failed. Common causes:
- WARP / outbound UDP blocked — check `cloudflared` log: `tail /home/ubuntu/.pm2/logs/cf-tunnel-iclix-out.log | grep -i quic`
- ISP blocked Cloudflare — rare on VPS, common on home network
- ping_group_range warning — harmless, the tunnel still works

Fix: `pm2 restart cf-tunnel-iclix` (PM2 will respawn, QUIC will reconnect, URL may or may not change).

## Why we have a PM2 ecosystem and not a systemd service

The original setup was systemd-based (`cf-tunnel-{9router,iclix}.service` in `~/.config/systemd/user/`), but during the Jun 13 2026 VPS crash the systemd user services were wiped. The PM2 ecosystem was the fallback. **Do not** try to "restore" the systemd version — the PM2 ecosystem is the source of truth and `tunnel-watchdog.sh` is the only shell-side backup. PM2 handles `autorestart`, `max_restarts: 99`, `exp_backoff_restart_delay`, and integrates with `pm2-logrotate` for log rotation — systemd would duplicate this.

## Last known URLs (Jun 13 2026 22:17 WIB)

Will be **invalid** the next time tunnels restart. For historical reference only.
- iclix: `prague-runner-cyber-volumes.trycloudflare.com`
- 9router: `washing-grade-hint-appreciation.trycloudflare.com`
