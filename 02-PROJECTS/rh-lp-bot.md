# RH LP Farming Bot

## Overview
Telegram bot untuk LP (Liquidity Provider) farming di Robinhood Chain (chainId 4663).

## Key Info
- **Bot:** @DinoLpFarmBot (ID: 8948042379)
- **PM2:** lp-bot-ui
- **Code:** /home/ubuntu/rh-lp-bot/
- **Chain:** Robinhood Chain
- **RPC:** https://rpc.mainnet.chain.robinhood.com
- **Wallet:** 0x1431ac91... (config.yaml)

## Features
1. **Token Analysis** — kirim 0x address → auto analisis (DexScreener-style)
   - Price, MC, FDV, Liquidity, 24H Volume, APR
   - Honeypot check, buy/sell tax, mintable, blacklist
   - Pool not found handling
2. **Auto LP** — auto-detect pool + strategy + amount selection
3. **Manual LP** — Add LP dengan custom settings
4. **Positions** — list, close, claim fees, PnL card
5. **PnL Card** — anime bg + row-based layout + neon pink→purple gradient
6. **Strategy** — range %, one-side, TP/SL, slippage, pool version, fee tier, gas
7. **Auto** — rebalance, compound, reinvest

## Architecture
```
rh-lp-bot/
├── bot/
│   ├── handlers.py      # Callback + message dispatch
│   ├── keyboards.py     # All inline keyboards
│   └── messages.py      # Text formatters
├── card/
│   ├── pnl_card.py      # PnL card generator (v5)
│   └── assets/anime_bg.jpg
├── core/
│   ├── token_analyzer.py  # DexScreener-style analysis
│   ├── lp_manager.py      # LP add/remove/claim
│   ├── position.py        # Position tracker
│   ├── rebalance.py       # Auto-rebalancer
│   ├── security.py        # Honeypot check
│   ├── strategy.py        # TP/SL/exit logic
│   └── gas.py             # Gas management
├── contracts.py          # RH Chain contract registry
├── config.py             # Config loader
├── config.yaml           # Bot config
├── uniswap_v2.py         # V2 LP (unused, no factory on RH)
├── uniswap_v3.py         # V3 LP manager
└── uniswap_v4.py         # V4 LP manager
```

## Contract Addresses (Robinhood Chain)
- **V2 Factory:** 0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f (NO CODE)
- **V3 Factory:** 0x1f7d7550B1b028f7571E69A784071F0205FD2EfA
- **V3 NFPM:** 0x73991a25C818Bf1f1128dEAaB1492D45638DE0D3
- **WETH:** 0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73
- **USDG:** 0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168

## Last Updated
2026-07-16 — Full overhaul (commit d120a55)