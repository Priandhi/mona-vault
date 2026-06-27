# Smart Money Watcher — Pitfalls & Fixes (June 2026)

## DexScreener Project Links
DexScreener API returns `info` object with `websites[]` and `socials[]` arrays:
```python
info = d.get("info", {})
websites = info.get("websites", [])
socials = info.get("socials", [])
# socials items have {"type": "twitter|telegram|discord", "url": "..."}
```
Include in alerts: 🌐 Website, 🐦 Twitter, 📱 Telegram, 💬 Discord.

## Deployer Detection via Alchemy Binary Search
BaseScan API v1 deprecated, Etherscan V2 free tier doesn't support Base, Blockscout doesn't expose deployer. Use Alchemy binary search:
1. `eth_blockNumber` → latest block
2. Binary search with `eth_getCode(contract, blockN)` for creation block
3. Linear scan block range for exact block
4. For each tx in block, `eth_getTransactionReceipt` → check `contractAddress` or logs

## DeBank API Status (June 2026)
Public endpoints all return 404. Wallet social profile lookup currently broken. Workaround: use Alchemy for deployer address, then manual Twitter lookup if needed.

## Liquidity Filter
```python
MIN_LIQUIDITY = 1_000  # $1K minimum
liq = td.get("liquidity_usd", 0) or 0
if liq < MIN_LIQUIDITY: continue
```

## Telegram Forum Topic
Bot must be admin with "Manage Topics" permission. Without this, `createForumTopic` returns "not enough rights".

## API Key Loading Pattern
```python
# CORRECT
if line.startswith('API_KEY='):
    api_key = line.split('=', 1)[1].strip()

# WRONG — causes SyntaxError
if line.startswith('API_KEY=***            api_key = line.split('=', 1)[1].strip()
```
