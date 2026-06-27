# Mona Futures Engine v2.0 — Reference

**Package:** `~/.hermes/scripts/mona_futures_v2/`
**CLI:** `mona_futures_v2_cli.py`
**Auto-trade:** `mona_futures_auto.py`
**Cron:** `every 5m` → alerts to 📈 Futures Trading (topic 387, chat -1003899936547)
**API Keys:** Optional for monitoring, required for trading. Store in `~/mona-workspace/vault/.binance_keys`

## Architecture (v2.0)

```
DataCollector (Binance + Bybit + OKX + Yahoo + Deribit + Alternative.me)
    ↓
SignalEngine (12 generators) + RegimeDetector + VPINCalculator
    ↓
RiskEngine (ATR-based sizing + adaptive trailing + circuit breakers + correlation limiter)
    ↓
ExecutionEngine (market/limit/stop + TWAP) + AutoTrader (paper/live modes)
    ↓
TelegramAlerts → 📈 Futures Trading topic
```

## 12 Signal Generators

| # | Signal | Data Source | Weight | Key Insight |
|---|--------|-----------|--------|-------------|
| 1 | OI Divergence | `/futures/data/openInterestHist` + klines | 15% | Price down + OI up = squeeze brewing |
| 2 | Funding Rate | `/fapi/v1/fundingRate` | 12% | > 0.05% = extreme crowding, reversal incoming |
| 3 | CVD | `/fapi/v1/aggTrades` (1000 trades) | 10% | Price up + CVD down = invisible selling |
| 4 | Taker Volume | `/futures/data/takerlongshortRatio` | 10% | > 65% buy = aggressive buying |
| 5 | Order Flow | `/fapi/v1/depth` (20 levels) | 10% | Bid/Ask imbalance > 2.0 = strong wall |
| 6 | Basis | `/fapi/v1/premiumIndex` | 5% | Mark vs Index gap > 0.15% = reversal |
| 7 | Structure | 1h klines (50 candles) | 8% | BOS (continuation) / CHoCH (reversal) |
| 8 | Volume Profile | 15m klines (96 candles) | 10% | POC + VWAP — price above/below value area |
| 9 | Fear & Greed | `api.alternative.me/fng` | 10% | Extreme Fear (≤15) = score 90, strong contrarian buy (was 5%, score 60) |
| 10 | DXY | Yahoo Finance (DX-Y.NYB) | 2% | DXY up = crypto down (often 0 on weekends) |
| 11 | Cross-Exchange Funding | Binance + Bybit + OKX | 3% | Spread > 0.03% = arbitrage opportunity |
| 12 | Liquidation Heatmap | `/fapi/v1/allForceOrders` | 5% | Squeeze zones — price hunts liquidation clusters |

## Market Regime Detection (ADX-based)

- **STRONG_TREND_UP:** ADX > 40, price > SMA20 → boost long signals 1.2x
- **TREND_UP:** ADX > 25, price > SMA20 → mild boost
- **RANGING:** ADX < 25 → reduce all signals 0.7x, SKIP TRADES
- **TREND_DOWN:** ADX > 25, price < SMA20 → boost short signals
- **HIGH_VOLATILITY:** ATR > 3% of price → reduce all signals 0.7x

**Critical:** When `skip_ranging_market = True`, Mona will NOT trade in ranging conditions. This prevents whipsaw losses.

## VPIN (Volume-Synchronized Probability of Informed Trading)

Detects informed vs uninformed flow. VPIN > 0.7 = toxic market → reduce signals by 0.6x.

```python
# Bucket trades into volume buckets
# VPIN = avg(|buy_vol - sell_vol|) / avg(total_vol) across buckets
# > 0.7 = high toxicity (informed traders dominating)
```

## High Leverage Position Sizing (CRITICAL)

**Formula (risk-based, leverage-independent):**
```python
risk_amount = balance * max_position_pct  # e.g., $50 * 0.04 = $2
stop_distance_pct = (atr * sl_atr_mult) / price  # e.g., 1.5%
size_usdt = risk_amount / stop_distance_pct  # e.g., $2 / 0.015 = $133
qty = size_usdt / price  # convert to base asset
```

