# Standard Workspace Tree

Reference layout for a builder/operator running crypto-ops + automation + product builds on a single VPS. Adapt categories to the operator's actual surface area — empty folders are noise.

```
<workspace-root>/
├── README.md                # Map + quick commands (du, tar, tree)
├── .gitignore               # Blocks vault, .env, keys, mnemonics, node_modules
│
├── crypto-ops/              # On-chain operations
│   ├── wallets/             # HD wallet mgmt, multi-sig
│   ├── airdrops/            # Multi-wallet airdrop farming
│   ├── snipers/             # Token / NFT snipers
│   ├── arbitrage/           # Cross-DEX / CEX arb
│   ├── mev/                 # MEV searchers, bundles
│   └── multichain/          # Bridges, cross-chain ops
│
├── automation/              # General automation
│   ├── scrapers/            # Web scraping
│   ├── bots/                # Telegram / Discord / X bots
│   ├── schedulers/          # Cron-based jobs
│   └── webhooks/            # Webhook in/out
│
├── builds/                  # Production projects
│   ├── web/                 # Next.js / Vite / static
│   ├── api/                 # Backend APIs
│   ├── cli/                 # CLI tools
│   └── mobile/              # RN / Expo / Flutter
│
├── scripts/                 # One-off utilities
│
├── data/
│   ├── raw/                 # Raw inputs
│   ├── processed/           # Cleaned
│   ├── exports/             # Final outputs (shareable)
│   └── backups/             # Tarball backups
│
├── logs/                    # Runtime logs (rotate periodically)
├── docs/                    # Notes, runbooks
├── sandbox/                 # Throwaway experiments
│
└── vault/  🔒               # chmod 700, owner-only
    ├── .gitignore           # "*\n!.gitignore" — block everything
    ├── keys/                # Keystores (NOT raw mnemonics)
    ├── configs/             # Secret configs shared across projects
    └── secrets/             # API keys, tokens
```

## Per-Subdirectory Rationale

- **crypto-ops** is class-organized by *operation type*, not by chain. Chains cut across — a sniper might be EVM and Solana. Folder by what you're doing, not where.
- **automation** is for ongoing recurring jobs. One-shot scripts go in `scripts/`.
- **builds** is for things meant to ship. Internal tools live in `automation/`.
- **sandbox** exists to discourage spawning `~/test1`, `~/quick-thing` outside the workspace. Anything experimental lands here and gets pruned monthly.
- **vault** is the only folder where raw secret material lives. Project `.env` files stay in the project folder, gitignored.
- **data** is split raw/processed because raw is large + reproducible-from-source (don't back up), processed is the expensive output (do back up).

## Root README Template

The README at the workspace root should contain:
1. Operator name, host, public IP, creation date.
2. The folder tree above.
3. Security notes (vault hardening, never commit secrets, mnemonics offline).
4. Quick commands: `cd`, `tree -L 2`, `du -sh */`, the backup tar one-liner.

Keep it scannable. The README is for the operator's future self at 3am, not a tutorial.
