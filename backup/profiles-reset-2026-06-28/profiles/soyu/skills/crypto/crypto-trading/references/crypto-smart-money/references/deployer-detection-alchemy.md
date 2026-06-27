# Contract Deployer Detection via Alchemy

BaseScan API v1 is deprecated (returns "switch to Etherscan API V2"). Etherscan V2 free tier doesn't support Base chain. Use Alchemy binary search instead.

## Algorithm

1. Get latest block number: `eth_blockNumber`
2. Binary search for creation block:
   - `eth_getCode(contract, blockN)` returns empty `0x` before creation, bytecode after
   - Converges in ~20 iterations (46M blocks → 100-block range)
3. Linear scan within 100-block range to find exact creation block
4. Scan all transactions in creation block:
   - `eth_getBlockByNumber(block, true)` returns full tx objects
   - For each tx: `eth_getTransactionReceipt(txHash)`
   - Match `receipt.contractAddress` to target contract
   - `tx.from` = deployer address

## Rate Limiting (CRITICAL)

Alchemy free tier: 330 compute units/second. Binary search makes ~20+ API calls per contract.

**Must-do:**
- `time.sleep(0.2)` between every Alchemy call (200ms delay)
- Global rate limit: max 1 deployer lookup per 5 seconds
- Cache results for 1 hour (dict with TTL)
- Limit scan range to 200 blocks max
- Limit to 50 transactions per block
- On HTTP 429: back off 2 seconds, skip token

## Code Pattern

```python
def alchemy_call(payload, url, timeout=10):
    time.sleep(0.2)  # CRITICAL: rate limit
    r = urllib.request.Request(url, data=json.dumps(payload).encode(),
                               headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(r, timeout=timeout).read())

def get_contract_deployer(contract_address):
    # Check cache first
    cached = _cache_get(f'deployer_{contract_address}')
    if cached:
        return cached

    # Global rate limit
    if time.time() - _cache_get('_deployer_rate') < 5:
        return {'address': '', 'rate_limited': True}
    _cache_set('_deployer_rate', time.time())

    url = f'https://base-mainnet.g.alchemy.com/v2/{ALCHEMY_KEY}'

    # Binary search
    latest = int(alchemy_call({'method': 'eth_blockNumber', 'params': []}, url)['result'], 16)
    lo, hi = 0, latest
    while hi - lo > 100:
        mid = (lo + hi) // 2
        code = alchemy_call({'method': 'eth_getCode', 'params': [contract, hex(mid)]}, url)
        if len(code.get('result', '')) > 2:
            hi = mid
        else:
            lo = mid

    # Linear scan
    for block in range(lo, min(lo + 200, hi + 1)):
        if has_code(block):
            txs = alchemy_call({'method': 'eth_getBlockByNumber', 'params': [hex(block), True]}, url)
            for tx in txs[:50]:
                receipt = alchemy_call({'method': 'eth_getTransactionReceipt', 'params': [tx['hash']]}, url)
                if receipt.get('contractAddress', '').lower() == contract.lower():
                    return {'address': tx['from'], 'tx_hash': tx['hash']}
```

## Pitfalls

1. **Factory contracts** — Contract created by factory won't have `contractAddress` in receipt. Check receipt `logs` for contract address instead.
2. **Rate limits** — Without 200ms delay, Alchemy returns 429 after ~15 rapid calls.
3. **Cache is essential** — Deployer never changes. Cache forever (or 1 hour as safety).
4. **Block range** — Don't scan more than 200 blocks linearly. Binary search gets you within 100.
5. **Transaction limit** — Some blocks have 200+ transactions. Limit to 50 to avoid rate limits.
