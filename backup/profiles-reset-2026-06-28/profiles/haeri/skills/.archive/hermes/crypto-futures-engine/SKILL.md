---
name: crypto-futures-engine
description: Build and operate automated crypto futures/derivatives trading engines — signal generation, risk management, execution, and market intelligence. Covers Binance Futures, Bybit, OKX. Use when building trading bots, signal scanners, risk engines, or market analysis systems for perpetual futures.
triggers:
  - futures trading bot/engine/system
  - signal generator for crypto futures
  - risk management for leveraged trading
  - market regime detection
  - funding rate arbitrage/comparison
  - liquidation heatmap
  - VPIN / informed trading detection
  - ATR-based trailing stop / chandelier exit
  - circuit breaker for trading
  - TWAP/VWAP execution
  - max pain options
  - fear & greed index integration
  - cross-exchange funding rate
  - DXY crypto correlation
---

# Crypto Futures Engine

Build professional-grade futures trading engines with signal generation, risk management, and automated execution.

## Architecture Pattern

```
mona_futures_v2/
├── __init__.py          # Package exports
├── config.py            # All thresholds, weights, API keys
├── data.py              # DataCollector — all external API calls
├── signals.py           # SignalEngine — signal generators
├── risk.py              # RiskEngine + RegimeDetector + VPIN + CircuitBreaker + ExecutionEngine
└── engine.py            # MonaFuturesEngine — orchestrator + CLI
```

Plus CLI entry point: `mona_futures_v2_cli.py` (one-liner that imports and runs `engine.main()`).

## Reference Files
- `references/backtest-results.md` — 90-day backtest results with pair blacklist and signal weight optimization
- `references/binance-futures-api.md` — Binance Futures API endpoints
- `references/dexscreener-project-links.md` — Extract project links from DexScreener
- `references/external-apis.md` — External API sources
- `references/high-leverage-position-sizing.md` — Small account leverage strategy
- `references/deployer-detection-alchemy.md` — Find contract deployer via Alchemy
- `references/binance-rate-limiting.md` — API rate limits, IP ban behavior, safe settings
- `references/debank-social-profiles.md` — Extract Twitter/Telegram/Discord/GitHub from DeBank
- `references/telegram-html-sanitization.md` — Fix Telegram HTML parse errors
- `references/autonomous-agent-architecture.md` — Full autonomous agent: decision engine + execution sandbox + self-healing loop
- `references/autonomous-engine-v1.md` — Silent self-learning autonomous engine v1.0: startup sync, position monitoring, self-correction, trade journaling
- `references/binance-execution-patterns.md` — Order execution flow, error format, step sizes, silent failure detection
- `references/binance-algo-order-api.md` — Algo Order API for SL/TP (conditional orders moved from /fapi/v1/order)
- `references/balance-reserve-guard.md` — Balance reserve + max positions guard for small accounts
- `references/autonomous-position-monitor.md` — Real-time position monitor: auto-close on breakdown/max-loss, trailing stop, CVD confirmation
- `references/dual-mode-trading.md` — Scalper + Sniper dual-mode system: momentum scanner, auto-switch, production results
- `references/dozero-smc-integration.md` — DOZERO.X SMC Engine: multi-timeframe, virgin FVG, liquidity sweep, BOS/CHOCH, premium/discount, confluence scoring, integrated into autonomous engine v2.0
- `references/signal-formulas.md` — All 16 signal calculation formulas + 30-day backtest results (BTC +5.7%, SOL +10.2%, high-vol alts lose money)
- `references/trading-knowledge-base.md` — Comprehensive TA/FA/Sentiment reference: indicators, chart patterns, Wyckoff, on-chain metrics, macro, sentiment signals
- `references/trading-discipline-rules.md` — Hardcoded discipline rules: entry/exit/risk/psychology/alert rules (no exceptions)
- `references/price-level-monitor.md` — Price-level entry monitor: watch for retrace to FVG/OB zone, alert on confirmation
- `references/trading-discipline-rules.md` — Hardcoded trading discipline: entry/exit rules, risk management, psychology, user communication patterns. Non-negotiable rules for micro-account management.
- `references/data-integrity-rules.md` — NEVER fabricate trade/market data for real-money accounts. Always fetch from API or admit unavailability. Trust violation = user leaves.
- `references/rate-limiter-implementation.md` — Production rate limiter for DataCollector: 50 req/min, auto-wait, 418/429 backoff, symbol cap, alert discipline
- `references/hermes-update-procedure.md` — How to update Hermes Agent safely: backup, git pull, pip install, gateway restart, post-update troubleshooting (409 conflict, deps, stale PIDs).
- `references/autonomous-safety-rails.md` — 9 safety rails for autonomous trading: per-pair cooldown, flip prevention, hourly trade limit, max positions, minimum balance, balance refresh, SL/TP verification, breakeven update to Binance, emergency close. Use when building or debugging autonomous engines that were overtrading or missing SL/TP protection.

## Signal Generators (12 built)

### Tier 1 — Core (always implement)
1. **OI Divergence** — Price direction ≠ OI direction = squeeze/dump incoming
2. **Funding Rate** — Extreme funding = reversal signal (>0.05% = short, <-0.05% = long)
3. **CVD (Cumulative Volume Delta)** — Invisible buying/selling detection from agg trades
4. **Taker Volume** — Buy/sell ratio from taker data (>65% one side = aggressive)
5. **Order Flow** — Bid/ask wall imbalance from orderbook depth
6. **Basis/Premium** — Futures vs spot price gap
7. **Market Structure** — BOS (Break of Structure) / CHoCH (Change of Character) via swing highs/lows
8. **Volume Profile + VWAP** — POC (Point of Control) distance + VWAP deviation

### Tier 2 — Advanced (competitive edge)
9. **Fear & Greed** — Contrarian: Extreme Fear (<25) = long, Extreme Greed (>75) = short
10. **DXY Monitor** — Dollar strength inverse correlation with crypto
11. **Cross-Exchange Funding** — Compare Binance vs Bybit vs OKX funding rates
12. **Liquidation Heatmap** — Cluster analysis from recent liquidation data

### Tier 3 — Expert (optional, high value)
13. **VPIN** — Volume-Synchronized Probability of Informed Trading (>0.7 = toxic flow)
14. **Max Pain** — Options expiry magnet from Deribit data
15. **Social Sentiment** — NLP on Twitter/Telegram (requires API access)

## Risk Management Components

### Adaptive Trailing Stop (Chandelier Exit)
- Stop distance = ATR × multiplier (not fixed percentage)
- ATR adapts to volatility: wide in high vol, tight in low vol
- Only moves in favorable direction (never backwards)
- Activate after TP1 hit, tighten after TP2

```python
atr = calculate_atr(klines, period=14)
sl_distance = atr * 2.5          # initial SL
trail_distance = atr * 2.0       # tighter after TP1
```

### Market Regime Detection (ADX-based)
- ADX > 40 + direction = STRONG_TREND (boost signals in trend direction)
- ADX 25-40 = TREND (moderate boost)
- ADX < 25 = RANGING (reduce all signals)
- ATR% > 3% = HIGH_VOLATILITY (reduce signals 30%)

```python
adx = calculate_adx(klines, period=14)
if adx > 25:
    regime = TREND_UP if price > sma20 else TREND_DOWN
```

### Circuit Breakers (5 checks)
1. Daily drawdown > max (5%) → pause
2. Emergency drawdown > 10% → stop all
3. Max daily trades (10) → stop
4. Cooldown after loss (5 min) → wait
5. Spread > max (0.5%) or abnormal (3x) → block
6. API latency > 2s → block

### Position Correlation Limiter
- Hardcoded correlation matrix (update quarterly from historical data)
- Max 2 positions with correlation > 0.7
- Block if new position correlates > 0.85 with existing
- Default correlation for unknown pairs: 0.3

### VPIN (Toxicity Detection)
- Bucket trades into groups (50 trades/bucket)
- VPIN = avg(|buy-sell|) / avg(total) across buckets
- VPIN > 0.7 = high toxicity → reduce signal by 40%
- VPIN > 0.4 = medium → reduce by 20%

## Execution Patterns

### Multi-TP with Partial Closes
```
TP1 = entry ± (SL_distance × 1.5)  → close 50%, activate trailing
TP2 = entry ± (SL_distance × 2.5)  → close 30%
TP3 = entry ± (SL_distance × 4.0)  → close 20% (runner)
```

### TWAP Execution
Split large orders into N slices with time delay to minimize market impact:
```python
await execution.twap_order(symbol, side, total_qty, slices=5, interval_sec=10)
```

## Free API Sources (No Auth Required)

| Source | Endpoint | Data |
|--------|----------|------|
| Binance Futures | fapi.binance.com | Klines, OI, Funding, AggTrades, Liquidations, Taker Volume |
| Bybit V5 | api.bybit.com/v5 | Funding rate, tickers |
| OKX | okx.com/api/v5 | Funding rate (format: BTC-USDT-SWAP) |
| Alternative.me | api.alternative.me/fng | Fear & Greed Index (7-day history) |
| Deribit | deribit.com/api/v2 | Options book summary (for max pain) |
| Yahoo Finance | query1.finance.yahoo.com/v8 | DXY, S&P500, NASDAQ, Gold, US10Y |

## Binance API Key Setup

1. Binance → Profile → API Management → Create API
2. Select **"Dihasilkan oleh sistem"** (HMAC, NOT Ed25519)
3. Label: descriptive name
4. **IP Restriction**: add VPS IP (required for Futures permission)
5. Enable permissions:
   - ✅ Enable Reading
   - ✅ Enable Futures
   - ❌ NEVER enable Withdrawal
6. Store in `vault/.binance_keys`:
```
API_KEY=your_key
API_SECRET=your_secret
```

### Mobile App Flow (Indonesian)
User will see screens in Indonesian. Key translations:
- "Dihasilkan oleh sistem" = System-generated (HMAC) — SELECT THIS
- "Dihasilkan sendiri" = Self-generated (Ed25519/RSA) — DON'T SELECT
- "Batasan API" = API Restrictions
- "Aktifkan Futures" = Enable Futures — MUST CHECK THIS
- "Batasi akses hanya ke IP tepercaya" = Restrict to trusted IPs — SELECT THIS
- "Tidak dibatasi (Kurang Aman)" = Unrestricted (Less Secure) — DON'T SELECT

**Gotcha:** "Aktifkan Futures" checkbox is DISABLED until IP address is entered first. User must:
1. Enter VPS IP in the IP field
2. Press Confirm/Save
3. THEN check "Aktifkan Futures"

**Security:** User will receive API Key + Secret Key. Instruct to send via Telegram DM only (not group), and delete the message immediately after Mona saves it to vault.

## Telegram Forum Topic Creation

Bot needs admin with **"Manage Topics"** permission:
```python
import requests
resp = requests.post(
    f'https://api.telegram.org/bot{token}/createForumTopic',
    json={'chat_id': chat_id, 'name': '📈 Futures Trading', 'icon_color': 0x6FB9F0}
)
topic_id = resp.json()['result']['message_thread_id']
```

## Composite Scoring

Weighted average of **active (non-neutral) signals only**, normalized to -100..+100:
- Score > 40 = STRONG_LONG
- Score > 15 = LONG
- Score < -40 = STRONG_SHORT
- Score < -15 = SHORT
- |Score| ≥ 40 + min 3 signals agreeing = TRADEABLE

**CRITICAL: Active-signal-only normalization**
```python
# WRONG — dilutes strong signals with zeros:
for s in signals:
    weighted_score += s.score * (w / 100)
    total_weight += w

# RIGHT — only count signals that actually fired:
for s in signals:
    if abs(s.score) > 0:
        weighted_score += s.score * (w / 100)
        total_weight += w
composite = (weighted_score / total_weight * 100) if total_weight > 0 else 0
```

Without this, FearGreed (score 90, weight 10%) contributes only 9 points when 8 other signals are neutral — impossible to reach threshold.

Regime adjustment:
- Trending with signal = ×1.2 boost
- Trending against signal = ×0.8 reduce
- High volatility = ×0.7 reduce
- VPIN toxic = ×0.6 reduce

### Signal Threshold Calibration Guide

Don't guess min_score_to_trade — calibrate it from real data:

1. **Run paper mode 24h** — Log all composite scores per scan cycle
2. **Collect score distribution** — Bin scores into ranges (0-10, 10-20, ..., 90-100)
3. **Identify tradeable range** — Look at scores where signals actually align (3+ non-zero)
4. **Set threshold at P25** — 25th percentile of the tradeable distribution
5. **Backtest** — Simulate trades at that threshold, check win rate > 55%

