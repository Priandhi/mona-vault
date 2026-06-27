# GoPlus Security API Reference

## Endpoint
```
GET https://api.gopluslabs.io/api/v1/token_security/{chain_id}
```

## Chain IDs
- 1 = Ethereum
- 56 = BSC
- 8453 = Base
- 42161 = Arbitrum
- 10 = Optimism
- 137 = Polygon

## Parameters
- `contract_addresses` — Comma-separated token contract addresses

## Example
```bash
curl "https://api.gopluslabs.io/api/v1/token_security/8453?contract_addresses=0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
```

## Response Structure
```json
{
  "code": 1,
  "result": {
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": {
      "is_honeypot": "0",
      "is_open_source": "1",
      "buy_tax": "0",
      "sell_tax": "0",
      "holder_count": "1234567",
      "top_10_holder_rate": "0.15",
      "owner_address": "0x...",
      "can_take_back_ownership": "0",
      "hidden_owner": "0",
      "is_mintable": "0",
      "can_pause": "0",
      "is_blacklisted": "0",
      "selfdestruct": "0",
      "external_call": "0",
      "is_proxy": "0",
      "trust_list": "1",
      "owner_change_balance": "0"
    }
  }
}
```

## Key Fields for Security Scoring

| Field | Value | Risk |
|---|---|---|
| `is_honeypot` | "1" | CRITICAL — cannot sell |
| `is_open_source` | "0" | HIGH — unverified contract |
| `buy_tax` > 10% | "0.15" | MEDIUM — high tax |
| `sell_tax` > 10% | "0.20" | HIGH — can't exit profitably |
| `is_mintable` | "1" | MEDIUM — supply inflation |
| `can_pause` | "1" | HIGH — trading freeze |
| `is_blacklisted` | "1" | HIGH — wallet blocking |
| `hidden_owner` | "1" | HIGH — rug risk |
| `selfdestruct` | "1" | CRITICAL — contract destruction |
| `can_take_back_ownership` | "1" | HIGH — renegable renouncement |
| `top_10_holder_rate` > 0.8 | "0.85" | MEDIUM — whale concentration |
| `trust_list` | "1" | POSITIVE — GoPlus verified |
| `owner_change_balance` | "0" | POSITIVE — ownership renounced |

## Rate Limits
- Free tier: ~10 req/s
- No auth required
- Use `time.sleep(0.5)` between calls to be safe

## Pitfalls
- Response keys are lowercase contract addresses
- Some tokens may not be in GoPlus database (return empty result)
- `owner_change_balance` = "0" means ownership is renounced
- Always check `is_honeypot` FIRST — it's the most critical flag
