---
name: "crypto-alerting"
description: "Professional Telegram crypto alert formatting and bot patterns. Covers whale alerts, signal hits, multi-topic delivery, and the silent-when-empty discipline. Use when wiring a Telegram bot to fire crypto alerts, designing an alert format, or troubleshooting alert spam."
tags:
  - "crypto"
  - "alerting"
  - "telegram"
  - "whale"
  - "signal"
  - "bot"
---
# Crypto Alerting

> Telegram-based crypto alert formatting and bot patterns. The class of "tell me when X happens" workflows.

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "crypto alert", "telegram alert", "whale alert", "token alert" | `references/crypto-alert-bot/` |

## Topic Pages

- `references/crypto-alert-bot/SKILL.md` — Professional Telegram crypto alert formatting (whale alerts, signal hits, etc.)

## Cross-Cutting Patterns

- **Silent-when-empty:** If no quality signals found, do NOT send empty "no signals" messages. Stay silent. The user explicitly rejected alert spam.
- **Topic-based delivery:** Multi-topic Telegram groups (forum mode) — deliver each alert type to its own topic.
- **Rate limit yourself:** Even if the data pipeline can fire 100 alerts/hour, throttle to what the user can actually act on.

## Related

- `mona-command-center` (in hermes/) — the broader Telegram bot architecture
- `crypto-alpha-sniper` (in crypto/) — the data sources that generate signals
- `crypto-trading` (in crypto/) — the actions to take on alert hits
