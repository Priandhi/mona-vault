# Kanban Agent Roles — Skill Stack Reference

> Quick reference for which skills each agent invokes. Load this when routing a task to the right kanban board. Last updated: 2026-06-14.

## YUNA — The Strategist (Trading & LP)

**Domain:** Spot/futures trading, LP management, OOR (out-of-range) alerts, PnL tracking.

**Primary skills:**
- `meridian-dlmm-agent` — Meteora DLMM LP agent on Solana. Telegram integration, screening, OOR monitoring.
- `binance-futures-trading` — Binance USDT-M futures, order placement, algo orders, position management.
- `crypto-futures-engine` — Generic crypto futures engine (Bybit, OKX, Binance).

**Decision keywords:** trading, LP, futures, PnL, OOR, Meridian, range, Meteora, position, SL, TP, leverage, margin.

**Wallet to use:** Main Solana wallet for Meridian LP; Binance spot/futures wallet for Binance ops.

---

## SOYU — The Phantom (Sniper & Alpha)

**Domain:** New token sniping, alpha signal generation, fast entry/exit, memecoin hunting.

**Primary skills:**
- `charon-sniper-bot` — Solana sniper via Charon API signals + Jupiter DEX.
- `solana-sniper-bot` — Generic Solana sniper (Jupiter, Raydium, pump.fun).
- `alpha-hunter-new-token-discovery` — GeckoTerminal + PumpFun API scanner.
- `crypto-signal-scanner` — Dual-mode futures signal scanner (momentum + reversal SMC).
- `crypto-data-scrapers` — DEXScreener, DeFiLlama, CoinGlass for market intel.

**Decision keywords:** snipe, alpha, launch, signal, pump, new token, rug, honeypot, bonding curve, pump.fun, Raydium, Jupiter.

**Wallet to use:** Dedicated sniper wallet (sub-wallet, NOT main `9XJU`). Per safety rule: never use main wallet for sniping.

---

## YERIN — The Grinder (Mining)

**Domain:** VPS mining, hashrate monitoring, payout tracking, rig uptime.

**Primary skills:**
- `vps-mining-setup` — RandomX/Juno Cash CPU mining on VPS.
- `gpu-cloud-mining` — GPU mining on Modal/RunPod/Vast.ai serverless.
- `pm2-process-health` — Mining process monitoring, auto-heal.

**Decision keywords:** mining, hashrate, rig, payout, RandomX, Juno, XMR, pool, worker, miner, GPU, CUDA.

**Infrastructure:** Mining runs on VPS via PM2 (process name pattern: `*-miner`). Check `/tmp/mining-*.log` for hashrate.

---

## HAERI — The Collector (Airdrop & NFT)

**Domain:** Airdrop farming, eligibility checking, NFT mint tracking, multi-wallet claim scheduling.

**Primary skills:**
- `galxe-reverse-engineering` — Galxe quest/airdrop platform API.
- `hermes-crypto-agent` — General crypto ops (multi-wallet, multi-chain).
- `crypto-smart-money` — Wallet tracking, useful for eligibility inference.

**Decision keywords:** airdrop, claim, NFT, mint, eligibility, Galxe, quest, snapshot, season, multi-wallet, distribute.

**Wallet to use:** Multi-wallet arrays (sub-wallets). Each airdrop campaign gets its own wallet to avoid sybil detection.

---

## MONA — The Architect (Self / Coordinator)

**Domain:** Cross-cutting work, setup, infra, integration tasks that don't fit other agents.

**Primary skills:**
- `mona-command-center` — Telegram command center.
- `mona-knowledge-vault` — This vault system.
- `operator-workspace-bootstrap` — VPS folder structure.
- `pm2-process-health` — Service health.
- `self-healing-services` — systemd hardening.
- `vps-agent-watchdog` — Self-heal cron for agent services.

**Decision keywords:** setup, bikin, configure, audit, integrate, fix, debug, infra, server, VPS, deploy, monitoring.

**Default for ambiguous tasks.** When in doubt → MONA.

---

## Routing Cheat Sheet

| User says | Agent |
|-----------|-------|
| "trading" / "LP" / "OOR" / "PnL" / "Meridian" | YUNA |
| "snipe" / "alpha" / "launch" / "signal" / "pump" | SOYU |
| "mining" / "hashrate" / "rig" / "payout" / "RandomX" | YERIN |
| "airdrop" / "claim" / "NFT" / "mint" / "eligibility" | HAERI |
| "setup" / "fix" / "audit" / "deploy" (no domain) | MONA |
| "telegram" / "command center" / "bot" | MONA |
| "watchdog" / "self-heal" / "auto-restart" | MONA |
| "wallet" / "keypair" / "import" (setup) | MONA |
| "swap" / "bridge" / "transfer" (execution) | YUNA (if trading-related) or HAERI (if airdrop-related) or MONA |
