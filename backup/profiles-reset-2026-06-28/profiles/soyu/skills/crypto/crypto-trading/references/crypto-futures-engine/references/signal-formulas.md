# Signal Calculation Formulas

## OI Divergence
```
price_chg = (price_now - price_4h_ago) / price_4h_ago * 100
oi_chg = (oi_now - oi_4h_ago) / oi_4h_ago * 100

if price_chg < -1 and oi_chg > 5:  → STRONG_LONG (squeeze)
if price_chg > 1 and oi_chg < -5:  → STRONG_SHORT (dump)
score = min(80, abs(oi_chg) * 8)
```

## CVD (Cumulative Volume Delta)
```
for each trade:
    value = qty * price
    if trade.is_maker_sell:  # taker sold
        cvd -= value
    else:                    # taker bought
        cvd += value

cvd_trend = cvd_second_half - cvd_first_half
# Divergence: price up + cvd down = invisible selling
```

## ATR (Average True Range) — Wilder's Smoothing
```
TR = max(high-low, |high-prev_close|, |low-prev_close|)
ATR = SMA(TR, period)  # initial
ATR = (ATR_prev * (period-1) + TR_current) / period  # subsequent
```

## ADX (Average Directional Index)
```
+DM = high - prev_high (if > 0 and > down)
-prev_low - low (if > 0 and > up)
Smooth +DM, -DM, TR with Wilder's method
+DI = 100 * smooth(+DM) / smooth(TR)
-DI = 100 * smooth(-DM) / smooth(TR)
DX = 100 * |+DI - -DI| / (+DI + -DI)
ADX = smooth(DX, period)
```

## VPIN (Volume-Synchronized Probability of Informed Trading)
```
Bucket trades into groups of N (default 50)
For each bucket:
    buy_vol = sum of taker buy value
    sell_vol = sum of taker sell value
VPIN = avg(|buy_vol - sell_vol|) / avg(buy_vol + sell_vol)
# > 0.7 = high toxicity (informed traders active)
```

## Max Pain (Options)
```
For each strike price:
    call_pain = sum(max(0, strike - test_strike) * call_OI)
    put_pain = sum(max(0, test_strike - strike) * put_OI)
    total_pain = call_pain + put_pain
max_pain = strike with minimum total_pain
```

## Composite Score
```
# CRITICAL: Active-signal-only normalization (see pitfall #39)
weighted = 0
total_weight = 0
for signal in signals:
    if abs(signal.score) > 0:           # ONLY count active signals
        weighted += signal.score * (weight / 100)
        total_weight += weight

composite = (weighted / total_weight * 100) if total_weight > 0 else 0

# Regime adjustment:
if regime == STRONG_TREND_UP and score > 0: score *= 1.2
if regime == STRONG_TREND_UP and score < 0: score *= 0.8
if regime == HIGH_VOLATILITY: score *= 0.7
if vpin > 0.7: score *= 0.6
```

## RSI (Relative Strength Index) + Divergence

```
# RSI-14 calculation
gains = [max(close[i] - close[i-1], 0) for i in range(1, len)]
losses = [max(close[i-1] - close[i], 0) for i in range(1, len)]
avg_gain = SMA(gains, 14)  # initial
avg_loss = SMA(losses, 14)
# Wilder's smoothing:
avg_gain = (avg_gain * 13 + current_gain) / 14
avg_loss = (avg_loss * 13 + current_loss) / 14
RS = avg_gain / avg_loss
RSI = 100 - (100 / (1 + RS))

# Signals:
RSI < 25: STRONG_LONG (deeply oversold, score +70)
RSI < 35: LONG (oversold, score +40)
RSI > 75: STRONG_SHORT (deeply overbought, score -70)
RSI > 65: SHORT (overbought, score -40)

# Bullish Divergence (last 15 candles):
# Price makes lower low BUT RSI makes higher low → +20 bonus
# Bearish Divergence:
# Price makes higher high BUT RSI makes lower high → -20 bonus
```

