---
name: "process-ops"
description: "Keep services alive and observable: PM2 process health, self-healing systemd units, watchdog crons, and webhook-driven event subscriptions. Use when a service is crashing, when setting up a long-lived process, or when wiring an external event to trigger an agent run."
tags:
  - pm2
  - systemd
  - watchdog
  - self-healing
  - webhook
  - process-management
---
# Process & Service Operations

> Umbrella for keeping services alive: PM2 process management, self-healing systemd services, watchdog crons, and webhook-driven event subscriptions.

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "pm2", "process down", "ecosystem config" | `references/pm2-process-health/` |
| "self-heal", "systemd restart on failure" | `references/self-healing-services/` |
| "watchdog", "cron that restarts things" | `references/vps-agent-watchdog/` |
| "webhook subscription", "event-driven agent" | `references/webhook-subscriptions/` |

## Cross-Cutting Patterns

**Always log to a stable path.** If a service is crashing, you need to read the log without sudo gymnastics. Standard: `~/.hermes/logs/<service>.log` and `journalctl -u <service>.service`.

**Auto-heal vs alert.** For non-critical background tasks (scanners, monitors): auto-restart on crash. For critical services (auth, payment): alert and require human intervention.

**Health check interval:** 30-60s is the sweet spot. Faster is wasteful; slower risks >2 min downtime.

**PITFALL: PM2 vs systemd.** PM2 is great for foreground long-running scripts. systemd is better for production services that need to survive reboots. Don't try to make PM2 do what systemd does (or vice versa).

## Topic Pages

- `references/pm2-process-health/SKILL.md` — PM2 ecosystem configs, auto-heal, log management
- `references/self-healing-services/SKILL.md` — Systemd units with Restart=always + health probes
- `references/vps-agent-watchdog/SKILL.md` — Cron-based watchdog for AI agent services
- `references/webhook-subscriptions/SKILL.md` — Event-driven agent runs via incoming webhooks

## Related

- `hermes/mona-command-center` — for cron jobs that auto-update the Kanban board / vault
- `mona-knowledge-vault` — for storing task receipts and audit trails
