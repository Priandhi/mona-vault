# Binance Futures Leverage Bracket API

## Problem
`/fapi/v1/exchangeInfo` does NOT contain leverage information. The `leverageFilter` field does not exist in the response. This caused Mona to hardcode 10x leverage for CAKEUSDT when the actual max was 75x.

## Correct Endpoint
```
GET /fapi/v1/leverageBracket
```
**Requires authentication** (API key + signature).

## Response Format
```json
[
  {
    "symbol": "CAKEUSDT",
    "brackets": [
      {
        "bracket": 1,
        "initialLeverage": 75,    // ← MAX leverage for this bracket
        "notionalCap": 5000,      // ← Max notional at this leverage
        "notionalFloor": 0,
        "maintMarginRatio": 0.01,
        "cum": 0.0
      },
      {
        "bracket": 2,
        "initialLeverage": 50,    // ← Lower leverage for larger positions
        "notionalCap": 25000,
        ...
      }
    ]
  }
]
```

## Key Points
- `brackets[0]['initialLeverage']` = **MAX leverage** for the symbol
- As notional size increases, leverage decreases (brackets[1], brackets[2], etc.)
- For small positions ($5 margin × 75x = $375 notional), always use brackets[0]
- The endpoint returns ALL symbols — filter by `symbol` field

## Working Example (2026-06-08)
```python
# CAKEUSDT actual max leverage: 75x (NOT 10x as assumed)
# BTCUSDT actual max leverage: 125x
# ETHUSDT actual max leverage: 100x
```

## Set Leverage After Fetching
```python
# After getting max_lev from leverageBracket
r = requests.post(f'{BASE}/fapi/v1/leverage', params={
    'symbol': symbol,
    'leverage': max_lev
}, headers=headers)
# Response: {"symbol": "CAKEUSDT", "leverage": 75, "maxNotionalValue": "5000"}
```
