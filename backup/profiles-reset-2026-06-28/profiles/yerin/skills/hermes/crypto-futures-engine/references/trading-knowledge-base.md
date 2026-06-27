# Mona Trading Knowledge Base — Technical, Fundamental & Sentiment Analysis
# Compiled from research + best practices for automated crypto futures trading

═══════════════════════════════════════════════════════════════
# PART 1: TECHNICAL ANALYSIS
═══════════════════════════════════════════════════════════════

## 1.1 INDICATORS — Best Combinations for Crypto

### TIER 1 (MUST HAVE — highest win rate in crypto):

**RSI (Relative Strength Index)**
- Period: 14 (standard), 7 (scalping)
- Buy signal: RSI < 30 (oversold) + price at support
- Sell signal: RSI > 70 (overbought) + price at resistance
- BEST: RSI Divergence — price makes new high but RSI doesn't = bearish divergence
- Code: rsi = 100 - (100 / (1 + avg_gain / avg_loss))

**MACD (Moving Average Convergence Divergence)**
- Fast: 12 EMA, Slow: 26 EMA, Signal: 9 EMA
- Buy: MACD crosses ABOVE signal line + histogram turning positive
- Sell: MACD crosses BELOW signal line + histogram turning negative
- BEST: MACD histogram divergence with price
- Code: macd = ema(12) - ema(26); signal = ema(macd, 9); histogram = macd - signal

**Volume Profile / VWAP**
- VWAP = cumulative(typical_price * volume) / cumulative(volume)
- Price above VWAP = bullish intraday bias
- Price below VWAP = bearish intraday bias
- POC (Point of Control) = price level with highest volume = strongest support/resistance
- Value Area (70% of volume) = range where price tends to revert

### TIER 2 (CONFIRMATION — increase win rate):

