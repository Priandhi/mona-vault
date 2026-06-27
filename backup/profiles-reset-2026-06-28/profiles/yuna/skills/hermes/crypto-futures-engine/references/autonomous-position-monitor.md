# Autonomous Position Monitor Pattern

## When to Use
User says "pantau terus", "eksekusi sendiri", "autonomous", or gives full delegation on existing positions. Build a real-time monitor that watches positions and auto-executes based on pre-defined rules.

## Architecture

```
mona_position_monitor_live.py
├── THRESHOLDS dict per symbol (entry, breakdown, breakout, max_loss, trail)
├── Peak price tracker (per symbol)
├── Trailing SL activator (+1.5% → activate, trail 0.8% below peak)
├── Signal re-check on breakdown (CVD confirmation before closing)
└── Logging via FlushingFileHandler
```

## Rule Priority (highest first)

1. **Max Loss** — PnL ≤ -3% from entry → auto close market, no confirmation needed
2. **Breakdown** — Price ≤ recent low AND CVD < -15% → auto close (selling confirmed)
3. **Breakdown without CVD confirmation** → log warning, hold (false breakdown possible)
4. **Trailing SL** — After +1.5% profit, activate trail at 0.8% below peak → auto close on trail hit
5. **Breakout** — Price ≥ recent high → log only (let it run with trailing active)

## Key Design Decisions

### CVD Confirmation on Breakdown
Don't close just because price touched support. Re-check CVD from last 500 agg trades:
- CVD < -15% = real selling → close
- CVD > -15% = false breakdown / bounce → hold

### Trailing Stop Activation Threshold
- Activate at +1.5% profit (not immediately)
- Trail distance: 0.8% below peak
- Trail only moves UP (never backwards)
- This locks profit on momentum plays while giving room to breathe

### 60-Second Check Interval
- Fast enough to catch sharp moves
- Slow enough to avoid Binance rate limits (~20 API calls/cycle)
- Each cycle: get positions + 3 mark prices + optional CVD checks

## Binance API Calls Per Cycle

1. `GET /fapi/v2/account` — all positions + balance (1 call)
2. `GET /fapi/v1/premiumIndex?symbol=X` — mark price (1 per position)
3. `GET /fapi/v1/aggTrades?symbol=X&limit=500` — CVD (only on breakdown trigger)
4. `POST /fapi/v1/order` — close position (only on execution)

Total per cycle: 1 + N positions = ~4 calls normally. Spikes to ~10 on breakdown.

## Pitfalls

1. **Trailing SL state is in-memory** — if process restarts, trailing state resets. Peak prices re-track from current mark. Trailing SL re-activates at next +1.5% threshold. This is acceptable for short-lived monitors (<24h).

2. **close_position qty must match positionAmt** — always re-fetch position before closing. Don't use cached qty.

3. **reduceOnly=true is mandatory** — without it, a SELL on a LONG position could open a SHORT if the position was already closed by another order.

4. **CVD from aggTrades is directional, not absolute** — it measures taker buy vs sell volume in the last 500 trades. A -20% CVD means sellers are 60% of volume, not that price dropped 20%.

5. **Process must run with `python3 -u`** — unbuffered output for log visibility in `process(action='log')`.

6. **Use `background=True, notify_on_complete=True`** — NOT nohup. Hermes tracks the process lifecycle.

## Template: Thresholds Config

```python
THRESHOLDS = {
    'SYMBOLUSDT': {
        'entry': <float>,           # actual entry price from Binance
        'breakdown_price': <float>, # recent swing low (from klines)
        'breakout_price': <float>,  # recent swing high (from klines)
        'max_loss_pct': -3.0,       # max loss from entry %
        'trail_activate_pct': 1.5,  # activate trailing after +X%
        'trail_distance_pct': 0.8,  # trail X% below peak
    },
}
```

## Integration with Signal Framework

Before auto-closing on breakdown, re-check signal state:
- CVD (agg trades) — selling pressure confirmation
- Taker buy/sell ratio — < 40% buy = confirmed bearish
- Orderbook imbalance — < 0.7 = heavy selling wall

If signals DON'T confirm the breakdown (CVD neutral/positive), the price touching support might be a bounce opportunity, not a sell signal. This prevents false exits on wicks.
