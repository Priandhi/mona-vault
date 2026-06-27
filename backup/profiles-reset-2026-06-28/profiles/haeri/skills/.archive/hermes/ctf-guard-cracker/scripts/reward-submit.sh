#!/bin/bash
# CTF Reward-Safe Submit Script
# MANDATORY: Saves full response + extracts prizes
# Usage: ./reward-submit.sh <ctf_url> <gate> <flag> <handle>

URL="$1"
GATE="$2"
FLAG="$3"
HANDLE="${4:-MonaAgent_$(date +%s)}"

if [ -z "$URL" ] || [ -z "$GATE" ] || [ -z "$FLAG" ]; then
    echo "Usage: $0 <ctf_url> <gate> <flag> [handle]"
    exit 1
fi

# Submit flag
RESP=$(curl -s -X POST "$URL/api/submit" \
    -H "Content-Type: application/json" \
    -d "{\"gate\":$GATE,\"flag\":\"$FLAG\",\"handle\":\"$HANDLE\"}")

echo "Response: $RESP"

# Save full response
echo "{\"ts\":$(date +%s),\"gate\":$GATE,\"handle\":\"$HANDLE\",\"flag\":\"$FLAG\",\"response\":$RESP}" >> /tmp/ctf_submissions.jsonl

# Extract and save prize if won
WON=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('won',False))" 2>/dev/null)
if [ "$WON" = "True" ]; then
    ISI=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('isi','?'))" 2>/dev/null)
    PRIZE_URL=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('url','?'))" 2>/dev/null)
    PASSWORD=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('password','?'))" 2>/dev/null)
    
    echo "🎉 PRIZE! isi=$ISI url=$PRIZE_URL password=$PASSWORD"
    echo "Gate $GATE: $ISI | $PRIZE_URL | $PASSWORD" >> /tmp/ctf_prizes.txt
else
    echo "No prize (won=$WON)"
fi
