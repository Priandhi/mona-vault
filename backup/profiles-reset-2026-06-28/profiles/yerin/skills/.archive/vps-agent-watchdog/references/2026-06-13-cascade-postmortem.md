# 2026-06-13 Python Swap Cascade — Post-Mortem

This is the post-mortem for the incident that motivated the `vps-agent-watchdog` skill.

## Timeline

1. **Mona's VPS** (43.163.85.51, VM-0-2-ubuntu, Ubuntu 24.04) was running the agent on Python 3.11 with uv-managed venv.
2. Mona suggested switching to Python 3.12 as a "more stable" option.
3. User followed the suggestion. Cascade began:
   - **Cascade step 1:** uv + Python 3.11 deletion → venv symlink broken
   - **Cascade step 2:** Someone ran `python3.12 -m venv --clear` → wiped all packages
   - **Cascade step 3:** `pyvenv.cfg` conflict between Python 3.11 (symlink) and 3.12 (venv config)
   - **Cascade step 4:** Full reinstall needed
4. User + Claude diagnosed the 4-step mess and fixed it. User frustration: high.
5. After fix, user shared Claude's proposal for a watchdog + restart policy. Mona reviewed, fabricated Bug 1 (heredoc variable expansion), Claude corrected. Lesson saved.
6. Final state: watchdog deployed, systemd restart policy verified, no recurrence.

## Root Causes

1. **Mona's suggestion was a guess, not a diagnosis.** "Ganti ke Python 3.12" was offered as a generic "more stable" advice without first inspecting:
   - Current venv state (`ls -la .venv`, `pyvenv.cfg`, symlink target)
   - What `uv` was actually doing
   - Whether Python 3.12 was even compatible with the agent's deps

2. **No safety net existed.** When the swap broke things, the system was down hard — no auto-repair, no watchdog, no quick rollback.

3. **No defensive policy on system Python versions.** `uv` and Python 3.11 were load-bearing for the agent; deleting them was catastrophic. There was no guardrail preventing that.

## Fixes Applied

1. **Reinstalled uv + Python 3.11** + redid the venv.
2. **Deployed the watchdog** (`~/.hermes/scripts/mona_watchdog.sh` + cron `*/5 * * * *`):
   - Venv integrity check (`import httpx, openai`)
   - Auto-repair via `uv pip install -e`
   - Service health check + auto-restart
   - Log rotation
3. **Verified systemd restart policies** — both services have `Restart=always` + `RestartSec`; `StartLimitIntervalSec=0` on hermes-gateway was left as-is (gentle restart, low concern).
4. **Memory updated** with two lessons: never casually suggest Python swap; don't fabricate bugs when reviewing.

## Lessons (Embedded in Skills)

### Lesson 1: Check First, Propose Last

**Saved in:** memory (entry 8) + `vps-agent-watchdog` pitfall section

When facing a Python/dep/version issue, INSPECT first:
```bash
ls -la .venv
cat .venv/pyvenv.cfg
which python
python --version
ls -la $(which python)
```

**Only** after understanding the state should you propose a change. And the proposal should be MINIMAL — don't swap versions as a casual fix.

### Lesson 2: Safety Net for Production-Like State

**Saved in:** `vps-agent-watchdog` skill (the entire skill exists because of this)

An agent running on a VPS with systemd services needs a watchdog. The combination of:
- `loginctl enable-linger` (user systemd persistence)
- `XDG_RUNTIME_DIR` export in cron
- Defensive path checks
- Venv integrity test
- Service auto-restart
- Log rotation

...is the minimum viable safety net. Without it, a single Python/uv mistake can take the agent down hard.

### Lesson 3: Don't Fabricate Bugs

**Saved in:** memory (entry 8) + `review-discipline` skill

When reviewing Claude's watchdog proposal, I claimed `<<'EOF'` heredoc didn't expand variables at runtime. **I was wrong.** The script worked fine. The cost was:
- Wasted user time arguing
- Loss of trust in all my future reviews
- User had to push back to correct me

**Rule:** If you can't trace the execution confidently, say "I'm not 100% sure" — not "this is broken." Wrong findings are FAR more expensive than missed issues.

## Pre-Mortem: What Would Have Prevented This

If the watchdog had existed BEFORE the Python swap:
- After swap, venv integrity check would have detected broken state
- Auto-repair would have run `uv pip install -e` and recovered
- Services would have stayed up
- No 4-step manual recovery needed

The 2-hour user effort to diagnose + fix would have been ~5 minutes of automated repair. **That's the ROI of the watchdog.**

## Reusable Patterns

- The full watchdog script is in `templates/mona_watchdog.sh` — copy and adapt for other agents.
- The verification sequence in the main SKILL.md applies to any systemd-based agent deployment.
- The "check first, propose last" rule applies to ANY system-level suggestion (not just Python).
- The review discipline lesson applies to ALL code/config reviews across the agent's work.
