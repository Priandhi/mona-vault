# OpenClaw Superagent v4.1 Integration Guide

## What It Is
A self-improving, self-healing agent framework (122 files, 802KB) designed as a Hermes skill overlay. Created by the user and sent as `SUPERAGENT-v4.1.zip`.

## Key Capabilities to Integrate

### 1. Reflection Engine → Hermes Cron
- Run reflection cycle every 6-24h
- Scan recent logs, distill patterns into lessons
- Auto-fix reversible issues (restart crashed processes, clear stale state)
- Propose non-reversible changes as operator review

### 2. Watchdog → Systemd/Cron Health Check
- Monitor critical processes: mona_autonomous.py, mona_bot.py, 9router, headroom
- Auto-restart with rate limiting (max 5/hour)
- Alert on repeated failures

### 3. Vault → Address/Macro Storage
- Store frequently-used addresses with labels
- Macro workflows (multi-step named sequences)
- FROZEN — cannot be edited by self-improve loop

### 4. Governor → Safety Rails
- Spend caps per tx and per day
- Approval flow for large transactions
- Fund movement restrictions

### 5. HIDS → Intrusion Detection
- File integrity monitoring on critical paths
- Unauthorized access detection
- Anomaly alerting

### 6. Skill Integrity → SKILLS.lock Verification
- SHA256 hash verification of all skill files
- Detect tampering or corruption
- Alert on integrity violations

## Security Model
- FROZEN_PATHS: 18+ files that self-improve CANNOT touch
- SAFE_AUTO_ACTIONS: only reversible, non-financial actions
- Audit log: all autonomous actions recorded
- Governor: hard spend caps, not advisory

## Files to Deploy
Source: `/tmp/superagent_v4/openclaw/`
Target: `~/.hermes/skills/hermes/openclaw-superagent-framework/`

### Tools (27 Python files)
All in `tools/` directory. Key ones:
- reflection.py (203 lines) — self-improvement loop
- watchdog.py (126 lines) — process monitoring
- vault.py (108 lines) — address/snippet storage
- governor.py — safety rails
- hids.py — intrusion detection
- skill_integrity.py — hash verification
- skill_forge.py — auto-create skills

### Skills (37 markdown files)
- m0-m29.md — progressive capability modules
- x1-x7.md — extension skills
- hermes/ — Hermes integration (SKILL.md, DISPATCH.md, 15 references, 11 scripts)

## Integration Priority
1. **Watchdog** — immediately useful (monitor Mona processes)
2. **Reflection** — high value (learn from logs, auto-fix)
3. **Vault** — medium value (address management)
4. **Governor** — medium value (safety rails)
5. **HIDS** — lower priority (security hardening)
6. **Skill Integrity** — lower priority (tamper detection)

## Pitfalls
1. Self-improve MUST NOT edit FROZEN_PATHS
2. Watchdog only monitors operator-registered processes
3. Vault is FROZEN (prevents address swap attack)
4. Governor spend caps are hard limits
5. SKILLS.lock must be verified before executing skills
6. Reflection proposals NEVER auto-applied (except SAFE_AUTO_ACTIONS)
