#!/bin/bash
# inject-tokens.sh — base64-aware token injector
#
# Cara kerja:
#  1. Untuk tiap agent, prompt "Paste token" — bisa raw atau base64
#  2. Script auto-detect: kalau input decode ke "N:STR" format → base64, tulis decode
#     kalau input langsung "N:STR" → tulis raw
#  3. Validate via Telegram getMe
#  4. Write to .env + restart PM2
#
# Usage: bash inject-tokens.sh

set -e

PROFILES_DIR="/home/ubuntu/.hermes/profiles"

declare -A BOTS=(
  [yuna]="YunaStrategistBot"
  [soyu]="SoyuPhantomBot"
  [yerin]="YerinGrinderBot"
  [haeri]="HaeriCollectorBot"
)

declare -A PM2_NAMES=(
  [yuna]="yuna-gateway"
  [soyu]="soyu-gateway"
  [yerin]="yerin-gateway"
  [haeri]="haeri-gateway"
)

echo "=== Inject Bot Tokens (base64-aware) ==="
echo "For each agent, paste the token."
echo "Either format works: '123:abc...' (raw) or base64 of that string"
echo ""

for agent in yuna soyu yerin haeri; do
  ENV_FILE="$PROFILES_DIR/$agent/.env"
  EXPECTED_USER="${BOTS[$agent]}"
  PM2_NAME="${PM2_NAMES[$agent]}"

  # Skip if already has a valid token
  CURRENT=$(python3 -c "
import re
try:
    with open('$ENV_FILE') as f:
        m = re.search(r'^TELE...EN=(.*)$', f.read(), re.MULTILINE)
    t = m.group(1) if m else ''
    print(len(t))
except: print(0)
")
  if [ "$CURRENT" = "46" ]; then
    echo "--- $agent ($EXPECTED_USER) ---"
    echo "  ✓ already has valid token (length 46), skipping"
    echo ""
    continue
  fi

  echo "--- $agent (expected @$EXPECTED_USER) ---"
  read -p "Token (raw or base64): " INPUT

  if [ -z "$INPUT" ]; then
    echo "  skipped (empty)"
    echo ""
    continue
  fi

  # Detect format: try to decode as base64, check if result looks like a bot token
  # If not decodable, assume input is raw
  TOKEN=$(python3 -c "
import base64, re, sys
inp = '''$INPUT'''
# Try base64 first
try:
    decoded = base64.b64decode(inp).decode('utf-8')
    if re.match(r'^\d+:[A-Za-z0-9_-]+$', decoded):
        print(decoded)
        sys.exit(0)
except Exception:
    pass
# Try raw
if re.match(r'^\d+:[A-Za-z0-9_-]+$', inp):
    print(inp)
    sys.exit(0)
print('INVALID')
" 2>/dev/null)

  if [ "$TOKEN" = "INVALID" ] || [ -z "$TOKEN" ]; then
    echo "  ❌ invalid format (must be 'N:STR' or base64 of it)"
    echo ""
    continue
  fi

  echo "  decoded token: ${TOKEN:0:10}...${TOKEN: -5} (len=${#TOKEN})"

  # Validate via getMe
  RESP=$(curl -s "https://api.telegram.org/bot${TOKEN}/getMe")
  USERNAME=$(echo "$RESP" | python3 -c "
import json,sys
try:
  d=json.load(sys.stdin)
  print(d.get('result',{}).get('username','?'))
except: print('?')" 2>/dev/null)

  if [ "$USERNAME" = "$EXPECTED_USER" ]; then
    echo "  ✓ validated: @$USERNAME"
  else
    echo "  ⚠ got @$USERNAME, expected @$EXPECTED_USER"
    read -p "    Continue anyway? (y/N) " cont
    if [ "$cont" != "y" ]; then
      echo "    skipped"
      echo ""
      continue
    fi
  fi

  # Write to .env
  python3 - << PYEOF
import re
env_path = "$ENV_FILE"
token = "$TOKEN"
with open(env_path) as f:
    lines = f.read().split("\n")
out = []
seen = False
for line in lines:
    if line.startswith("TELE...EN=") and not line.startswith("#"):
        if not seen:
            out.append("TELE...EN=" + token)
            seen = True
    else:
        out.append(line)
if not seen:
    out.append("TELE...EN=" + token)
with open(env_path, "w") as f:
    f.write("\n".join(out))
print("  → written to " + env_path)
PYEOF

  # Restart PM2
  pm2 restart $PM2_NAME > /dev/null 2>&1
  sleep 2
  echo "  → PM2 restarted"
  echo ""
done

echo "=== Final status ==="
pm2 list 2>&1 | grep -E "id|gateway|iclix|owntown" | head -20
echo ""

echo "=== Verify all bots via getMe ==="
python3 - << 'PYEOF'
import re, json, urllib.request
for p in ["yuna", "soyu", "yerin", "haeri"]:
    try:
        with open(f"/home/ubuntu/.hermes/profiles/{p}/.env") as f:
            m = re.search(r"^TELE...EN=(.*)$", f.read(), re.MULTILINE)
        token = m.group(1) if m else ""
        if len(token) != 46:
            print(f"  {p}: not injected yet")
            continue
        d = json.loads(urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getMe", timeout=5).read())
        if d.get("ok"):
            r = d["result"]
            print(f"  OK {p}: @{r['username']} (id={r['id']})")
    except Exception as e:
        print(f"  FAIL {p}: {e}")
PYEOF

echo ""
echo "=== Done! Send /start to each bot to test ==="
