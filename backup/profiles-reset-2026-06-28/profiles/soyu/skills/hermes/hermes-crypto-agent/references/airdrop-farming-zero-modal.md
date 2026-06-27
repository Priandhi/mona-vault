# Zero-Capital Airdrop Farming

Strategy for farming airdrops with $0 modal. All activities use free faucets, social tasks, or testnet tokens.

## Tier 1: Galxe Social Tasks (Highest Priority)
- Social tasks: follow Twitter, join Discord/Telegram, retweet, like, quiz
- On-chain tasks: swap, bridge, stake (need gas — use faucet)
- Modal: $0-5 (gas for on-chain tasks)
- Reward: points → convert to token
- 12 wallets × N campaigns
- **Requirement:** 12 email + 12 Discord + 12 Twitter accounts
- User will provide emails manually. Discord accounts: automated via `discord_creator.py` (needs hCaptcha solving via yescaptcha API)

## Tier 2: DePIN / Node
- **Grass** — share bandwidth for points
  - **LIMITATION (June 2026):** Grass now requires desktop app (not headless node). Can't multi-instance on VPS. One VPS = one Grass account. Run via VNC.
  - Desktop app download: https://grass.io/download (Linux .AppImage)
  - Run through VNC: `DISPLAY=:99 ./grass.AppImage`
  - Account required: sign up at https://app.grass.io
- **Nodepay** — similar to Grass but user said "skip nodepay itu depin lama"
- Modal: $0

## Tier 3: Testnet Farming
- Claim faucet tokens (free)
- Interact with testnet dApps (swap, bridge, stake)
- Deploy contracts
- Modal: $0
- Reward: token when mainnet launches ($100-5000+ potential)
- **PITFALL:** User explicitly said old testnets (Monad, Berachain, MegaETH, Eclipse) are "udah gak worth it semua". Always check for NEW testnets before recommending. Source: airdrops.io, but blocked on VPS (Cloudflare). User needs to check from their device.

## Tier 4: NFT Mint Farming
- Free/cheap mint NFTs
- Some collections airdrop to holders
- Modal: $0-5

## Account Requirements (per wallet)
- 1 email address
- 1 Discord account
- 1 Twitter account (currently blocked for user — @ppriandi locked)
- 1 Telegram (user has)

## Scripts
- `~/.hermes/scripts/discord_creator.py` — Discord account creator (hCaptcha via yescaptcha)
- `~/.hermes/scripts/galxe_claimer.py` — Galxe quest automation (half-built)
- `~/.hermes/scripts/mona_cli_wallet.py` — CLI wallet for on-chain tasks

## Filtering Strategy
- Skip airdrops requiring Twitter (user's account locked)
- Focus on email/Discord/Telegram/On-chain tasks
- Prioritize tasks with confirmed token reward
- Multi-wallet: run same task on all 12 wallets with jitter
