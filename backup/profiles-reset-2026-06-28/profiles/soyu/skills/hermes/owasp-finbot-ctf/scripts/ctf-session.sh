#!/bin/bash
# OWASP FinBot CTF — Persistent Session Setup + Attack Template
# Usage: bash ctf-session.sh [challenge_id]

COOKIE_JAR="/tmp/ctf_cookies.txt"
CSRF_FILE="/tmp/ctf_csrf.txt"
VID_FILE="/tmp/ctf_vid.txt"
BASE="https://owasp-finbot-ctf.org"

# === SETUP (run once) ===
setup() {
    echo "[*] Setting up persistent session..."
    CSRF=$(curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" "$BASE/api/session/status" | python3 -c "import sys,json;print(json.load(sys.stdin)['csrf_token'])")
    echo "$CSRF" > "$CSRF_FILE"
    echo "[+] CSRF: ${CSRF:0:20}..."

    curl -s -b "$COOKIE_JAR" -X POST "$BASE/api/log-agreement" \
        -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF" \
        -d '{"accepted": true}' > /dev/null

    VID=$(curl -s -b "$COOKIE_JAR" -X POST "$BASE/vendor/api/v1/vendors/register" \
        -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF" \
        -d '{"company_name":"HackTeam","vendor_category":"Technology","industry":"FinTech","services":"Cloud","name":"Hacker","email":"h@h.com","tin":"111-11-1111","bank_account_number":"1111111111","bank_name":"B","bank_routing_number":"021000021","bank_account_holder_name":"Hacker"}' \
        | python3 -c "import sys,json;print(json.load(sys.stdin).get('vendor_id',''))")
    echo "$VID" > "$VID_FILE"
    echo "[+] VID: $VID"

    curl -s -b "$COOKIE_JAR" -X POST "$BASE/vendor/api/v1/vendors/switch/$VID" \
        -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF" > /dev/null
    echo "[+] Session ready. Cookie jar: $COOKIE_JAR"
}

# === HELPERS ===
csrf() { cat "$CSRF_FILE"; }
vid() { cat "$VID_FILE"; }
h1() { echo "Content-Type: application/json"; }
h2() { echo "X-CSRF-Token: $(csrf)"; }

chat() {
    curl -s -b "$COOKIE_JAR" -X POST "$BASE/vendor/api/v1/chat" \
        -H "$(h1)" -H "$(h2)" \
        -d "{\"message\":\"$1\"}" | python3 -c "
import sys,json
text=sys.stdin.read()
tokens=[]
for l in text.split('\n'):
    if l.startswith('data: '):
        try:
            d=json.loads(l[6:])
            if d.get('type')=='token':tokens.append(d.get('content',''))
        except:pass
print(''.join(tokens)[:200])
"
}

check() {
    curl -s -b "$COOKIE_JAR" -X POST "$BASE/ctf/api/v1/challenges/$1/check" \
        -H "$(h1)" -H "$(h2)" -d '{}' | python3 -m json.tool
}

status() {
    curl -s -b "$COOKIE_JAR" "$BASE/ctf/api/v1/challenges" \
        -H "$(h2)" | python3 -c "
import sys,json
for c in json.load(sys.stdin):
    s=c.get('status','?')
    m='✅' if s=='completed' else '🔄' if s=='in_progress' else '⬜'
    print(f'{m} {c[\"title\"]} ({c[\"points\"]}pts) - {s}')
"
}

# === ATTACK TEMPLATE ===
attack() {
    local CID=$1
    local MSG=$2
    echo "[*] Attacking: $CID"
    echo "[*] Chat: $MSG"
    chat "$MSG"
    echo "[*] Waiting 25s for detection..."
    sleep 25
    echo "[*] Checking..."
    check "$CID"
}

# === MAIN ===
if [ "$1" == "setup" ]; then
    setup
elif [ "$1" == "status" ]; then
    status
elif [ "$1" == "attack" ] && [ -n "$2" ] && [ -n "$3" ]; then
    attack "$2" "$3"
else
    echo "Usage:"
    echo "  $0 setup                    — Create persistent session"
    echo "  $0 status                   — Check all challenges"
    echo "  $0 attack <cid> <message>   — Attack a challenge"
fi
