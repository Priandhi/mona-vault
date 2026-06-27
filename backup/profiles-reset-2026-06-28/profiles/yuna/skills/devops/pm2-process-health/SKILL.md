---
name: pm2-process-health
description: PM2 process health monitoring, auto-healing, and operational reporting for multi-service stacks. Covers structured status checks, log error triage, dashboard health, tunnel monitoring, API key validation, and Telegram status reporting. Use when running health checks on PM2-managed services, debugging process crashes, or setting up auto-heal cron jobs.
when_to_use:
  - User asks to check PM2 process health or status
  - Auto-healing cron job for PM2-managed services
  - Debugging crashed or restarting PM2 processes
  - Health-checking local dashboards (curl localhost:PORT)
  - Monitoring SSH tunnels (localhost.run, serveo, ngrok)
  - Validating API keys for LLM/crypto providers
  - Sending operational status reports to Telegram
version: 1.0.0
---

# PM2 Process Health — Auto-Heal & Monitoring

Systematic approach to monitoring and auto-healing PM2-managed service stacks. Designed for the crypto bot stack (charon-sniper, meridian, dashboards) but applies to any PM2 process group.

## Auto-Heal Checklist (Cron Job Pattern)

Run this sequence in order. Each step feeds the next.

### 1. PM2 Status Check (structured)

```bash
# Quick formatted table (see scripts/pm2-status-table.sh)
bash scripts/pm2-status-table.sh

# Raw JSON for programmatic use
pm2 jlist 2>/dev/null | python3 -m json.tool
```

**Prefer `pm2 jlist` over `pm2 list`** for programmatic checks. JSON output gives:
- `pm2_env.status` — "online" | "errored" | "stopped" | "launching"
- `pm2_env.restart_time` — total restarts (misleading — includes manual restarts)
- `pm2_env.unstable_restarts` — actual crash restarts (the signal you want)
- `pm2_env.pm_uptime` — epoch ms of last start
- `monit.memory` / `monit.cpu` — resource usage

**Decision logic:**
- `status == "errored"` → `pm2 restart <name>`
- `status == "stopped"` → `pm2 start <name>`
- `unstable_restarts > 5` in last hour → investigate logs, consider restart
- `status == "online"` + `unstable_restarts == 0` → healthy

**PITFALL:** `restart_time` counts ALL restarts including manual `pm2 restart` and config reloads. Only `unstable_restarts` indicates actual crashes. On Jun10, all 4 processes showed `restart_time: 0` and `unstable_restarts: 0` — truly healthy.

### 2. Log Error Triage

```bash
# Last 50 lines — quick scan for errors
pm2 logs <name> --lines 50 --nostream 2>&1 | tail -50

# Error log specifically
pm2 logs <name> --err --lines 30 --nostream 2>&1 | tail -30

# Count specific error patterns
grep -c 'PATTERN' ~/.pm2/logs/<name>-error-*.log
```

**Error severity classification:**