## Bollinger Bands + Squeeze

```
SMA = mean(close, 20)
STD = stddev(close, 20)
Upper = SMA + 2 * STD
Lower = SMA - 2 * STD
%B = (price - Lower) / (Upper - Lower)
Bandwidth = (Upper - Lower) / SMA * 100

# Squeeze detection:
avg_bw = mean(bandwidth, last 50 candles)
squeeze = bandwidth < avg_bw * 0.6  # compressed > 40%

# Signals:
%B < 0.0: LONG +50 (price below lower band)
%B > 1.0: SHORT -50 (price above upper band)
%B < 0.2: LONG +25 (near lower band)
%B > 0.8: SHORT -25 (near upper band)
squeeze + price > EMA10: LONG +30 (expecting upside breakout)
squeeze + price < EMA10: SHORT -30 (expecting downside breakout)
```

## Wyckoff Accumulation/Distribution

```
# Selling Climax (SC):
volume_spike = current_vol > 2x avg_vol
large_down_candle = (close - low) > 1.5 * (high - close)
reversal = close[-1] > close[-2] > close[-3]
SC = volume_spike AND large_down_candle AND reversal → LONG +55

# Spring:
recent_low = min(lows[-20:-1])
spring = (low[-1] < recent_low) AND (close[-1] > recent_low) AND (vol > 1.3x avg)
→ STRONG_LONG +70

# Sign of Strength (SOS):
recent_high = max(highs[-20:-1])
sos = (close[-1] > recent_high) AND (vol > 1.5x avg)
→ LONG +60

# Last Point of Support (LPS):
lps = (vol < 0.6x avg) AND (close[-1] > close[-5])
→ LONG +40

# Upthrust After Distribution (UTAD):
utad = (high[-1] > recent_high) AND (close[-1] < recent_high) AND (vol > 1.3x avg)
→ SHORT -60
```

## Real-World Score Distribution (20 USDT pairs, 16 signals)

Based on live engine data (Jun 2026) with FearGreed=10%, OI=15%, Funding=12%, CVD/Taker/OrderFlow/VolumeProfile=10%, SMC=15%, RSI=10%, Bollinger=8%, Wyckoff=10%:

| Score Range | Frequency | Signals Firing | Action |
|-------------|-----------|----------------|--------|
| 0-15        | ~55%      | 0-2            | Skip (noise) |
| 15-30       | ~25%      | 2-3            | Skip (weak) |
| 30-50       | ~15%      | 3-5            | Consider (moderate) |
| 50+         | ~5%       | 5+             | **Trade** (strong) |

**Key insight:** With 16 signals, the composite score normalizes by active-signal weights only. FearGreed dominates at extreme values (score 90 when F&G=12). Setting min_score=50 is appropriate — captures ~5% of scan results.

## Backtest Results (30 days, 1H candles, Jun 2026)

| Pair | Trades | WinRate | PnL | Profit Factor | Max DD |
|------|--------|---------|-----|---------------|--------|
| SOLUSDT | 25 | 56.0% | +10.2% | 1.44 | 7.7% |
| BTCUSDT | 27 | 51.9% | +5.7% | 1.38 | 7.2% |
| ETHUSDT | 27 | 55.6% | +0.5% | 1.02 | 13.7% |
| ZECUSDT | 17 | 41.2% | -10.2% | 0.78 | 20.7% |
| HYPEUSDT | 29 | 34.5% | -17.4% | 0.72 | 24.6% |

**Conclusions:**
- Strategy works on BTC/SOL (trending, high-volume) — PF > 1.3
- ETH breakeven — needs better regime filter
- High-volatility altcoins (ZEC, HYPE) lose money — PF < 0.8
- **Filter: skip pairs with ATR% > 3% or regime=HIGH_VOLATILITY**
- **Filter: only trade top 10 by 24h volume**
