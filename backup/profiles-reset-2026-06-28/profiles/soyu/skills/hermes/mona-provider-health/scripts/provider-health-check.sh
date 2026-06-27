#!/bin/bash
# Mona Provider Health Check Script
# Usage: ~/mona-workspace/scripts/provider-health-check.sh

echo "🔍 Mona Provider Health Check — $(date)"
echo "========================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test function
test_provider() {
    local name=$1
    local url=$2
    local headers=$3
    local data=$4
    
    echo -n "  $name: "
    
    # Make request
    response=$(curl -s --connect-timeout 5 -X POST "$url" \
        -H "Content-Type: application/json" \
        -H "$headers" \
        -d "$data" 2>/dev/null)
    
    # Check response
    if echo "$response" | grep -q '"choices"'; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    elif echo "$response" | grep -q '"error"'; then
        error=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',{}).get('message','Unknown')[:50])" 2>/dev/null)
        echo -e "${RED}❌ Error: $error${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠️  No response${NC}"
        return 2
    fi
}

echo ""
echo "📊 Primary Provider (MiMo):"
test_provider "MiMo-V2.5-Pro" \
    "https://token-plan-sgp.xiaomimimo.com/v1/chat/completions" \
    "Authorization: Bearer *** \
    '{"model":"mimo-v2.5-pro","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'

echo ""
echo "📊 Fallback Provider 1 (9Router):"
test_provider "9Router (OpenRouter)" \
    "http://localhost:20128/v1/chat/completions" \
    "Authorization: Bearer *** \
    '{"model":"openrouter/deepseek/deepseek-chat-v3-0324","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'

echo ""
echo "📊 Fallback Provider 2 (GeneralCompute):"
test_provider "GeneralCompute (Minimax 2.7)" \
    "https://api.generalcompute.com/v1/chat/completions" \
    "Authorization: Bearer *** \
    '{"model":"minimax-m2.7","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'

echo ""
echo "📊 Summary:"
echo "  - Primary: MiMo-V2.5-Pro (user's credit)"
echo "  - Fallback 1: 9Router → OpenRouter (343 models)"
echo "  - Fallback 2: GeneralCompute → Minimax 2.7 (3 keys)"

echo ""
echo "🔗 Quick Commands:"
echo "  - Status: ~/mona-workspace/scripts/mona-status.sh"
echo "  - Dashboard: ~/mona-workspace/scripts/mona-dashboard.sh"
echo "  - Startup: ~/mona-workspace/scripts/mona-startup.sh"

echo ""
echo "✅ Health check complete!"
