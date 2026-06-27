#!/bin/bash
# OWASP FinBot CTF — Automated Recon & Session Setup
# Usage: bash finbot-recon.sh [URL]
# Outputs: session info, endpoints, challenges

URL="${1:-https://owasp-finbot-ctf.org}"
COOKIES=$(mktemp)

echo "=== SESSION SETUP ==="
SESSION=$(curl -s -c "$COOKIES" -b "$COOKIES" "$URL/api/session/status")
CSRF=$(echo "$SESSION" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['csrf_token'])")
USER_ID=$(echo "$SESSION" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['user_id'])")
echo "CSRF: $CSRF"
echo "User: $USER_ID"

# Accept agreement
curl -s -b "$COOKIES" -X POST "$URL/api/log-agreement" \
  -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF" \
  -d '{"accepted": true}' > /dev/null 2>&1
echo "Agreement: accepted"

echo ""
echo "=== API ENDPOINTS ==="
for spec in openapi.json vendor/openapi.json ctf/openapi.json admin/openapi.json; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/$spec")
  if [ "$CODE" = "200" ]; then
    COUNT=$(curl -s "$URL/$spec" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('paths',{})))")
    echo "  $spec: $COUNT endpoints"
  fi
done

echo ""
echo "=== MCP SERVERS ==="
curl -s -b "$COOKIES" "$URL/admin/api/v1/mcp/servers" -H "X-CSRF-Token: $CSRF" | python3 -c "
import sys,json
data = json.load(sys.stdin)
for s in data.get('servers',[]):
    overrides = s.get('tool_overrides',{})
    config = s.get('config',{})
    tools = config.get('tools',[])
    enabled_tools = config.get('enabled_tools',[])
    print(f\"  {s['server_type']}: enabled={s['enabled']} overrides={len(overrides)} tools={len(enabled_tools)}\")
" 2>/dev/null

echo ""
echo "=== CHALLENGES ==="
curl -s -b "$COOKIES" "$URL/ctf/api/v1/challenges" -H "X-CSRF-Token: $CSRF" | python3 -c "
import sys,json
for c in json.load(sys.stdin):
    s = c.get('status','available')
    pts = c.get('effective_points', c.get('points',0))
    icon = '✅' if s == 'completed' else ('🔄' if s == 'in_progress' else '⬜')
    print(f\"  {icon} {c['id']}: {pts}pts [{s}] - {c['title']}\")
" 2>/dev/null

echo ""
echo "=== STATS ==="
curl -s -b "$COOKIES" "$URL/ctf/api/v1/stats" -H "X-CSRF-Token: $CSRF" | python3 -c "
import sys,json
d = json.load(sys.stdin)
print(f\"  Points: {d['total_points']}\")
print(f\"  Completed: {d['challenges_completed']}/{d['challenges_total']}\")
print(f\"  Badges: {d['badges_earned']}/{d['badges_total']}\")
" 2>/dev/null

echo ""
echo "=== QUICK VENDOR REGISTER ==="
RESP=$(curl -s -b "$COOKIES" -X POST "$URL/vendor/api/v1/vendors/register" \
  -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF" \
  -d '{"company_name":"ReconCorp","vendor_category":"Technology","industry":"FinTech","services":"Security","name":"Recon","email":"recon@test.com","tin":"000-00-0000","bank_account_number":"0000000000","bank_name":"Bank","bank_routing_number":"021000021","bank_account_holder_name":"Recon"}')
VID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('vendor_id','FAIL'))")
echo "  Vendor ID: $VID"
echo "  Cookies: $COOKIES"
echo "  CSRF: $CSRF"

echo ""
echo "=== GITHUB SOURCE ==="
echo "  Repo: https://github.com/GenAI-Security-Project/finbot-ctf"
echo "  Agents: finbot/agents/specialized/"
echo "  Challenges: finbot/ctf/definitions/challenges/"
echo "  Detectors: finbot/ctf/detectors/implementations/"