**Bollinger Bands**
- Period: 20, StdDev: 2
- Squeeze (bands narrow) = volatility expansion coming
- Price touching lower band + RSI < 30 = strong buy
- Walk the band = strong trend (don't counter-trade)

**ATR (Average True Range)**
- Period: 14
- Use for: Dynamic stop loss (SL = entry ± 1.5-2x ATR)
- Use for: Position sizing (smaller position when ATR is high)
- ATR expanding = volatility increasing = trend starting
- ATR contracting = consolidation = breakout coming

**ADX (Average Directional Index)**
- Period: 14
- ADX > 25 = trending market (trade the trend)
- ADX < 20 = ranging market (use mean reversion)
- ADX > 40 = strong trend (ride it, don't counter)
- +DI > -DI = bullish; -DI > +DI = bearish

### TIER 3 (ADVANCED — for edge):

**Ichimoku Cloud**
- Tenkan (9), Kijun (26), Senkou A (26), Senkou B (52), Chikou (26)
- Price above cloud = bullish; below = bearish
- Cloud twist = trend reversal
- TK cross + price above cloud = strong buy
- BEST for: 4H and Daily timeframes in crypto

**Stochastic RSI**
- More sensitive than regular RSI
- Buy: K crosses above D when both < 20
- Sell: K crosses below D when both > 80

**OBV (On Balance Volume)**
- OBV rising + price flat = accumulation (bullish)
- OBV falling + price flat = distribution (bearish)
- OBV confirms trend if moving same direction as price

---

## 1.2 CHART PATTERNS (highest reliability in crypto):

### REVERSAL PATTERNS:
1. **Head & Shoulders** — bearish reversal, 78% accuracy in crypto
   - Entry: break of neckline
   - SL: above right shoulder
   - Target: height of head from neckline

2. **Inverse Head & Shoulders** — bullish reversal
   - Same logic, inverted

3. **Double Top (M pattern)** — bearish, 72% accuracy
   - Entry: break of support between the two tops
   - SL: above the second top

4. **Double Bottom (W pattern)** — bullish, 72% accuracy
   - Entry: break of resistance between the two bottoms

### CONTINUATION PATTERNS:
5. **Bull/Bear Flag** — continuation, 68% accuracy
   - Strong move + consolidation channel = flag
   - Entry: break of flag in trend direction
   - Target: flagpole length projected from breakout

6. **Ascending/Descending Triangle**
   - Ascending = bullish (higher lows, flat resistance)
   - Descending = bearish (lower highs, flat support)
   - Entry: breakout from triangle

7. **Cup & Handle** — bullish, 75% accuracy
   - U-shaped recovery + small pullback = handle
   - Entry: break above handle resistance

---

## 1.3 SMART MONEY CONCEPTS (SMC) — Already in DOZERO.X:

**Order Blocks (OB):**
- Last candle before a strong move (institutional entry zone)
- Bullish OB = last down candle before rally
- Bearish OB = last up candle before dump
- Price tends to return to OB before continuing

**Fair Value Gaps (FVG):**
- Gap between candle 1 high and candle 3 low (bullish)
- Market tends to fill FVG before continuing
- Virgin FVG = never filled = strongest signal

**Liquidity Levels:**
- Equal highs/lows = liquidity pools
- Stop losses cluster below swing lows / above swing highs
- Smart money hunts these levels before reversing

**BOS (Break of Structure):**
- Break of previous swing high (bullish) or swing low (bearish)
- Confirms trend continuation

**CHOCH (Change of Character):**
- First break against the trend = reversal signal
- More powerful than BOS

**Premium/Discount Zones:**
- Above 50% of range = premium (sell zone)
- Below 50% of range = discount (buy zone)
- Buy in discount, sell in premium

---

## 1.4 WYCKOFF THEORY:

**Accumulation Phase (Smart Money Buying):**
1. Preliminary Support (PS) — first buying wave
2. Selling Climax (SC) — panic selling, high volume
3. Automatic Rally (AR) — bounce after climax
4. Secondary Test (ST) — retest of SC low
5. Spring — final shakeout below support (BEST entry)
6. Sign of Strength (SOS) — strong rally on volume
7. Last Point of Support (LPS) — final pullback (second entry)

**Distribution Phase (Smart Money Selling):**
- Mirror of accumulation
- Preliminary Supply → Buying Climax → UTAD → markdown

**How to detect programmatically:**
- SC: Volume spike (> 2x average) + large down candle + reversal
- Spring: Break below support + quick reclaim + low volume on break
- SOS: Break above resistance on high volume

---

## 1.5 MULTI-TIMEFRAME ANALYSIS:

**Best practice for crypto:**
- Daily (D1): Trend direction + major S/R levels
- 4H: Structure + bias
- 1H: Entry signals
- 15M: Precision entries + timing
- 5M: Exact entry candle

**Rule: NEVER trade against the 4H trend**
- If 4H is bullish → only look for longs on 1H/15M
- If 4H is bearish → only look for shorts on 1H/15M

---

## 1.6 ELLIOTT WAVE (simplified for algo):

**Basic pattern: 5 waves impulse + 3 waves correction**
- Wave 1: Initial move (hard to catch)
- Wave 2: Retracement (0.382-0.786 of Wave 1) — NEVER beyond Wave 1 start
- Wave 3: Strongest, longest (usually 1.618x Wave 1)
- Wave 4: Retracement (0.236-0.5 of Wave 3) — NEVER overlaps Wave 1
- Wave 5: Final move (often = Wave 1 or 0.618x Wave 1-3)
- A-B-C: Correction after the 5-wave impulse

**Automated detection:**
- Count swing highs/lows
- Measure retracement ratios
- Wave 3 entry is the highest probability trade


═══════════════════════════════════════════════════════════════
# PART 2: FUNDAMENTAL ANALYSIS
═══════════════════════════════════════════════════════════════

## 2.1 ON-CHAIN METRICS (for BTC/ETH primarily):

**Active Addresses**
- Rising active addresses + rising price = healthy rally
- Rising addresses + falling price = accumulation (bullish divergence)
- Falling addresses + rising price = weak rally (bearish divergence)

**Exchange Inflow/Outflow**
- Large exchange inflow = selling pressure (bearish)
- Large exchange outflow = holding/accumulation (bullish)
- BEST signal: massive outflow from exchanges → supply squeeze

**MVRV Ratio (Market Value to Realized Value)**
- MVRV > 3.5 = overvalued (sell zone)
- MVRV < 1.0 = undervalued (buy zone)
- Historical tops: MVRV 3.5-4.0
- Historical bottoms: MVRV 0.7-1.0

**NVT Ratio (Network Value to Transactions)**
- NVT > 90 = overvalued (network value exceeds utility)
- NVT < 45 = undervalued
- Like P/E ratio for crypto

**Whale Movements**
- Whale buying + price dipping = smart money accumulation
- Whale selling + price pumping = smart money distribution
- Track: wallets > 1000 BTC

**Stablecoin Flows**
- Rising USDT/USDC supply on exchanges = dry powder ready to buy
- Falling stablecoin supply = capital leaving crypto
- Stablecoin inflow to exchanges = buying pressure incoming

## 2.2 MACRO FACTORS:

**DXY (US Dollar Index)**
- DXY up = crypto down (inverse correlation ~70%)
- DXY down = crypto up
- BEST: DXY at major resistance → crypto buy signal

**Interest Rates / Fed Policy**
- Rate hike = bearish for crypto (risk-off)
- Rate cut / pause = bullish (risk-on)
- FOMC meetings = high volatility events

**Bitcoin Dominance (BTC.D)**
- BTC.D rising = altcoins underperform, focus on BTC
- BTC.D falling = altcoin season, rotate to alts
- BTC.D > 60% = risk-off, avoid altcoins

**Total Crypto Market Cap**
- Rising market cap + rising volume = healthy bull market
- Falling market cap + rising volume = capitulation

**CPI (Consumer Price Index)**
- High CPI → Fed hawkish → crypto bearish
- Low CPI → Fed dovish → crypto bullish

## 2.3 TOKENOMICS (for altcoin trading):

**Supply Schedule**
- High inflation (> 10%/year) = sell pressure
- Deflationary (burns > emissions) = bullish long-term

**Vesting Unlocks**
- Token unlock events = sell pressure
- Track: TokenUnlocks.app for upcoming unlocks
- Avoid buying 1-2 weeks before major unlocks

**Staking Ratio**
- High staking ratio (> 50%) = supply locked = bullish
- Low staking ratio = liquid supply = sell pressure

**Protocol Revenue**
- Protocols with real revenue > emissions = sustainable
- Revenue growing + token buyback = very bullish


═══════════════════════════════════════════════════════════════
# PART 3: SENTIMENT ANALYSIS
═══════════════════════════════════════════════════════════════

## 3.1 FEAR & GREED INDEX:
- 0-25: Extreme Fear → Contrarian BUY
- 25-45: Fear → Lean bullish
- 45-55: Neutral → No edge
- 55-75: Greed → Lean bearish
- 75-100: Extreme Greed → Contrarian SELL
- BEST: Combine with price action. Extreme Fear + support = strong buy

## 3.2 FUNDING RATE:
- Funding > 0.05% = extreme long crowding → SHORT signal
- Funding < -0.05% = extreme short crowding → LONG signal
- Funding flip from negative to positive = momentum shift
- BEST: funding divergence with price (price up + funding negative = strong buy)

## 3.3 OPEN INTEREST:
- OI rising + price rising = trend strengthening (new money entering)
- OI rising + price falling = new shorts opening (bearish)
- OI falling + price rising = short covering (weak rally)
- OI falling + price falling = long liquidation (bearish exhaustion)
- BEST: OI spike + price reversal = liquidation cascade incoming

## 3.4 LONG/SHORT RATIO:
- Ratio > 2.0 = overcrowded long → short signal
- Ratio < 0.5 = overcrowded short → long signal
- BEST: combine with funding rate for confirmation

## 3.5 OPTIONS DATA:
- Put/Call ratio > 1.0 = bearish sentiment (contrarian bullish)
- Put/Call ratio < 0.5 = bullish sentiment (contrarian bearish)
- Max Pain = price where most options expire worthless
- Price tends to gravitate toward max pain at expiry
- IV (Implied Volatility) crush after events = opportunity

## 3.6 LIQUIDATION DATA:
- Large liquidation clusters = magnets for price
- Cascading long liquidations = flash crash
- Cascading short liquidations = short squeeze
- BEST: trade toward liquidation clusters (smart money does this)

## 3.7 SOCIAL SENTIMENT:
- Twitter mentions spike + price dump = capitulation (buy)
- Twitter mentions spike + price pump = euphoria (sell)
- Google Trends "buy bitcoin" spike = retail FOMO (sell signal)
- Google Trends "bitcoin dead" spike = retail panic (buy signal)

## 3.8 STABLECOIN INTEREST RATES:
- High USDT/USDC lending rates on AAVE/Compound = demand for leverage
- Very high rates = overleveraged market = correction coming
- Very low rates = deleveraged market = safe to enter


═══════════════════════════════════════════════════════════════
# PART 4: BEST STRATEGIES FOR AUTOMATED TRADING
═══════════════════════════════════════════════════════════════

## 4.1 HIGHEST WIN-RATE SETUPS IN CRYPTO:

**Setup 1: Trend Continuation (60-70% win rate)**
- 4H/1D trend confirmed (higher highs/lows)
- Price pulls back to support/FVG/order block
- RSI not oversold (30-50 range)
- Entry on 1H/15M bullish candle close
- SL below the pullback low
- TP at previous high or 2x ATR

**Setup 2: Breakout + Retest (65-75% win rate)**
- Price breaks above resistance on high volume
- Wait for retest of broken resistance (now support)
- Enter on retest with tight SL below the breakout level
- Target: next resistance or measured move

**Setup 3: SMC Spring + Displacement (70-80% win rate)**
- Price sweeps liquidity below support (spring)
- Strong bullish displacement candle (> 1.5x ATR)
- FVG formed on the displacement
- Enter at the FVG with SL below the sweep low
- This is what DOZERO.X detects!

**Setup 4: Funding Rate Extreme Reversal (55-65% win rate)**
- Funding rate > 0.1% or < -0.1%
- Price at key resistance/support
- OI spiking (overleveraged market)
- Counter-trade the crowd with tight SL

**Setup 5: Volume Divergence (60-70% win rate)**
- Price makes new high but volume declining
- RSI bearish divergence
- Enter short with SL above the high
- TP at nearest support

## 4.2 RISK MANAGEMENT RULES:

1. Never risk more than 2% per trade
2. Minimum 2:1 reward-to-risk ratio
3. Maximum 3 correlated positions
4. No trading during major news events (FOMC, CPI)
5. Reduce size after 2 consecutive losses
6. Stop trading after 5% daily drawdown
7. Always use stop loss — no exceptions
8. Move SL to breakeven after TP1
9. Trail SL using ATR (1.5x ATR behind price)
10. Take partial profits (50% at TP1, 30% at TP2, 20% runner)

## 4.3 MARKET REGIME STRATEGY SELECTION:

**Trending (ADX > 25):**
- Strategy: Trend continuation + breakout
- Tools: EMA crossover, MACD, structure breaks
- Avoid: Mean reversion, counter-trend

**Ranging (ADX < 20):**
- Strategy: Mean reversion at S/R levels
- Tools: RSI oversold/overbought, Bollinger Bands
- Avoid: Breakout trading, trend following

**High Volatility (ATR > 3% of price):**
- Strategy: Reduce position size by 50%
- Tools: Wider SL (2x ATR), tighter TP (1.5x ATR)
- Avoid: Tight stops (will get wicked out)

**Low Volatility (ATR < 1% of price):**
- Strategy: Prepare for breakout
- Tools: Bollinger squeeze, volume accumulation
- Avoid: Range trading (breakout imminent)
