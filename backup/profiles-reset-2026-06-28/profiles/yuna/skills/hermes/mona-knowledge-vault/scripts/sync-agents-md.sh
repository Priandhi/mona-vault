#!/bin/bash
# sync-agents-md.sh — Keep root AGENTS.md and vault AGENTS.md in sync
#
# Usage:
#   ./sync-agents-md.sh
#
# What it does:
#   1. Diffs /home/ubuntu/AGENTS.md vs /home/ubuntu/obsidian-vault/AGENTS.md
#   2. If different, copies root → vault
#   3. Stages and commits the change to vault repo
#   4. Prints status
#
# Pitfall this prevents:
#   AGENTS.md protocol drift between root (auto-injected) and vault (Git-tracked).
#   When out of sync, future sessions load stale protocol.

set -e

ROOT_AGENTS="/home/ubuntu/AGENTS.md"
VAULT="/home/ubuntu/obsidian-vault"
VAULT_AGENTS="${VAULT}/AGENTS.md"

if [ ! -f "$ROOT_AGENTS" ]; then
  echo "❌ Root AGENTS.md not found: $ROOT_AGENTS"
  exit 1
fi

if [ ! -d "$VAULT" ]; then
  echo "❌ Vault not found: $VAULT"
  exit 1
fi

# Check if files differ
if cmp -s "$ROOT_AGENTS" "$VAULT_AGENTS" 2>/dev/null; then
  echo "✅ AGENTS.md already in sync (root == vault)"
  exit 0
fi

echo "🔄 AGENTS.md drift detected. Syncing root → vault..."

cp "$ROOT_AGENTS" "$VAULT_AGENTS"

cd "$VAULT" || exit 1
git add AGENTS.md

# Only commit if there's actually a staged change
if git diff --cached --quiet; then
  echo "✅ Sync complete (no commit needed — vault copy was already current)"
  exit 0
fi

COMMIT_MSG="vault: AGENTS.md sync — $(date +%Y-%m-%d)"

git commit -m "$COMMIT_MSG"

echo "✅ AGENTS.md synced + committed"
echo "   Commit: $COMMIT_MSG"
echo "   Files: root=$ROOT_AGENTS"
echo "          vault=$VAULT_AGENTS"

# Show the diff summary
git log -1 --stat -- AGENTS.md

# Optional: notify via Telegram
# Uncomment if you want sync notifications
# if [ -f /home/ubuntu/.hermes/.env ]; then
#   source /home/ubuntu/.hermes/.env
#   curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
#     -d "chat_id=${TELEGRAM_CHAT_ID}" \
#     -d "text=📝 AGENTS.md synced" > /dev/null
# fi