**Real-world reference (20 USDT pairs, 12 signals):**
- Score 0-15: Most scans (60%) — 0-1 signals firing, noise
- Score 15-30: Common (25%) — 1-2 signals, weak alignment
- Score 30-45: Uncommon (12%) — 3-4 signals, moderate alignment ← **sweet spot**
- Score 45-60: Rare (3%) — 4-5 signals, strong alignment
- Score 60+: Very rare (<1%) — 6+ signals, exceptional setup

**Recommended thresholds by market condition:**
- Normal market: min_score=35, min_signals=3
- High volatility: min_score=40, min_signals=3 (be more selective)
- Low volatility/ranging: min_score=30, min_signals=2 (or skip entirely)

## Small Account Optimization ($50-100)

### User Preference: High Leverage + Small Margin
User explicitly wants: **lev 35-50x, margin ~10% of balance**. NOT low leverage with large margin.

```
❌ WRONG: Lev 10x, margin $33 (62% of $53) → user: "woi yang bener aja margin 33$"
✅ RIGHT: Lev 35x, margin $5 (10% of $53)  → same risk, 3.5× better ROI
```

### Margin Cap (CRITICAL)
With small accounts, the standard risk formula produces positions too large for available margin:

```
risk $4 / SL% 0.4% = $1,000 position → needs $50 margin at 20x → INSUFFICIENT
```

**Fix: Cap at 85% of max notional:**
```python
max_notional = balance * leverage * 0.85  # leave 15% buffer
size_usdt = min(risk_based_size, max_notional)
margin = size_usdt / leverage  # target: 8-10% of balance
```

### Dynamic Leverage by Score
```python
if score >= 85: leverage = 50   # elite signals
elif score >= 70: leverage = 40
elif score >= 50: leverage = 35  # minimum tradeable
else: skip  # below threshold, don't enter
```

### Risk Communication: Absolute Dollars
User prefers dollar amounts, NOT percentages:
```
✅ "Risk: $4.01"
❌ "Risk: 7.5% of $55.37"
```

```
Leverage  | Position Size | SL Distance | Risk ($1)
----------|---------------|-------------|----------
5x        | $10           | 2%          | $1
25x       | $2            | 2%          | $1
50x       | $1            | 2%          | $1
75x       | $0.67         | 2%          | $1
```

**Formula:** `size_usdt = risk_amount / stop_distance_pct`

Where:
- `risk_amount = balance * max_position_pct` (e.g., $50 * 0.03 = $1.50)
- `stop_distance_pct = (atr * sl_atr_mult) / price` (e.g., 1.5%)

### Dynamic Leverage (Signal Strength Based)
Strong signals get higher leverage, weak signals get lower:

```python
def calculate_dynamic_leverage(score, min_lev=25, max_lev=50, threshold=80):
    if score >= threshold:
        return max_lev
    elif score >= 70:
        ratio = (score - 65) / (threshold - 65)
        return int(min_lev + ratio * (max_lev - min_lev))
    else:
        return min_lev
```

### Balanced $10/Day Target Settings (Aggressive)
For $50-55 balance with 50x leverage:

```python
# Config
max_position_pct = 0.04        # 4% risk ($2)
max_total_exposure = 0.12      # 12% max ($6)
max_drawdown_pct = 0.10        # 10% pause ($5)
default_leverage = 50
max_leverage = 75
max_daily_trades = 8
min_time_between_trades_sec = 600  # 10 min cooldown
min_score_to_trade = 35        # 50+ was too high — signals rarely aggregate above 45 (see pitfall #38+45)
min_signals_agree = 3           # 4+ was too strict — 3 is realistic for 12-signal ensemble

# TP/SL
sl_atr_mult = 1.5              # Tight SL
tp1_risk_reward = 1.0          # TP1 = 1x risk
tp2_risk_reward = 2.0          # TP2 = 2x risk
tp3_risk_reward = 3.5          # TP3 = 3.5x risk
tp1_close_pct = 0.50           # Close 50% at TP1
tp2_close_pct = 0.30           # Close 30% at TP2
tp3_close_pct = 0.20           # Close 20% at TP3
```

**Signal Weights (optimized):**
```python
weight_oi_divergence = 15
weight_funding_rate = 12
weight_cvd = 10
weight_taker_volume = 10
weight_order_flow = 10
weight_basis = 5
weight_structure = 8
weight_volume_profile = 10
weight_fear_greed = 10          # Increased from 5 — reliable contrarian
weight_dxy = 2                  # Often 0 (weekends), reduce weight
weight_cross_exchange_funding = 3
weight_liquidation = 5
```

### Selective Entry Rules (Don't Overtrade)
- Min score: 40 (not 60 or 70 — too conservative with 12 signals)
- Min signals agree: 3/12 (not 5 or 6 — need realistic threshold)
- Skip ranging market (ADX < 25)
- Skip toxic VPIN (> 0.7)
- Skip adverse DXY movement
- Max 8 trades/day
- 10 min cooldown between trades

### Balance Reserve Guard (Small Account Protection)
With small accounts ($50-55), deploying 100% of balance is dangerous. Always keep a reserve:

```python
balance_reserve_pct = 0.20  # Always keep 20% free ($11 on $55)
max_simultaneous_positions = 3  # Hard cap on concurrent positions
```

**Implementation in `analyze_and_trade()`:**
```python
# 1. Count active positions from Binance API
acc = await signed_get('/fapi/v2/account')
active_positions = len([p for p in acc['positions'] if float(p.get('positionAmt', 0)) != 0])
available = float(acc.get('availableBalance', 0))

# 2. Max positions guard
if active_positions >= config.max_simultaneous_positions:
    log.info(f"Max positions reached ({active_positions}/{config.max_simultaneous_positions})")
    return

# 3. Balance reserve guard
reserve = total_balance * config.balance_reserve_pct
if available < reserve:
    log.info(f"Balance reserve guard: available ${available:.2f} < reserve ${reserve:.2f}")
    return

# 4. Position sizing uses USABLE balance (after reserve)
usable_balance = total_balance - reserve
risk_amount = usable_balance * config.max_position_pct
```

**Why this matters:** Without the reserve, 4 positions can deploy $53 of $54 balance, leaving $0.48 available. If a strong signal appears, the engine can't enter. The reserve ensures there's always capital for high-conviction setups. The max positions cap prevents over-correlation (all LONG = no hedge).

## Auto-Trade Execution Mode

### Paper → Live Workflow
1. **Paper trade first** — Simulate 1-24 hours without real money
2. **Check win rate** — Must be > 60% before going live
3. **Code changes** — Fix hardcoded balance, add `_refresh_live_balance()`, update `get_report()` for live mode (see references/auto-trade-execution.md Step 3)
4. **Kill paper process** — `ps aux | grep mona_futures` → `kill <PID>`
5. **Start live** — `terminal(command=..., background=True, notify_on_complete=True)` (NOT nohup)
6. **Clean cron jobs** — Remove paper one-shot crons, update recurring scanner
7. **Set rate limits** — Balance check 300s, scan interval 120s, 0.5s delay between symbols (see references/binance-rate-limiting.md)
8. **Monitor first hour** — Check balance refresh in logs, verify position sizes, watch for IP ban warnings

### References

- `references/engine-v2-session-learnings.md` — SMC integration, pre-filter scanning, leverage sizing, entry consistency, config pitfalls, DXY fallback
- `references/live-trading-day1-learnings.md` — Real-money mistakes: position churn ($1.68), limit-at-market ($0.26), trade history, config fixes applied

## File Structure
```
mona_futures_auto.py — Auto-trade engine (paper + live modes)
├── PaperTrader class — Simulates trades, tracks PnL
├── AutoTrader class — Main engine with signal analysis
├── monitor_loop() — Continuous scanning + execution
└── get_report() — Generate trading statistics
```

### Alert Format (Paper vs Live)
Paper trades prefix with "PAPER TRADE" to distinguish from live.
Live trades use same format but without "PAPER" prefix.

## Autonomous Agent (Level Up)

Beyond the signal engine, build a full autonomous agent that makes decisions and executes trades without user input. See `references/autonomous-agent-architecture.md` for full details.

For the production silent self-learning engine, see `references/autonomous-engine-v1.md` — this is the recommended architecture for ongoing autonomous operation.

**Components:**
1. **Decision Engine** — Multi-signal scoring + confidence-based execution
2. **Execution Sandbox** — Safe TX with limits ($25/trade, $100/day)
3. **Self-Healing Loop** — Auto-restart on crash, error alerts to Telegram

**Key difference from futures engine:**
- Futures engine = generates signals and executes based on thresholds
- Autonomous agent = makes decisions (BUY/SELL/WATCH) with reasoning, learns from outcomes

## Multi-Position & Dual-Mode Trading
See `references/multi-position-and-dual-mode.md` for signal comparison, trimming rules, and scalper/sniper auto-switch logic.

Switch cooldown: 10 minutes minimum between mode changes to prevent oscillation.

### State Initialization
```python
# In AutonomousEngine.__init__():
self._active_mode = 'sniper'  # 'scalper' or 'sniper'
self._mode_switch_ts = 0
self._consecutive_empty_scans = 0  # Track empty sniper scans for auto-switch
```

### Momentum Scanner Architecture
```python
class MomentumScanner:
    def scan(self) -> List[MomentumCandidate]:
        # 1. Fetch ALL tickers in ONE call (cache 30s)
        tickers = self._fetch_all_tickers()  # GET /fapi/v1/ticker/24hr
        
        # 2. Filter: volume > $5M, change > 1.5%
        candidates = filter_by_volume_and_change(tickers)
        
        # 3. Sort by absolute change, take top 15
        top = sorted(candidates, key=abs_change)[:15]
        
        # 4. Quick TA on each (RSI + EMA from klines)
        results = [analyze(c) for c in top if c.momentum_score >= 50]
        
        return sorted(results, key=momentum_score, reverse=True)
```

### Telegram Alert Format
Scalper trades show mode indicator:
```
⚡ TRADE OPENED [SCALPER]
━━━━━━━━━━━━━━━
Pair: BLESSUSDT
Side: LONG
Entry: 0.005991
...
```
Sniper trades use 🎯 icon instead.

## References Updated (2026-06-07)
## References

- `references/dozero-x-comparison.md` — Gap analysis vs Dozero.x SMC system, improvement roadmap
- `references/pitfalls-and-lessons.md` — Critical bugs, signal quality issues, best practices
- `references/trading-knowledge-base.md` — Technical, fundamental, sentiment analysis knowledge base
- `references/price-level-monitor.md` — Price-level entry monitor for retrace setups (VIRTUALUSDT pattern)

## Pitfalls

