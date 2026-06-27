# Social Context Enrichment for Crypto Alerts

## Overview
When a whale buys a token, enrich the alert with:
1. **Deployer info** — Who created the contract (Twitter, Telegram, reputation)
2. **Buyer info** — Who's buying (Twitter, Telegram, followers)
3. **Project links** — Website, Twitter, Telegram, Discord from DexScreener

## Architecture
```
mona_social_context.py
├── get_contract_deployer(contract) → {address, tx_hash}
│   └── Uses Alchemy binary search (see deployer-detection-alchemy.md)
├── get_wallet_profile(address) → {twitter, telegram, discord, github, ...}
│   └── Uses DeBank API (see debank-social-profiles.md)
├── get_social_context(contract, buyer) → {deployer: {...}, buyer: {...}}
├── score_deployer_reputation(context) → 0-10
└── format_social_context(context) → formatted HTML string
```

## Integration Point
Add social context AFTER building trade data, BEFORE sending alert:

```python
# Get social context
social_ctx = None
try:
    social_ctx = get_social_context(token_addr, wallet_addr)
except Exception as e:
    log(f"Social context error: {e}")

# Build alert
msg = format_enhanced_buy_alert(w, trade_data, td, ...)

# Append social context
if social_ctx:
    social_text = format_social_context(social_ctx)
    if social_text:
        msg += f"\n\n{social_text}"

# Send
send_message(TOPIC_ALPHA, msg)
```

## Alert Output Example
```
🟢 SMART MONEY BUY — $KLEO (BASE)
━━━━━━━━━━━━━━━━━━━━━━🐋 Wallet GG1
📊 Win Rate: New
💰 Spent: 0.05 ETH ($150.50)
🪙 Got: 2B KLEO ($150.50)
💎 Price: $0.0000000750
🧢 MC: $150K | 💧 Liq: $25K
🟢 Security: 9/10 | 🟢 Risk: 2/5

📊 Chart · 🌐 Website · 🐦 Twitter · 📱 Telegram

👨‍💻 Deployer
   🐦 Twitter: @blackchip
      👤 無為 free lunch capital
      👥 6,900 followers
   📱 Telegram: @blackchip_tg
      👤 BlackChip Official
   🐙 GitHub: @blackchip-dev
   📝 ex Shopify GTM/BD, crypto degen
   🟡 Reputation: medium
   📄 0x4ed0...caab

👤 Buyer Context
   🐦 Twitter: @WalletGG1
      👤 DeFi Degen
      👥 850 followers
   📱 Telegram: @walletgg1_tg
      👤 GG1 Trading
   📝 Active trader on Base
```

## Performance Considerations
- Deployer lookup: ~10-15s (binary search + receipt scan)
- DeBank profile: ~1-2s per wallet
- Total enrichment: ~15-20s per alert
- Cache deployer results for 1 hour (deployer never changes)
- Cache wallet profiles for 1 hour
- Rate limit: 200ms between API calls

## Pitfalls
1. **Deployer lookup is slow** — Don't block the main loop. Consider running enrichment in background and sending alert with basic info first, then updating with social context.
2. **DeBank may return empty** — Many wallets have no social accounts linked. Handle gracefully — skip sections with no data.
3. **Rate limiting** — Binary search uses ~20-30 API calls. Add delays, cache aggressively.
4. **Message length** — Social context adds ~500-1000 chars. Watch the 4096 Telegram limit.
5. **Platform separation** — NEVER mix Twitter handles with Telegram links. Each platform has its own emoji and URL pattern.