**Key insight:** With high leverage, position size is automatically SMALLER because SL distance is tighter. The formula ensures dollar risk stays constant regardless of leverage.

**Example with $50 balance, 50x leverage:**
- Risk: $2 (4% of $50)
- SL distance: 1.5% (ATR-based)
- Position size: $2 / 0.015 = $133
- At 50x leverage, margin used: $133 / 50 = $2.66

## Dynamic Leverage

Leverage adjusts based on signal strength (updated June 2026):
- Signal score 50-60 → 20x (minimum)
- Signal score 60-70 → 20-35x (interpolation)
- Signal score 70+ → 50x (maximum)

```python
def calculate_dynamic_leverage(score, min_lev=20, max_lev=50, threshold=70):
    if score >= threshold:
        return max_lev
    elif score >= 60:
        ratio = (score - 60) / (threshold - 60)
        return int(min_lev + ratio * (max_lev - min_lev))
    else:
        return min_lev
```

## TP/SL Optimization for High Leverage

**SL:** ATR * 1.5 (tighter than low leverage — prevents large losses)
**TP1:** 1.0x risk → close 50% (lock profit fast)
**TP2:** 2.0x risk → close 30% (good profit)
**TP3:** 3.5x risk → close 20% (runner for big moves)

**Trailing Stop (Chandelier Exit):**
- Activates after TP1 hit
- Trail distance: ATR * 2.0
- Only moves in profit direction (never backward)

## Aggressive Settings for Small Accounts ($50)

```python
# Signal thresholds (SELECTIVE — calibrated June 2026)
min_score_to_trade = 35      # Lowered from 50 — signals rarely aggregate above 45
min_signals_agree = 3        # Lowered from 4 — 3 signals agreeing is solid enough

# Risk management
max_position_pct = 0.04      # 4% risk per trade ($2 on $50)
max_total_exposure = 0.12    # 12% max total ($6 on $50)
max_drawdown_pct = 0.10      # 10% daily drawdown → pause ($5)
default_leverage = 50        # 50x default
max_leverage = 75            # 75x max

# Trade limits
max_daily_trades = 8         # Max 8 trades/day
min_time_between_trades = 600  # 10 min cooldown

# Dynamic leverage
dynamic_lev_min = 25
dynamic_lev_max = 75
dynamic_lev_threshold = 80   # Score 80+ gets max leverage

# CRITICAL: Rate limiting (see pitfall below)
scan_interval_sec = 120      # 2 min between full scans (was 30s — caused IP ban)
balance_refresh_sec = 300    # 5 min between balance checks
symbol_delay_sec = 0.5       # 500ms between symbol analyses
```

**Proyeksi $10/hari dari $50:**
- Win rate 65%: 5.2 wins × $2.50 - 2.8 losses × $2.00 = $7.40/day
- Win rate 70%: 5.6 wins × $2.50 - 2.4 losses × $2.00 = $9.20/day
- Win rate 75%: 6.0 wins × $2.50 - 2.0 losses × $2.00 = $11.00/day

## Auto-Trade Execution Mode

**Paper trading (default for testing):**
```bash
python3 mona_futures_auto.py --mode paper --interval 30
```

**Live trading (real orders!):**
```bash
python3 mona_futures_auto.py --mode live --interval 30
```

**Auto-trade flow:**
1. Scan all symbols every 120 seconds (was 30s — caused IP ban)
2. Run 12 signal generators + regime detection + VPIN (with 0.5s delay between symbols)
3. Skip if: ranging market, toxic VPIN, adverse DXY, daily limit reached, cooldown active
4. Calculate dynamic leverage based on signal strength
5. Calculate position size (risk-based, ATR-adjusted, using cached live balance)
6. Execute: entry + SL + 3 TPs (50/30/20% partial closes)
7. Monitor positions for exit (TP/SL/trailing)
8. Send alerts to 📈 Futures Trading topic
9. Refresh live balance every 300 seconds (not every cycle)

**Paper trader features:**
- Simulates balance, positions, PnL
- Tracks win rate, total PnL, ROI
- No real orders placed
- Same logic as live mode

## Binance Futures API Endpoints

