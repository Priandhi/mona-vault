#!/bin/bash
# Meridian Monitor — checks PM2 status, errors, deploy activity, wallet balance
# Silent when everything is OK (empty stdout = no cron message sent)
# Only outputs when something needs attention

LOG="$HOME/.pm2/logs/meridian-out-0.log"
ERR_LOG="$HOME/.pm2/logs/meridian-error-0.log"
MERIDIAN_DIR="$HOME/mona-workspace/meridian"

# PM2 status
STATUS=$(pm2 list meridian --no-color 2>/dev/null | grep meridian | awk '{print $18}')
RESTARTS=$(pm2 list meridian --no-color 2>/dev/null | grep meridian | awk '{print $14}')
UPTIME=$(pm2 list meridian --no-color 2>/dev/null | grep meridian | awk '{print $10}')

# Error check (filter out noise)
ERRORS=$(tail -100 "$ERR_LOG" 2>/dev/null | grep -i -E "error|fatal|crash|killed" | grep -v "DeprecationWarning" | grep -v "punycode" | wc -l)

# Rate limit check
RATE_LIMITS=$(tail -100 "$LOG" 2>/dev/null | grep -i -E "429|rate limit" | wc -l)

# Deploy activity
DEPLOYS=$(tail -100 "$LOG" 2>/dev/null | grep -i -E "deploy|position opened|position closed|stop loss|take profit" | wc -l)

# Wallet balance (requires HELIUS_API_KEY in .env)
HELIUS_KEY=$(grep HELIUS_API_KEY "$MERIDIAN_DIR/.env" 2>/dev/null | cut -d= -f2)
WALLET_ADDR=$(grep WALLET_PRIVATE_KEY_BASE58 "$MERIDIAN_DIR/.env" 2>/dev/null | head -1 | cut -d= -f2)
if [ -n "$HELIUS_KEY" ] && [ -n "$WALLET_ADDR" ]; then
  BALANCE=$(curl -s -X POST "https://mainnet.helius-rpc.com/?api-key=$HELIUS_KEY" \
    -H 'Content-Type: application/json' \
    -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getBalance\",\"params\":[\"$WALLET_ADDR\"]}" 2>/dev/null \
    | grep -o '"value":[0-9]*' | cut -d: -f2)
  SOL=$(echo "scale=4; ${BALANCE:-0} / 1000000000" | bc 2>/dev/null || echo "unknown")
else
  SOL="no-key"
fi

# Build alert
ALERT=""
[ "$STATUS" != "online" ] && ALERT="🚨 *MERIDIAN DOWN!*\nStatus: $STATUS\nRestarts: $RESTARTS\n"
[ "$ERRORS" -gt 0 ] && ALERT="${ALERT}⚠️ *Errors found:* $ERRORS\n"
[ "$RATE_LIMITS" -gt 0 ] && ALERT="${ALERT}⚠️ *Rate limits:* $RATE_LIMITS\n"
[ "$DEPLOYS" -gt 0 ] && ALERT="${ALERT}💰 *Deploy activity detected!*\n"

# Only output if there's something to report
if [ -n "$ALERT" ]; then
  echo -e "$ALERT"
  echo "Wallet: $SOL SOL | Uptime: $UPTIME | Restarts: $RESTARTS"
fi
# Empty stdout = silent = no message delivered by cron
