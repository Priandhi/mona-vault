---
date: 2026-06-14
agent: MONA
task: Multi-bot topic router migration (Hermes → python-telegram-bot)
result: SUCCESS
---

# Multi-Bot Topic Router — Migration Complete

## Stack
- **Runtime:** Python 3.12 + `python-telegram-bot` 22.6 + `httpx`
- **AI:** 9Router (local) at `http://10.3.0.2:20128/v1/chat/completions`
- **Process manager:** PM2 (id 7: `bot-router-new`)
- **Code:** `/home/ubuntu/bot_router/` (config.py, bot_router.py, migrate.sh, step1_discover_topics.py)

## Architecture
- 5 bots in single Python process: MONA (dispatcher) + YERIN/YUNA/HAERI/SOYU (agents)
- Each bot has unique token, only 1 polling process per token
- Group chat = `BOKONG SEMOK` (chat_id = -1003899936547)
- Topics: MONA=2475, YUNA=2476, SOYU=2477, YERIN=2478, HAERI=2479
- `BOT_APPS: dict[str, Application]` global registry populated in `run_all()`, used by MONA dispatch to post via agent bot instance (avoids is_bot filter on forwarded messages)

## Critical Fixes
1. **9Router IP**: `13.211.42.29` (Hye-Jin's AWS SG) is NOT this server. This server is `10.3.0.2`. Update `AI_ENDPOINT` accordingly.
2. **SSE parsing**: 9Router returns `text/event-stream`, not JSON. Need custom `_parse_sse()` parser that reads `data: {...}\n\ndata: [DONE]` lines.
3. **max_tokens**: 400 too low for mimo-v2.5-pro reasoning — use 800.
4. **Forwarding bug**: MONA's first attempt to "forward user msg" to agent topic got dropped by agent's `is_bot` filter. Fix: MONA calls AI in-process and posts reply via `BOT_APPS[agent].bot` (so sender = agent bot, not user).

## 5 Bot Tokens (in `~/.hermes/profiles/{mona-bot,yuna,soyu,yerin,haeri}/.env`)
- MONA: `8991657398:AAHp...euL0bk`
- YUNA: `8851569779:AAF6...OBO0to`
- SOYU: `8655750338:AAFK...Tx3KoE`
- YERIN: `8920788455:AAGm...mdBXxY`
- HAERI: `8752855971:AAHo...FNnjaU`

## Env vars needed in `~/.hermes/.env`
- `NINEROUTER_API_KEY` (64 char, from `~/.9router/auth/cli-secret`)
- `TELEGRAM_GROUP_ID=-1003899936547`

## Rollback
```bash
pm2 stop bot-router-new
pm2 restart mona-bot-gateway yuna-bot-gateway soyu-bot-gateway yerin-bot-gateway haeri-bot-gateway
```

## Status
- bot-router-new (id 7) — online, all 5 bots polling
- 5 Hermes gateways — stopped (id 1-5)
- AI working — test message "hashrate SOL?" → MiMo jawab: "Solana pakai PoS, bukan PoW"
