# Sprint 2: Wallet Manager — Multi-Chain Orchestrator

## Architecture

Two modules working together:
- `mona_wallet_manager.py` — Core engine (balance queries, health checks, bridge routing, watchlist, labels/groups, anti-sybil jitter, honeypot checks via GoPlus)
- `mona_wallet_commands.py` — Telegram bot integration (parses commands, formats responses, delegates to manager)

Bot delegates wallet handler: `from mona_wallet_commands import handle_wallet_command`

## Supported Chains
Ethereum, Base, Arbitrum, Optimism, Polygon, BSC, Avalanche + Solana (separate)

## Commands (Topic 💸 Wallet)

| Command | Function |
|---------|----------|
| `portfolio` | Full portfolio summary across all chains |
| `cek semua` | All EVM + Solana balances |
| `cek [1-10]` | Single wallet balance |
| `cek [chain] [id]` | Balance on specific chain |
| `cek sol` | Solana wallet |
| `label [id] [nama]` | Set wallet label |
| `labels` | List all labels |
| `group [nama] [id1,id2,...]` | Create wallet group |
| `cek group [nama]` | Group balance |
| `health [id]` | Wallet health check |
| `health semua` | All wallets health |
| `honeypot [contract]` | GoPlus scam check |
| `bridge [dari] [ke] [amount]` | Bridge routes (LI.FI) |
| `gas [chain]` | Gas price in Gwei |
| `watch [addr] [label]` | Add to watchlist |
| `check watches` | Check watchlist activity |
| `distribute [amount]` | Fund distribution plan |

## Key Implementation Details

### Wallet Loading
```python
# Always handle both key formats
data.get("wallets", data.get(" wallets", []))
```

### Anti-Sybil Jitter
- `jitter_delay(min_sec=5, max_sec=60)` — Random sleep between operations
- `jitter_amount(base, variation_pct=10)` — Vary amounts ±10%
- `jitter_address()` — Deterministic hourly shuffle of wallet execution order

### Honeypot Detection (GoPlus)
```python
url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={token_address}"
# Check: is_honeypot, buy_tax, sell_tax, can_sell, hidden_owner, selfdestruct
```

### Bridge Router (LI.FI)
```python
url = f"https://li.quest/v1/quote?fromChain={id}&toChain={id}&fromToken=0x0...&toToken=0x0...&fromAmount={wei}"
# Fallback to static routes if API fails
```

### Health Checks
- Balance sufficiency (gas reserves)
- Token approval scanning
- Suspicious contract interactions
- GoPlus security integration

## Storage Files
- `vault/.wallet_labels.json` — Wallet ID → label mapping
- `vault/.wallet_groups.json` — Group name → wallet IDs
- `vault/.wallet_watchlist.json` — Watched addresses with activity tracking
- `vault/.wallet_activity_log.json` — Last 500 wallet operations

## Future: Batch Executor
TX Builder + Batch Execution not yet wired to real signing. The build_tx/simulate_tx functions exist but need eth_account signing integration for actual on-chain execution. When wiring:
1. Build TX with build_tx()
2. Simulate with simulate_tx()
3. Gate through governor (spend limit check)
4. Sign with eth_account
5. Broadcast via evm_rpc_call("eth_sendRawTransaction")
6. Log activity