- **Duplicate config fields.** Python dataclasses don't error on duplicate field names — the second silently overwrites the first. Always grep for duplicates after editing: `grep -n 'field_name' config.py`. Known case: `max_daily_trades` defined twice (5 and 4) in `mona_futures_v2/config.py`.
- **Sync calls in async context.** `urllib.request.urlopen()` blocks the event loop. In async engines, ALL HTTP calls must use `aiohttp`. Known case: `_round_qty()` and `_round_price()` used sync urllib, freezing the engine during order placement. Fix: `async def` + `aiohttp` + per-symbol caching.
- **Patch tool creates nested classes.** When using the `patch` tool to insert methods into a Python class, it can create `class Foo:\n    class Foo:\n        ...` (nested). Fix: use `execute_code` with Python string replacement instead of the patch tool for complex class insertions.
- **Breakeven SL after TP1 (CRITICAL).** Without moving SL to entry after TP1 hits, profits evaporate on retracement. Pattern: `pos.sl_price = max(pos.sl_price, pos.entry_price + atr * 0.1)` for LONG. Activate BEFORE enabling trailing stop.
- **SL/TP retry logic.** Binance algo order API can return transient errors. Always retry 3x with exponential backoff. Treat `-4130` (already exists) and `-4028` (duplicate) as SUCCESS (position is protected).
- **Balance must be synced, not hardcoded.** Auto-traders that hardcode initial balance ($55.5) drift from reality. Sync from Binance API each cycle: `balance = await self.execution.get_balance()`.
- **Position reconciliation on startup.** After engine restart, local state may be stale. Query Binance positions on startup and log them. Clean up stale local positions that don't exist on Binance.
- **DXY from Yahoo Finance is unreliable.** Yahoo Finance frequently returns 429 for DXY quotes. Add CoinGecko fallback: `https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=usd&include_24hr_change=true`. Last resort: Binance BTCUSDT 24hr ticker as rough proxy.
- **Safety rail test ordering.** Per-pair cooldown (300s) fires BEFORE flip prevention (600s). To test flip prevention, use fresh RiskEngine with `_pair_last_trade[sym]` set to 700s ago.
- **SMC threshold 50.** Most scans return score=0. Expected — SMC only fires on strong multi-confluence setups.
- **Method naming in tests.** Always verify method names match implementation. Known: `dxy_signal()` vs `dxy()`.
- **User: autonomous execution.** "Kamu atur sendiri" — execute standard fixes without asking, report results. No fabrication.
- **NEVER place limit at market price.** A limit order at market fills instantly like a market order but charges TAKER fee (0.04%) instead of MAKER (0.02%). Always offset from market: use 0.3% ATR offset, or place at best_bid (LONG) / best_ask (SHORT) from orderbook. If limit doesn't fill in 60s, cancel and wait for next scan. The $0.26 lesson.
- **NEVER open-close-reopen positions.** If position size is wrong, DO NOT close and re-enter. Adjust SL/TP on existing position or wait for natural SL/TP exit. Opening-closing-reopening costs 2× taker fee + 2× spread = pure waste. The $1.68 lesson.
- **Don't apologize repeatedly.** User hates excuses. Acknowledge mistake ONCE briefly, fix immediately, move on. User: "lu enak tinggal minta maaf masalah nya gak mungkin kamu bisa ngasih aku duit" — they want results, not remorse.
- **Pre-flight test suite.** `python3 mona_preflight_test.py` before live. Details: `references/pre-flight-test-suite.md`.

## References

- `references/engine-fixes-june2026.md` — Full code fixes applied to mona_futures_v2/: safety rails, async rounding, breakeven SL, retry logic, balance sync, position reconciliation.
- `references/trading-knowledge-base.md` — Comprehensive TA/FA/Sentiment analysis reference: indicators, chart patterns, SMC, Wyckoff, on-chain metrics, macro factors, sentiment signals, best strategies for automated trading.

1. **numpy not needed** — All calculations work with pure Python (lists, sum, max, min). Don't import numpy unless actually using array operations.
2. **Cron script path** — `cronjob(script=...)` expects relative filename (e.g., `mona_futures_v2_cli.py`), NOT absolute path.
3. **@property syntax** — Always include `def` keyword: `@property\ndef method_name(self):` not `@property\nmethod_name(self):`.
4. **startswith() quotes** — `line.startswith('API_KEY=')` not `line.startswith('API_KEY=***`. The `=` must be followed by closing quote.
5. **Telegram Bot permissions** — Bot must be admin with "Manage Topics" enabled, not just regular admin.
6. **OKX symbol format** — Uses `BTC-USDT-SWAP` not `BTCUSDT`. Convert: `symbol.replace('USDT', '-USDT-SWAP')`.
7. **Yahoo Finance** — Market data may show 0 during market close hours (weekends). DXY/S&P only available during trading hours.
8. **API rate limits** — Binance: 1200 req/min theoretical, but ACTUAL LIMIT is much lower for Futures endpoints. Exceeding triggers a FULL IP BAN (not 429). See pitfall #42 for exact settings and ban behavior.
9. **VPIN bucket size** — Too small = noisy, too large = delayed. 50 trades/bucket is good default for 1000-trade window.
10. **ATR period** — 14 is standard. Lower (7) for scalping, higher (20) for swing. ATR multiplier 2.5 for SL, 2.0 for trailing.
11. **Module-level asyncio.run()** — If the CLI script has `asyncio.run(main())` at module level AND the package is imported elsewhere (e.g., by the watcher), it will execute on import. Guard with `if __name__ == '__main__':` or put the CLI entry point in a separate file.
12. **Cron no_agent scripts** — For script-only cron jobs (`no_agent: true`), the `script` parameter is treated as a RELATIVE FILENAME under `~/.hermes/scripts/`, NOT a shell command. If you need `cd ... && python3 ...`, create a wrapper `.sh` file:
    ```bash
    #!/bin/bash
    cd ~/.hermes/scripts && python3 mona_futures_v2_cli.py report 2>&1
    ```
    Save as `mona_futures_report.sh`, `chmod +x`, then reference it as `script='mona_futures_report.sh'`. Without this, the entire string `cd ~/.hermes/scripts && python3 ...` gets treated as a filename → "Script not found".
