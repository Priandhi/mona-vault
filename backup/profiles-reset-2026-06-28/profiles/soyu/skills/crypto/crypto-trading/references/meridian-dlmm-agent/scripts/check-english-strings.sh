#!/bin/bash
# check-english-strings.sh
# Verifies that all user-facing strings in the Meridian bot are in Bahasa Indonesia.
# Run from the meridian repo root (cd ~/mona-workspace/meridian first).
#
# Returns exit code 0 if clean, 1 if any English strings found.
# Usage: bash ~/.hermes/skills/crypto/meridian-dlmm-agent/scripts/check-english-strings.sh

set -uo pipefail

# Common English output phrases that should NOT appear in bot source code
# Add new patterns here when you find new leak sources.
PATTERNS=(
  # notify functions in telegram.js
  "Deployed "
  "Closed "
  "Swapped "
  "Out of Range"
  # command labels
  "Open Positions"
  "No open positions"
  "Invalid number"
  "Closing "
  "Close failed"
  "Close-all finished"
  "Closed position"
  # config labels
  "Config snapshot"
  "SOL price:"
  "Open positions:"
  "Next deploy amount"
  "HiveMind: on"
  "HiveMind: off"
  "Strategy: "
  "Screening: "
  "Intervals: manage"
  # TUI
  "Commands:"
  "Let the agent"
  "Shut down"
  "Agent is busy"
  "Deploying "
  "No eligible pools found"
  # morning briefing
  "Morning Briefing"
  "Positions Opened:"
  "Positions Closed:"
  "Fees Earned:"
  "All-time PnL"
  "No new lessons recorded"
  "Current Portfolio"
  # help text
  "Telegram commands"
  "show commands"
  "list open positions"
  "detailed info"
  "close one position"
  "set note/instruction"
  "show important runtime config"
  "button menu"
  "update persisted config"
  "refresh deterministic"
  "show latest cached"
  "deploy candidate by"
  "morning briefing"
  "HiveMind sync status"
  "manual HiveMind pull"
  "stop cron cycles"
  "start cron cycles"
  "shut down agent"
  # candidates
  "Top candidates"
  "Latest candidates"
  "No candidates available"
  "Filtered examples"
  "No cached candidates"
  "Invalid candidate index"
  # ranges
  "Price range:"
  "Range cover:"
  "Amount:"
  # errors
  "Failed to "
  "Error fetching"
)

cd ~/mona-workspace/meridian || { echo "FAIL: Cannot cd to ~/mona-workspace/meridian"; exit 1; }

LEAKS=0
echo "Scanning for English strings in Meridian bot source..."
echo ""

for pattern in "${PATTERNS[@]}"; do
  # Search across the 4 files that contain user-facing strings
  matches=$(grep -nE "$pattern" index.js telegram.js briefing.js prompt.js 2>/dev/null \
    | grep -v "languageRule" \
    | grep -v "BAHASA INDONESIA" \
    | grep -v "Translate technical terms" \
    | grep -v "Indonesian equivalents" \
    | grep -v "Indonesian)" || true)
  if [ -n "$matches" ]; then
    echo "LEAK: \"$pattern\""
    echo "$matches" | sed 's/^/   /'
    echo ""
    LEAKS=$((LEAKS + 1))
  fi
done

# Verify the LANGUAGE RULE is still in prompt.js
RULE_COUNT=$(grep -c "BAHASA INDONESIA" prompt.js 2>/dev/null || echo 0)
if [ "$RULE_COUNT" -lt 1 ]; then
  echo "MISSING: prompt.js is missing the LANGUAGE RULE constant!"
  echo "   Add: const languageRule = \`\\n🌐 LANGUAGE RULE... BAHASA INDONESIA...\`"
  echo "   And inject it into ALL buildSystemPrompt() branches."
  LEAKS=$((LEAKS + 1))
fi

# Verify BOT_COMMANDS array exists and has Indonesian
CMD_COUNT=$(grep -cE "description: \"(Tampilkan|Refresh|Set|Update|Tutup|Biar|Snapshot|Matikan|Hentikan|Mulai|Pelajari|Trigger)" telegram.js 2>/dev/null || echo 0)
if [ "$CMD_COUNT" -lt 10 ]; then
  echo "WARNING: BOT_COMMANDS array may have non-Indonesian descriptions (found $CMD_COUNT Indonesian descriptions)"
  echo "   Expected: 19 Indonesian descriptions matching /help text"
fi

echo ""
if [ "$LEAKS" -eq 0 ]; then
  echo "OK: All clear - no English strings found in user-facing output"
  exit 0
else
  echo "FAIL: Found $LEAKS category/ies of English leaks. Fix and re-run."
  exit 1
fi
