# Cloudflare WARP as SOCKS5 Proxy for 9Router

**When to use:** Mona VPS IP blocked by Cloudflare 1010 (Error code 1010 in body) on the Kimchi.dev API. The previous workaround was routing through Hye-Jin VPS (13.211.42.29) via SSH tunnel — but if Hye-Jin is unreachable, WARP on Mona itself is the fallback. Free, no extra VPS needed.

**Field-tested 2026-06-13:** Hye-Jin sshd hung, no proxy route. WARP installed on Mona → Kimchi went from HTTP 1010 to HTTP 402 (credits exhausted, NOT network error — proof the proxy works).

## What WARP Does

Cloudflare WARP is their free WireGuard-based VPN. On Linux, the `cloudflare-warp` package can run in several modes:
- `warp` — full tunnel (routes ALL traffic)
- `doh` / `dot` — DNS proxy only
- **`proxy`** — establishes a tunnel and exposes a **SOCKS5 proxy** on `127.0.0.1:1080` (default port)

The `proxy` mode is what we want. It does NOT route system traffic. Only processes that explicitly use the SOCKS5 proxy get the WARP exit IP. Everything else keeps using Mona's real IP.

## Install (4 Steps)

```bash
# 1. Add Cloudflare apt repo
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflare-client.list
sudo apt-get update

# 2. Install
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y cloudflare-warp
```

## ToS Acceptance (PITFALL: requires PTY)

`warp-cli registration new` will refuse with "Please accept the WARP Terms of Service by running this command in a TTY or by passing the --accept-tos flag." The `--accept-tos` flag is NOT recognized by the CLI. You must wrap in a TTY:

```bash
# ✅ Works — PTY wrapper via `script`
sudo pty=true script -q -c "warp-cli registration new" /dev/null < /dev/null

# ❌ Does NOT work — non-TTY, no input pipe
echo "y" | sudo warp-cli registration new
sudo warp-cli registration new --accept-tos
```

After registration, subsequent commands can be run directly without PTY:
```bash
sudo warp-cli mode proxy
sudo warp-cli proxy port 1080
sudo warp-cli connect
```

## Verify the Proxy Works

```bash
# 1. Port listening
ss -tlnp | grep 1080
# LISTEN 127.0.0.1:1080

# 2. Check exit IP (should be a Cloudflare IP, NOT Mona's 43.163.85.51)
curl -sS --max-time 10 --proxy socks5h://127.0.0.1:1080 https://ifconfig.me

# 3. Test Kimchi
KEY=$(sqlite3 ~/.9router/db/data.sqlite "SELECT json_extract(data, '\$.apiKey') FROM providerConnections WHERE name='Kimchi-01';")
curl -sS --max-time 15 --proxy socks5h://127.0.0.1:1080 \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -H "User-Agent: curl/8.5.0" \
  -d '{"model":"minimax-m2.7","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
  https://llm.kimchi.dev/openai/v1/chat/completions
# HTTP 200 = works. HTTP 402 = credits exhausted (key works, account empty). HTTP 1010 = WARP IP also blocked (rare, switch WARP endpoint or use different provider).
```

## Configure 9Router to Use WARP SOCKS5

Per-connection proxy in the `providerConnections.data` JSON:

```python
import sqlite3, json
from datetime import datetime, timezone

db = sqlite3.connect('/home/ubuntu/.9router/db/data.sqlite')
now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
for row in db.execute("SELECT id, data FROM providerConnections WHERE name='Kimchi-01'"):
    d = json.loads(row[1] or '{}')
    d['providerSpecificData']['connectionProxyEnabled'] = True
    d['providerSpecificData']['connectionProxyUrl'] = 'socks5://127.0.0.1:1080'
    d['providerSpecificData']['connectionNoProxy'] = ''
    db.execute("UPDATE providerConnections SET data=?, updatedAt=? WHERE id=?",
               (json.dumps(d), now, row[0]))
db.commit()
# 9router reads the new config on next provider call — no restart needed
```

Note: URL format for 9Router is `socks5://` (NOT `socks5h://`). 9Router handles DNS resolution itself; `h` (resolve via proxy) is curl-specific. If you use `socks5h://` in the 9Router config, it may fail with hostname resolution errors.

## Persist Across Reboot

The `warp-svc` systemd service is enabled by default after install. Verify:
```bash
systemctl is-enabled warp-svc   # enabled
```

It will auto-connect after reboot. If the proxy port isn't listening on boot, run:
```bash
sudo warp-cli connect
```

## Distinguishing Proxy Failure vs Account Issue

After WARP is set up, the error codes mean different things:

| HTTP Code | Body | Meaning | Fix |
|-----------|------|---------|-----|
| 200 | JSON completion | Works | None |
| 401 | "Authorization Required" (HTML) | Key invalid/revoked | Generate new key from app.kimchi.dev (MANUAL, not script) |
| 402 | "provider ... exhausted its credits" JSON | Key VALID, account out of credits | Top up at app.kimchi.dev, or use different account |
| 403 | `error code: 1010` | WARP IP is also Cloudflare-banned (rare) | Try WARP+ (paid), or fall back to non-Cloudflare path |

**401 ≠ 402 ≠ 403.** Conflating these is a common mistake. The proxy might be working perfectly while the *account* is empty. Always check both the HTTP code AND the body format.

## Why Not Just System-Wide WARP?

You could use `warp-cli mode warp` (full tunnel) instead of `proxy`. **Don't.** Reasons:
- Full tunnel breaks `localhost` services (9Router dashboard at :20128 might still work, but other services may not)
- Breaks Hye-Jin tunnel access (if it comes back)
- Affects monitoring tools that check Mona's real IP
- More failure surface

`proxy` mode is surgical: only the processes that explicitly opt in get the WARP IP. 9Router does, everything else doesn't.

## When WARP Itself Is Blocked

WARP uses Cloudflare's network. If Cloudflare has blocked a destination site (Kimchi in our case) AT THEIR EDGE — not just our IP — then WARP exit IP will also be blocked (rare, but happens if Cloudflare adds Kimchi to a global block). The diagnostic curl from this doc will return 1010 even via WARP. Fallbacks:
- Wait 24-48h for Cloudflare's block to age out
- Use a different provider through 9Router (MiMo, Kiro)
- Set up WARP+ (paid Cloudflare plan, different IP pool)

## Fallback Chain

When configuring 9Router for production use with WARP, keep the proxy URL pointing to `socks5://127.0.0.1:1080`. If WARP is down (warp-cli disconnect, port not listening), curl will fail with "Connection refused" — that's a real proxy failure, not a credit issue. Restart:
```bash
sudo warp-cli connect
sleep 3
ss -tlnp | grep 1080  # verify
```

## Summary

| Step | Command |
|------|---------|
| Install | `apt-get install -y cloudflare-warp` (after adding Cloudflare repo) |
| Register | `sudo pty=true script -q -c "warp-cli registration new" /dev/null < /dev/null` |
| Set mode | `sudo warp-cli mode proxy` |
| Set port | `sudo warp-cli proxy port 1080` |
| Connect | `sudo warp-cli connect` |
| Verify IP | `curl --proxy socks5h://127.0.0.1:1080 https://ifconfig.me` |
| Verify Kimchi | curl `/v1/chat/completions` with proxy, expect 200/402 (not 1010) |
| Update 9Router | Set `connectionProxyEnabled=True`, `connectionProxyUrl='socks5://127.0.0.1:1080'` |
| Persist | `warp-svc` systemd service is enabled by default |
