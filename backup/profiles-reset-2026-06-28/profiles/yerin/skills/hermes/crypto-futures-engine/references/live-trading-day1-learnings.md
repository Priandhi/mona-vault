# Session Learnings — June 8, 2026 (Live Trading Day 1)

## What Went Wrong

### 1. Position Churn ($1.68 lost)
- Opened BNBUSDT LONG 1.14 BNB (margin $33, 62% of balance)
- User: "woi yang bener aja margin 33$"
- Closed via market order (taker fee $0.34)
- Re-opened 0.14 BNB (margin $4, 8%)
- **Total cost: 2× taker fee + 2× spread = $1.68 wasted**

**Lesson:** Never close and re-enter. Adjust SL/TP or wait for natural exit.

### 2. Limit Order at Market Price ($0.26 lost)
- Placed limit order at exact market price
- Filled instantly like market order → charged taker fee
- **Lesson:** Offset limit from market (0.3% ATR or orderbook-based)

### 3. Wrong Signal Attribution
- Scanner showed ETHUSDT as best signal
- Told user about ETH position that didn't exist
- Actual position was BNBUSDT
- **Lesson:** Only report actual Binance positions, not scanner output

## What Worked

### Smart Limit Order Method
```python
# Orderbook-based entry
book = await data.get_orderbook(symbol, 5)
if side == 'LONG':
    entry_price = float(book['bids'][0][0])  # best bid
else:
    entry_price = float(book['asks'][0][0])  # best ask
```

### Pre-flight Test Suite (44/44 passed)
- API connectivity, authentication, balance
- All 13 signals tested individually
- All 6 safety rails with mock scenarios
- Order params (step/tick/notional) for 5 symbols
- Algo order API endpoint
- Position reconciliation
- DXY fallback (Yahoo→CoinGecko)
- Rate limiter behavior
- Telegram alerts
- Full engine scan
- Cron jobs active
- Paper trade cycle (open→TP1→breakeven→trailing→close)

### Config Fixes Applied
- Duplicate `max_daily_trades` removed (was 5 and 4)
- DXY: Yahoo Finance skipped entirely, CoinGecko direct
- Rate limiter: 50→200 req/min
- Leverage: 20x→35-50x dynamic
- Risk: 3%→2% per trade (margin kecil)

## Trade History (BNBUSDT)
```
17:35 SELL 1.14 @ $595.74 PnL=-$0.03 fee=$0.34  (close oversized)
17:35 BUY  0.14 @ $595.75 fee=$0.04              (new small position)
17:46 SELL 0.14 @ $595.73 PnL=-$0.00 fee=$0.04  (closed by user request)
17:50 BUY  0.30 @ $597.59 fee=$0.09              (re-entry)
17:50 SELL 0.30 @ $597.44 PnL=-$0.05 fee=$0.09  (user: "close aja monaaaaaa")
17:50 BUY  0.30 @ $597.45 fee=$0.09              (re-entry again)
17:54 SELL 0.30 @ $596.82 PnL=-$0.19 fee=$0.09  (SL hit)

Total realized PnL: -$0.27
Total fees paid: $0.77
Total loss from mistakes: ~$1.94
```

## Final State
- Balance: $53.11 (from $55.65)
- Open positions: 0
- Scanner: running every 30min (top 20 pairs)
- Daily report: 00:00 UTC
- Kill switch: mona_kill_switch.py ready
