# Git Source Update — Hermes Agent

When Hermes was installed from git clone (not pip/wheel), update via `git pull` + `pip install`.

## Pre-update Checklist

```bash
# 1. Check current version
hermes --version

# 2. Backup critical files
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak
cp -r ~/.hermes/skills/ /tmp/skills_backup_$(date +%Y%m%d_%H%M%S)/

# 3. Check how far behind
cd ~/.hermes/hermes-agent && git log --oneline -5
git tag --sort=-creatordate | head -3
```

## Update Procedure

```bash
cd ~/.hermes/hermes-agent

# 1. Stash any local changes
git stash

# 2. Pull latest
git pull origin main

# 3. Install updated deps
pip install -e .

# 4. Verify
hermes --version
```

## Post-update Verification

```bash
# Version check
hermes --version  # should show new version + "Up to date"

# Gateway restart (REQUIRED — old gateway still runs old code)
# Option A: systemd
systemctl restart hermes-gateway
# Option B: kill + hermes will respawn
pkill -f "hermes_cli.main gateway"
# Option C: manual restart
hermes gateway restart
```

## Common Issues

1. **Gateway still on old version** — Gateway process keeps running old code in memory. MUST restart after update.
2. **Telegram 409 Conflict** — If `mona-bot.service` and gateway both use the same bot token, only one can poll. Stop `mona-bot.service` before gateway restart.
3. **pip install fails** — Check Python version compatibility. Hermes requires Python 3.11+.
4. **Config schema changes** — New versions may add config keys. Check release notes. Old config usually still works (backward compatible).
5. **Skills directory conflict** — `git pull` may rename/move skill files. Check `git stash` before pull if you have local modifications.

## What Changes in Major Updates

Check `git log vOLD_TAG..vNEW_TAG --oneline` for:
- `feat()` — new features
- `fix()` — bug fixes (many affect stability)
- `perf()` — performance improvements
- `fix(gateway)` — gateway/platform fixes (most impactful for Telegram users)
- `fix(cli)` — CLI improvements
- `fix(update)` — self-update safety fixes

## Gateway Restart Gotcha

After `pip install`, the gateway process still runs the OLD code. The new code only takes effect after restart. If user reports "bot acting weird after update" → check if gateway was restarted.

```bash
# Check gateway process age
ps aux | grep "hermes_cli.main gateway" | grep -v grep
# If started BEFORE the update → restart needed
```
