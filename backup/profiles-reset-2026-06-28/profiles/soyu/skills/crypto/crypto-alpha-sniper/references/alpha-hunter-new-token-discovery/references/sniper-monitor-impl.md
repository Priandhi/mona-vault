# PumpFun Sniper Monitor — Implementation Reference

## Script: `~/.hermes/scripts/pumpfun_sniper.py`

Fast-polling daemon (every 2 min) that catches new tokens at birth, before CT shares them.
No AI overhead — pure Python script, `no_agent=True` cron, stdout = Telegram message.

## Architecture

```
PumpFun API (newest + KOTH)          GeckoTerminal (new_pools)
        ↓                                      ↓
        └──────── Merge + Dedup ───────────────┘
                      ↓
              Quality Filter
         (MCap $10K-$5M, vol>$500, min 3 buys)
                      ↓
              DexScreener Enrichment
           (socials if PumpFun had none)
                      ↓
              Sort (PumpFun first, then vol)
                      ↓
              Format → stdout (Telegram)
              Debug → stderr (not delivered)
```

## Cronjob Config

- Schedule: `every 2m`
- `no_agent: true` — script-only, no LLM tokens consumed
- Deliver: `telegram:-1003899936547:13` (Alpha topic)
- Script: `pumpfun_sniper.py`

## Key Design Decisions

1. **Max 3 per alert** — anti-spam, user explicitly said "jangan terlalu spam"
2. **Two seen files** — `.sniper_seen.json` (sniper) separate from `.alpha_seen.json` (deep hunter)
3. **PumpFun first in sort** — earliest signal, before GeckoTerminal
4. **DexScreener enrichment** — only when PumpFun has no socials, with 0.5s delay between calls
5. **Empty stdout = silent** — no "no tokens found" messages

## Two-Layer System

| Layer | Interval | Method | Purpose |
|---|---|---|---|
| 🎯 Sniper | 2 min | Script (no AI) | Catch tokens at birth |
| 🔥 Alpha Hunter | 20 min | AI-driven | Deep research + social signals |

The sniper catches what APIs show fast. The Alpha Hunter catches what needs social signal analysis (CT mentions, KOL activity, web search).