### Market Data (no auth needed)
- `GET /fapi/v1/klines` — Candlestick (symbol, interval, limit)
- `GET /fapi/v1/ticker/price` — Current price
- `GET /fapi/v1/depth` — Order book (symbol, limit)
- `GET /fapi/v1/aggTrades` — Aggregated trades (taker buy/sell via `m` field)

### Open Interest & Funding
- `GET /fapi/v1/openInterest` — Current OI
- `GET /futures/data/openInterestHist` — OI history
- `GET /fapi/v1/fundingRate` — Funding history
- `GET /fapi/v1/premiumIndex` — Mark/Index/Funding (all symbols)

### Volume & Flow
- `GET /futures/data/takerlongshortRatio` — Taker buy/sell ratio
- `GET /futures/data/topLongShortPositionRatio` — Top trader L/S ratio

### Execution (needs API key)
- `POST /fapi/v1/leverage` — Set leverage
- `POST /fapi/v1/order` — Place order (MARKET, LIMIT, STOP_MARKET, TAKE_PROFIT_MARKET)
- `DELETE /fapi/v1/allOpenOrders` — Cancel all orders
- `GET /fapi/v2/balance` — Account balance
- `GET /fapi/v2/positionRisk` — Open positions

### Cross-Exchange (for funding comparison)
- **Bybit:** `GET /v5/market/tickers?category=linear&symbol={SYMBOL}`
- **OKX:** `GET /api/v5/public/funding-rate?instId={SYMBOL}-USDT-SWAP`

## CLI Modes

```bash
# One-time scan (all 20 symbols)
python3 mona_futures_v2_cli.py scan --symbols BTCUSDT,ETHUSDT

# Continuous monitoring (blocking)
python3 mona_futures_v2_cli.py monitor --interval 30

# Full report with market overview
python3 mona_futures_v2_cli.py report

# Specific analysis
python3 mona_futures_v2_cli.py regime --symbols BTCUSDT    # Market regime
python3 mona_futures_v2_cli.py funding --symbols BTCUSDT   # Cross-exchange funding
python3 mona_futures_v2_cli.py maxpain --symbols BTCUSDT   # Max pain (options)
python3 mona_futures_v2_cli.py vpin --symbols BTCUSDT      # VPIN toxicity
python3 mona_futures_v2_cli.py feargreed                    # Fear & Greed index
```

## Pitfalls

