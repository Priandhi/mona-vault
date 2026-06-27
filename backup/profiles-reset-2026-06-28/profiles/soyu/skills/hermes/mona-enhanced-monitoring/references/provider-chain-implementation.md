# Provider Chain Implementation

## Circuit Breaker Pattern

```python
class ProviderChain:
    def __init__(self):
        self.providers = [
            {'name': 'alchemy', 'priority': 1, 'failures': 0, 'max_failures': 5, 'cooldown': 300, 'last_failure': 0},
            {'name': 'zerion',  'priority': 2, 'failures': 0, 'max_failures': 5, 'cooldown': 300, 'last_failure': 0},
            {'name': 'helius',  'priority': 3, 'failures': 0, 'max_failures': 5, 'cooldown': 300, 'last_failure': 0},
        ]
    
    def get_active_provider(self):
        now = time.time()
        for p in sorted(self.providers, key=lambda x: x['priority']):
            if p['failures'] >= p['max_failures']:
                if now - p['last_failure'] > p['cooldown']:
                    p['failures'] = 0  # Reset after cooldown
                else:
                    continue
            return p
        return None  # All providers down
    
    def record_failure(self, provider):
        provider['failures'] += 1
        provider['last_failure'] = time.time()
    
    def record_success(self, provider):
        provider['failures'] = 0  # Reset on success
```

## Helius Key Extraction

The Helius API key is stored inside `.meridian_env` as a key-value pair, not as a standalone file.

```python
def _load_helius_key(self):
    meridian_env = self._read_vault_key('.meridian_env')
    if meridian_env and 'HELIUS_API_KEY=*** in meridian_env:
        for line in meridian_env.splitlines():
            if line.startswith('HELIUS_API_KEY=***                return line.split('=', 1)[1].strip()
    return None
```

## Provider Rate Limits

| Provider | Rate Limit | Best For |
|----------|-----------|----------|
| Alchemy | 300M CU/month (~15s polling OK) | ETH, Base, Arbitrum |
| Zerion | 3 req/sec (persistent 429 possible) | Multi-chain wallet tracking |
| Helius | 10 req/sec | Solana + EVM |

## Pitfalls

1. **Zerion persistent 429** — Free tier has per-minute/hour limits, not per-second. Adding 8 wallets simultaneously causes 30+ minute rate limits.
2. **Alchemy free tier** — 300M CU/month, ~15s polling = ~170K CU/day. Block-aware polling (check blockNumber first, only fetch transfers on new block) saves ~90% of CU.
3. **Helius key format** — NOT a standalone file, must parse from `.meridian_env` key-value format.
