# Bot Trading Architecture — Separation Pattern

## Key Lesson
User corrected: "bukan nya sistem nya beda ya kok di gabung jadi satu?"

Charon Sniper and Meridian DLMM are SEPARATE systems:
- **Charon Sniper:** Buy/sell tokens (sniper strategy)
- **Meridian DLMM:** Liquidity provider (LP strategy)

They share Charon API as signal source but execution/management/dashboards are completely different.

## Build Order for Trading Bots

1. Backend modules (fetcher, filter, executor, manager)
2. Config file (single source of truth for all settings)
3. Main loop (integrates modules)
4. Dashboard (monitoring web UI)
5. Telegram notifications
6. PM2 deployment
7. localhost.run tunnel (NEVER pipe through `head -20` — truncates URL)

## DRY RUN First Pattern

Always start with DRY RUN:
- Simulate trades based on real data
- Track PnL even in simulation
- Collect data for several hours before going LIVE
- User preference: "pelan pelan aja ya biar bisa mikir dengan cerdas"

## Dashboard Port Allocation

| Bot | Port |
|---|---|
| Charon Sniper | 3456 |
| Meridian DLMM | 3457 |
| Charon Sniper (new) | 3458 |

Avoid conflicts by checking `lsof -i :PORT` before binding.
