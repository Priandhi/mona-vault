# Alpha Alert Template Design

## User's Reference Example (from another bot)

User showed this as the baseline they liked:

```
🟢 BUY $PEAK (BASE)
👤 0xb511417caf48ac96f53841360e68cdc2fdebdbb8
💰 1.0000 ETH ($1.31K) → 2.02M $PEAK (0.202%)

🚀 Launchpad: Virtuals Protocol
📊 MC · $649.2K | VOL · $71.75K | 581tx/1h | 24h +70.7%
⏰AGE : 1d

CA: 0x296eB9c4D8fCbd00fBc6D5027e4202BF955fA76f
👨🏻‍💻 Dev: 0x384d…78b3 · DeBank

🔗 X · Chart
```

## Iteration Rounds

1. User rejected first draft as "too long" — had whale info, entry/TP/SL, safety details
2. User said "no whale, no entry TP SL, just the important stuff"
3. User wanted launchpad info added
4. User wanted dev social profile links (full URLs, not just handles)
5. User wanted fee recipient with social links for bankr.bot deployments
6. Final format: clean, minimal, emoji-forward, all links clickable

## Final Format (with clickable HTML links)

All links are Telegram HTML `<a href>` rendered via `parse_mode="HTML"`.
CA links to BaseScan, Dev links to DeBank, Twitter shows handle.

```
💎 $PEAK · BASE

🚀 Virtuals Protocol
📊 MC $649K · VOL $72K · 581tx/1h
📈 24h +70.7% · ⏳ 1d
🛡️ ✅ Safe · ✅ Verified · 0% Tax

📄 CA: 0x296e…A76f ← clickable to BaseScan
👨‍💻 Dev: 0x384d…78b3 ← clickable to DeBank
   🐦 devhandle ← clickable to Twitter
   🌐 debank.com/profile/0x... ← clickable to DeBank
📊 Chart · 🐦 X · 🔍 Scan ← all clickable
```

## Design Decisions

- **Token + Chain** on first line with 💎 emoji
- **Launchpad** as first body line with 🚀 — user considers this important context
- **Metrics** grouped on one line: MC · VOL · tx/1h
- **Price change + age** on same line with 📈 and ⏳
- **Safety** on one line with 🛡️ — verified, honeypot, tax %
- **CA** with truncated address (first 6 + last 4), **clickable to BaseScan/Etherscan**
- **Dev** with DeBank link (**clickable**), social links indented below (**all clickable**)
- **Fee** only for bankr.bot, with same social treatment as dev
- **Links** at bottom: Chart + X (Twitter) + Scan — **all clickable HTML links**
- **No bot signature** — clean ending
- **Strip `https://`** from display text for cleaner look
- **Explorer URL** based on chain: `basescan.org` for Base, `etherscan.io` for ETH

## Anti-patterns (user rejected these)

- ❌ Whale info (wallets, amounts, win rates)
- ❌ Entry zone / SL / TP suggestions
- ❌ Confluence signals (multi-whale alerts)
- ❌ Risk/Reward ratios
- ❌ Social buzz metrics (Twitter mentions)
- ❌ Long safety breakdowns (honeypot details, contract analysis)
- ❌ Bot signature at end
- ❌ Just handles without links (user: "jangan cuma username tapi lengkap link nya")
- ❌ Plain text links (non-clickable) — ALL links must be HTML `<a href>`
- ❌ Full URLs in display text — strip `https://`, show handle only for Twitter
- ❌ Custom emoji complexity — dropped in favor of simple HTML links
