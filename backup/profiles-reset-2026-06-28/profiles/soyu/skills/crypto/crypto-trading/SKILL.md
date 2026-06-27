---
name: "crypto-trading"
description: "Active crypto trading: Binance USDT-M futures, Meteora DLMM LP, general crypto futures engine, smart money / whale tracking. Use when trading, managing LP positions, following whale wallets, or orchestrating a futures strategy."
tags:
  - "crypto"
  - "trading"
  - "futures"
  - "binance"
  - "dlmm"
  - "meteora"
  - "lp"
  - "whale"
  - "smart-money"
---
# Crypto Trading & LP

> Spot, futures, derivatives, LP, and on-chain smart-money tracking. The class of "actively trade crypto capital" workflows.

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "binance futures", "usd-m", "leverage", "position" | `references/binance-futures-trading/` |
| "meridian", "DLMM", "Meteora", "LP" | `references/meridian-dlmm-agent/` |
| "futures engine", "trading bot", "automated strategy" | `references/crypto-futures-engine/` |
| "smart money", "whale tracking", "wallet following" | `references/crypto-smart-money/` |

## Topic Pages

- `references/binance-futures-trading/SKILL.md` — Binance USDT-M futures: order placement, positions, leverage
- `references/meridian-dlmm-agent/SKILL.md` — Meridian / Meteora DLMM: LP operations, position management
- `references/crypto-futures-engine/SKILL.md` — General crypto futures engine (strategy orchestration, backtest, live)
- `references/crypto-smart-money/SKILL.md` — Smart money / whale wallet tracking (EVM chains)

## Common PITFALLS

1. **Always use a testnet or paper-trading first** when wiring a new strategy. The user has lost money on bad config.
2. **Never store API keys in plaintext.** Use base64 encoding + restricted permissions, or a secret manager.
3. **Slippage is real** — for sniping or LP, the on-chain price has moved by the time the tx confirms. Use `minOut` parameters.
4. **Whale data is noisy.** Smart-money signals are most useful as confirmation, not as the entry trigger.

## Related

- `crypto-alpha-sniper` (sibling) — for the sniping/alpha class
- `crypto-alerting` (sibling) — for telegram alerts
- `hermes-crypto-agent` (in hermes/) — class-level crypto operations toolkit
