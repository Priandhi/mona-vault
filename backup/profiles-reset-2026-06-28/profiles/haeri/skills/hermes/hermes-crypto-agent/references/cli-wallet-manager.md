# CLI Wallet Manager

Full EVM wallet operations via CLI. Script: `~/.hermes/scripts/mona_cli_wallet.py`

## Commands

```bash
python3 ~/.hermes/scripts/mona_cli_wallet.py wallets              # List all wallets
python3 ~/.hermes/scripts/mona_cli_wallet.py balance [wallet] [chain]  # Show balances
python3 ~/.hermes/scripts/mona_cli_wallet.py send <to> <amount> [token] [chain]
python3 ~/.hermes/scripts/mona_cli_wallet.py swap <from> <to> <amount> [chain]
python3 ~/.hermes/scripts/mona_cli_wallet.py bridge <token> <from_chain> <to_chain> <amount>
python3 ~/.hermes/scripts/mona_cli_wallet.py stake <protocol> <amount> [chain]
python3 ~/.hermes/scripts/mona_cli_wallet.py unstake <protocol> <amount> [chain]
python3 ~/.hermes/scripts/mona_cli_wallet.py approve <token> <spender> <amount> [chain]
python3 ~/.hermes/scripts/mona_cli_wallet.py gas [chain]
python3 ~/.hermes/scripts/mona_cli_wallet.py tx <hash> [chain]
python3 ~/.hermes/scripts/mona_cli_wallet.py wallet <id>          # Switch active wallet
```

## Chains
ethereum, base, arbitrum, optimism, polygon

## Protocols
lido, aave, rocketpool

## Swap Providers
1inch API, 0x Protocol API

## Bridge Provider
LI.FI API

## Active Wallet
priandhi.eth (0xe489306e4330Ae58De8aBfE8A3e3287d071aE2Ff) — set as primary

## Wallets (12 total)
- priandhi.eth (PRIMARY) — Galxe/ENS wallet
- W1-W10 — EVM fleet wallets
- Burner — browser automation wallet

## Natural Language Interface (User Preference)

User does NOT want CLI commands. Mona translates natural language to CLI calls:

| User says | Mona executes |
|---|---|
| "cek balance semua wallet" | `balance w1`, `balance w2`, ... (loop all 12) |
| "swap 0.01 ETH ke USDC di Base" | `swap ETH USDC 0.01 base` |
| "send 10 USDC ke 0xABC... di Base" | `send 0xABC... 10 USDC base` |
| "bridge 5 USDC dari Ethereum ke Polygon" | `bridge USDC ethereum polygon 5` |
| "stake 0.01 ETH di Lido" | `stake lido 0.01 ethereum` |
| "cek gas Ethereum" | `gas ethereum` |
| "cek balance priandhi" | `balance priandhi` |

## Import to Rabby Wallet

All 12 wallets are also imported in Rabby Wallet (browser extension on VNC).
Same private keys, same addresses — CLI and Rabby are two interfaces to the same wallets.

Keystore backup files: `~/mona-workspace/vault/keystores/` (password: mona2026)
