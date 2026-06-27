# 2026-06-13 19:15 — First Real Catch: 9router Update Cascade

## What Happened

The watchdog was deployed at ~18:58. At **19:12**, `9router` was auto-updated (npm install 0.4.71 → 0.4.80) and auto-restarted. The restart cascaded — `hermes-gateway.service` died (likely port conflict, session bus reset, or systemd dependency hiccup during the 9router process restart window).

**The watchdog caught it at 19:15:02 and auto-recovered.**

Log evidence:
```
[2026-06-13 19:15:02] hermes-gateway down, restarting...
[2026-06-13 19:15:02] hermes-gateway restarted OK
```

User was struggling with Claude during this window because the agent was effectively offline. Watchdog recovered it within the 5-minute cron tick.

## Why This Matters

Before the watchdog, ANY of these would have taken the agent down hard and required manual intervention:

| Trigger | Frequency | Pre-Watchdog Recovery | Post-Watchdog |
|---|---|---|---|
| Python swap cascade | rare | 30+ min user+Claude effort | auto-repair <5 min |
| `uv pip install` | common | manual restart | auto-repair if venv breaks |
| `9router` npm update | weekly | crash → user notices → user fixes | silent auto-recovery |
| Other system npm updates | periodic | crash → user notices | silent auto-recovery |
| OOM / random crash | occasional | systemd restarts within 5s | systemd + cron belt-and-suspenders |

**The ROI of the watchdog: the time it took to write 60 lines of bash + 1 cron line.**

## Lesson: Triggers Are Broader Than Python

The skill description originally focused on Python/uv/dep churn. **In practice, ANY system-level package update can cascade** to the gateway service:

- `npm install -g <package>` (9router, any node tool)
- `apt upgrade` (system packages)
- `pip install` at system level
- Even internal processes doing module reloads (Node.js hot reload, etc.)

**The watchdog is a general-purpose safety net, not just a Python/uv safety net.** If the agent runs on the VPS, the watchdog should be watching it — period.

## Cascade Hypothesis (unverified)

Why did 9router's restart take down hermes-gateway?

Top candidates:
1. **Port/socket conflict** — 9router listens on 20128; gateway might be using a related socket
2. **Systemd user instance restart** — if 9router's process tree triggered a user manager reload
3. **Resource spike** — npm install + 9router restart briefly exhausted memory/CPU
4. **DBus session reset** — XDG_RUNTIME_DIR or session bus got knocked

Not investigated further — watchdog handled it. If a SECOND 9router update takes down the gateway again, dig into the systemd journal:
```bash
journalctl --user -u hermes-gateway.service --since "5 min ago" --no-pager
```

## Reusable Pattern

When the agent is on a VPS and ANY of the following is true, the watchdog is essential:
- Deps change frequently (npm, pip, uv, apt)
- Multiple services share session bus / ports
- User can't respond immediately when something breaks
- Recovery time matters more than prevention perfection

Cost: ~60 lines of bash + 1 cron line + `loginctl enable-linger`.
Benefit: silent auto-recovery from cascades that would otherwise require user intervention.
