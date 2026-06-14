#!/bin/bash
# inject-tokens.sh
# Inject real bot tokens into each profile's .env, then restart PM2 agents.
# Run this ONCE on your VPS after Mona creates the agent profiles.
#
# Usage: bash inject-tokens.sh
# You will be prompted to paste each token. Tokens are written directly to disk
# (bypasses the agent's terminal-redaction layer).

set -e

PROFILES_DIR="/home/ubuntu/.hermes/profiles"

declare -A BOTS=(
  [yuna]="@YunaStrategistBot"
  [soyu]="@SoyuSnipetBot"
  [yerin]="@YerinGrinderBot"
  [haeri]="@HaeriCollectorBot"
)

declare -A PM2_NAMES=(
  [yuna]="yuna-gateway"
  [soyu]="soyu-gateway"
  [yerin]="yerin-gateway"
  [haeri]="haeri-gateway"
)

echo "=== Inject Real Bot Tokens ==="
echo ""

for agent in yuna soyu yerin haeri; do
  ENV_FILE="$PROFILES_DIR/$agent/.env"
  BOT_NAME="${BOTS[$agent]}"
  PM2_NAME="${PM2_NAMES[$agent]}"

  echo "--- $agent ($BOT_NAME) ---"
  echo "Get token from @BotFather → paste here (input hidden if possible)"
  read -p "Token: " TOKEN
  if [ -z "$TOKEN" ]; then
    echo "  skipped (empty)"
    continue
  fi

  # Validate via getMe
  RESP=$(curl -s "https://api.telegram.org/bot${TOKEN}/getMe")
  USERNAME=$(echo "$RESP" | python3 -c "import json,sys
try:
  d=json.load(sys.stdin)
  print(d.get('result',{}).get('username','?'))
except: print('?')" 2>/dev/null)

  if [ "$USERNAME" = "${BOTS[$agent]#@}" ] || [ "$USERNAME" != "?" ]; then
    echo "  ✓ Token valid → @$USERNAME"
  else
    echo "  ⚠ Token returned: $USERNAME (expected ${BOTS[$agent]})"
    read -p "    Continue anyway? (y/N) " cont
    if [ "$cont" != "y" ]; then
      echo "  skipped"
      continue
    fi
  fi

  # Write to .env (replaces placeholder line, removes any duplicates)
  python3 << PYEOF
import re
env_path = "$ENV_FILE"
with open(env_path) as f:
    lines = f.read().split("\n")
out = []
seen = False
for line in lines:
    if line.startswith("TELE...EN=") and not line.startswith("#"):
        if not seen:
            out.append("TELE...EN=***            seen = True
        # drop duplicates
    else:
        out.append(line)
if not seen:
    out.append("TELE...EN=***with open(env_path, "w") as f:
    f.write("\n".join(out))
print("  → written to $ENV_FILE")
PYEOF

  # Restart the agent
  pm2 restart $PM2_NAME 2>&1 | tail -1

  echo ""
done

echo "=== Verifying all bots ==="
sleep 3
python3 << 'PYEOF'
import os, re, json, urllib.request
for p in ["yuna", "soyu", "yerin", "haeri"]:
    with open(f"/home/ubuntu/.hermes/profiles/{p}/.env") as f:
        m = re.search(r"^TELE...EN=(.*)$", f.read(), re.MULTILINE)
    token = m.group(1) if m else ""
    if not token or "REPLACE" in token:
        print(f"  {p}: still placeholder")
        continue
    try:
        d = json.loads(urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getMe", timeout=5).read())
        r = d.get("result", {})
        print(f"  OK {p}: @{r.get('username')} (id={r.get('id')})")
    except Exception as e:
        print(f"  FAIL {p}: {e}")
PYEOF

echo ""
echo "=== Done! Send /start to each bot to test. ==="