13. **DXY zero on weekends** — Yahoo Finance returns 0 for DXY/S&P during market close. Handle gracefully — don't treat 0 as a signal.
14. **`startswith()` quote gotcha** — `line.startswith('API_KEY=*** must end the string literal after the `=`. Don't bake the actual value into the startswith check. Always: `if line.startswith('API_KEY='):` then `line.split('=', 1)[1].strip()`.
15. **Indonesian Binance UI** — "Aktifkan Futures" checkbox is greyed out until IP is entered. Step 1: Enter IP, Step 2: Save, Step 3: THEN check the box. User will see Indonesian labels — guide them through it.
16. **API key security** — User will send API keys via Telegram. Instruct to DELETE the message immediately after Mona saves to vault. Never echo keys back. Store in `vault/.binance_keys` with `chmod 600`.
17. **Futures balance check** — After API key setup, always verify balance with `get_balance()`. If 0 USDT, instruct user to transfer from Spot to Futures wallet in Binance app.
18. **Multiple watcher processes** — When restarting watcher, ALWAYS kill ALL related processes first with `pkill -9 -f "mona_smart_money_watcher"`. Running multiple instances causes duplicate alerts and wasted API calls.
19. **Liquidity filter** — Always add `MIN_LIQUIDITY = 1000` ($1K minimum). Tokens with $0 liquidity are untradeable dust. Check `liquidity_usd` from DexScreener before alerting.
20. **Never hardcode DEX links** — Don't use `aerodrome.finance/swap?...`. Extract project links from DexScreener `info.websites` and `info.socials`. Each token has different DEX.
21. **Social platform separation** — When displaying wallet social profiles, ALWAYS label each platform: 🐦 Twitter (→twitter.com), 📱 Telegram (→t.me), 💬 Discord (plain text), 🐙 GitHub (→github.com). NEVER mix handles across platforms.
22. **Deployer lookup rate limiting** — Binary search uses ~20-30 API calls per contract. Add 200ms delay between calls, cache results for 1 hour, limit scan range to 200 blocks max, and handle 429 with 2s backoff.
23. **Telegram message truncation** — Telegram limit is 4096 chars. Truncate to 4000 + `<i>(truncated)</i>` notice. Long alerts with social context can easily exceed this.
24. **HTML sanitization** — Always sanitize HTML before sending to Telegram. Count open/close tags, escape stray `&` and `<`. See references/telegram-html-sanitization.md.
25. **Small account leverage** — With $50 balance, use 25-50x leverage (not 3x). Position size MUST be smaller with higher leverage: `size = risk_amount / SL_distance`. See references/high-leverage-position-sizing.md.
26. **Dynamic leverage** — Don't use fixed leverage for all trades. Strong signals (score > 80) get 50x, weak signals (65-75) get 25x. This optimizes risk/reward.
27. **Quick profit TP levels** — For high leverage, use tighter TP levels: TP1 = 1.2x risk (not 1.5x), TP2 = 2x (not 2.5x), TP3 = 3x (not 4x). Close more at TP1 (55%, not 50%).
28. **Paper before live** — ALWAYS run paper trade mode first (1-24 hours). Check win rate > 60% before switching to live. Same code, just `--mode paper` vs `--mode live`.
29. **Selective entry** — Don't enter constantly, but don't be TOO conservative either. After real-world calibration: min_score=35, min_signals=3, skip ranging market (ADX<25), skip toxic VPIN (>0.7), 15 min cooldown, max 5-6 trades/day. Earlier versions used min_score=65 + min 5 signals which produced ZERO trades — signals rarely aggregate that high.
30. **Multiple process cleanup** — When restarting ANY background process, ALWAYS `pkill -9 -f "process_name"` first. Running duplicates cause wasted API calls and duplicate alerts.
31. **Indonesian user communication** — User prefers casual Indonesian slang ("sayang", "bro", "gas"). Don't use formal language. Match their energy.
32. **Don't ask too many questions** — User prefers when Mona sets things up optimally herself. Only ask for critical decisions (leverage level, risk tolerance). For everything else, use best judgment.
33. **Hardcoded balance pitfall** — When switching paper→live, the fallback `50 * config.max_position_pct` is WRONG. Must use `_live_balance` cache refreshed from Binance API each cycle. Position sizing depends on actual available balance, not estimate.
34. **Hermes background process** — `nohup ... &` is REJECTED by Hermes terminal tool. Use `terminal(command=..., background=True, notify_on_complete=True)` so Hermes can track the process lifecycle.
35. **Paper→Live cron cleanup** — One-shot paper trade cron jobs (status check, switch trigger) must be explicitly `cronjob(action='remove')` before starting live. Don't leave orphaned cron jobs.
36. **Binance balance via REST (no SDK)** — Can check balance with `hmac.new(secret, query, sha256)` + `aiohttp` GET to `/fapi/v2/account`. No need for `python-binance` SDK. Works in `asyncio` context.
37. **Live report format** — Live mode `get_report()` must NOT reference `self.paper` (it's None). Use `self._live_balance` instead. Template the report for live mode separately.
38. **Signal calibration (CRITICAL)** — Default thresholds are TOO CONSERVATIVE. In normal market conditions, most signals return 0 (neutral), making composite impossibly low. MUST lower thresholds:
    - OI Divergence: trigger at ±0.1%/±0.5% (not ±0.5%/±2%)
    - Funding Rate: trigger at ±0.003% (not ±0.01%)
    - Taker Volume: trigger at 53%/47% (not 55%/45%)
    - VolProfile: trigger at ±0.3%/±0.2% (not ±0.5%/±0.3%)
    - FearGreed: score 90 for extreme fear ≤15 (not 60 for ≤25)
    - OrderFlow: cap at ±50 (not ±60) to prevent overwhelming other signals
39. **Neutral signal dilution** — If composite formula divides by total_weight of ALL signals (including neutral ones with score=0), strong signals get diluted to nothing. Fix: only sum weights of active (non-zero) signals. See Composite Scoring section above.
40. **FearGreed weight** — Increase to 10% (from 5%). It's the most reliable contrarian indicator, especially in extreme fear (≤15) which historically leads to bounces. Don't let OrderFlow (real-time) overwhelm it.
41. **User: "atur strategi mu aja"** — User wants Mona to take FULL control of strategy decisions. Don't ask for confirmation on signal thresholds, weight adjustments, or entry rules. Just set it up optimally and report results. Only ask for critical decisions: funding the wallet, leverage level changes, or stopping the bot.
42. **Binance IP BAN (CRITICAL)** — Binance does NOT return HTTP 429 on rate limit. It returns `{'code': -1003, 'msg': 'Way too many requests; IP(xxx) banned until TIMESTAMP'}` with an IP BAN lasting ~30 minutes. Timestamp is milliseconds. To avoid this, use these EXACT settings:
    - Balance check: every 300s (5 min), NOT every cycle
    - Scan interval: 120s (2 min), NOT 30s
    - Delay between symbol analysis: 0.5s minimum
    - Total API calls per cycle: aim for ~20 (was 100+ before ban)
    - Cache aggressively: klines TTL 60s, price TTL 5s, OI TTL 30s
    Implementation: track `last_balance_check` timestamp, only refresh if `now - last > 300`. Add `await asyncio.sleep(0.5)` between symbol loops. If ban happens, kill engine, wait for expiry, restart with reduced frequency.
43. **OrderFlow division by zero** — `1 / imbalance` raises `ZeroDivisionError` when `imbalance = 0` (happens when `bid_total = 0`). The `_safe_div` function handles `bid_total / ask_total` but NOT the subsequent `1 / imbalance` calculation. Fix: add `and imbalance > 0` guard to all `1 / imbalance` branches:
    ```python
    # WRONG:
    elif imbalance < 0.5:
        score = -min(50, (1 / imbalance - 1) * 15)
    # RIGHT:
    elif imbalance < 0.5 and imbalance > 0:
        score = -min(50, (1 / imbalance - 1) * 15)
    ```
    Apply to both `< 0.5` and `< 0.77` branches.
44. **Missing `_alert_entry_live` method** — When switching paper→live, the `AutoTrader` class calls `self._alert_entry_live()` after executing a live trade, but this method doesn't exist (only `_alert_entry` for paper mode). This causes `AttributeError: 'AutoTrader' object has no attribute '_alert_entry_live'` AFTER the trade is already executed (trade goes through, alert fails). Fix: add `_alert_entry_live` method that formats live trade alerts (without PAPER prefix, with balance from `self._live_balance`).
45. **Aggregate score ceiling (CRITICAL)** — Even with active-signal-only normalization (pitfall #39), the practical composite score in normal market conditions rarely exceeds 40-45. Why: typically only 3-4 out of 12 signals fire per symbol per scan. FearGreed at 90 * 10% weight = 9 points. One or two other signals at 60-80 * 10% weight = 6-8 each. Total: ~25-35. Setting `min_score_to_trade = 50` produces ZERO trades. After real-world calibration on 20 USDT pairs:
    - **min_score_to_trade = 35** — sweet spot. Allows entry when 3-4 signals align at moderate strength.
    - **min_signals_agree = 3** — out of 12 signals, 3 agreeing is meaningful. 4+ is too rare.
    - If you want stricter: use 40/3 instead of 50/4. Never go above 45 unless you add more signal sources or increase individual weights.
    - Monitor actual signal distribution: run engine in paper mode for 24h, log all composite scores, then set threshold at P25 (25th percentile of tradeable scores).
46. **Binance error key mismatch (CRITICAL)** — Binance API returns errors as `{'code': -1102, 'msg': 'Mandatory parameter missing'}` and success as `{'orderId': 12345, 'status': 'FILLED', ...}`. The error key is `'code'`, NOT `'error'`. Checking `'error' not in result` ALWAYS passes on both success AND failure because Binance never uses the `'error'` key. This causes the engine to log "Live LONG" and count the trade even when the order was rejected. Fix in `execute_full_trade()`:
    ```python
    # WRONG — Binance never returns 'error' key:
    if 'error' not in results['entry']:
        # assumes success — WRONG
    
    # RIGHT — check for orderId (success) instead:
    if 'orderId' not in results['entry']:
        error_code = results['entry'].get('code', 'unknown')
        error_msg = results['entry'].get('msg', 'Unknown error')
        results['error'] = f'Binance error {error_code}: {error_msg}'
        return results
    ```
    Also add error logging in the caller:
    ```python
    if 'error' not in result:
        # success path
    else:
        log.error(f"❌ Trade FAILED {side} {symbol}: {result.get('error', result)}")
    ```
    Without this fix, the engine silently "succeeds" on every rejected order — no positions open, no error logs, balance unchanged, but daily_trades counter increments and cooldown activates.
48. **HMAC Signature Invalid for POST (-1022)** — Binance returns `{"code": -1022, "msg": "Signature for this request is not valid"}` on POST requests but NOT on GET requests, even when using the same `_sign()` method. Root cause: aiohttp's `params=` parameter URL-encodes values differently from the raw query string used for HMAC signing. GET works because aiohttp's encoding happens to match; POST fails because the encoding diverges. **Fix:** In `_sign()`, convert ALL param values to strings first. In `_post()`, build query string manually with `urlencode(sorted(params.items()))` and append to URL directly — do NOT use aiohttp's `params=` or `data=`:
    ```python
    def _sign(self, params: dict) -> dict:
        params['timestamp'] = str(int(time.time() * 1000))
        for k in list(params.keys()):
            params[k] = str(params[k])  # ALL values must be strings
        query = '&'.join(f'{k}={params[k]}' for k in sorted(params.keys()))
        sig = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        params['signature'] = sig
        return params

    async def _post(self, endpoint: str, params: dict) -> dict:
        await self._ensure_session()
        params = self._sign(params)
        query_string = urlencode(sorted(params.items()))
        url = f'https://fapi.binance.com{endpoint}?{query_string}'
        async with self.session.post(url) as resp:  # NO params= or data=
            return await resp.json()
    ```
    **Verification:** Test signing with a simple script that compares manual query string vs `urlencode(sorted(...))` — they must match. Then test actual API call with a small order (expect `-4164 notional too small` = signing works, just qty too small for test).
50. **Binance Algo Order API for conditional orders (CRITICAL)** — As of 2025/2026, Binance moved ALL conditional order types (STOP_MARKET, TAKE_PROFIT_MARKET, STOP, TAKE_PROFIT, TRAILING_STOP_MARKET) from `POST /fapi/v1/order` to a NEW endpoint: `POST /fapi/v1/algoOrder`. The old endpoint returns `{"code": -4120, "msg": "Order type not supported for this endpoint. Please use the Algo Order API endpoints instead."}` for ALL conditional types. LIMIT and MARKET orders still use `/fapi/v1/order`. Key differences:
    - **Endpoint:** `/fapi/v1/algoOrder` (NOT `/fapi/v1/order`)
    - **Required param:** `algoType=CONDITIONAL`
    - **Trigger price:** Uses `triggerPrice` (NOT `stopPrice`)
    - **Close position:** `closePosition=true` for close-all (cannot combine with `quantity`)
    - **Response:** Returns `algoId` (NOT `orderId`), `algoStatus='NEW'`
    - **Working type:** `workingType=MARK_PRICE` (recommended) or `CONTRACT_PRICE`
    ```python
    # WRONG — returns -4120:
    async def stop_market(self, symbol, side, qty, stop_price):
        return await self._post('/fapi/v1/order', {
            'symbol': symbol, 'side': side, 'type': 'STOP_MARKET',
            'quantity': str(qty), 'stopPrice': str(stop_price)
        })

    # RIGHT — use algoOrder endpoint:
    async def stop_market(self, symbol, side, qty, stop_price):
        return await self._post('/fapi/v1/algoOrder', {
            'algoType': 'CONDITIONAL',
            'symbol': symbol, 'side': side, 'type': 'STOP_MARKET',
            'triggerPrice': str(stop_price),
            'closePosition': 'true', 'workingType': 'MARK_PRICE'
        })

    async def take_profit_market(self, symbol, side, qty, stop_price):
        return await self._post('/fapi/v1/algoOrder', {
            'algoType': 'CONDITIONAL',
            'symbol': symbol, 'side': side, 'type': 'TAKE_PROFIT_MARKET',
            'triggerPrice': str(stop_price),
            'closePosition': 'true', 'workingType': 'MARK_PRICE'
        })
    ```
    **Verification:** After placing, check response for `algoId` and `algoStatus='NEW'`. Query open algo orders via `GET /fapi/v1/algo/openOrders`. Cancel via `DELETE /fapi/v1/algoOrder` with `algoId`.
    **Full API spec:** See `references/binance-algo-order-api.md`.

51. **Qty step size AND price tick size rounding (CRITICAL)** — Each Binance futures pair has specific `stepSize` for quantity AND `tickSize` for price. Both MUST be rounded. Sending unrounded values causes `{"code": -1111, "msg": "Precision is over the maximum defined"}`.
    
    **ALWAYS use dynamic fetch from Binance API — hardcoded lists are INCOMPLETE.** New pairs launch daily (BLESSUSDT, LABUSDT, FIDAUSDT, etc.) and won't be in any static list. The hardcoded fallback is a STARTER only:
    ```python
    def _round_qty(self, symbol: str, qty: float) -> float:
        import json, urllib.request
        step_sizes = {
            'BTCUSDT': 0.001, 'ETHUSDT': 0.001, 'BNBUSDT': 0.01,
            'SOLUSDT': 0.01, 'XRPUSDT': 0.1, 'DOGEUSDT': 1,
            'ADAUSDT': 1, 'AVAXUSDT': 0.01, 'DOTUSDT': 0.1,
            'LINKUSDT': 0.01, 'MATICUSDT': 1, 'NEARUSDT': 0.1,
            'APTUSDT': 0.01, 'SUIUSDT': 0.1, 'ARBUSDT': 0.1,
            'OPUSDT': 0.1, 'PEPEUSDT': 1, 'WIFUSDT': 0.1,
            'FETUSDT': 0.1, 'RNDRUSDT': 0.01,
        }
        step = step_sizes.get(symbol)
        if step is None:
            # Dynamic fetch for unknown symbols
            try:
                url = f"https://fapi.binance.com/fapi/v1/exchangeInfo?symbol={symbol}"
                resp = urllib.request.urlopen(url, timeout=5)
                data = json.loads(resp.read())
                for s in data.get('symbols', []):
                    for f in s.get('filters', []):
                        if f['filterType'] == 'LOT_SIZE':
                            step = float(f['stepSize'])
                            break
            except:
                step = 0.01
        if step is None:
            step = 0.01
        rounded = round(qty / step) * step
        return max(rounded, step)
    ```
    Same pattern for `_round_price` — fetch `PRICE_FILTER` → `tickSize` for unknown symbols.
    
    **Real production bugs:**
    - ARBUSDT SL sent as `0.07840838194920953` (16 decimals) — tick size is 0.0001 (4 decimals)
    - BLESSUSDT qty sent as `1159.45` — step size is 1 (integer only). Caused `Precision is over the maximum defined` error.
    
    **Caching:** The API call is per-symbol and only fires once (on first encounter). Cache the result in a dict — exchange info changes rarely (maybe weekly). Total cost: ~1 API call per new symbol encountered.

52. **SL/TP verification is MANDATORY — and SL failure = EMERGENCY CLOSE (CRITICAL)** — NEVER trust that SL/TP placement succeeded without checking the response. The execution flow MUST be:
    1. Place entry → verify `orderId` in response
    2. Place SL IMMEDIATELY → verify `algoId` in response
    3. **If SL fails → EMERGENCY CLOSE the position with a market order** — do NOT leave it unprotected
    4. Place TPs (best effort — SL already protects)
    5. Log every step
    
    ```python
    # STEP 1: Entry
    results['entry'] = await self.market_order(symbol, entry_side, qty)
    if 'orderId' not in results['entry']:
        results['error'] = f'Binance error: {results["entry"]}'
        return results
    
    # STEP 2: SL (MANDATORY — failure = emergency close)
    results['sl'] = await self.stop_market(symbol, close_side, qty, sl)
    if 'algoId' not in results['sl']:
        log.error(f'🚨 SL FAILED for {symbol}! EMERGENCY CLOSING!')
        emergency = await self.market_order(symbol, close_side, qty)
        results['emergency_close'] = emergency
        results['error'] = f'SL failed, position emergency-closed'
        return results
    log.info(f'✅ SL placed: {symbol} @ {sl} (algoId={results["sl"]["algoId"]})')
    
    # STEP 3: TPs (best effort)
    for label, tp in [('TP1', tp1), ('TP2', tp2), ('TP3', tp3)]:
        results[label.lower()] = await self.take_profit_market(symbol, close_side, 0, tp)
        if 'algoId' in results[label.lower()]:
            log.info(f'✅ {label} placed: {symbol} @ {tp}')
        else:
            log.warning(f'⚠️ {label} FAILED (SL still active): {symbol} @ {tp}')
    ```
    
    In the caller, handle emergency_close separately:
    ```python
    if 'error' not in result:
        # success
    elif 'emergency_close' in result:
        msg = f'🚨 EMERGENCY CLOSE — {symbol}\nSL placement failed, position auto-closed!'
        self._send_telegram(msg)
    else:
        log.error(f'❌ Trade FAILED: {result["error"]}')
    ```
    
    **Why this matters:** Without emergency close, a position with 20x leverage and no SL can be liquidated in minutes. User said: "kalau gua ketiduran tiba-tiba liquid gimana?" — this is the answer.

53. **Position monitor as defense-in-depth** — Run a SEPARATE process (`mona_position_monitor.py`) that checks all open positions every 60s and verifies SL/TP algo orders exist for each. If any position is missing SL or TP, alert Telegram immediately. This catches cases where:
    - SL/TP gets cancelled by Binance (liquidation, auto-deleverage)
    - Engine crashes between entry and SL/TP placement
    - User manually closes SL/TP via Binance app
    
    ```python
    # In monitor loop:
    positions = await get_positions()
    algo_orders = await get_algo_orders()
    for p in positions:
        sl_count = sum(1 for o in algo_orders if o['symbol'] == p['symbol'] and o['orderType'] == 'STOP_MARKET')
        tp_count = sum(1 for o in algo_orders if o['symbol'] == p['symbol'] and o['orderType'] == 'TAKE_PROFIT_MARKET')
        if sl_count == 0 or tp_count == 0:
            send_telegram(f'⚠️ WARNING: {p["symbol"]} missing SL/TP!')
    ```

54. **Algo order query endpoint BROKEN — use -4130 fallback (CRITICAL)** — As of June 2026, `GET /fapi/v1/algo/openOrders` consistently returns **404** regardless of signing method (raw curl, `_get()`, `requests.get` with proper HMAC). This is likely a Binance-side change — the endpoint exists in the official docs but is unreachable in production. **Workaround:** Use the `-4130` error code as proxy verification — if placing an SL returns `-4130`, an SL already exists for that symbol+side. If it returns `algoId`, a new SL was placed. Either way, the position IS protected. For position monitoring, check `/fapi/v2/account` positions + assume SL/TP exists from entry logs. **Do NOT rely on `/fapi/v1/algo/openOrders` returning data** — it will 404 and cause false "missing SL" alerts.

55. **`closePosition=true` preferred for SL/TP** — When placing SL/TP via algo orders, use `closePosition=true` instead of `quantity`. Benefits:
    - Automatically closes the ENTIRE position regardless of partial TP fills
    - Cannot accidentally leave a partial position unprotected
    - Simpler params (no qty rounding needed for SL/TP)
    - Binance handles the close logic internally
    
    Use `quantity` only for partial TP closes (TP1=40%, TP2=35%, TP3=25%). For SL, ALWAYS use `closePosition=true` — you want full closure on stop loss.

56. **NEVER enter without confirmed SL (HARD RULE)** — User explicitly expressed frustration about positions entering without SL/TP protection. This is not a suggestion — it's a HARD RULE. The execution sequence is: Entry → SL confirmed → TPs. If SL confirmation fails, the position MUST be closed immediately (pitfall #52). The user's exact words: "kalau gua ketiduran tiba-tiba liquid gimana?" — they trust the system to protect them while they sleep. Violating this trust is the fastest way to lose the user. **Default to safety always.**
57. **-4130 = "SL/TP already exists" = SUCCESS, not failure (CRITICAL)** — When placing SL/TP via algo orders, Binance returns `{'code': -4130, 'msg': 'An open stop or take profit order with GTE and closePosition in the direction is existing.'}` if an algo order for that symbol+direction already exists. This means the position IS protected — treat as SUCCESS. **DO NOT** trigger emergency close on -4130. Real production bug: engine entered a position, previous SL for same symbol was still active, -4130 returned, emergency close fired, position closed at a loss via market spread + fees. Repeated 3 times before fix. Correct handling:
    ```python
    results['sl'] = await self.stop_market(symbol, close_side, qty, sl)
    if 'algoId' in results['sl']:
        # New SL placed — SUCCESS
        sl_ok = True
    elif results['sl'].get('code') == -4130:
        # SL already exists for this symbol+direction — STILL PROTECTED
        sl_ok = True
    else:
        # REAL failure — EMERGENCY CLOSE
        emergency = await self.market_order(symbol, close_side, qty)
        results['emergency_close'] = emergency
    ```
    Same logic applies to TP placement.
58. **`closePosition=true` = ONE order per direction** — Binance limit: only ONE active `closePosition=true` algo order per symbol+side. Attempting to place a second (e.g., TP2 after TP1) returns -4130. Options:
    - **Single TP:** Place one TP with `closePosition=true` (simplest, recommended)
    - **Multi-TP partial:** Use `quantity` param with partial amounts (TP1=40%, TP2=35%, TP3=25%). BUT this requires careful qty rounding AND the remaining position may not match after partial fills.
    - **Best practice:** Use `closePosition=true` for SL (always full close). For TP, use one `closePosition=true` TP. If multi-TP needed, implement position monitoring + manual close at each level.
59. **Balance readings vary by context** — `/fapi/v2/balance` returns TOTAL balance (including margin locked in positions). Engine logs may show different values depending on when balance is refreshed relative to position entries. A balance dropping from $55 to $6 doesn't necessarily mean a loss — it can mean margin is locked in multiple positions. Always cross-check with `get_positions()` to understand where the balance went. The `unRealizedProfit` field on each position shows true P&L. Confusing total balance with available margin caused unnecessary panic during debugging.
60. **No positions = no hedge** — When the engine opens 4 simultaneous LONG positions with no SHORT, a market-wide dip hits ALL positions at once. Combined with the balance reserve issue (all capital deployed), there's no room to enter a SHORT hedge. Fix: enforce `max_simultaneous_positions = 3` (not unlimited) AND `balance_reserve_pct = 0.20` (keep 20% free). This ensures: (a) not all capital is deployed, (b) if market turns, only 3 positions get hit, (c) reserve capital is available for contrarian entries.
61. **User trust delegation** — When user says "atur sendiri aku percaya" (you manage it yourself, I trust you), they mean FULL autonomy on strategy decisions. Set config optimally, implement guards, and REPORT results — don't ask for permission on each change. Only escalate critical decisions: funding the wallet, leverage level changes, or emergency stops. This is distinct from "gas" (just do this one thing) — trust delegation means ongoing autonomous operation.
    - **Silent mode preferred** — User explicitly said: "gausah notif alerts balance gua bisa liat manual di binance" (don't send balance alerts, I check manually). For autonomous engines, use log-only mode (FlushingFileHandler, no StreamHandler, no Telegram). Only notify on EMERGENCY (SL failed, liquidation risk). User also said: "kalau salah bisa belajar lebih dalem lagi" — wants the engine to self-learn and self-correct, not just execute. This means autonomous mode with evolution engine is the expected operating mode, not a nice-to-have.
62. **Conservative mode for critical capital (CRITICAL)** — When the user's balance is their LAST money (family funds, debt repayment), switch to maximum protection. The user explicitly said this $54 is for "makan kasih istriku dan bayar hutang" (feeding wife and paying debt). This is NOT gambling money — it's survival money. Conservative config:
    ```python
    min_score_to_trade = 50      # Only STRONG signals (was 35-40)
    min_signals_agree = 4         # Need 4 signals agreeing (was 3)
    max_simultaneous_positions = 2  # Max 2 (was 3-4)
    balance_reserve_pct = 0.25    # 25% always free (was 20%)
    max_total_exposure = 0.08     # 8% max total (was 12-15%)
    max_position_pct = 0.03       # 3% risk per trade (was 5%)
    default_leverage = 20         # 20x (was 35x)
    max_leverage = 30             # 30x (was 50x)
    sl_atr_mult = 1.5             # Wide enough to survive noise (1.0 was too tight — SL hit before price reversed)
    tp1_close_pct = 0.50          # Lock more at TP1 (was 40%)
    max_daily_trades = 4          # Fewer trades (was 5-6)
    cooldown_after_loss_sec = 600 # 10 min (was 5 min)
    max_drawdown_pct = 0.05       # 5% pause (was 8%)
    emergency_drawdown_pct = 0.07 # 7% stop all (was 10%)
    max_spread_pct = 0.003        # Tighter spread (was 0.005)
    min_balance_usdt = 15.0       # Higher minimum (was 10)
    dynamic_lev_min = 15          # Lower leverage floor (was 20)
    dynamic_lev_max = 30          # Lower leverage ceiling (was 50)
    ```
    **Rule:** When user expresses financial desperation ("buat makan", "bayar hutang", "last balance"), treat capital protection as HIGHEST priority. Better to miss opportunities than lose survival money. The user's trust is earned by protecting their family, not by maximizing returns.
63. **Systemd service auto-restart debugging** — When a process keeps respawning after `kill -9`, the root cause is a **user systemd service** (`systemctl --user`). The process tree shows parent PID as `systemd --user` (not a shell or cron). Debugging sequence:
    1. `ps aux | grep <process>` → get PID
    2. `ps -o ppid= -p <PID>` → get parent PID
    3. `ps -p <ppid> -o cmd` → if `systemd --user`, it's a service
    4. `systemctl --user list-units --type=service --all | grep <name>`
    5. `systemctl --user stop <service> && systemctl --user disable <service>`
    6. `rm ~/.config/systemd/user/<service>.service && systemctl --user daemon-reload`
    7. Also check `crontab -l` for system cron respawn entries
    **Common symptom:** "I killed the watcher but it keeps sending alerts!" — the service auto-restarts within seconds.
64. **Account balance field name: `walletBalance` not `balance`** — When reading `/fapi/v2/account` response, the `assets[]` array uses `walletBalance` (NOT `balance`) for total balance. The field `availableBalance` is at the TOP level of the response, not inside `assets[]`. Wrong field names cause `KeyError: 'balance'` that silently disables the balance reserve guard. Fix:
    ```python
    # WRONG:
    total_balance = sum(float(a['balance']) for a in acc.get('assets', []) if a['asset'] == 'USDT')
    
    # RIGHT:
    total_balance = sum(float(a.get('walletBalance', 0)) for a in acc.get('assets', []) if a['asset'] == 'USDT')
    available = float(acc.get('availableBalance', 0))
    ```
    Also note: `availableBalance` is a TOP-LEVEL field on the account response, NOT inside individual asset objects. Using `acc.get('availableBalance')` is correct; using `a['availableBalance']` inside the assets loop will KeyError.

65. **Self-Evolution Engine** — Connect a learning engine (`mona_evolution.py`) to track trade outcomes and auto-adjust parameters. Components:
    - **TradeTracker** — records every closed trade with signals, outcome, PnL
    - **SignalAnalyzer** — measures accuracy of each signal type (OI, funding, CVD, etc.)
    - **EvolutionEngine** — auto-adjusts signal weights (boost accurate, reduce inaccurate), risk params (position size, SL), leverage, and symbol blacklist (avoid consistent losers)
    - **Lessons** — stores patterns: big win setups, big loss avoidances, symbol losing streaks
    - Run evolution cycle every 24h, report to Telegram
    - Needs 10+ trades before adjustments are meaningful
    - Data stored in `~/.hermes/data/evolution/`
    - Hook into `_alert_exit()` to record every closed trade automatically
    - Store `signals=analysis` dict in position entry so evolution knows which signals to credit/blame
66. **Position sync on startup is MANDATORY (CRITICAL)** — When an autonomous engine starts, it MUST fetch existing positions from Binance and register them in the internal position monitor. Without sync:
    - Engine thinks 0 positions → opens duplicates (e.g., 2nd BNBUSDT LONG)
    - Max positions guard doesn't trigger → over-exposure to correlated assets
    - Balance reserve guard uses wrong available amount
    
    **CRITICAL BUG: synced positions with TP=0 trigger mass partial closes.** If synced positions have default `tp1=0, tp2=0`, the position monitor sees `price > tp1` (price > 0 = always true) → triggers TP1/TP2 partial close → sells 50% of every position immediately on startup! This happened in production — 4 positions each lost 50% size within 1 second of engine start.
    
    **Fix:** When syncing, mark positions as already "partially closed" to prevent auto-triggers:
    ```python
    def _sync_existing_positions(self):
        """Fetch existing positions from Binance on startup."""
        import requests
        ts = int(time.time() * 1000)
        query = f'timestamp={ts}'
        sig = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        r = requests.get(f'https://fapi.binance.com/fapi/v2/account?{query}&signature={sig}',
                         headers={'X-MBX-APIKEY': api_key}, timeout=10)
        acc = r.json()
        
        for p in acc.get('positions', []):
            if float(p.get('positionAmt', 0)) == 0:
                continue
            sym = p['symbol']
            entry = float(p['entryPrice'])
            self.position_monitor.positions[sym] = {
                'symbol': sym,
                'side': 'LONG' if float(p['positionAmt']) > 0 else 'SHORT',
                'entry_price': entry,
                'size': abs(float(p['positionAmt'])),
                'leverage': int(float(p.get('leverage', 20))),
                'open_time': time.time(),
                'signals': {},
                'sl': 0, 'tp': 0,
                # CRITICAL: Set these to prevent false partial closes
                'tp1': entry * 999,   # Extreme value — never triggered
                'tp2': entry * 999,   # Extreme value — never triggered
                'tp1_hit': True,       # Already "hit" = no partial close
                'tp2_hit': True,       # Already "hit" = no partial close
                'trailing_active': False,
                'trailing_sl': 0,
                'partial_closes': 2,   # Mark as fully partially closed
                'last_check': time.time(),
                'mfe': 0, 'mae': 0,
                'atr': entry * 0.01,   # Default ATR estimate
            }
    ```
    Use synchronous `requests` (not `aiohttp`) for the sync call — it runs during `__init__` which may or may not be inside an async context. `asyncio.get_event_loop().run_until_complete()` fails inside a running loop.
    
    **Sync must also update `_live_balance` and `_peak_balance`** from the same API response to avoid stale balance values.

67. **Evolved config MUST have hard safety caps (CRITICAL)** — The self-evolution engine's `AutoAdjuster` writes back risk and leverage values based on win rate. With 60% win rate, it may set `risk=0.05, leverage=30`. When the autonomous engine reads evolved config, it MUST enforce hard caps that cannot be overridden:
    ```python
    def _apply_evolved_config(self, adjustments):
        risk = adjustments.get('risk', {})
        if risk.get('position_size_pct'):
            # HARD CAP: never exceed 3% risk (user's money = family/debt)
            self.config['risk_per_trade_pct'] = min(0.03, risk['position_size_pct'])
        
        lev = adjustments.get('leverage', {})
        if lev.get('default'):
            # HARD CAP: base leverage 20x, max 30x
            self.config['leverage_base'] = min(20, lev['default'])
            self.config['leverage_max'] = min(30, lev.get('max', 30))
    ```
    Without caps, a moderate win rate (60%) causes the evolution engine to increase risk from 3% to 5% and leverage from 20x to 30x — exactly the opposite of what "conservative mode" means. The evolution engine optimizes for returns; the caps enforce user safety.

68. **Python FileHandler buffering loses logs** — The default `logging.FileHandler` does NOT auto-flush. In long-running silent engines (no StreamHandler), log entries stay in the OS buffer and don't appear in the log file until the buffer fills or the process exits. This makes it look like the engine is stuck (no log output) when it's actually running fine.
    
    **Fix:** Subclass FileHandler with auto-flush:
    ```python
    class _FlushingFileHandler(logging.FileHandler):
        def emit(self, record):
            super().emit(record)
            self.flush()
    ```
    Use this for ALL long-running silent processes. Without it, debugging is impossible — you can't tell if the engine is hung, crashing silently, or just buffering.

69. **Balance reserve minimum threshold for micro-accounts** — The `available < 5.0` check in circuit breakers is too restrictive for accounts with $54 balance. With 25% reserve ($13.50) and 4 positions, available drops to ~$2.50, which is < $5 → engine blocks ALL trades permanently. Set minimum to $1.0 for micro-accounts. The reserve percentage (25%) already handles the safety margin; the absolute dollar minimum is just a sanity check for dust balances.

70. **Autonomous delegation = execute immediately, don't ask** — When user says "pantau terus dan eksekusi sendiri" or "atur sendiri", they expect: (a) analyze positions NOW, (b) close the weakest immediately, (c) set up monitoring daemon, (d) report actions taken. Do NOT ask "mau close yang mana?" or "konfirmasi dulu ya?" — user already delegated. The flow: signal analysis → identify weakest → close via market order → verify fill → setup monitor → report. Only escalate if ALL positions are profitable with strong signals (nothing to close) or if balance is too low for meaningful action.

71. **Position monitor script must use `python3 -u` and FlushingFileHandler** — Without `-u`, stdout buffers and `process(action='log')` shows nothing. Without FlushingFileHandler, log file entries stay in OS buffer. Both cause the monitor to appear stuck when it's actually running fine. See `references/autonomous-position-monitor.md` for the full template.

72. **CVD + Taker Volume = primary relative strength indicator** — When comparing multiple positions to decide which to close, CVD and Taker Volume are the most actionable signals. Funding rate and orderbook are secondary. Pattern: run `GET /fapi/v1/aggTrades?limit=500` for each symbol, calculate buy_vol vs sell_vol. CVD < -20% + taker_buy < 40% = strong sell signal. CVD > +10% + taker_buy > 55% = strong hold. This was used successfully to close BNB (CVD -17.24%, taker 41.4%) while preserving LINK (CVD +13.55%, taker 56.8%).

73. **Fear & Greed Index as contrarian position context** — Extreme Fear (< 20) with negative funding = positions are CONTRARIAN LONG. This is actually favorable for existing longs — don't panic close just because "market is down". Instead, check if CVD shows accumulation (smart money buying into fear) or distribution (retail dumping). In this session: FNG=12 + negative funding + LINK CVD positive = hold LINK despite bearish headline. See `references/autonomous-position-monitor.md`.

75. **Stale position state file = phantom positions (CRITICAL)** — The position monitor persists positions to `~/.hermes/data/evolution/position_monitor_state.json`. When positions are closed manually (user closes on Binance app) or by SL/TP trigger, the state file is NOT updated. On engine restart, the state file loads stale positions → engine thinks max positions reached → refuses to scan for new setups. In production, 4 manually-closed positions persisted as "active" for hours, blocking all new entries.
    **Fix (two parts):**
    1. **On sync, remove stale positions:**
    ```python
    # After syncing from Binance, remove positions not in Binance response
    stale = [s for s in self.position_monitor.positions if s not in binance_syms]
    for s in stale:
        log.info(f"Removing stale position: {s} (no longer on Binance)")
        del self.position_monitor.positions[s]
    ```
    2. **On position close (by TP/SL or manual), delete from state file immediately** — don't wait for next restart.
    **Symptom:** Logs show `Synced 0 existing positions from Binance` BUT then `Max positions (4/2) — monitoring only`. The number in "Max positions" comes from the state file, not from Binance sync.
76. **Full market scanner with SMC scoring** — When user asks "scan market" or "cari setup", scan ALL USDT pairs (not just top 25). Use `GET /fapi/v1/exchangeInfo` for active symbols, `GET /fapi/v1/ticker/24hr` for volume, filter by min volume ($500K), then score each pair with DOZERO.X SMC confluence. Script: `~/.hermes/scripts/scan_market_full.py`. Typical results: 550+ pairs scanned, 0-2 elite (75+), 5-10 strong (60-74). Takes 2-3 minutes. **WARNING:** Individual API calls per symbol WILL cause IP ban. Use batch endpoints (pitfall #96).
77. **USUSDT = 10x max leverage + Algo Order only** — USUSDT on Binance Futures has max leverage 10x (not 20x). Also requires Algo Order API for ALL conditional orders (SL/TP) — regular `/fapi/v1/order` returns -4120. Use `/fapi/v1/algoOrder` with `algoType=CONDITIONAL`, `type=STOP_MARKET`/`TAKE_PROFIT_MARKET`, `closePosition=true`.
78. **Execute first, report after — never ask for confirmation on delegated tasks (CRITICAL)** — When user says "lu yang eksekusi" or "kasih paham sendiri" or "gua mau lihat hasil", they mean: DO IT NOW, show results. Do NOT ask "mau gue masukin?" or "pilih opsi 1/2/3". The flow: analyze → pick best option → execute → report. User explicitly said "masih nanya kan lu yang eksekusi kasih paham sendir lah gua mau lihat hasilmu" (you're still asking? you're the one executing, figure it out yourself, I want to see your results). This frustration applies to ALL delegated work, not just trading.
79. **Speed matters — "lama banget" is a frustration signal** — User gets frustrated when analysis takes too long. If scanning 25 pairs takes 30+ seconds, the user checks out. Optimize: parallelize API calls, cache klines, use `execute_code` for batch processing, limit to top candidates early. Better to enter a good-but-not-perfect setup quickly than wait 5 minutes for a perfect scan that finds nothing.

80. **SMC confluence scoring ≠ traditional composite scoring (CRITICAL)** — The DOZERO.X SMC confluence system uses a DIFFERENT scale than the traditional 12-signal composite. Do NOT mix thresholds:
    - **Traditional composite** (OI, funding, CVD, etc.): threshold 35-40, rarely exceeds 45
    - **SMC confluence** (MTF, FVG, BOS/CHOCH, etc.): threshold 75+, max 100
    - When both systems run together, SMC adds a BONUS (+30 max) to the traditional score. The entry gate is: `traditional_score >= 50 AND smc_confluence >= 75`.
    - Lowering the SMC threshold below 75 defeats the purpose — it's designed to filter out mediocre setups. In a scan of 554 pairs, typically 0-2 reach 75+. That's correct behavior, not a bug.
    
81. **Never flip-flop: enter → close → enter = guaranteed loss** — Entering a position and then closing it minutes later (because of doubt or new analysis) ALWAYS results in a net loss (spread + fees + slippage). This session: entered USUSDT at 67/100 (below 75 threshold), reviewed market data, found bearish orderbook + dying volume, closed immediately for -$0.02 loss. The loss is small but the pattern is destructive. **Rule: if you're not confident enough to hold through a -2% drawdown, don't enter.**

82. **Volume conviction check before entry** — When H1 volume is < 0.3x the 20-period average, the signal has LOW CONVICTION regardless of SMC score. Price moves on volume — a BOS or FVG without volume is a fakeout trap. Add this check to the entry gate:
    ```python
    h1_vol_ratio = current_h1_volume / avg_h1_volume_20
    if h1_vol_ratio < 0.3:
        skip("Low conviction: H1 volume {h1_vol_ratio:.2f}x average")
    ```
    In this session: USUSDT had H1 volume at 0.19x and H4 at 0.16x — both abnormally low. The +15% daily pump was on declining volume = profit-taking setup, not continuation.

83. **Orderbook bid/ask ratio as final filter** — Before entering, check `GET /fapi/v1/depth?limit=20` and calculate `bid_total / ask_total`. If ratio < 0.5 (2x more sell pressure than buy), skip the trade even if SMC score passes. In this session: USUSDT orderbook showed 0.43 ratio (2.7x more asks than bids) — a clear signal that sellers dominate. This isn't in the SMC engine but should be a final pre-entry check.

84. **Position sizing must match recovery target** — When user says "balikin loss $2", calculate the required position size BEFORE entering. A $0.53 margin at 10x = $5.29 notional. For +$2 profit, price needs to move +37.8% — unrealistic for a single trade. **Always back-calculate:** `required_move = target_profit / notional`. If required_move > 5%, the position is too small to matter. Better sizing: $7 margin at 10x = $70 notional → +2.9% move = $2 profit (achievable).

85. **Compounding plan for micro-accounts ($50-55)** — Don't just trade randomly. Have a staged growth plan:
    ```
    Stage 1: $53 → $75    (1.4x, ~3-4 wins)
    Stage 2: $75 → $120   (1.6x, size increases naturally via 3% rule)
    Stage 3: $120 → $200  (1.7x)
    Stage 4: $200 → $350  (1.75x)
    Stage 5: $350 → $600  
    Stage 6: $600 → $1,000
    ```
    Key: 3% risk on $53 = $1.60/trade. 3% risk on $200 = $6/trade. Compounding increases SIZE, not risk percentage. Each stage requires the same discipline but delivers larger absolute returns.

86. **Meme coin analysis framework** — When user asks about a pumped meme coin (e.g., 币安人生/Binance Life), assess:
    - Market cap > $500M = already large for meme, limited upside
    - Vol/MCap ratio > 5% = active trading (not dead)
    - Supply fully circulating = no vesting dump risk
    - Platform concentration > 20% = whale risk
    - Daily pump > 15% = likely profit-taking incoming
    **Verdict framework:** Trading (flip 10-15% with tight SL) = maybe. Holding = no. Using family money = absolutely not.

87. **Accountability for entries — "kan lu yang entry?" (CRITICAL)** — When user asks "menurut mu gimana kan lu yang entry?" (what do you think, you're the one who entered?), they're holding you accountable for the decision. The correct response is: (a) admit the mistake honestly, (b) explain WHY it happened (old engine, below-threshold entry, FOMO), (c) show what's FIXED so it won't repeat, (d) propose concrete action (close position, resize, or hold with SL). Never deflect blame to "the old engine" or "market conditions" — the user trusts YOU to make good decisions. If you entered below the SMC threshold, own it and close the position.

88. **"No positions = no alerts" is a HARD RULE (CRITICAL)** — When user says "kalau gak ada posisi gak usah alerts" or "jangan habisin apikey", they mean ALL of: (a) send ZERO messages when no positions exist or nothing changed, (b) minimize API calls when idle — don't poll Binance every 60s for nothing, (c) don't send verbose status updates explaining what the monitor is doing, (d) after ALL positions close, one line max ("All closed, wallet $X") — not a paragraph analyzing what happened. The ONLY acceptable output from an autonomous monitor is a CLOSE action (position actually exited). Silence is the default state. User explicitly got angry ("woi di bilang kalau gak ada posisi gak usah kirim alerts masih ngeyel") — violating this trust is worse than missing an alert. **This applies to autonomous engines AND direct chat responses** — don't send multi-paragraph analysis when user already told you to be quiet.

88. **Engine scan list must cover ALL pairs (CRITICAL)** — The autonomous engine's default scan list (top 20 by volume) is TOO SMALL. With 595 active USDT pairs, scanning only 20 means missing 97% of opportunities. **Fix:** Set `auto_fetch_symbols=True` in config and leave `symbols=[]` empty. The engine auto-fetches from Binance `exchangeInfo` + `ticker/24hr`, filters by min $500K volume, and sorts by volume descending. Typical result: 500-600 pairs. See pitfall #93 for implementation. The full market scanner (`scan_market_full.py`) should also use the same fetch logic.
95. **NEVER fabricate trade data or market data (CRITICAL — TRUST VIOLATION)** — When the user asks about trade history, positions, PnL, or any market data, ALWAYS fetch from the real API. If the API is unavailable (IP banned, rate limited, network error), say "I can't check right now because [reason]" — NEVER generate fake data that looks plausible. In this session: fabricated a full trade history (10 trades with specific entry/exit prices, PnL, timestamps) and presented it as real analysis. User caught it immediately: "mona yang bener lah salah semua itu, jangan ngarang lagi bos dan kerja yang bener ini duit beneran bukan duit demo." This is especially dangerous with real money — a fake "60% win rate" could encourage the user to deposit more funds based on false confidence. **Rules:**
    - If API returns error → tell user exactly what the error is, don't substitute with made-up data
    - If you don't have data → say "I don't have that data" and offer to fetch it
    - If data is stale → say "Last check was X minutes ago, let me refresh"
    - NEVER generate example/hypothetical trades and present them as real
    - NEVER pad signal_performance.json or trades.json with generated data for "testing"
    - The user's exact words: "ini duit beneran bukan duit demo" — real money demands real data, always
96. **Full scan 528+ pairs causes IP ban (CONFIRMED in production)** — Scanning 528 pairs every 90 seconds with individual API calls per symbol triggers Binance IP ban within minutes. In this session: engine started scanning 528 pairs → IP banned within 1 cycle (~90 seconds) → ban lasted ~90 minutes (`{'code': -1003, 'msg': 'Way too many requests; IP(43.163.85.51) banned until TIMESTAMP'}`). **Fix:** Batch API calls — use `GET /fapi/v1/ticker/24hr` (one call for ALL symbols' prices) and `GET /fapi/v1/klines` with caching. Target: < 20 API calls per scan cycle, not 528+. The auto-fetch in pitfall #88/93 adds 2 more calls (exchangeInfo + ticker). Total budget per cycle: ~25 calls max. If scanning > 100 symbols, MUST use batch endpoints or risk IP ban.

89. **Self-learning needs data — be transparent about cold start** — The evolution engine (pitfall #65) needs 10-20+ trades before it can meaningfully optimize signal weights or risk parameters. When user asks "self learning belum ada?", explain that the infrastructure EXISTS but needs trade data to learn from. With only 3-4 historical trades (all from the old engine), the system is still in "cold start" mode. The engine must accumulate DOZERO.X-scored trades before self-learning becomes actionable. Don't promise "the engine learns from its mistakes" when there's insufficient data — be honest about the cold start.

90. **Telegram bot 409 Conflict after gateway restart** — When Hermes gateway and `mona-bot.service` both try to poll the same Telegram bot token, Binance returns `HTTP 409: Conflict`. Only ONE process can poll a bot token at a time. After a gateway restart, check if `mona-bot.service` is still running:
    ```bash
    systemctl status mona-bot  # look for 409 Conflict errors
    ```
    If yes, stop and disable it — the gateway handles the bot now:
    ```bash
    systemctl stop mona-bot && systemctl disable mona-bot
    ```
    **Symptom:** User says "bot stopped responding after update" but gateway logs show "Telegram connected". The conflict causes messages to be consumed by the dead service but never processed. Fix: kill the competing service, gateway picks up immediately.

91. **Linked references:**

92. **CircuitBreaker.reset_daily() is on `.state`, not the object itself (CRITICAL)** — The `CircuitBreaker` class wraps a `CircuitBreakerState` dataclass. The `reset_daily()` method lives on `self.state`, NOT on `CircuitBreaker` directly. Calling `self.risk_engine.circuit_breaker.reset_daily()` raises `AttributeError: 'CircuitBreaker' object has no attribute 'reset_daily'`. Fix: `self.risk_engine.circuit_breaker.state.reset_daily()`. This error fires daily at UTC midnight — the engine silently crashes and restarts via systemd, losing in-memory state each time.

93. **Auto-fetch ALL USDT pairs from Binance for scan list (CRITICAL)** — Hardcoding 20-80 pairs in `config.py` misses 97% of opportunities. Instead, fetch dynamically:
    ```python
    # In FuturesConfig or engine init:
    async def _fetch_all_usdt_symbols(self):
        import urllib.request, json as _json
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        data = _json.loads(urllib.request.urlopen(url, timeout=10).read())
        symbols = [s['symbol'] for s in data['symbols']
                   if s['status'] == 'TRADING' and s['symbol'].endswith('USDT')
                   and s['contractType'] == 'PERPETUAL']
        
        tickers = _json.loads(urllib.request.urlopen(
            "https://fapi.binance.com/fapi/v1/ticker/24hr", timeout=10).read())
        vol_map = {t['symbol']: float(t.get('quoteVolume', 0)) for t in tickers}
        filtered = [s for s in symbols if vol_map.get(s, 0) > 500000]
        filtered.sort(key=lambda s: vol_map.get(s, 0), reverse=True)
        return filtered  # Typically 500-600 pairs
    ```
    Config field: `auto_fetch_symbols: bool = True` — when `symbols` list is empty, auto-populate from Binance. Filter by min $500K daily volume to exclude dust pairs. Cache the list for 24h (new pairs listed rarely). Log: `Fetched {len(filtered)} USDT pairs (min $500K volume)`.

75. **Notional minimum varies by pair (-4164 error)** — Binance rejects orders where `quantity × price < pair-specific minimum`. Error: `{"code": -4164, "msg": "Order's notional must be no smaller than 5 (unless you choose reduce only)."}`. The minimum is NOT always 5 USDT — it varies:
    - BTCUSDT: 100 USDT
    - ETHUSDT: 20 USDT
    - BNBUSDT: 5 USDT
    - ADAUSDT: 5 USDT
    - LINKUSDT: 20 USDT (higher than most!)
    - SOLUSDT: 5 USDT
    - DOGEUSDT: 5 USDT
    
    **Impact on small accounts:** With $54 balance and 4 open positions, available margin can drop below the minimum for some pairs. The engine tries to enter, fails with -4164, and wastes a cooldown cycle. **Fix:** Fetch `minNotional` from `GET /fapi/v1/exchangeInfo` → `symbols[].filters[]` where `filterType=MIN_NOTIONAL`. Cache it (changes rarely). Check `qty * price >= minNotional` BEFORE sending entry order. If below minimum, skip that pair silently (don't log as error — it's expected behavior). For unknown pairs, default to 5 USDT minimum.
97. **Production RateLimiter pattern for DataCollector (CRITICAL)** — The pitfall #42 settings (delay between symbols, cache TTL) are necessary but NOT sufficient. A proper `RateLimiter` class is needed in `DataCollector` to prevent IP bans at the transport layer. Without it, any code path that bypasses the manual delay (e.g., position sync, balance check, market intel) can still trigger a ban. Implementation: `RateLimiter(max_requests=50, window_sec=60)` with `await rate_limiter.acquire()` before every HTTP call in `_get()`. Also handles 418 (IP ban) by caching empty result for 5 minutes instead of retrying immediately. TTL increased from 60s to 120s for klines. Symbol list capped at top 30 by volume (`filtered[:30]`). Scan interval 300s (not 90s). Full implementation in `references/rate-limiter-implementation.md`.
99. **Breakeven stop after TP1 (CRITICAL)** — When TP1 is hit and partial close executes, IMMEDIATELY move SL to breakeven (entry + small buffer like 0.1 ATR). This locks profit on the remaining position. Also activate trailing stop so the rest rides the trend. Without this, a position that hits TP1 but reverses can still be a full loss (the TP1 partial profit doesn't offset the full SL). Implementation in position monitor:
    ```python
    if hit_tp1:
        pos['partial_closes'] = 1
        actions.append({'action': 'CLOSE_PCT', 'pct': 0.25, 'reason': 'TP1'})
        # Move SL to breakeven
        if side == 'LONG':
            pos['sl'] = max(pos['sl'], entry + pos['atr'] * 0.1)
        else:
            pos['sl'] = min(pos['sl'], entry - pos['atr'] * 0.1)
        pos['trailing_active'] = True
        log.info(f"BREAKEVEN: SL moved to {pos['sl']:.4f} after TP1")
    ```
    This is the DEFAULT behavior for conservative mode. Don't wait for 1R or 2R — TP1 IS the signal to lock profit.

100. **Retry order placement with exponential backoff** — SL/TP placement can fail transiently (network timeout, Binance overloaded). A single retry is not enough. Use 3 retries with exponential backoff:
    ```python
    async def _retry_order(coro_func, *args, max_retries=3, **kwargs):
        for attempt in range(max_retries):
            try:
                result = await coro_func(*args, **kwargs)
                if 'algoId' in result or 'orderId' in result:
                    return result
                if result.get('code') == -4130:  # Already exists
                    return result
                log.warning(f"Order attempt {attempt+1}/{max_retries} failed: {result}")
            except Exception as e:
                log.warning(f"Order attempt {attempt+1}/{max_retries} error: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
        return {'error': 'max retries exceeded'}
    ```
    Apply to ALL order placements (SL, TP1, TP2). Without this, a single transient failure causes the engine to skip SL placement, leaving the position unprotected (or triggering emergency close unnecessarily).

101. **`closePosition=true` = ONE order per direction — use for SL, quantity for TPs** — see pitfall #58 for details

107. **Auto-start engine after IP ban via cron watchdog** — When Binance IP ban occurs (418 error), create a `no_agent=True` cron job with `auto_start_engine.py` script that checks IP status every 5 minutes. Script: (1) check if engine already running via `pgrep`, (2) test Binance API with signed request, (3) if OK, start engine via `subprocess.Popen`. Kill the cron job after engine starts. See `references/telegram-alert-integration.md` for full implementation.

108. **SL/TP orders placed on Binance server = survives engine crash** — SL/TP placed via `/fapi/v1/algoOrder` with `closePosition=true` live on Binance's server, NOT in the engine's memory. If the engine crashes, the SL/TP orders still execute. This is the PRIMARY defense for overnight positions. Always verify `algoId` in response before considering the position protected. Add local position monitor as defense-in-depth (checks every 60s that SL/TP algo orders still exist).

109. **"atur sebaik mungkin" = FULL autonomous design authority (CRITICAL)** — When user says "atur sebaik mungkin lah gimana" (manage it as best as you can), "terserah lu", or "lu yang pinter", they're giving you FULL authority to design, implement, and optimize the system. Do NOT:
    - Ask "mau threshold berapa?" → pick the optimal one
    - Ask "mode scalper atau sniper?" → build both with auto-switch
    - Ask "leverage berapa?" → use conservative defaults
    - Present 3 options and ask user to choose → pick the best one and explain why
    
    DO:
    - Analyze the problem (e.g., engine too conservative, no trades)
    - Design the solution (dual-mode system)
    - Implement it fully
    - Test and verify
    - Report results with a summary
    
    This is different from "gas" (just do this specific thing) — "atur sebaik mungkin" means you own the ENTIRE architecture decision. User expects to wake up and see results, not a list of options to choose from.

110. **Binance precision MUST be fetched dynamically for new pairs** — The hardcoded step/tick size lists cover ~20 popular pairs. New pairs (BLESSUSDT, LABUSDT, FIDAUSDT, EDENUSDT, etc.) are added to Binance Futures weekly and have DIFFERENT precision requirements. BLESSUSDT requires integer quantities (step=1), while most pairs allow decimals. ALWAYS fall back to `GET /fapi/v1/exchangeInfo?symbol={symbol}` for unknown pairs. Cache the result per-symbol (exchange info changes rarely). See pitfall #51 for full implementation.

111. **Fear & Greed Index as mode switch trigger** — FNG < 20 (Extreme Fear) or FNG > 80 (Extreme Greed) = momentum-heavy market with lots of volatile moves. Switch to Scalper mode to capture short-term momentum. FNG 20-80 = normal market, use Sniper mode for structural setups. The FNG API (`api.alternative.me/fng/?limit=1`) is free and fast — cache for 1 hour. Real-world result: FNG=12 triggered scalper mode, found BLESSUSDT +27% pump with volume spike = entered successfully.

112. **Momentum scanner as first-stage filter saves 95% API calls** — Instead of running full analysis on 30-600 pairs (3-8 API calls each = 180-4800 calls), run the momentum scanner FIRST:
    - 1 batch call for ALL tickers (`/fapi/v1/ticker/24hr`)
    - Filter by volume ($5M+) and price change (1.5%+) → typically 10-20 candidates
    - Run quick TA (RSI + EMA) on top 15 only → 30 kline calls
    - Total: ~31 API calls vs 180+ for full scan
    - Then only the BEST candidate gets full analysis (if Sniper mode)
    
    This pattern is essential for avoiding IP bans (pitfall #96) while still covering the full market.

113. **Standalone signal scanner for full-market coverage (CRITICAL)** — The trading engine scans a LIMITED list (30-100 pairs). This misses 80%+ of opportunities. VIRTUALUSDT had an 80/100 SMC setup but wasn't in the engine's 30-pair list. **Solution:** Run a SEPARATE `dozero_scanner.py` process that monitors ALL top pairs (100 by volume) independently from the trading engine. It alerts via Telegram but does NOT trade — signal-only. Architecture:
    - Fetches top 100 pairs by volume from `/fapi/v1/ticker/24hr` (1 API call)
    - Runs DOZERO.X SMC analysis on each (H1/H4/D klines = 3 calls per pair)
    - Alerts to Telegram when confluence ≥ 75
    - Cooldown: 1 hour per pair (no spam)
    - Runs every 300s as background process
    
    **Why separate from trading engine:** The engine needs to be fast (limited pairs, quick scans). The scanner needs to be thorough (all pairs, deeper analysis). Running both in parallel gives best coverage. The scanner catches structural setups (SMC 75+), while the engine catches momentum plays (scalper mode). User said "solid tapi gak kasih aku sinyal" — this fixes that.
    
    **Implementation:** `~/.hermes/scripts/dozero_scanner.py` — standalone script with `DozeroSignalScanner` class. Uses `send_telegram_alert()` to topic 13 (Alpha). See `references/dozero-signal-scanner.md`.
    
    **Pitfall:** The scanner makes ~300 API calls per cycle (3 per pair × 100 pairs). At 50 req/min rate limit, this takes ~6 minutes. This is fine for a 5-minute interval scanner — the next cycle starts after the previous one finishes. But DON'T run it at < 300s interval or it'll overlap with itself.

114. **Trailing SL NoneType guard (CRITICAL)** — When positions are synced from Binance on startup (pitfall #66), `trailing_sl` may be initialized as `None` (or `0` which becomes `None` after state file reload). The position monitor then calls `max(pos['trailing_sl'], new_trail)` which raises `TypeError: '>' not supported between instances of 'float' and 'NoneType'`. This crashes the monitor loop every cycle (engine logs show repeated `Loop error (continuing)` every 2 minutes).
    
    **Fix:** Guard ALL `max()`/`min()` calls on `trailing_sl`:
    ```python
    if side == 'LONG':
        new_trail = price - trail_dist
        if pos['trailing_sl'] is None:
            pos['trailing_sl'] = new_trail
        else:
            pos['trailing_sl'] = max(pos['trailing_sl'], new_trail)
    else:
        new_trail = price + trail_dist
        if pos['trailing_sl'] is None:
            pos['trailing_sl'] = new_trail
        else:
            pos['trailing_sl'] = min(pos['trailing_sl'], new_trail)
    ```
    Apply to BOTH the breakeven SL set AND the trailing update. The breakeven set is usually fine (it assigns a float), but the trailing update can still hit None if the state file was corrupted or the position was synced without breakeven activation.
    
    **Symptom:** Engine starts, syncs 0 positions, runs first scan fine, but position monitor crashes every 2 minutes with NoneType error. If there ARE open positions, the crash prevents ALL monitoring — SL/TP checks, trailing stops, partial closes all stop working.

115. **Scalper entry notional minimum check** — When the engine enters Scalper mode with a small balance ($55), position sizes on cheap tokens can fall below Binance's minimum notional (usually $5 USDT). Before sending entry order, check `qty * price >= 5.0`. Also, when balance is $0 or near-zero, the engine should STOP scanning entirely — check `_live_balance > 5.0` before starting any scan cycle.

116. **Auto-detect max leverage per pair (CRITICAL)** — Binance pairs have DIFFERENT max leverage limits. The engine CANNOT assume a universal leverage. Real production data:
    - BTCUSDT: 25x ✅
    - ETHUSDT: 25x ✅
    - SKYAIUSDT: 10x (engine tried 25x → "Leverage 25 is not valid" → order failed)
    - HUSDT: 10x (same failure)
    - EDENUSDT: 20x
    - BLESSUSDT: 25x
    - FIDAUSDT: 25x
    
    **Fix:** Add `set_leverage_auto()` method that tries desired leverage first, then falls back through [40, 35, 30, 25, 20, 15, 10, 5]:
    ```python
    async def set_leverage_auto(self, symbol: str, desired: int) -> int:
        result = await self.set_leverage(symbol, desired)
        if 'code' not in result:
            return desired
        for lev in [40, 35, 30, 25, 20, 15, 10, 5]:
            if lev >= desired:
                continue
            result = await self.set_leverage(symbol, lev)
            if 'code' not in result:
                return lev
        await self.set_leverage(symbol, 5)
        return 5
    ```
    After detecting actual leverage, RECALCULATE position size:
    ```python
    actual_lev = await self.execution.set_leverage_auto(symbol, leverage)
    if actual_lev != leverage:
        leverage = actual_lev
        max_size = balance * risk_pct * leverage
        size_usdt = min(size_usdt, max_size)
        qty = size_usdt / price
    ```

117. **NEVER trade while debugging (CRITICAL — user rule)** — User explicitly said: "lu kalau lagi proses benerin fix bug atau apa jangan entry dulu jirr". Engine must be KILLED before debugging, restarted ONLY after all fixes verified. Workflow: (1) Kill engine, (2) Fix bugs, (3) Verify import OK, (4) Test with dry-run, (5) Restart.

118. **Evolved config MUST preserve mode-specific sub-configs (CRITICAL)** — `_apply_evolved_config()` was overwriting scalper's risk_per_trade_pct (9%→3%) and leverage_base (25x→20x). Fix: save/restore mode-specific configs around evolved config application. Without this, scalper settings silently revert after first evolution cycle.

119. **Position verification after entry** — After market order, verify position exists on Binance before placing SL/TP. Phantom entries can leave SL/TP orphaned.

120. **Entry retry with size reduction** — On "Exceeded maximum allowable position" error, retry at 50% then 25% size before giving up.

121. **Daily PnL tracking + minimum balance guard** — Track cumulative daily PnL, pause at -$3 loss or balance below $35. Update in `_close_position()`, reset in `_daily_reset()`.

122. **Limit order price must be on correct side of market** — Limit buy must be BELOW current price, limit sell must be ABOVE. Binance rejects with "Price not increased by tick size" if on wrong side. After rounding, verify: `if LONG and price >= current: price = current * 0.997`.
123. **`execute_code` redacts secrets — use `terminal()` for API key scripts** — The `execute_code` tool auto-redacts strings matching `API_KEY=` and `API_SECRET=` patterns in inline Python code. When the script reads `.binance_keys` (which contains `API_KEY=xxx` / `API_SECRET=xxx`), the redaction mangles variable assignments causing SyntaxError. **Fix:** Write the script to `/tmp/check_pos.py` via `write_file()`, then run via `terminal(command='python3 /tmp/check_pos.py')`. The `write_file` + `terminal` path does NOT trigger redaction. Never put Binance key-reading logic inside `execute_code` inline code.
124. **Duplicate process kill notifications are NORMAL** — When restarting a background engine, the old process gets SIGKILL'd and Hermes sends "Background process completed (exit code -9)" notifications. This is EXPECTED, not an error. Don't alarm the user. Verify the NEW process is running with `ps aux | grep <process>` and check latest log lines. If new PID is alive and logging, everything is fine. Brief response: "Engine aman, PID XXX masih jalan. Yang ke-kill itu process lama."

102. **OpenClaw tools directory structure requirement** — OpenClaw tools (watchdog, reflection, vault, hids, etc.) use `Path(__file__).resolve().parent.parent` to find the project root. They MUST be in a `tools/` subdirectory under the project root, NOT flat in a single directory. Structure:
    ```
    openclaw/
    ├── tools/
    │   ├── watchdog.py
    │   ├── reflection.py
    │   ├── vault.py
    │   └── ...
    └── skills/
        └── hermes/
            ├── scripts/
            └── references/
    ```
    If tools are flat in `openclaw_tools/`, the parent.parent path resolves wrong and imports fail silently with `'NoneType' object has no attribute '__dict__'` (the dataclass `__module__` lookup fails because the module isn't in `sys.modules`).

103. **`sys.modules` registration for dataclass-heavy modules** — When using `importlib.util.spec_from_file_location()` to load Python modules dynamically, modules with `@dataclass` decorators MUST be registered in `sys.modules` BEFORE `exec_module()`. Without registration, the dataclass processor tries to look up `cls.__module__` in `sys.modules` and gets `None` → `'NoneType' object has no attribute '__dict__'`. Fix:
    ```python
    spec = importlib.util.spec_from_file_location('module_name', 'path.py')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['module_name'] = mod  # MUST register BEFORE exec
    spec.loader.exec_module(mod)
    ```

104. **Find Telegram group chat ID from config** — When you need to send messages to a Telegram forum topic but don't know the group chat ID, check `~/.hermes/config.yaml` under `telegram:` → `allowed_chats:`. The value is the group chat ID (e.g., `-1003899936547`). For direct bot alerts (not via Hermes), use this ID as `chat_id` with `message_thread_id` for the specific topic.

105. **Strengthened data fabrication rule (CRITICAL UPDATE)** — Pitfall #95 covers "never fabricate data" but this session demonstrated how severe the consequence is. User said: "mona yang bener lah salah semua itu, jangan ngarang lagi bos dan kerja yang bener ini duit beneran bukan duit demo jadi jangan main main ya cukup sekali ini saja oke sayang yang pinter". Key additions:
    - Don't fabricate even "example" data to illustrate a pattern — if you don't have real data, say so
    - Don't create fake trades.json or signal_performance.json files with generated data
    - When Binance API returns 418 (IP banned), the correct response is "IP banned, can't check" — NOT generating plausible-looking trade history
    - The user explicitly said "cukup sekali ini saja" (just this once) — meaning they will NOT tolerate a second offense
    - This applies to ALL real-money contexts, not just Binance — any financial data (wallet balances, TX history, portfolio values) must come from the actual API or be explicitly marked as unavailable

98. **Alert discipline: ONLY trade open/close (CRITICAL)** — see `references/telegram-alert-integration.md` for implementation templates

106. **Agent Skills Hub for discovering agent tools** — `https://agentskillshub.top/best/` indexes 25,000+ AI agent tools across 79 categories. Useful for finding MCP servers, Claude skills, and agent frameworks. Relevant categories for crypto agents: Telegram Bot (30 tools), Workflow Automation (10 tools), Monitoring & Observability, Security Auditing. Top picks: AstrBot (★33.7k, Python MCP server), telegram-mcp (★1.2k, Python), bux (★348, browser automation + Telegram), dagu (★3.5k, Go workflow engine). — Autonomous engines must send Telegram alerts ONLY on two events: (1) trade OPENED, (2) trade CLOSED. No periodic status updates, no scan summaries, no balance reports, no "monitoring X pairs" messages. The user explicitly said "jangan terus-menerus, 10 menit sekali aja" and then clarified: only when there's a position or PnL change. After all positions close, one line max. The only exception is EMERGENCY alerts (SL failed, IP banned, engine crashed). Violating this causes alert fatigue → user mutes the bot → misses real alerts. Implementation: add `send_telegram_alert()` calls in `_execute_trade()` and `_close_position()` ONLY. See `references/rate-limiter-implementation.md` for code templates.
