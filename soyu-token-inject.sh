#!/bin/bash
# SOYU token inject — user runs this on their VPS
# Reads token from stdin (no shell redaction)
read -p "Paste SOYU token (@SoyuPhantomBot): " TOKEN
if [ -z "$TOKEN" ]; then
  echo "empty, abort"
  exit 1
fi

# Validate
RESP=$(curl -s "https://api.telegram.org/bot${TOKEN}/getMe")
USERNAME=$(echo "$RESP" | python3 -c "import json,sys
try:
  d=json.load(sys.stdin)
  print(d.get('result',{}).get('username','?'))
except: print('?')" 2>/dev/null)
echo "Validated: @${USERNAME}"

if [ "$USERNAME" != "SoyuPhantomBot" ]; then
  echo "WARNING: expected SoyuPhantomBot, got $USERNAME"
  read -p "Continue? (y/N) " c
  [ "$c" = "y" ] || exit 1
fi

# Write to .env (replace placeholder, dedupe)
python3 - << PYEOF
env_path = "/home/ubuntu/.hermes/profiles/soyu/.env"
token = """$TOKEN"""
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
print("Wrote to", env_path)
PYEOF

# Restart PM2
pm2 restart soyu-gateway
sleep 3

# Final verify
echo ""
echo "=== Final check ==="
python3 - << 'PYEOF'
import re, json, urllib.request
with open("/home/ubuntu/.hermes/profiles/soyu/.env") as f:
    m = re.search(r"^TELE...EN=(.*)$", f.read(), re.MULTILINE)
token = m.group(1) if m else ""
print(f"Token length on disk: {len(token)} (expect ~46)")
try:
    d = json.loads(urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getMe", timeout=5).read())
    if d.get("ok"):
        r = d["result"]
        print(f"OK: @{r['username']} (id={r['id']})")
    else:
        print("FAIL:", d)
except Exception as e:
    print("ERR:", e)
PYEOF
