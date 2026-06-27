---
name: "crypto-alpha-sniper"
description: "Token discovery, alpha signals, sniping bots, and the data scrapers that feed them. Covers EVM and Solana (Charon, pump.fun, Raydium, DexScreener, GoPlus). Use when sniping, hunting new tokens, generating entry signals, or scraping on-chain market data."
tags:
  - "crypto"
  - "sniper"
  - "alpha"
  - "signal"
  - "pump-fun"
  - "raydium"
  - "dexscreener"
  - "charon"
  - "solana"
  - "evm"
---
# Crypto Sniper & Alpha

> Token discovery, alpha signals, sniping, and the data pipelines that feed them. The class of "find the next 10x before the market does" workflows.

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "charon", "charon sniper", "EVM sniping" | `references/charon-sniper-bot/` |
| "solana sniper", "pump.fun", "raydium" | `references/solana-sniper-bot/` |
| "alpha hunter", "new token discovery", "DexScreener" | `references/alpha-hunter-new-token-discovery/` |
| "signal scanner", "momentum", "entry signal" | `references/crypto-signal-scanner/` |
| "data scraper", "DexScreener", "GoPlus", "token data" | `references/crypto-data-scrapers/` |

## Topic Pages

- `references/charon-sniper-bot/SKILL.md` — Charon: Solana/EVM sniper bot
- `references/solana-sniper-bot/SKILL.md` — Solana-only sniper (pump.fun, Raydium)
- `references/alpha-hunter-new-token-discovery/SKILL.md` — Discover newly launched tokens across EVM and Solana
- `references/crypto-signal-scanner/SKILL.md` — Dual-mode crypto futures signal scanner
- `references/crypto-data-scrapers/SKILL.md` — Scrape crypto market data from free APIs (DexScreener, GoPlus, etc.)

## Common PITFALLS

1. **Honeypot detection is mandatory** before any snipe. Use GoPlus (`gopluslabs.io`) for buy/sell tax and can_sell check.
2. **First 5 minutes are gas-war territory.** High gas or sandwich-bot losses. Wait for liquidity to settle.
3. **Pump.fun is Solana-only.** Don't try to use it for EVM.
4. **PITFALL: DexScreener boosts/profiles may return 0** at certain times. Always combine with the direct launchpad API (Clanker for Base).
5. **Quality > quantity.** Don't spam tokens — filter for liquidity, volume, and age. User explicitly rejected alert spam.

## Related

- `crypto-trading` (sibling) — for the post-snipe holding and exit
- `crypto-alerting` (sibling) — for telegram alerts on signal hits
- `mona-command-center` (in hermes/) — Telegram bot that surfaces these signals
