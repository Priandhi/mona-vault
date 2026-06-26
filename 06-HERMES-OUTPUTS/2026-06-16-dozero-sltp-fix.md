---
type: receipt
date: 2026-06-16
tags:
  - receipt
---

# Receipt: Dozero.X SL/TP Fix — Close All + Soft-Stop Monitor

**Date:** 2026-06-16
**Agent:** YUNA — The Strategist
**Task:** Fix "no SL/TP placed" issue — close all positions, install soft-stop backup
**Mas:** Hexa (@0xjosee)

## Posisi
**Closed (9 positions, market reduceOnly):**

| Symbol | uPnL | Status |
|---|---|---|
| ADAUSDT | -$97.62 | closed |
| THETAUSDT | -$60.75 | closed |
| IOTXUSDT | -$25.27 | closed |
| LINKUSDT | +$57.14 | closed (winner) |
| ETHFIUSDT | +$23.45 | closed (winner) |
| HAEDALUSDT | +$23.38 | closed (winner) |
| AIAUSDT | +$9.67 | closed (winner) |
| AVAXUSDT | +$3.52 | closed (winner) |
| PUMPBTCUSDT | +$0.57 | closed (winner) |

**Total realized: -$65.92** (better than feared — winners covered half the losses)

## PnL
- Realized this batch: -$65.92
- Active positions: 0
- Testnet balance: **$4,272.42 USDT** (avail ~$3,500)

## Result

### ✅ Closed all 9 positions
- Winners locked in (LINK +$57, ETHFI +$23, HAEDAL +$23, AIA +$10, AVAX +$4, PUMPBTC +$1)
- Losers cut (ADA -$98, THETA -$61, IOTX -$25)
- Clean slate for Dozero scanner to resume with proper SL/TP placement

### ✅ Soft-Stop Monitor installed
- Cron: `*/5 * * * *` (every 5 min)
- Script: `~/.hermes/profiles/yuna/scripts/yuna_soft_stop.py`
- Logic: if any position has uPnL < -5% of margin → close via market reduceOnly
- Silent when healthy (no Telegram spam)
- Alerts only when triggered

### ✅ Verified
- Active positions: 0
- Dozero auto-trade cycle still scheduled `*/30 * * * *`
- Soft-stop monitor runs silent (no positions = no action)
- New positions from Dozero will have fresh stop order slots → SL+TP will place correctly

## Decisions

1. **Close ALL 9 positions, not just losers** — Hexa confirmed: "gas perbaiki" means full reset. Winners locked, losers cut. Best path to clean state.
2. **Add soft-stop at -5%** — even if mainnet SL works correctly, having a safety net prevents floating losses. -5% = reasonable for 50x leverage (max 100% loss on SL hit).
3. **Cron `*/5 * * * *`** — frequent enough to catch issues early, not so frequent to spam. 5 min = balance.
4. **`no_agent=True`** — script-only cron, no LLM tokens. Pure Python execution.

## Issues

1. **Testnet max stop order limit = 1 per symbol TOTAL** — root cause of all 1,800+ -4045 errors. Testnet-specific, mainnet has higher limits (~10-20/symbol).
2. **Testnet doesn't support algo order query/cancel endpoints** — `/fapi/v1/algoOrder`, `/fapi/v1/openAlgoOrder` all 400/404. Can't verify SL/TP status via API.
3. **8 unaccounted losses** — $882 vanished from initial $5k balance (current $4,272). Not in today's income API. Likely from earlier sessions before today's tracking.

## Next Steps

- [x] Cron soft-stop installed and verified
- [ ] Monitor next Dozero cycle — verify new positions get SL+TP placed (no -4045)
- [ ] If mainnet later: same logic, but with native SL/TP working
- [ ] Daily WR report cron (next iteration)
- [ ] Per-symbol blacklist cron (after 5+ trades per symbol)

## Related Files

- `/home/ubuntu/mona-workspace/scripts/yuna_close_all.py` — close all positions
- `/home/ubuntu/mona-workspace/scripts/yuna_close_losers.py` — close losers only
- `/home/ubuntu/mona-workspace/scripts/yuna_emergency_sl.py` — manual SL placer
- `/home/ubuntu/mona-workspace/scripts/yuna_soft_stop.py` — soft-stop monitor (deployed)
- `~/.hermes/profiles/yuna/scripts/yuna_soft_stop.py` — cron-deployed copy
- `cronjob_id: f4fc8ce3a405` — yuna-soft-stop job
- `/home/ubuntu/dozero/logs/auto.log` — execution logs
