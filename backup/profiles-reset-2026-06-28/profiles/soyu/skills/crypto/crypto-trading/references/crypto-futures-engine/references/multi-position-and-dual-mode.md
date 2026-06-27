# Multi-Position Signal Comparison & Dual-Mode Trading

## When to Trim (Multiple Open Positions)

When user has multiple open positions and asks "masih valid?" or "cek posisi":

1. Fetch all position data (entry, mark, PnL)
2. Run signal analysis per symbol (CVD, taker volume, funding, orderbook imbalance, ATR, trend)
3. Score each position — combine signals into relative ranking
4. Identify weakest — worst signal alignment = candidate for closure
5. Compare against market context (Fear & Greed, BTC direction, funding rates)

**Decision matrix:**
- CVD positive + taker buying + negative funding = STRONG HOLD
- CVD negative + taker selling + neutral funding = CONSIDER EXIT
- CVD negative + taker selling + negative funding = CAPITULATION PLAY (high risk/reward)
- CVD positive + taker buying + neutral funding = HOLD, monitor

**When trimming:**
- Close worst CVD + taker combo first
- Preserve bullish flow positions even if PnL is lower
- Signal quality > profit amount

## Dual-Mode Trading (Scalper + Sniper)

### Scalper Mode (Momentum)
- When: Extreme Fear/Greed (FNG < 20 or > 80), or 3+ consecutive empty sniper scans
- Pre-filter: ONE API call (`/fapi/v1/ticker/24hr`), filter volume spike + price change, top 15
- Signals: RSI (5m), EMA 9/21 cross (15m), volume ratio, price momentum (24h change)
- Thresholds: score >= 55, 2+ signals agreeing
- Risk: 2% risk, 1.0 ATR SL, 0.8%/1.5% TP, 15x leverage, max 3 positions
- Speed: Scan every 120s

### Sniper Mode (Confluence)
- When: Normal market conditions
- Analysis: Full 7-layer — DOZERO.X SMC, debate, CoinGlass, Fear & Greed
- Thresholds: score >= 75, 4+ signals agreeing, SMC confluence >= 75
- Risk: 3% risk, 1.5 ATR SL, multi-TP, 20x leverage, max 2 positions
- Speed: Scan every 300s

### Auto-Switch Logic
```python
def _determine_mode(self) -> str:
    fng = get_fear_greed_cached()['value']
    if fng < 20 or fng > 80:
        return 'scalper'
    elif len(active_positions) == 0 and self._consecutive_empty_scans >= 3:
        return 'scalper'
    else:
        return 'sniper'
```
