# Wallet Manager Features — Full Reference

> Module: `mona_wallet_manager.py` + `mona_wallet_commands.py`

## Commands (Topic 💸 Wallet)

| Command | Description |
|---------|-------------|
| `portfolio` | Full portfolio: all EVM + Solana, total USD estimate |
| `cek semua` | All wallet balances (EVM + Solana) |
| `cek [1-10]` | Single wallet: ETH + Base balance |
| `cek sol` | Solana wallet balance |
| `cek [chain] [id]` | Balance on specific chain (eth/base/arb/op/polygon/bsc) |
| `label [id] [nama]` | Label a wallet |
| `labels` | Show all labels |
| `group [nama] [id1,id2,...]` | Create wallet group |
| `groups` | Show all groups |
| `cek group [nama]` | Check balance of wallet group |
| `health [id]` | Health check: approvals, scam tokens, suspicious TX |
| `health semua` | Health check all wallets |
| `honeypot [contract]` | Check if token is honeypot (GoPlus API) |
| `bridge [dari] [ke] [amount]` | Find cheapest bridge route |
| `gas [chain]` | Gas price on specified chain |
| `watch [address] [label]` | Add to on-chain watchlist |
| `unwatch [address]` | Remove from watchlist |
| `watches` | Show watchlist |
| `check watches` | Check watchlist for new activity |
| `distribute [amount]` | Plan ETH distribution to all wallets |

## Supported Chains

```python
CHAINS = {
    "ethereum": {"id": 1, "symbol": "ETH", "rpc": "eth-mainnet.g.alchemy.com"},
    "base": {"id": 8453, "symbol": "ETH", "rpc": "base-mainnet.g.alchemy.com"},
    "arbitrum": {"id": 42161, "symbol": "ETH"},
    "optimism": {"id": 10, "symbol": "ETH"},
    "polygon": {"id": 137, "symbol": "POL"},
    "bsc": {"id": 56, "symbol": "BNB"},
    "avalanche": {"id": 43114, "symbol": "AVAX"},
}
```

## Anti-Sybil Jitter

```python
def jitter_delay(min_sec=5, max_sec=60):
    """Random delay between wallet operations"""

def jitter_amount(base_amount, variation=0.1):
    """Vary amount by ±10%"""
```

## Honeypot Detection (GoPlus)

```python
def check_honeypot(contract_address, chain_id=1):
    """Check via GoPlus Security API
    Returns: {is_honeypot, buy_tax, sell_tax, can_sell, ...}
    """
```

## Bridge Router

Compares routes across:
- Stargate (LayerZero)
- Across Protocol
- LI.FI aggregator
- Native bridges

Returns sorted by fee with estimated time.

## Wallet Health Checks

- Unlimited token approvals → suggest revoke
- Interaction with known scam contracts
- Low gas reserves → suggest top-up
- Honeypot tokens in portfolio
- Suspicious recent transactions

## Pitfalls

1. **JSON key space prefix**: `data.get("wallets", data.get(" wallets", []))`
2. **Alchemy key**: Use `LUnQ5tB09bfQQGQ5Ri_MH` for EVM RPC
3. **Helius key**: Use `2f166885-a270-415e-93f8-a8000f7363ff` for Solana RPC
4. **Wallet #10**: Dedicated airdrop wallet (`0x83c82ca6bebff06d86130e8cbc7ea97bd02709aa`)
