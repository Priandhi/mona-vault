# Pre-Flight Test Suite for Crypto Futures Engine

## Purpose
Run BEFORE going live. Validates all systems work correctly. Target: 100% pass.

## Test Matrix (44 tests)

### 1. API Connectivity (2 tests)
- GET /fapi/v1/ticker/price → BTC price, latency < 200ms
- GET /fapi/v2/balance → authenticated, balance returned

### 2. Balance Check (1 test)
- Balance > minimum threshold ($40)
- If $0: BLOCKED — deposit required

### 3. All 13 Signals (13 tests)
For each signal, verify it returns a valid SignalResult:
1. OI Divergence — /futures/data/openInterestHist
2. Funding Rate — /fapi/v1/fundingRate
3. CVD — /fapi/v1/aggTrades
4. Taker Volume — /futures/data/takerlongshortRatio
5. Order Flow — /fapi/v1/depth
6. Basis — /fapi/v1/premiumIndex
7. Market Structure — BOS/CHOCH from klines
8. Volume Profile + VWAP — from 15m klines
9. Fear & Greed — alternative.me API
10. DXY — CoinGecko fallback (Yahoo always 429)
11. Cross-Exchange Funding — Bybit + OKX
12. Liquidation Heatmap — /fapi/v1/allForceOrders
13. SMC Confluence (DOZERO.X) — multi-timeframe analysis

### 4. Safety Rails (6 tests)
- Per-pair cooldown (300s) — verify blocks same-pair within window
- Flip prevention (600s) — verify blocks direction reversal within window
- Hourly trade limit (4/hr) — verify blocks after limit
- Min balance check ($40) — verify blocks below threshold
- Circuit breaker (7% emergency) — verify triggers on drawdown
- Position sizing — verify qty calculation correct for balance

### 5. Order Parameters (6 tests)
For BTC, ETH, SOL, BNB, XRP:
- Fetch exchange info → verify stepSize, tickSize, minNotional
- Set leverage → verify response

### 6. Algo Order API (1 test)
- POST /fapi/v1/algoOrder with invalid price → verify endpoint responds (not -4120)

### 7. Position Reconciliation (1 test)
- GET /fapi/v2/positionRisk → verify returns positions list

### 8. DXY Fallback (2 tests)
- Yahoo Finance → verify 429 (expected, non-critical)
- CoinGecko → verify returns price

### 9. Rate Limiter (1 test)
- Send 7 requests rapidly → verify 6th+ waits

### 10. Telegram Alerts (1 test)
- Send test message to topic → verify no error

### 11. Full Engine Scan (1 test)
- Scan BTCUSDT → verify returns analysis with 12+ signals

### 12. Cron Jobs (1 test)
- Verify futures-scanner + futures-daily-report exist and enabled

### 13. Paper Trade Simulation (1 test)
- Open paper position → hit TP1 → verify breakeven SL → trailing → close

## Script Location
`~/.hermes/scripts/mona_preflight_test.py`

## Running
```bash
cd ~/.hermes/scripts && python3 mona_preflight_test.py
```

## Expected Output
```
Total: 44 | Passed: 44 | Failed: 0
🟢 ALL PASSED — Engine ready for live trading
```

If any test fails, FIX IT before going live. The only acceptable failure is Balance Check ($0) — deposit required.
