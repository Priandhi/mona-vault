# Social Context Enrichment — Deployer + Buyer Intelligence

**Script:** `~/.hermes/scripts/mona_social_context.py`
**Used by:** `mona_smart_money_watcher.py` (smart money alerts)

## Purpose

When a whale buys a token, enrich the alert with:
1. **Deployer info** — who created the contract (Twitter, Telegram, Discord, GitHub, bio, reputation)
2. **Buyer info** — whale's social profiles
3. **Project links** — website, Twitter, Telegram, Discord from DexScreener

## Deployer Detection (Alchemy Binary Search)

BaseScan API v1 deprecated. Etherscan V2 free tier doesn't support Base chain. Use Alchemy:

```python
def get_contract_deployer(contract_address):
    # Binary search for creation block
    lo, hi = 0, latest_block
    while hi - lo > 100:
        mid = (lo + hi) // 2
        if contract_exists_at(mid):
            hi = mid
        else:
            lo = mid
    
    # Scan transactions in creation block (max 50)
    for tx in block_transactions[:50]:
        receipt = get_receipt(tx['hash'])
        if receipt['contractAddress'] == target_contract:
            return tx['from']  # deployer address
        
        # Also check logs (for factory-created contracts)
        for log in receipt['logs']:
            if log['address'].lower() == target_contract.lower():
                return tx['from']
    
    return None
```

**Rate limiting (CRITICAL):**
- Max 1 deployer lookup per 5 seconds
- Cache results 1 hour
- Max 200 blocks to scan
- Max 50 transactions per block
- On HTTP 429: back off 2 seconds, skip token

## Wallet Profile Lookup (DeBank)

DeBank API returns `social_accounts` with separate platform objects:

```python
def get_wallet_profile(address):
    url = f'https://api.debank.com/user/address/{address}'
    data = call_api(url)
    
    if data and data.get('data'):
        accounts = data['data'].get('social_accounts', {})
        
        # Twitter
        twitter = accounts.get('twitter', {})
        profile['twitter'] = twitter.get('screen_name', '')
        profile['twitter_followers'] = twitter.get('followers_count', 0)
        
        # Telegram
        telegram = accounts.get('telegram', {})
        profile['telegram'] = telegram.get('username', '')
        
        # Discord
        discord = accounts.get('discord', {})
        profile['discord'] = discord.get('username', '')
        
        # GitHub
        github = accounts.get('github', {})
        profile['github'] = github.get('username', '')
```

**PITFALL:** DeBank API may return 404 for some addresses. Always handle gracefully.

## Platform Separation (CRITICAL)

NEVER mix platforms in alerts. Always label clearly:

```
🐦 Twitter: @handle → link to twitter.com/handle
📱 Telegram: @username → link to t.me/username
💬 Discord: username#1234
🐙 GitHub: @username → link to github.com/username
```

**PITFALL:** User complained about Telegram handle being attributed as Twitter. Always check which platform the data came from and label accordingly.

## Reputation Scoring (0-10)

```python
def score_deployer_reputation(deployer):
    score = 5  # neutral baseline
    
    # Twitter followers
    followers = deployer.get('twitter_followers', 0)
    if followers > 50000: score += 3
    elif followers > 10000: score += 2
    elif followers > 1000: score += 1
    
    # Has Twitter linked
    if deployer.get('twitter'): score += 1
    else: score -= 1
    
    # Bio keywords
    bio = deployer.get('bio', '').lower()
    tech_keywords = ['founder', 'ceo', 'cto', 'engineer', 'developer', 'investor']
    for kw in tech_keywords:
        if kw in bio: score += 0.5; break
    
    scam_keywords = ['airdrop', 'free', 'giveaway', 'pump', 'moon', '100x']
    for kw in scam_keywords:
        if kw in bio: score -= 2; break
    
    return max(0, min(10, round(score)))
```

## Project Links (DexScreener)

Extract from DexScreener `info` field:

```python
info = dex_data.get('info', {})

# Websites
websites = info.get('websites', [])
if websites:
    result['website'] = websites[0].get('url')

# Socials
socials = info.get('socials', [])
for s in socials:
    s_type = s.get('type', '').lower()
    if s_type == 'twitter': result['twitter'] = s.get('url')
    elif s_type == 'telegram': result['telegram'] = s.get('url')
    elif s_type == 'discord': result['discord'] = s.get('url')
```

**NEVER hardcode DEX swap URLs** (e.g., `aerodrome.finance/swap`). Use project links from DexScreener. If no project links, fall back to DexScreener chart URL only.

## Alert Format

```html
🟢 <b>SMART MONEY BUY</b> — $SYMBOL (BASE)
━━━━━━━━━━━━━━━━━━━━━━

🐋 <b>Whale Name</b>
👤 <code>0x1234...5678</code>
📊 Win Rate: 85% (17/20)

💰 <b>Spent:</b> 0.05 ETH ($150)
🪙 <b>Got:</b> 2B SYMBOL ($150)

💎 <b>Price:</b> $0.0000000750
🧢 <b>MC:</b> $150K
💧 <b>Liquidity:</b> $25K

🟢 <b>Security: 9/10</b>
🟢 <b>Risk: 2/5</b>

📊 <a href="...">Chart</a> · 🌐 <a href="...">Website</a> · 🐦 <a href="...">Twitter</a>

👨‍💻 <b>Deployer</b>
   🐦 Twitter: <a href="...">@handle</a>
      👤 Name
      👥 6,900 followers
   📱 Telegram: <a href="...">@username</a>
   🟡 Reputation: medium (7/10)
   📄 <code>0x4ed0...caab</code>

👤 <b>Buyer Context</b>
   🐦 Twitter: <a href="...">@whale_handle</a>
      👤 Name
      👥 850 followers
```
