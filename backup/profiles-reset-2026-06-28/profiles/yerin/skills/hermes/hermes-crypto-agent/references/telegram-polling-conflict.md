## Telegram Polling Conflict Resolution (June 2026)

When Meridian and Hermes share the same Telegram bot token, they both call `getUpdates` (polling) and **steal each other's messages** — one process consumes the update before the other sees it. Symptoms: Hermes stops responding to chat, or Meridian misses `/positions` commands.

### Solution: TELEGRAM_NO_POLL

Add to Meridian `.env`:
```env
TELEGRAM_NO_POLL=true
```

Modify `telegram.js` — in `startPolling()`:
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

**Effect**: Meridian only SENDS notifications (deploy/close/swap/OOR/cycle reports) — no polling. Hermes handles all incoming messages exclusively. No conflict.

**Limitation**: Meridian's native Telegram commands (`/positions`, `/close`, `/set`) won't work because polling is disabled. User must go through Mona to manage Meridian positions.

### Alternative: Separate Bot Token (GitHub default)

Create a dedicated bot via @BotFather for Meridian. This is the GitHub-recommended setup:
- `@Monaa_Ai_Bot` → Hermes (polling)
- `@Meridian_Bot` → Meridian (polling)

Both poll independently, no conflict. Meridian commands work natively. Downside: user must chat with 2 different bots.

### GitHub Default vs Our Custom Setup

| Aspect | GitHub Default | Our Setup |
|--------|---------------|-----------|
| LLM | OpenRouter (`OPENROUTER_API_KEY`) | GeneralCompute (`LLM_BASE_URL` + `LLM_API_KEY`) |
| Model | `openai/gpt-oss-20b:free` | `minimax-m2.7` |
| Telegram | Bot polling + commands | No polling (Hermes handles chat) |
| Bot token | Separate Meridian bot | Shared with Mona |
| Config | Default thresholds | Optimized for 0.36 SOL wallet |

To follow GitHub exactly: replace `LLM_BASE_URL`/`LLM_API_KEY` with `OPENROUTER_API_KEY`, change model to `openai/gpt-oss-20b:free`, remove `TELEGRAM_NO_POLL`, create separate bot token, and revert config to defaults.
