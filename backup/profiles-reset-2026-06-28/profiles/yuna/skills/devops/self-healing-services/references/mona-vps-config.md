# Mona Stack — Canonical VPS Config

The specific deployment being maintained by this agent. Use this as a reference for any Mona-stack work.

## VPS Identity

| Field | Value |
|---|---|
| IP | 43.163.85.51 |
| Hostname | VM-0-2-ubuntu (Volcengine-style) |
| OS | Ubuntu 24.04.4 LTS |
| User | ubuntu (uid 1000) |
| HOME | /home/ubuntu |

This is **NOT** the Hye-Jin VPS (13.211.42.29, AWS). Two different machines. Don't conflate.

## Path Conventions

| Path | Purpose |
|---|---|
| `~/.hermes/` | Hermes config + logs + state |
| `~/.hermes/hermes-agent/` | Hermes Agent source + venv |
| `~/.hermes/hermes-agent/venv/` | Primary venv used by both services |
| `~/.hermes/venv-mona/` | Secondary venv (used by some cron scripts) |
| `~/.hermes/scripts/` | Operational scripts (watchdog, startup check, safety check) |
| `~/.hermes/scripts/autonomous_agent/` | Mona autonomous agent source |
| `~/.hermes/config.yaml` | Hermes config |
| `~/.hermes/.env` | API keys (do NOT source in bash — see pitfalls) |
| `~/.hermes/logs/` | All operational logs |
| `~/.config/systemd/user/` | Systemd user service files |
| `~/.local/bin/uv` | uv (Python package manager) |

## Services

### hermes-gateway.service

```ini
[Unit]
Description=Hermes Agent Gateway - Messaging Platform Integration
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=60
StartLimitBurst=5

[Service]
Type=simple
ExecStart=/home/ubuntu/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main gateway run --replace
WorkingDirectory=/home/ubuntu/.hermes
Environment="PATH=/home/ubuntu/.hermes/hermes-agent/venv/bin:/home/ubuntu/.hermes/hermes-agent/node_modules/.bin:/usr/bin:/home/ubuntu/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="VIRTUAL_ENV=/home/ubuntu/.hermes/hermes-agent/venv"
Environment="HERMES_HOME=/home/ubuntu/.hermes"
Restart=always
RestartSec=5
RestartMaxDelaySec=300
RestartSteps=5
RestartForceExitStatus=75
KillMode=mixed
KillSignal=SIGTERM
ExecReload=/bin/kill -USR1 $MAINPID
TimeoutStopSec=210
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

### mona-autonomous.service

```ini
[Unit]
Description=Mona Autonomous Agent - Full Autonomous Trading
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/ubuntu/.hermes/scripts/autonomous_agent
ExecStart=/home/ubuntu/.hermes/hermes-agent/venv/bin/python3 autonomous_loop.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mona-autonomous

# Environment
Environment="PYTHONUNBUFFERED=1"
Environment="PATH=/home/ubuntu/.hermes/hermes-agent/venv/bin:/home/ubuntu/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="VIRTUAL_ENV=/home/ubuntu/.hermes/hermes-agent/venv"
Environment="HERMES_HOME=/home/ubuntu/.hermes"
TimeoutStopSec=30

# Resource limits
MemoryMax=512M
CPUQuota=50%

[Install]
WantedBy=default.target
```

## Cron Jobs (user crontab)

```
# Watchdog — every 5 min
*/5 * * * * /home/ubuntu/.hermes/scripts/mona_watchdog.sh

# Laporan Garapan — every 10 min (PAUSED)
# */10 * * * * /home/ubuntu/.hermes/venv-mona/bin/python /home/ubuntu/.hermes/scripts/mona_laporan_garapan.py >> /tmp/laporan_garapan.log 2>&1 (paused by Mona 2026-06-13)

# Airdrop Scan @airdropfind — every 5 hours
0 */5 * * * /home/ubuntu/.hermes/venv-mona/bin/python /home/ubuntu/.hermes/scripts/mona_airdrop_scanner.py >> /tmp/airdrop_scan.log 2>&1

# Logs Reporter — every 3 hours
0 */3 * * * /home/ubuntu/.hermes/venv-mona/bin/python /home/ubuntu/.hermes/scripts/mona_logs_reporter.py >> /tmp/logs_reporter.log 2>&1

# Daily Research — 10:00 WIB (UTC+7 = 03:00 UTC)
0 3 * * * /home/ubuntu/.hermes/venv-mona/bin/python /home/ubuntu/.hermes/scripts/mona_daily_research.py >> /tmp/daily_research.log 2>&1

# Airdrop Auto Pipeline — every 3 hours
0 */3 * * * /home/ubuntu/.hermes/venv-mona/bin/python /home/ubuntu/.hermes/scripts/mona_airdrop_auto_pipeline.py --run >> /tmp/airdrop_pipeline.log 2>&1
@reboot nohup hermes gateway run > ~/.hermes/logs/gateway.log 2>&1 &   # legacy dead code
```

## Required Prereqs (one-time setup)

```bash
# 1. Enable user service persistence
sudo loginctl enable-linger ubuntu
loginctl show-user ubuntu | grep Linger  # must be Linger=yes

# 2. Verify runtime dir exists
test -d /run/user/1000 && echo "OK" || echo "MISSING — login first to create"

# 3. Install watchdog
(crontab -l 2>/dev/null | grep -qF "mona_watchdog.sh") || \
  (crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/.hermes/scripts/mona_watchdog.sh") | crontab -
```

## Tunnel Endpoints (CF quick tunnel, ephemeral)

URLs change on reconnect. Always read from `/tmp/tunnel-watchdog/urls.json`.

```bash
cat /tmp/tunnel-watchdog/urls.json
# {
#   "9router": "https://<random>.trycloudflare.com",
#   "iclix":   "https://<random>.trycloudflare.com",
#   "updated": "ISO timestamp"
# }
```

The watcher (`pm2: tunnel-url-watcher`) auto-updates `urls.json` and posts to Telegram on URL change.

## User Communication Conventions

- **Language:** Bahasa Indonesia, casual
- **Address:** "sayang" (always)
- **Terse signals to match:** "gas", "lanjut", "ok", short emoji reactions
- **Stop signals:** "jangan muter-muter", "lu masih nasehati gua lagi?", frustration emoji 😭
- **Discuss-not-act signals:** "dengerin dulu", "jangan dikerjain", sharing external suggestions for review
- **Frustration triggers:** fabricating bugs, lecturing after being told to stop, refusing tasks as "can't be done"
- **Praise triggers:** owning mistakes fast, finding real bugs, executing without asking, being honest about limits
