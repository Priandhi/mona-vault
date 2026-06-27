# Hermes Agent Update Procedure

## When to Update
- `hermes --version` shows "Update available: N commits behind"
- `git tag --sort=-creatordate` shows newer tags than current
- User asks to update or check for updates

## Pre-Update Checklist
```bash
# 1. Backup critical files
BACKUP_DIR=~/.hermes/backup_$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
cp ~/.hermes/config.yaml "$BACKUP_DIR/"
cp -r ~/.hermes/skills/ "$BACKUP_DIR/" 2>/dev/null
cp -r ~/.hermes/data/ "$BACKUP_DIR/" 2>/dev/null
cp ~/.hermes/.env "$BACKUP_DIR/" 2>/dev/null

# 2. Record current version
hermes --version > "$BACKUP_DIR/version.txt"
```

## Update Steps
```bash
cd ~/.hermes/hermes-agent

# 1. Stash any local changes
git stash

# 2. Pull latest
git pull origin main

# 3. Install updated dependencies
pip install -e .

# 4. Verify new version
hermes --version

# 5. Check changelog
git log --oneline -50 --since="$(git describe --tags --abbrev=0)" | grep -E "feat|fix|perf"
```

## Post-Update
```bash
# Restart gateway (picks up new code)
# Gateway auto-restarts via systemd, or manually:
hermes gateway restart

# Check gateway logs for errors
tail -20 ~/.hermes/logs/gateway.log

# Verify Telegram bot is connected
grep "Telegram connected" ~/.hermes/logs/gateway.log
```

## Common Post-Update Issues

### 1. Telegram 409 Conflict
If bot stops responding after update, check for competing processes:
```bash
systemctl status mona-bot  # Look for 409 errors
systemctl stop mona-bot && systemctl disable mona-bot  # If running
```
Only ONE process can poll a bot token at a time. See pitfall #90.

### 2. Dependency Conflicts
If `pip install -e .` fails, try:
```bash
pip install --upgrade pip
pip install -e . --force-reinstall
```

### 3. Config Compatibility
New versions may add/change config fields. Check release notes for breaking changes:
```bash
git log --oneline --grep="BREAKING" HEAD~50..HEAD
```

### 4. Stale PID Files
If gateway won't start after update:
```bash
pkill -f "hermes_cli.main gateway"
sleep 2
hermes gateway restart
```

## Key Changelog Entries (v0.16.0 — June 2026)
- `hermes portal` — new setup wizard with model picker
- max_tokens propagation fix (config → provider)
- Multi-profile remote gateway support
- Self-update safety (no more brick on failed swap)
- Stale HERMES_MAX_ITERATIONS config fix
- Desktop app improvements (i18n, profiles, reconnect)
- Gateway stability fixes

## Reference
- Full changelog: `cd ~/.hermes/hermes-agent && git log --oneline v2026.5.29..HEAD`
- Release tags: `git tag --sort=-creatordate | head -10`
