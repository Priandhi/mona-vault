# Telegram Command Center Architecture

## Concept
Topics are **interactive command rooms**, NOT one-way alert feeds.
User commands → Mona executes → Mona reports results.

## Topic Spec (Mona Ai Group Example)

### 💸 Wallet — On-demand only
- NO auto-refresh
- User says "cek wallet 3" → Mona checks and reports
- User says "cek semua" → Mona checks all wallets

### 💎 Alpha — Active multi-chain research + analysis
- Mona actively hunts new projects across ALL chains (ETH, Base, Solana, Sui, TON, Aptos)
- Covers: tokens, NFTs, DeFi, mining, DePIN, new protocols
- Must include: social links (Twitter, Discord, Website, Telegram, docs)
- Focus on NEW projects with potential, not already-hyped ones
- ALSO analyzes info user sends (links, screenshots, tips)
- Two-way: Mona researches + User sends leads

### ⭐️ NFT — Execute on command
- User says "mint project X with wallet 5" → Mona executes TX → reports hash + status
- User picks which wallet to use
- NOT just alerts — Mona actually mints

### 📣 Airdrop — Self-grinding agent
- Mona FINDS fresh airdrops (from Telegram groups like Airdrop Finder, Twitter, Discord)
- Mona EXECUTES social tasks (follow, retweet, join, claim)
- When Mona needs materials → asks user (email accounts, social logins, wallet signatures)
- User provides → Mona continues grinding
- NEVER report old/expired airdrops (PENGU, BONK etc are dead)
- Only fresh, active, worth-grinding airdrops
- Designated "airdrop wallet" for all airdrop activities

### ⛏️ Live Mining — On-demand monitoring
- User says "garap project X" → Mona starts monitoring
- Mining progress, earnings, status updates
- NOT auto-start — waits for user command
- Examples: cloud mining, DePIN, web-based mining (e.g., Hash on Base)

### 📊 Cron Status — Best practice
- Mona manages optimal scheduling

### 📝 Laporan Garapan — Progress reports
- Results from all Mona's self-initiated work
- Airdrop grinding progress, mining earnings, alpha research summaries
- Auto-updates when there's meaningful progress

### 📚 Logs — Every 3 hours
- System health, errors, activity

## Key Principles
1. **Execute, don't just observe** — Mona is an agent, not a dashboard
2. **Ask for materials** — When grinding needs accounts/logins, ask user
3. **Fresh content only** — No expired airdrops, no dead projects
4. **Multi-chain** — Don't limit to one chain
5. **Social links mandatory** — Every alpha signal must have project links
6. **User picks wallet for TX** — Never auto-select wallet for transactions
