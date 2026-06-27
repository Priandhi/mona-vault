# Deployer Detection via Alchemy Binary Search

## Problem
BaseScan API v1 deprecated. Etherscan V2 free tier doesn't support Base chain. Blockscout doesn't expose `contractCreator`. Need alternative to find who deployed a contract.

## Solution: Binary Search + Receipt Scan

```python
def get_contract_deployer(contract_address, alchemy_key):
    url = f'https://base-mainnet.g.alchemy.com/v2/{alchemy_key}'
    
    # 1. Get latest block
    p = {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_blockNumber', 'params': []}
    latest = int(alchemy_request(url, p)['result'], 16)
    
    # 2. Binary search for creation block
    def check_code(block):
        p2 = {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getCode',
              'params': [contract_address, hex(block)]}
        return len(alchemy_request(url, p2).get('result', '')) > 2
    
    lo, hi = 0, latest
    while hi - lo > 100:
        mid = (lo + hi) // 2
        if check_code(mid): hi = mid
        else: lo = mid
    
    # 3. Linear scan to exact block
    for block in range(lo, hi + 1):
        if check_code(block):
            # 4. Scan txs in block
            p3 = {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getBlockByNumber',
                  'params': [hex(block), True]}
            txs = alchemy_request(url, p3)['result']['transactions']
            
            for tx in txs:
                p4 = {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getTransactionReceipt',
                      'params': [tx['hash']]}
                receipt = alchemy_request(url, p4).get('result', {})
                
                # Check direct contract creation
                if receipt.get('contractAddress', '').lower() == contract_address.lower():
                    return tx['from']
                
                # Check logs for factory-created contracts
                for log in receipt.get('logs', []):
                    if log['address'].lower() == contract_address.lower():
                        return tx['from']
            break
    return None
```

## Performance
- Binary search: ~14-17 iterations (46M blocks → 100-block range)
- Each iteration: 1 RPC call (`eth_getCode`)
- Linear scan: up to 100 blocks, but usually finds in first few
- Total: ~20-30 RPC calls, ~10-15 seconds

## Pitfalls
- Factory-created contracts (CREATE2) may not show up in `contractAddress` field — check logs instead
- Some contracts are created via proxies — the `from` address may be another contract, not an EOA
- Alchemy free tier: 300M compute units/month. This search uses ~30 CU per contract, so ~10K searches/month
- Cache results aggressively — deployer never changes
