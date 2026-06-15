# Receipt — Full VPS restore: PM2 daemon crashed, brought back 11 services

**Date**     : 2026-06-15
**Agent**    : MONA — The Architect
**Task**     : Diagnose why user-facing services were down, restore all in PM2 + persist dump

## Root Cause
PM2 daemon restarted at **10:40** (likely crash or `hermes gateway install`). On restart, only `pm2-logrotate` survived. The dump file was wiped to a single entry after `pm2 save` was called later. All user services (iclix-api, bot-router, 5 hermes gateways, charon, meridian, tunnel-watcher) were dead. Only 9Router + cloudflared tunnels (started Jun 13 via root systemd) + the autonomous_loop gateway were alive.

## What I Did

### 1. Fixed Aerolink (preliminary)
- Started `aerolink-openai` PM2 process on :20129 (Python proxy, bridges Anthropic native → OpenAI chat)
- Fixed 9Router DB: `Aerolink-01/02` were pointing to `capi.aerolink.lat` directly (Anthropic native, 9Router can't speak that) → re-pointed to `http://localhost:20129/v1`
- Reset error state (testStatus=active, errorCode=0, cleared modelLocks)
- User confirmed live: `aerolink/claude-opus-4-6` → 200 OK 6.2s, then switched default to opus-4-6

### 2. Cleaned up dead services (per user request)
- **owntown-farming-bot** (59M) → renamed to `.DELETED-2026-06-15` (rollback-able). User: "hapus owntown dan freellm"
- **freellmapi** — already gone (project folder deleted previously). Cleaned up residual PM2 logs.

### 3. Restored 11 services

| # | Service | Port | Status |
|---|---------|------|--------|
| 1 | aer-olink-openai | 20129 | ✓ online |
| 2 | iclix-api | 3000 | ✓ online (HTTP 200) |
| 3 | tunnel-url-watcher | — | ✓ online |
| 4 | charon-sniper | — | ✓ online |
| 5 | charon-sniper-dashboard | — | ✓ online |
| 6 | meridian | — | ✓ online (DRY_RUN=true) |
| 7 | yuna-gateway | — | ✓ Telegram connected |
| 8 | soyu-gateway | — | ✓ Telegram connected |
| 9 | yerin-gateway | — | ✓ Telegram connected |
| 10 | haeri-gateway | — | ✓ Telegram connected |
| 11 | mona-bot-gateway | — | ✓ Telegram connected |

### 4. Resolved architecture conflict
**Found:** `bot-router-new` (legacy 5-bot dispatcher) was using the SAME 5 Telegram tokens as the 5 hermes gateways (yuna/soyu/yerin/haeri/mona-bot). They were fighting each other via 409 Conflict errors.

**Fix (user chose option 1):** Stopped + deleted `bot-router-new`. The 5 hermes gateways now own those 5 bots exclusively. Each hermes has its own profile = memory/skills/config isolation, which bot-router didn't have.

### 5. Gotchas hit + fixed
- **PM2 default interpreter = node**, but `hermes` is a Python venv symlink. First attempt → 4/5 hermes crashed with `SyntaxError`. **Fix:** added `--interpreter python3` to all 5 hermes starts.
- **bot-router orphan kill:** When stopping bot-router, the existing getUpdates sessions on Telegram's servers took ~20s to expire, causing one more conflict wave. Resolved cleanly.

## Decisions
- **Why option 1 (drop bot-router):** bot-router was legacy single-process in-process AI dispatch. The 5 hermes gateways are the new per-profile architecture with proper isolation. bot-router = redundant.
- **Why rename-not-delete for owntown:** "asal aman" rule. User can `mv` back. 59M still on disk but recoverable.
- **Why 5 hermes use --interpreter python3:** PM2 doesn't auto-detect shebang. `hermes` → Python venv script, not Node. Must specify.

## Issues
- **Test mona-bot still shows 24 conflicts in log** — those are all from BEFORE the clean restart at 11:25. Fresh state since then is clean. Verified via `gateway_state.json`: `"telegram": {"state": "connected"}` for all 5.
- **Root hermes-agent gateway (PID 1121865) still running** — this is MY session's gateway. Uses main config TELEGRAM_BOT_TOKEN (838976...), different from the 5 profile tokens, so NO conflict with the 5 hermes. Leaving it alone.
- **meridian 100% CPU initially** — that was config-load burst, normalized to 0% within seconds.
- **freellmapi DELETED from history** — no recovery possible, project was already gone. Only PM2 logs remain in `.pm2/logs/` as historical record.

## Verification
- 9Router: 14 models, `aerolink/claude-opus-4-6` returns 200 OK
- ICLIX frontend (port 3000): HTTP 200
- 5 hermes gateways: each shows `state: "connected"` in `gateway_state.json`
- No new conflict warnings since 11:25:40
- `pm2 save` persisted all 11 services to `/home/ubuntu/.pm2/dump.pm2`

## Next Steps
- None required — system is operational
- Optional: `rm -rf /home/ubuntu/owntown-farming-bot.DELETED-2026-06-15/` if 59M wants reclaiming
- Optional: clean up rotated PM2 logs in `/home/ubuntu/.pm2/logs/` (mostly historical)
- Future: if PM2 daemon restarts again, all 11 services will auto-resurrect from dump

## Lessons Saved
- When adding a new connection to 9Router with an existing provider: **must reuse same `provider` UUID** as siblings, or it creates a separate group
- PM2 needs `--interpreter python3` for Python scripts (hermes, bot_router, etc.)
- Always `pm2 save` after starting services, or new starts won't survive daemon restart
- Two Telegram architectures (bot-router + hermes-gateways) on same tokens = persistent 409 Conflict
