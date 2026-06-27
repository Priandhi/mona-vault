# Meridian + Hermes Telegram Conflict Resolution

## Problem

Both Hermes and Meridian use the same Telegram bot token (`@Monaa_Ai_Bot`). When both processes call `getUpdates` simultaneously, Telegram only delivers updates to ONE of them. The other gets nothing or alternating batches — causing missed messages and the appearance that Mona "disappeared."

## Root Cause

Meridian's `telegram.js` has a `startPolling()` function that calls `getUpdates` in a loop. Hermes also polls the same token for its own Telegram connection. Telegram API limitation: only one polling session per token.

## Solution: TELEGRAM_NO_POLL

### Step 1: Add env var to Meridian `.env`

```bash
TELEGRAM_NO_POLL=true
```

### Step 2: Modify `telegram.js` startPolling()

```javascript
export function startPolling(onMessage) {
  if (!TOKEN) return;
  if (process.env.TELEGRAM_NO_POLL === "true") {
    log("telegram", "Polling disabled (TELEGRAM_NO_POLL) — Hermes handles incoming messages");
    return;
  }
  _polling = true;
  poll(onMessage);
  registerCommands();
  log("telegram", "Bot polling started");
}
```

### What still works without polling

- `sendMessage()`, `sendHTML()` — outbound notifications ✅
- `notifyDeploy()`, `notifyClose()`, `notifySwap()`, `notifyOutOfRange()` ✅
- `createLiveMessage()` — streaming screening reports ✅
- `editMessage()` — updating existing messages ✅

### What doesn't work without polling

- `/positions`, `/close <n>`, `/set <n>` commands from Telegram ❌
- Any incoming message handling from Meridian's bot ❌

These commands are handled by Hermes anyway, so no functionality is lost.

## Forum Topic Integration

To send Meridian notifications to a specific forum topic (not just the group):

### Step 1: Add to `.env`

```bash
TELEGRAM_MESSAGE_THREAD_ID=947
```

### Step 2: Modify `telegram.js`

After the `chatId` declaration, add:

```javascript
const THREAD_ID = process.env.TELEGRAM_MESSAGE_THREAD_ID || null;
```

In `postTelegram()`, modify the body:

```javascript
body: JSON.stringify({
  chat_id: chatId,
  ...(THREAD_ID ? { message_thread_id: Number(THREAD_ID) } : {}),
  ...body
}),
```

This ensures ALL notifications go to the correct topic. No changes needed to individual send functions — they all go through `postTelegram`.

## Verification

```bash
# Check polling is disabled
pm2 logs meridian --lines 20 | grep "Polling disabled"

# Test notification still works
cd ~/mona-workspace/meridian && node -e "
import dotenv from 'dotenv';
dotenv.config();
import('./telegram.js').then(async (tg) => {
  console.log('isEnabled:', tg.isEnabled());
  const r = await tg.sendHTML('✅ Test notification');
  console.log('Sent:', r?.ok);
});
"
```