- **numpy not needed** — all calculations are pure Python
- **aggTrades limit** — max 1000 per request. For deeper CVD, need WebSocket
- **Funding rate timing** — Binance funding every 8h (00:00, 08:00, 16:00 UTC). Between intervals, shows NEXT expected funding
- **aiohttp required** — not in system python. Use venv-mona
- **Cron `5m` vs `every 5m`** — `"5m"` = one-shot, `"every 5m"` = recurring forever
- **Cron script path** — MUST be filename only (e.g., `mona_futures_v2_cli.py report`), NOT absolute path
- **DXY from Yahoo Finance** — may return 0.00 on weekends/holidays when market is closed
- **VPIN calculation** — needs at least 1000 trades for accuracy. Low-volume symbols may show VPIN=0
- **Dynamic leverage** — Binance requires setting leverage BEFORE placing order. Always call `set_leverage` first
- **Position sizing with high leverage** — formula ensures dollar risk is constant, NOT percentage risk. A 50x leveraged position with 1.5% SL has the same dollar risk as a 5x position with 15% SL
- **Paper trade first** — ALWAYS run paper mode for at least 1 hour before going live. Verify signals, position sizing, and TP/SL logic work correctly
- **Max daily trades** — resets at midnight UTC. Track `daily_trades` counter and reset on new day
- **Cooldown after loss** — 5 min cooldown after SL hit prevents revenge trading
- **Correlation limiter** — prevents opening BTC + ETH simultaneously (correlation > 0.7). Only 1 correlated position allowed
- **Skip ranging market** — ADX < 25 = ranging. Don't trade, wait for trend
- **Skip toxic VPIN** — VPIN > 0.7 = informed traders dominating. Reduce or skip
- **Skip adverse DXY** — DXY up > 0.3% = crypto bearish. Reduce long signals
- **Binance IP BAN (CRITICAL)** — Exceeding rate limits triggers FULL IP BAN (~30 min), NOT HTTP 429. Response: `{'code': -1003, 'msg': 'Way too many requests; IP(xxx) banned until TIMESTAMP'}`. Safe settings: balance check 300s, scan 120s, 0.5s delay between symbols, ~20 API calls/cycle. See `crypto-futures-engine` skill `references/binance-rate-limiting.md` for full details.
- **Neutral signal dilution** — Composite score MUST only count active (non-zero) signals in weighted average. If all 12 weights are summed including neutral signals, FearGreed (score 90, weight 10%) contributes only 9 points — impossible to reach threshold. Fix: `if abs(s.score) > 0: total_weight += w`
- **Signal thresholds too conservative** — Default thresholds (OI ±0.5%/±2%, funding ±0.01%, taker 55%/45%) rarely trigger in normal market. Lowered to: OI ±0.1%/±0.5%, funding ±0.003%, taker 53%/47%, VolProfile ±0.3%/±0.2%. Without this, most signals return 0 (neutral) and composite stays near 0.
- **`_safe_div` doesn't protect inline arithmetic** — The `_safe_div(a, b)` wrapper only helps when explicitly used. Direct division like `1 / imbalance` in OrderFlow signal caused `ZeroDivisionError` when `imbalance = 0` (no bids). Fix: always add `and x > 0` guard before `1 / x` patterns. Pattern: `elif imbalance < 0.5 and imbalance > 0:`.
- **Missing alert methods for live mode** — When building paper/live dual-mode traders, BOTH modes need their own alert methods. The paper mode had `_alert_entry()` but live mode called `_alert_entry_live()` which didn't exist. Fix: always implement alert methods for ALL modes BEFORE first live run. Checklist: `_alert_entry`, `_alert_entry_live`, `_alert_exit`, `_alert_exit_live`.
- **Signal engine tuning — FearGreed as primary driver** — In extreme fear (F&G ≤ 15), FearGreed score should be 90 (was 60). This is the strongest contrarian signal and should have outsized weight. FearGreed weight increased to 10% (was 5%). Combined with active-only normalization, FearGreed at F&G=12 contributes ~9 points to composite — enough to push tradeable symbols over threshold when paired with 2-3 other bullish signals.
- **OrderFlow score cap** — OrderFlow imbalance can produce extreme scores (±60) that overwhelm other signals. Cap at ±50 for strong signals, ±25 for mild signals. This prevents orderbook noise from dominating composite.
- **Live balance caching** — Never fetch live balance every scan cycle. Cache it and refresh every 300 seconds. This alone cut API calls from ~100+/cycle to ~20/cycle and prevented IP bans.
- **Engine produces NO stdout output — by design.** `mona_futures_auto.py` sends ALL alerts to Telegram via `_send_telegram()`. When running as a background process (Hermes `terminal background=true` or systemd), expect zero stdout/stderr. This is normal — don't restart or kill the process thinking it's stuck. Verify it's running with `ps aux | grep mona_futures_auto`. To see engine activity, check Telegram topic 387 or the process CPU usage.
- **Operational restart workflow.** Standard sequence for restarting the futures engine: (1) `pkill -f mona_futures_auto.py` — kill old instance, (2) `python3 _check_positions.py` — verify balance + open positions, (3) `python3 -u mona_futures_auto.py --mode live --interval 120` — start fresh. Always check positions BEFORE starting — prevents accidentally running two engines or starting with stale state. Use `python -u` for unbuffered output (though engine sends to Telegram, not stdout).
- **Trade logged but NOT on Binance.** Engine may log `🔴 Live LONG WIFUSDT @ $0.15 | Size: $235.61 | Lev: 20x` but Binance shows 0 positions and 0 recent trades. This happens when: (1) `execute_full_trade()` returns a result without `'error'` key but the order was rejected (e.g., insufficient margin, precision error), OR (2) the order was placed and immediately liquidated/SL-hit before the position check runs. Debug: check `fapi/v1/userTrades` (trade history) AND `fapi/v1/allOrders` (order history, not just open orders) for the symbol. The engine logs the TRADE ATTEMPT, not the confirmed execution. Always verify on Binance after first live trade.
