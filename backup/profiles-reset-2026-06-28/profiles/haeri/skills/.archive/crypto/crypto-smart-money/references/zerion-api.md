# Zerion API Reference

## Auth
- Type: HTTP Basic Auth
- Username: API key (e.g. `zk_266b88bc2e644a9ca895bd6a67e1fd54`)
- Password: empty
- Header: `Authorization: Basic base64("{key}:")`
- Python: `base64.b64encode(f"{key}:".encode()).decode()`

## Endpoints

### GET /wallets/{address}/transactions/
Transaction history with rich metadata.

**Query params:**
- `currency=usd`
- `filter[chain_ids]=base` (or comma-separated: `base,ethereum`)
- `filter[operation_types]=trade` (or `send,receive,trade,approve`)
- `filter[trash]=no_filter`
- `page[size]=10` (max 100)
- `page[cursor]=...` (pagination)

**Response structure:**
```json
{
  "data": [
    {
      "type": "transactions",
      "id": "uuid",
      "attributes": {
        "address": "0x...",
        "operation_type": "trade|send|receive|approve",
        "hash": "0x...",
        "mined_at": "ISO timestamp",
        "sent_from": "0x...",
        "sent_to": "0x...",
        "status": "confirmed|pending|failed",
        "nonce": 12345,
        "fee": {
          "fungible_info": {"name": "...", "symbol": "..."},
          "quantity": {"float": 0.001},
          "value": 2.50
        },
        "transfers": [
          {
            "fungible_info": {
              "id": "token-id",
              "name": "Token Name",
              "symbol": "TKN",
              "icon": {"url": "https://..."},
              "flags": {"verified": true},
              "implementations": [
                {"chain_id": "base", "address": "0x...", "decimals": 18},
                {"chain_id": "ethereum", "address": "0x...", "decimals": 18}
              ]
            },
            "direction": "in|out",
            "quantity": {"float": 123.45, "numeric": "123.4500"},
            "value": 50.0,
            "price": 0.4,
            "sender": "0x...",
            "recipient": "0x..."
          }
        ],
        "acts": [
          {
            "type": "trade",
            "application_metadata": {
              "contract_address": "0x...",
              "method": {"id": "0x...", "name": "Exact Input Single"}
            }
          }
        ]
      },
      "relationships": {
        "chain": {"data": {"id": "base"}}
      }
    }
  ],
  "links": {
    "self": "...",
    "next": "..."
  }
}
```

### GET /wallets/{address}/portfolio/
Portfolio overview: total value, chain breakdown, positions.

## Rate Limits
- Free tier: 3 requests/second
- Use 5s poll interval for real-time monitoring
- `time.sleep(0.3)` between enrichment calls

## Supported Chains
Over 60 chains including: base, ethereum, arbitrum, optimism, polygon, binance-smart-chain, avalanche, solana, sui, aptos, ton, and many more.

## Trade Parsing Logic
```python
def parse_trade(tx, wallet_addr):
    attrs = tx["attributes"]
    received = [t for t in attrs["transfers"] if t["direction"] == "in"]
    sent = [t for t in attrs["transfers"] if t["direction"] == "out"]
    # Filter out stables/WETH from received
    received = [r for r in received if get_contract(r) not in IGNORED_TOKENS]
    return {"received": received, "sent": sent, "hash": attrs["hash"]}

def get_contract(transfer):
    """Get Base chain contract from fungible_info implementations"""
    for impl in transfer["fungible_info"].get("implementations", []):
        if impl["chain_id"] == "base":
            return impl["address"]
    return None
```

## Sell Detection
Sells appear as trades where the wallet SENDS non-stable tokens and RECEIVES WETH/USDC.
Since WETH/USDC are in IGNORED_TOKENS, the `received` list will be empty after filtering.
**Key insight**: Check the `sent` list for non-stable tokens — that's the sell signal.

```python
# In the watcher loop:
for sent in trade["sent"]:
    sent_contract = get_contract(sent)
    if sent_contract and sent_contract not in IGNORED_TOKENS:
        # This is a SELL — whale sent out a non-stable token
        update_holdings(wallet, sent_contract, "sell", sent["quantity"]["float"], sent["price"])
        send_sell_alert(wallet, sent, trade)
```

## Holdings Tracking
Track holdings per wallet to calculate PnL on sells:
```python
# On buy: record entry with average cost basis
update_holdings(wallet, token, "buy", amount, price)

# On sell: calculate PnL against average entry
holdings = get_holdings(wallet)
entry = holdings[token]["avg_cost"]
pnl_pct = (sell_price - entry) / entry * 100
```
