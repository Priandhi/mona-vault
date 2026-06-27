# Dashboard Link Management & Tunnel Workflow

## localhost.run Tunnel Pattern

Dashboard links expire when SSH tunnels disconnect. To regenerate:

```bash
# 1. Kill old tunnels
pkill -f "localhost.run" 2>/dev/null

# 2. Start new tunnels (background processes)
# Charon Sniper dashboard (:3458)
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:localhost:3458 nokey@localhost.run

# Meridian DLMM dashboard (:3457)
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:localhost:3457 nokey@localhost.run

# 3. Wait for URL output (look for "https://XXXX.lhr.life" after "authenticated as anonymous user")
```

**PITFALL:** Never pipe SSH tunnel through `head` — it truncates the URL. Run directly.

**PITFALL:** The URL appears AFTER the "authenticated as anonymous user" line. Wait 5-10 seconds.

## Sending + Pinning Links to Telegram Topics

Each bot can ONLY pin messages it sent. When using different bots for different topics:

```bash
# Load bot tokens
source ~/.hermes/.env 2>/dev/null  # Mona bot token
source ~/mona-workspace/meridian/.env 2>/dev/null  # DinoCantik bot token

# For Meridian (topic 947) — use DinoCantik bot
RESULT=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id":"-1003899936547","message_thread_id":947,"text":"🌊 MERIDIAN DLMM DASHBOARD\nhttps://NEW_URL.lhr.life","parse_mode":"Markdown"}')
MSG_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['message_id'])")
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/pinChatMessage" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\":\"-1003899936547\",\"message_id\":${MSG_ID}}"

# For Charon (topic 1309) — use Mona bot
source ~/.hermes/.env 2>/dev/null
RESULT=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id":"-1003899936547","message_thread_id":1309,"text":"🔫 CHARON SNIPER DASHBOARD\nhttps://NEW_URL.lhr.life","parse_mode":"Markdown"}')
MSG_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['message_id'])")
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/pinChatMessage" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\":\"-1003899936547\",\"message_id\":${MSG_ID}}"
```

**PITFALL:** `pinChatMessage` returns `{"ok":false,"error_code":400,"description":"Bad Request: message to pin not found"}` when using the WRONG bot token. The message must have been sent by the same bot that's pinning it.

## Verifying Tunnel URLs Before Pinning

After tunnel reconnects, multiple SSH processes may exist with different URLs. Always verify which URLs are actually working before pinning:

```bash
# Check all tunnel processes
ps aux | grep "localhost.run" | grep -v grep | awk '{print $2, $NF}'

# Verify each URL returns 200 (not 503)
curl -s -o /dev/null -w "%{http_code}" --max-time 5 "https://URL1.lhr.life"
curl -s -o /dev/null -w "%{http_code}" --max-time 5 "https://URL2.lhr.life"
```

**PITFALL (Jun8):** 4 tunnel processes existed — 2 old (503) and 2 new (200). The new URLs came from background process notifications (user forwarded them), not from the process logs. Always check response codes. Kill stale tunnels: `kill OLD_PID1 OLD_PID2`.

## PM2 Flush for Clean Debugging

After restarting Meridian, old process logs persist in PM2 log files. This makes it look like fixes aren't working:

```bash
# Flush old logs before debugging
pm2 flush meridian

# Now check fresh logs only
pm2 logs meridian --lines 50 --nostream
```

**When to use:** After fixing 429 errors, changing Connection config, or any code change where you need to verify the fix took effect. Without flush, you'll see 429 messages from OLD processes (different PIDs) mixed with new process output.

**Detection:** Check if 429 messages contain the current process PID:
```bash
CURRENT_PID=$(pm2 list meridian --no-color | grep meridian | awk '{print $6}')
pm2 logs meridian --lines 100 --nostream 2>/dev/null | grep "429" | grep "$CURRENT_PID" | wc -l
# If 0, the 429s are from old processes — flush and recheck
```

## fabriq.trade for PnL Tracking

fabriq.trade is a Solana liquidity and market-intelligence tool with:
- Portfolio overview (Net PnL, Position Win %, Profit Factor, Day Win %)
- Realized PnL calendar view
- Cumulative and daily PnL charts
- Active position tracking
- HawkFi integration for DLMM positions

**No public API** — behind Cloudflare, OpenAPI spec is placeholder (Plant Store). App is a SPA — does NOT support URL-based wallet deep linking.

**Correct URL:** `https://fabriq.trade/portfolio` (base URL — user searches wallet manually)
**NOT this:** ~~`https://fabriq.trade/portfolio/WALLET_ADDRESS`~~ — returns 404

### Styled Button in Dashboard Header (Recommended)

For both Charon and Meridian dashboards, add a styled orange button in the `header-right` div. Use the BASE portfolio URL with wallet address in the `title` attribute for easy copy-paste:

```html
<!-- In the header-right div, BEFORE existing badges -->
<a href="https://fabriq.trade/portfolio" target="_blank"
   title="Search wallet: WALLET_ADDRESS"
   style="background:#FF4500;color:#fff;padding:4px 12px;border-radius:6px;font-size:12px;text-decoration:none;font-weight:600;">
  📊 Fabriq PnL
</a>
```

**Injection points:**
- Charon (`charon-sniper/public/index.html`): inside `<div class="header-right">` at line ~120
- Meridian (`meridian-dashboard/public/index.html`): inside `<div class="header-right">` at line ~109

After editing, restart both dashboards:
```bash
pm2 restart charon-sniper-dashboard meridian-dashboard
```

Then recreate tunnels and re-pin links in Telegram topics.

**WALLET_ADDRESS:** Derive from `.env` WALLET_PRIVATE_KEY:
```bash
cd ~/mona-workspace/meridian
node -e "
const { Keypair } = require('@solana/web3.js');
const bs58 = require('bs58');
require('dotenv').config();
const kp = Keypair.fromSecretKey(bs58.decode(process.env.WALLET_PRIVATE_KEY));
console.log(kp.publicKey.toString());
"
```

### General Pattern: External Portfolio Trackers

Most Solana portfolio trackers (Birdeye, Step Finance, Solana FM, fabriq.trade) are behind Cloudflare and don't support deep linking from server-side. The practical pattern is:

1. Link to the base portfolio/overview page
2. Embed wallet address in `title` attribute for copy-paste
3. User searches manually in-app

This is less professional than deep linking but reliable across all trackers.
