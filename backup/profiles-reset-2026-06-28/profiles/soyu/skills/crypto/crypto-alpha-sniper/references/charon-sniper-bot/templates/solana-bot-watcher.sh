#!/bin/bash
# Auto-watch wallet for SOL → auto-swap to required token → start bot
# Usage: ./solana-bot-watcher.sh <WALLET> <TOKEN_MINT> <REQUIRED_AMOUNT> <BOT_DIR> <BOT_COMMAND> <BOT_PM2_NAME>
#   WAT...   — Solana wallet address to monitor
#   TOKEN... — SPL token mint address required by bot (e.g. OTWN mint)
#   REQ...   — required token amount (e.g. 5000)
#   BOT_DIR  — directory to cd into before running bot
#   BOT...   — command to run bot (e.g. "node bot.js" or "node index.js")
#   PM2...   — name for pm2 process

WALLET="${1:?need wallet address}"
TOKEN_MINT="${2:?need token mint}"
REQUIRED="${3:?need required amount}"
BOT_DIR="${4:?need bot dir}"
BOT_CMD="${5:?need bot command}"
PM2_NAME="${6:?need pm2 name}"

LOG="/tmp/${PM2_NAME}-auto.log"
RESERVE_SOL=0.005  # keep this much SOL for gas

log() {
  echo "[$(date '+%H:%M:%S')] $@"
  echo "[$(date '+%H:%M:%S')] $@" >> "$LOG"
}

get_sol() {
  curl -s "https://mainnet.helius-rpc.com/?api-key=${HELIUS_API_KEY:-2f166885-a270-415e-93f8-a8000f7363ff}" \
    -X POST -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":\"w\",\"method\":\"getBalance\",\"params\":[\"$WALLET\"]}" \
    | python3 -c "import json,sys; print(json.load(sys.stdin).get('result',{}).get('value',0)/1e9)"
}

get_token() {
  curl -s "https://mainnet.helius-rpc.com/?api-key=${HELIUS_API_KEY:-2f166885-a270-415e-93f8-a8000f7363ff}" \
    -X POST -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":\"w\",\"method\":\"getTokenAccountsByOwner\",\"params\":[\"$WALLET\",{\"mint\":\"$TOKEN_MINT\"},{\"encoding\":\"jsonParsed\"}]}" \
    | python3 -c "
import json, sys
d = json.load(sys.stdin)
accts = d.get('result', {}).get('value', [])
print(accts[0].get('account', {}).get('data', {}).get('parsed', {}).get('info', {}).get('tokenAmount', {}).get('uiAmount', 0) if accts else 0)
"
}

log "=== $PM2_NAME AUTO-START WATCHER ==="
log "Wallet: $WALLET"
log "Required: $REQUIRED tokens of $TOKEN_MINT"

while true; do
  SOL=$(get_sol)
  TOK=$(get_token)
  log "Balance: $SOL SOL, $TOK tokens"

  if (( $(echo "$TOK >= $REQUIRED" | bc -l 2>/dev/null || echo 0) )); then
    log "OK ENOUGH tokens! Starting $PM2_NAME..."
    cd "$BOT_DIR"
    pm2 delete "$PM2_NAME" 2>/dev/null
    pm2 start $BOT_CMD --name "$PM2_NAME" --time
    pm2 save
    log "Bot started. Monitor: pm2 logs $PM2_NAME"
    exit 0
  fi

  if (( $(echo "$SOL >= $(echo "$RESERVE_SOL + 0.001" | bc)" | bc -l 2>/dev/null || echo 0) )); then
    log "SOL detected ($SOL). Auto-swapping to token..."
    cd "$BOT_DIR"
    if [ -f "autoswap.js" ]; then
      node autoswap.js "$WALLET" "$TOKEN_MINT" "$SOL" "$RESERVE_SOL" 2>&1 | tee -a /tmp/${PM2_NAME}-swap.log
    else
      log "autoswap.js not found. Manual swap needed."
      log "Send $REQUIRED tokens directly to $WALLET to skip swap."
    fi
    sleep 30
  fi

  sleep 30
done
