#!/bin/bash
# Test all Kimchi connections in 9Router
# Usage: bash test_kimchi_connections.sh [--proxy http://localhost:8888]
#
# PITFALL (patched 2026-06-13): parens `(...)` inside double-quoted strings are
# interpreted by bash as command substitution, breaking the script silently.
# Use ${var} syntax or escape with \( \). See SKILL.md Common Review Traps.

PROXY=""
if [ "$1" = "--proxy" ] && [ -n "$2" ]; then
    PROXY="--proxy $2"
    echo "📡 Using proxy: $2"
fi

DB="$HOME/.9router/db/data.sqlite"

echo "🔍 Testing all Kimchi connections..."
echo "=================================="

# Get all Kimchi connections
connections=$(sqlite3 "$DB" "SELECT name, json_extract(data, '\$.apiKey') FROM providerConnections WHERE name LIKE 'Kimchi%' ORDER BY name;")

passed=0
failed=0
total=0

while IFS='|' read -r name key; do
    [ -z "$name" ] && continue
    total=$((total + 1))
    prefix="${key:0:20}..."

    # Test the key (User-Agent: curl/8.5.0 required — Cloudflare blocks default Python UA)
    result=$(curl -s $PROXY --max-time 15 \
        -H "Authorization: Bearer *** \
        -H "Content-Type: application/json" \
        -H "User-Agent: curl/8.5.0" \
        "https://llm.kimchi.dev/openai/v1/chat/completions" \
        -d '{"model":"minimax-m2.7","messages":[{"role":"user","content":"test"}],"max_tokens":5}' 2>&1)

    if echo "$result" | grep -q '"choices"'; then
        echo "✅ ${name} [${prefix}]: VALID"
        passed=$((passed + 1))
    elif echo "$result" | grep -q '401'; then
        echo "❌ ${name} [${prefix}]: INVALID KEY (401)"
        failed=$((failed + 1))
    elif echo "$result" | grep -q '403'; then
        echo "🚫 ${name} [${prefix}]: IP BLOCKED (403)"
        failed=$((failed + 1))
    else
        echo "⚠️  ${name} [${prefix}]: UNKNOWN ERROR"
        failed=$((failed + 1))
    fi
done <<< "$connections"

echo "=================================="
echo "📊 Results: ${passed}/${total} passed, ${failed} failed"

if [ "$failed" -gt 0 ]; then
    echo ""
    echo "💡 For invalid keys (401): Generate new keys manually from HP browser"
    echo "💡 For blocked IPs (403): Setup proxy with --proxy flag"
fi
