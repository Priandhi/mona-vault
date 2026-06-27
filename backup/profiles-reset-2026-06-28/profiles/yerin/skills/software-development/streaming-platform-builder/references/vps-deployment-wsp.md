# ICLIX Deployment Infrastructure Notes

Reference notes for the ICLIX streaming platform deployment on the Mona VPS
(`43.163.85.51`, Tencent Cloud Singapore, AS132203, eth0=`10.3.0.2/22`).
Hard-won context from 2026-06-13/14 session.

## The Public IP Is Basically Useless

**Critical:** The VPS public IP `43.163.85.51` has **ALL inbound ports filtered at the
Tencent Cloud security group** — even ports 80, 443, 22 from non-local addresses.
The only egress pattern that works is through `cloudflared` running as a process
inside the VPS (which the cloud provider whitelists as part of its tunnel service).

**Confirmed dead from outside** (timeout on every test):
- 22, 80, 443, 3000, 3001, 8000, 8080, 8888, 9000

**Conclusion:** Don't waste time trying to expose a new service on a custom port
on this VPS. Use cloudflared, period. The only exception would be if the user
opens a port in the Tencent Cloud security group via the web console.

## The 3 Active Services Already on Port 80

Nginx is pre-configured with `novnc` site that proxies two internal services on
port 80:
- `/` → `127.0.0.1:20128` (the **9router** Next.js dashboard, "iclix-api" in PM2
  is NOT this — it's a different process)
- `/vnc/` → `127.0.0.1:6080` (noVNC web client)

**When adding a new service:**
1. Don't fight for port 80 — use a subpath on the existing config
2. New subpath → `location /myapp/` → proxy_pass to internal port
3. Make sure path is preserved: `proxy_set_header Host $host` + `proxy_pass
   http://127.0.0.1:PORT;` (with trailing slash on proxy_pass if needed)
4. Add a separate file in `/etc/nginx/sites-available/myapp` and symlink to
   `sites-enabled/`
5. `sudo nginx -t && sudo systemctl reload nginx`

## Cloudflare trycloudflare.com URLs — The Honest Truth

`cloudflared tunnel --url http://localhost:PORT` gives a random
`https://<random>.trycloudflare.com` URL. This URL is:
- ✅ **STABLE during the cloudflared process lifetime** (hours/days)
- ❌ **Changes on every cloudflared restart** (VPS reboot, watchdog kill, etc.)

**Existing infrastructure already handles this:**
- The `tunnel-url-watcher.py` PM2 process (#19 in PM2) tails
  `/tmp/tunnel-watchdog/{iclix,9router}.err.log`, parses
  `https://...trycloudflare.com` URLs, saves to `/tmp/tunnel-watchdog/urls.json`,
  and **auto-sends to Telegram** on URL change.
- The `tunnel-url-watcher` state file is
  `/tmp/tunnel-watchdog/watcher.state.json` — last-known URL per source.

**For a PERMANENT URL** (never changes), need:
- Cloudflare account (free) + domain on Cloudflare
- `cloudflared tunnel create <name>` + DNS route
- Requires user action — they need to give you CF account + domain
- ~10 min setup; link becomes `iclix.yourdomain.com` forever

## Quick Alternatives When CF tunnel is down

For emergency access (e.g., CF account not set up yet):
- **localhost.run** — `ssh -R 80:127.0.0.1:8080 nokey@localhost.run`. Gives
  `https://<random>.lhr.life` URL, **stable for the SSH session lifetime**.
  No signup. Free. Auto-cleanup when SSH drops.
- **serveo.net** — `ssh -R <name>:80:127.0.0.1:8080 serveo.net`. Custom
  subdomain possible (`<name>.serveo.net`) but may be claimed by other users.
- **bore.pub** — No URL, just port forwarding; needs client + server setup.
- All these give **per-session random URLs** unless you pay for custom domains.

## PM2 Tunnel Process Anatomy

```
id  name                    type    port
19  tunnel-url-watcher      python  (no port)  parses logs, sends to Telegram
20  iclix-api               node    3000       backend
21  cf-tunnel-9router       cloudflared        9router tunnel
22  cf-tunnel-iclix         cloudflared        iclix tunnel
```

**Tunnel start scripts** at `/home/ubuntu/.local/bin/`:
- `cf-tunnel-iclix.sh` — starts the iclix cloudflared tunnel
- `cf-tunnel-9router.sh` — starts 9router cloudflared
- `tunnel-ecosystem.config.js` — PM2 ecosystem config
- `tunnel-watchdog.sh` — kills + restarts tunnels if dead

**Tunnel log location** (where watcher reads from):
- `/tmp/tunnel-watchdog/iclix.err.log`
- `/tmp/tunnel-watchdog/9router.err.log`

## Reading Current URLs

```bash
# Always the source of truth
cat /tmp/tunnel-watchdog/urls.json

# Or one-liner for the iclix URL
cat /tmp/tunnel-watchdog/urls.json | python3 -c "import sys,json; print(json.load(sys.stdin)['iclix'])"
```

The user has `/url` Telegram command (via HyeJin1_Bot on Hye-Jin VPS) that also
returns the current URL.

## Firewall Quirk: iptables Has a Custom Chain

```
Chain INPUT (policy ACCEPT)
YJ-FIREWALL-INPUT  all  -- 0.0.0.0/0  0.0.0.0/0
ACCEPT  tcp  -- 0.0.0.0/0  0.0.0.0/0  tcp dpt:20128
```

`YJ-FIREWALL-INPUT` is a user-defined chain (probably from initial VPS setup).
The default policy is ACCEPT and the chain is empty — so this is effectively
allowing everything. The "ACCEPT tcp dpt:20128" line is redundant but
documented. Don't worry about iptables — the blocking is at the cloud
provider level, not OS level.