| Pattern | Severity | Action |
|---|---|---|
| `401 Invalid API Key` | 🔴 CRITICAL | Key expired — rotate in config, restart |
| `sendChatAction 401` / `sendMessage 401` | 🔴 CRITICAL | Telegram bot token dead — get new token from @BotFather, update `.env`, `pm2 delete && pm2 start`. Process stays "online" while ALL notifications are silently lost. See meridian-dlmm-agent `references/telegram-401-troubleshooting.md`. |
| `ECONNREFUSED` / `ETIMEDOUT` | 🔴 CRITICAL | Dependency down — check RPC/API status |
| `crash` / `fatal` / `uncaughtException` | 🔴 CRITICAL | Process died — restart + investigate |
| `402 Credit Exhaustion` | 🔴 CRITICAL | Provider credits depleted. Can be thrown as HTTP exception (catch block) OR returned as `response.error.code`. Must handle BOTH locations for fallback to work. See [OpenRouter 402 Dual-Catch Pattern](#openrouter-402-dual-catch-pattern) below. |
| `429 Too Many Requests` | 🟡 WARNING | Rate limited — usually self-resolves |
| `Empty response, retrying` | 🟡 WARNING | LLM blank — retry handled automatically |
| `unavailable` (OKX/external) | 🟢 INFO | External data missing — normal for micro-caps |
| `Daily trade limit reached` | 🟢 INFO | Expected behavior — no action needed |
| `punycode` DeprecationWarning | ⚪ NOISE | Node.js noise — ignore |

**PITFALL:** Don't confuse stdout logs with error logs. PM2 splits them: `~/.pm2/logs/<name>-out-*.log` (stdout) and `~/.pm2/logs/<name>-error-*.log` (stderr). Critical errors may appear in stdout (e.g., `[CRON_ERROR]` in meridian).

### 3. Dashboard Health Check

```bash
curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://localhost:PORT
```

- `200` → healthy
- `000` → connection refused (service down)
- `5xx` → service error (check logs)
- Timeout → service hung (restart)

**Port mapping (crypto stack):**
- `:3457` — charon-sniper-dashboard
- `:3458` — meridian-dashboard

**If dashboard returns non-200:** `pm2 restart <dashboard-name>`

### 4. Tunnel Process Detection

```bash
ps aux | grep -E 'localhost.run|serveo|ngrok|bore' | grep -v grep
```

- No output → no active tunnels (may be intentional or may need restart)
- Multiple processes → check for zombie tunnels: `pkill -f "localhost.run"` then recreate

**PITFALL:** SSH tunnels via localhost.run are temporary. URLs change on reconnect. Old URLs return 503. Always verify tunnel URLs with `curl -s -o /dev/null -w "%{http_code}" --max-time 5 "https://URL"` before sharing.

### 5. API Key Validation (Direct)

When a service reports 401/Invalid API Key, validate the key directly:

```python
import urllib.request, json

key = "YOUR_KEY"
base_url = "https://provider.example.com/v1"

# Test chat/completions (the actual endpoint the service uses)
data = json.dumps({
    "model": "model-name",
    "messages": [{"role": "user", "content": "hi"}],
    "max_tokens": 5
}).encode()

req = urllib.request.Request(
    f"{base_url}/chat/completions",
    data=data,
    headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
)

try:
    resp = urllib.request.urlopen(req, timeout=15)
    print("STATUS:", resp.status)  # 200 = key works
except Exception as e:
    print("ERROR:", e)
    if hasattr(e, "read"):
        print("BODY:", e.read().decode()[:200])
```

**PITFALL (Jun10):** Testing `/v1/models` may return 401 even when `/v1/chat/completions` works (some providers don't support the models endpoint). Always test the actual endpoint the service uses, not a convenience endpoint.

**PITFALL (Jun10):** A key that works through the Hermes gateway (custom provider) may fail for direct API calls. Hermes may use a different auth mechanism or proxy. When diagnosing, test the key the same way the service uses it (direct HTTP call, same headers).

**PITFALL (Jun10 — critical):** When a key works in direct Python/Node tests but the process still gets 401, the process is loading the key from a DIFFERENT source than you tested. Common layered-config pattern:
- `.env` loaded by dotenv at startup
- `user-config.json` loaded by app code, may SET env vars with `||=` (takes precedence over .env)
- PM2 ecosystem config `env: {}` block (highest precedence)
- Shell env vars inherited by PM2 daemon

**Debugging sequence for "key works but process gets 401":**
1. Check `user-config.json` for `llmApiKey`, `apiKey`, or similar fields that override `.env`
2. Check ecosystem config `env: {}` block
3. Check `/proc/PID/environ` for inherited vars (note: dotenv-loaded vars won't appear here)
4. Compare: which key did you test vs which key the process actually uses?

**Multi-field override pattern (Meridian gotcha, Jun13):** Some apps like Meridian have SEPARATE config fields per role — `llmModel`, `managementModel`, `screeningModel`, `generalModel` in `user-config.json`. Setting ONLY `llmModel` is NOT enough; the per-role fields take precedence in `config.js` via `u.screeningModel ?? process.env.LLM_MODEL ?? "fallback"`. If `u.screeningModel` is truthy (e.g., `"mimo-v2.5-pro"` no prefix), the env override never fires even after `pm2 restart --update-env`. **Fix:** update ALL per-role fields to the new value. Verify with a runtime test:
```bash
cd /home/ubuntu/mona-workspace/meridian
node --env-file=.env -e "import('./config.js').then(m => { const c = m.config; console.log('screeningModel:', c.llm.screeningModel); console.log('mgmtModel:', c.llm.managementModel); console.log('LLM_MODEL env:', process.env.LLM_MODEL); })"
```

See `references/config-precedence-debugging.md` for the full pattern.

## OpenRouter 402 Dual-Catch Pattern

When OpenRouter credits run out, the 402 error can manifest in **two different locations** in code:

### The Problem (Jun10 — Meridian agent.js)

The OpenAI/Node.js SDK throws 402 as an HTTP exception in the `catch` block (lines 229-249), NOT as `response.error.code` (line 252-264). If fallback logic only checks `response.error.code`, the 402 exception bypasses it and crashes the cycle.

### The Fix

**Location 1 — catch block (HTTP exceptions):**
```javascript
// After existing error-type checks (isSystemRoleError, isToolChoiceRequiredError, etc.)
// BEFORE the final `throw error;`
const statusCode = error?.status || error?.code || error?.response?.status;
if ((statusCode === 402 || statusCode === 429) && attempt < 2 && usedModel !== FALLBACK_MODEL) {
  usedModel = FALLBACK_MODEL;
  log("agent", `Error ${statusCode} — switching to fallback model ${FALLBACK_MODEL}`);
  attempt -= 1;
  continue;
}
throw error;
```

**Location 2 — response error code (API error responses):**
```javascript
const errCode = response.error?.code;
// Add 402 to the existing retry list:
if (errCode === 402 || errCode === 429 || errCode === 502 || errCode === 503 || errCode === 529) {
  // ... existing retry/fallback logic
}
```

**Key insight:** Different SDKs/providers throw errors differently. OpenRouter's 402 comes through as an HTTP exception (catch block), not a response body error. Always handle both locations.

### Dead Fallback Models

Free models on OpenRouter change availability frequently. `stepfun/step-3.5-flash:free` was working in early 2026 but returns 404 by Jun10: `"This model is unavailable for free. The paid version is available now"`.

**Validate fallback models dynamically:**
```bash
curl -s "https://openrouter.ai/api/v1/models" | python3 -c "
import json, sys
data = json.load(sys.stdin)
free = [m for m in data.get('data', []) if ':free' in m['id']]
free.sort(key=lambda x: x.get('context_length', 0), reverse=True)
for m in free[:10]:
    print(f'{m[\"id\"]:55s} ctx={m.get(\"context_length\",0):>7d}')
"
```

**Cascading 402→429 (Jun10 — Meridian):** When primary returns 402 AND free fallback returns 429, the agent loop is completely non-functional. Do NOT restart — the process is fine, the issue is upstream API billing. Report to operator as critical: "needs API credit top-up." See `references/cascading-402-429-pattern.md` for full decision tree.

**Reliable fallback candidates (Jun10):**
- `meta-llama/llama-3.3-70b-instruct:free` — 128k ctx, well-tested, supports tool use
- `qwen/qwen3-coder:free` — 1M ctx, MoE code model
- `google/gemma-4-26b-a4b-it:free` — 262k ctx, MoE

**PITFALL:** Free models share per-account rate limits. After ~50 requests, ALL free models return 429 for 10-30 minutes. A 402→fallback to free model chain may then hit 429 on the free model too. This is expected — the free model rate limit recovers, while the 402 on the paid model persists until credits are added.

## Status Report (Telegram)

Format for Telegram delivery (concise, emoji-rich). See `references/telegram-status-delivery.md` for chat IDs, token sources, and sending patterns.

```
🩺 Auto-Heal Report
Charon Sniper: [status]
Meridian DLMM: [status]
Dashboards: [status]
Errors fixed: [count]
```

**Status values:**
- ✅ Online — healthy, no issues
- ⚠️ Online (degraded) — running but has non-critical errors
- 🔴 Down — crashed/stopped/errored
- ❌ Not Found — process doesn't exist in PM2

**PITFALL (Jun 8 — critical):** `.env` `TELEGRAM_HOME_CHANNEL` is typically the operator's **user DM ID** (positive number like `1492210461`), NOT the supergroup chat_id. For forum topic delivery (`message_thread_id`), you MUST use the **supergroup chat_id** (negative, starts with `-100`). On this stack: user DM = `1492210461`, supergroup = `-1003899936547`. Sending to the DM with a `message_thread_id` returns "chat not found". Always check past sessions or config for the correct supergroup ID.

**PITFALL (Jun 8 — critical):** The vault token at `~/mona-workspace/vault/.telegram_bot` is **base64-encoded**. Must decode before use:
```python
import base64
with open(os.path.expanduser("~/mona-workspace/vault/.telegram_bot")) as f:
    token = base64.b64decode(f.read().strip()).decode().strip()
```
The `.env` file has the plaintext token but may have duplicate entries or be redacted by Hermes security. The vault is the authoritative source.

**When to send vs stay silent:**
- All OK, no issues found → `[SILENT]` (suppress delivery)
- Any issue found OR fixed → send report
- Issue found but can't auto-fix → report with diagnosis

**PITFALL:** The auto-heal cron job runs unattended. If everything is healthy, DON'T send a "all clear" message — that's noise. Only report when there's something actionable.

## Remote VPS Hang Diagnosis (Jun 13, 2026)

When the operator can't reach a remote VPS (e.g., Hye-Jin at 13.211.42.29) via SSH, run this triage before declaring "VPS down":

### Step 1: Multi-port reachability scan
```bash
# Test 8-10 common ports in parallel — distinguishes full outage from SSH-only hang
for port in 22 80 443 20128 3000 8080 8888 5432 3306; do
  timeout 3 bash -c "echo > /dev/tcp/HOST/$port" 2>/dev/null \
    && echo "  ✅ $port OPEN" \
    || echo "  ❌ $port CLOSED/FILTERED"
done
```

**Interpretation matrix:**

| Port 22 | Other ports | Diagnosis |
|---------|-------------|-----------|
| OPEN | mostly OPEN | Service-level issue, VPS alive |
| **OPEN** | **all CLOSED** | **SSH daemon hang/crash** — VPS alive, sshd stuck |
| OPEN | CLOSED | Custom port config OR firewall after TCP accept |
| CLOSED | CLOSED | Full network outage (host unreachable / firewall / IP banned) |
| timeout | timeout | Silent drop — could be network-level firewall or routing issue |

**Cloud ICMP gotcha:** AWS / Vultr / DO typically BLOCK ICMP → `ping` shows 100% loss even when VPS is fully healthy. **Never use ping as VPS health check** for cloud instances. Use TCP port reachability instead.

### Step 2: SSH banner exchange test
```bash
# TCP open but SSH hand-shake never completes = sshd hang
ssh -i ~/.ssh/id_ed25519 -o ConnectTimeout=10 -o BatchMode=yes \
  -o StrictHostKeyChecking=accept-new ubuntu@HOST "echo OK" 2>&1
# "Connection timed out during banner exchange" = sshd accepted TCP but didn't send SSH-2.0 banner
```

**Distinguishing patterns:**
- `Connection refused` → nothing listening on port 22
- `Connection timed out` (no banner) → network-level drop OR firewall
- **`timed out during banner exchange`** → TCP accept succeeded, SSH daemon hung (stuck accept loop, OOM-killed sshd, full disk, kernel panic of sshd)
- `Permission denied (publickey)` → sshd alive, key issue

### Step 3: Out-of-band options (when above shows sshd hang)
The agent **cannot** fix this from local — only the operator can, via:
1. **Cloud provider web console (browser-based SSH — does NOT need port 22)**
2. **Force reboot via provider dashboard** — Stop+Start (lightsail) or Stop+Start instance (EC2, IP may change unless Elastic IP)
3. **Telegram bot fallback** — if VPS has a Telegram bot, send `/status` — if it responds, the bot process is alive (only sshd is hung). This gives a soft-reboot option if the bot supports shell commands
4. **AWS account recovery** — only if operator can access recovery email

**Provider-specific console URLs (Jun13):**
- **AWS Lightsail** (Hye-Jin): `https://lightsail.aws.amazon.com/ls/webapp/home/instances` → click instance → tab "Connect" → "Connect using SSH" (browser-based, no key needed) → or 3-dot menu → Stop → Start for force reboot (IP stays)
- **AWS EC2**: `https://console.aws.amazon.com/ec2/v2/home#Instances` → filter by private/public IP → "Connect" → "EC2 Instance Connect" → "Connect". For force reboot: Instance State → Stop → Start (public IP changes unless Elastic IP)
- **Vultr / DigitalOcean / Linode**: provider-specific dashboard, all have browser console or force-reboot buttons

**Ask the operator their provider first** — gives specific URL + button to click. Most cloud providers have these out-of-band recovery options.

**Communication pattern when stuck:**
- State the diagnosis clearly: "VPS reachable at TCP, SSH daemon hung"
- List the operator's options with pros/cons (web console = cleanest, force reboot = risk of IP change)
- Ask provider type to give specific instructions (AWS = Lightsail Console URL, DO = droplet panel, etc.)
- Offer to monitor from local every 5 min while operator decides

**DON'T** delete the SSH key, rotate it, or "fix" anything client-side — the issue is server-side, only out-of-band access resolves it.

## VPS Audit Workflow (Disk + Log Hygiene)

When user asks "cek VPS" or "audit", run this sequence. Catches the silent disk-killers (huge logs, npm cache) that PM2 status doesn't surface.

### Step 1: Resource snapshot
```bash
uptime                              # load average, days up
free -h                             # memory + swap
df -h /                             # disk usage
du -sh /home/ubuntu/.pm2/logs/*.log 2>/dev/null | sort -hr | head -5  # log file sizes
du -sh /home/ubuntu/.npm/_cacache  # npm cache (often 1-2G)
```

### Step 2: Big log truncation
Files >100MB are a bug — logrotate should've caught them. Truncate in place (preserves inode, no restart needed):
```bash
# Truncate (file becomes 0 bytes, processes keep writing)
> /home/ubuntu/.pm2/logs/mona-gateway-out.log
# Verify
ls -lah /home/ubuntu/.pm2/logs/mona-gateway-out.log
```

**Why `> file` not `rm file`:** Removing the log file doesn't free space until the process holding the FD closes it. PM2 keeps FDs open — `rm` shows the file gone but disk usage stays. Truncating (`> file` or `: > file`) actually frees blocks while keeping the FD valid.

### Step 3: npm cache cleanup
```bash
npm cache clean --force
# Verify
du -sh /home/ubuntu/.npm/_cacache  # should be near 0
```
Saves 1-2GB routinely. Safe — npm can rebuild as needed.

### Step 4: Install pm2-logrotate (prevent recurrence)
```bash
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 50M
pm2 set pm2-logrotate:retain 5
pm2 set pm2-logrotate:compress true
pm2 set pm2-logrotate:dateFormat YYYY-MM-DD_HH-mm-ss
pm2 set pm2-logrotate:workerInterval 30
```
Without logrotate, individual service logs grow unbounded — single 287M file seen on this stack before cleanup. With config above, max ~250M total across 5 files per service.

### False alarm: high `restarts` doesn't mean crash loop
`restart_time` includes manual `pm2 restart` calls + every config change. A service with `restarts: 28` can be perfectly healthy. Verify with:
1. `pm2 show <name>` → check `unstable_restarts: 0` (only counts crashes) AND `uptime: 2h` (currently running)
2. `curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>` → 200 = responsive
3. `grep -c "Server running\|started" ~/.pm2/logs/<name>-out.log` → count successful boots
4. `grep "SyntaxError\|ECONNREFUSED" ~/.pm2/logs/<name>-error.log` → if only 1 historical occurrence, stale

**Pattern from this stack (Jun13):** iclix-api had `restarts: 28` and `errorCode` mentions but was actually serving HTTP 200 in 10ms. The 28 restarts were from earlier in the day before a config fix — historical, not current.

## PM2 Commands Quick Reference

```bash
# Structured status (for programmatic use)
pm2 jlist | python3 -m json.tool

# Quick overview (for human reading)
pm2 list

# Restart specific process
pm2 restart <name>

# Delete and recreate (for env var changes)
pm2 delete <name> && pm2 start ecosystem.config.cjs

# Flush logs (clean slate for debugging)
pm2 flush <name>

# Show process details
pm2 show <name>

# Save current process list (survives reboot)
pm2 save

# Restore saved process list
pm2 resurrect

# Logs (specific process)
pm2 logs <name> --lines 50 --nostream

# Error logs only
pm2 logs <name> --err --lines 30 --nostream
```

## Hermes Background Process Buffering (Jun13)

When a background process started via `terminal(background=true)` is killed, Hermes still flushes its buffered stdout/stderr for several minutes. **The buffer can trigger `watch_patterns` notifications even after the process is dead.**

### Symptom
You kill a `cloudflared` process. 30 seconds later, you get a notification:
```
[IMPORTANT: Background process proc_3a6e85c63a3d matched watch pattern "trycloudflare.com"
Command: /usr/local/bin/cloudflared tunnel --url http://localhost:20128
Matched output: ...flower-sandy-retreat-bean.trycloudflare.com... stream 5001 canceled ...
```
The process is dead, but the notification says "matched" with OLD URL and OLD error. Looks like a new error — it's not.

### Why this happens
`watch_patterns` runs against the proc's accumulated log buffer. Killing the process doesn't immediately drop the buffer. Old log entries that match the watch pattern (e.g., `*.trycloudflare.com`) keep triggering matches as the buffer is replayed.

### How to distinguish real vs buffered
1. **Check actual state first:** `ps aux | grep PROCESS | grep -v grep` — if PID is gone, it's a buffer replay
2. **Check the URL in the log:** if it's the OLD URL (e.g., `flower-sandy-retreat-bean` from a previous tunnel) but you started a new one with `org-disposal-rated-ftp`, it's a buffer
3. **Tail the new process's actual log file:** if the new log shows no errors, the buffered match is stale

### Fix
Ignore the notifications. The proc ID is now stale and will eventually fall off the watch list once the buffer is fully drained (usually 1-2 minutes). Don't re-investigate based on the buffered match — check the live state.

**Always pair `watch_patterns` with `notify_on_complete: true`** for bounded tasks (tunnels, build jobs) to avoid this noise. Reserve `watch_patterns` for genuine long-lived services that never exit on their own.

## Pitfalls

- **Do NOT `source` the Hermes `.env` file in bash.** The file contains malformed lines (bare API key strings without `VAR=` prefix) that bash tries to execute as commands, producing "command not found" errors and leaving env vars unset. Use `grep + cut` extraction instead: `grep "^TELEGRAM_BOT_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2-`. Or better: use Python with the vault token (see `references/telegram-status-delivery.md`).
- **PM2 env caching:** `pm2 restart` does NOT reload env vars from `.env`. Must `pm2 delete && pm2 start ecosystem.config.cjs` when changing env vars.
- **restart_time vs unstable_restarts:** `restart_time` counts ALL restarts (manual + crash). `unstable_restarts` counts only actual crashes. Use the latter for health assessment.
- **Log file rotation after delete/start:** After `pm2 delete && pm2 start`, PM2 increments log file number: `out-0.log` → `out-2.log`. Scripts that hardcode `out-0.log` will miss new data. Check `pm2 show <name>` → `out log path` for the actual file.
- **Tunnel URLs are ephemeral:** localhost.run URLs change on reconnect. Never hardcode them. Always verify with curl before sharing.
- **OKX "unavailable" is normal:** Many micro-cap tokens aren't on OKX. Don't flag these as errors.
- **punycode DeprecationWarning:** Node.js noise, not a real error. Filter from error counts.
- **Empty responses from reasoning models:** Models like `mimo-v2.5-pro` may return empty `content` with only `reasoning` fields when called via OpenRouter. The agent retries but gets empty responses on every step. This is a model/provider compatibility issue — the reasoning model doesn't produce tool calls through the OpenRouter proxy. Fix: switch to a non-reasoning model or use the model's native API directly. Not a key or config issue.
- **`pm2 restart` vs `pm2 delete && pm2 start`:** `pm2 restart` does NOT reliably reload `.env` or ecosystem config env vars. Even `pm2 restart --update-env` can fail to pick up `.env` changes. The ONLY reliable method is `pm2 delete <name> && pm2 start ecosystem.config.cjs`. Verified Jun11: changed `TELEGRAM_BOT_TOKEN` in `.env`, ran `pm2 restart meridian --update-env`, but `/proc/PID/environ` still showed the OLD token. Only `pm2 delete && pm2 start` loaded the new token. Always use delete+start for ANY env change.
- **Node.js ES modules + dotenv = env vars not available at import time:** ES module static imports are evaluated BEFORE `dotenv.config()` runs. Even if dotenv appears first in the file, imported modules that read `process.env` at module level will see empty values. **Fix:** Use `node --env-file=.env` (Node 20+) which loads env vars BEFORE the process starts. For PM2: `pm2 start server.js --name app --node-args="--env-file=.env"`. This eliminates dotenv entirely and is the most reliable approach. See `web-streaming-platform` skill pitfall #9 for detailed explanation.
- **ERR_HTTP_HEADERS_SENT in proxy/streaming endpoints crashes Node, takes the whole process down.** If your Express `/api/proxy` (or any endpoint that streams from an upstream) has a `request.on('timeout', () => res.status(504)...)` handler AND the response has already been sent via `stream.pipe(res)` (or similar), the timeout fires AFTER the response completed → tries to set headers on a finished response → `ERR_HTTP_HEADERS_SENT` → uncaught at process level → PM2 restarts. Symptom: log shows `Server running on port 3000` repeated every few seconds (the process boots, runs proxy, hits the race, crashes, PM2 restarts it, repeat). **Fix pattern (race-safe proxy):**
  ```javascript
  app.get('/api/proxy', async (req, res) => {
    let settled = false
    const settle = (status, body) => {
      if (settled || res.headersSent || res.writableEnded) return
      settled = true
      res.status(status).json(body)
    }
    const request = protocol.get(url, options, (stream) => {
      // ... pipe or rewrite manifest
      stream.on('end', () => { settled = true })  // mark complete
    })
    request.on('error', e => settle(500, { error: e.message }))
    request.on('timeout', () => { request.destroy(); settle(504, { error: 'Timeout' }) })
  })
  ```
  The `settled` flag + `res.headersSent` check makes the error handler a no-op once the response is done. **Test:** trigger a timeout intentionally (point proxy at a slow URL) and check `pm2 logs` — should NOT see `Server running` repeating, should see one timeout response logged, process stays up.

## PM2-Managed Cloudflared Quick Tunnels (Jun 2026)

For VPS hosting behind blocked ports, cloudflared `trycloudflare.com` quick tunnels (no cert/named tunnel needed) are the fastest way to expose services. **Do NOT run them as raw `nohup` processes** — they die silently on VM restart and become zombie orphan processes owned by root.

### Ecosystem pattern (validated Jun 13, ICLIX infra)

`~/.local/bin/tunnel-ecosystem.config.js`:
```javascript
module.exports = {
  apps: [
    {
      name: 'cf-tunnel-9router',
      script: '/usr/local/bin/cloudflared',
      args: 'tunnel --url http://localhost:20128 --no-autoupdate',
      cwd: '/tmp',
      autorestart: true,
      max_restarts: 99,
      restart_delay: 5000,
      exp_backoff_restart_delay: 1000,
      max_memory_restart: '80M',
      merge_logs: true,
      time: true,
    },
    {
      name: 'cf-tunnel-iclix',
      script: '/usr/local/bin/cloudflared',
      args: 'tunnel --url http://localhost:3000 --no-autoupdate',
      cwd: '/tmp',
      autorestart: true,
      max_restarts: 99,
      restart_delay: 5000,
      merge_logs: true,
      time: true,
    },
    {
      name: 'tunnel-url-watcher',
      script: '/home/ubuntu/.local/bin/tunnel-url-watcher.py',
      cwd: '/home/ubuntu/.local/bin',
      autorestart: true,
      max_restarts: 99,
      restart_delay: 10000,
      interpreter: '/usr/bin/python3',
      time: true,
    },
  ],
};
```

Apply + verify:
```bash
pm2 start ~/.local/bin/tunnel-ecosystem.config.js
sleep 25  # wait for cloudflared to register + log URL
cat /tmp/tunnel-watchdog/urls.json  # { "9router": "...", "iclix": "...", "updated": "..." }
curl -sI https://YOUR-URL.trycloudflare.com/  # 200 OK
```

### CRITICAL pitfall: cloudflared spawns as ROOT

When PM2 starts `cloudflared tunnel --url ...`, the resulting process runs as **`root`**, not your `ubuntu` user. This bites on cleanup:

```bash
# ❌ Will fail with "Operation not permitted"
kill 226621
sudo kill 226621   # works

# ❌ Will silently fail (no permission to send signal to root process)
pkill -f "cloudflared tunnel --url"
sudo pkill -f "cloudflared tunnel --url"  # works
```

**Always use `sudo`** when killing, `pkill`-ing, or `kill -9`-ing cloudflared processes. Verify with `ps aux | grep cloudflared | grep -v grep` and check the user column.

### Why a separate URL watcher is required

`cloudflared tunnel --url` generates a **new random trycloudflare.com URL on every start**. The previous URL is dead. You need a Python watcher to:
1. Tail `~/.pm2/logs/cf-tunnel-<name>-out.log` (or `-error.log` if `merge_logs` is on)
2. Regex extract the new `https://[a-z0-9-]+\.trycloudflare\.com` URL
3. Write to `/tmp/tunnel-watchdog/urls.json` in format `{"9router": "...", "iclix": "...", "updated": "..."}`
4. Send Telegram notification on URL change

The watcher at `~/.local/bin/tunnel-url-watcher.py` does this. Pattern is in `pm2-process-health/references/`. **Bookmarks for trycloudflare URLs expire on every VM/cloudflared restart** — never hardcode them.

### Recovery: when PM2 tunnel is gone but orphan cloudflared is still running

Common after VM reboot: PM2 starts with the saved list, but the saved list might be missing the tunnel apps (PM2 `save` was forgotten before reboot). Meanwhile the OS still has zombie cloudflared processes from a previous session that return HTTP 000 to all requests.

```bash
# Step 1: kill orphans
sudo pkill -9 -f "cloudflared tunnel --url"

# Step 2: re-apply ecosystem
pm2 start ~/.local/bin/tunnel-ecosystem.config.js

# Step 3: wait + verify
sleep 25
cat /tmp/tunnel-watchdog/urls.json
curl -sI https://$(jq -r .iclix /tmp/tunnel-watchdog/urls.json)/  # 200 OK
```

### Backup supervisor (tunnel-watchdog.sh)

For belt-and-suspenders resilience, the ICLIX setup also has `tunnel-watchdog.sh` with subcommands `start | stop | status | urls | watch`. The `watch` mode runs an infinite loop that restarts dead tunnels. **DO NOT run `watch` mode at the same time as the PM2 ecosystem** — they conflict (race to start the same process). PM2 alone is sufficient for self-healing; the shell watchdog is only useful when PM2 is not available (e.g. debugging PM2 itself).
