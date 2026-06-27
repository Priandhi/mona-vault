# Pre-Flight Test Suite for Crypto Trading Engines

Before ANY live trading deployment, run a comprehensive pre-flight test suite. This validates ALL systems work together before risking real money.

## Test Categories (10 total)

### 1. API Connectivity
- `GET /fapi/v1/ticker/price?symbol=BTCUSDT` — returns price in <200ms
- Measure latency — flag if >500ms

### 2. API Authentication
- `GET /fapi/v2/balance` with HMAC signature — returns balance
- Verify API key has futures permission

### 3. Balance Check
- Balance must exceed `min_balance_to_trade` (default $40)
- FAIL if balance = $0 (deposit required)

### 4. Signal Generators (13 total)
Test each signal individually:
- OI Divergence, Funding Rate, CVD, Taker Volume, Order Flow, Basis
- Structure, Volume Profile, Fear & Greed, DXY
- Cross-Exchange Funding, Liquidation, SMC Confluence
- Each should return a SignalResult with score and signal direction

### 5. Safety Rails (6 scenarios)
- Per-pair cooldown (300s) — must block
- Flip prevention (600s) — must block after cooldown expires
- Hourly trade limit (4/hour) — must block
- Min balance check ($40) — must block with $10 balance
- Circuit breaker (7% drawdown) — must trigger
- Position sizing — verify qty calculation

**PITFALL:** Flip prevention test needs fresh RiskEngine. If per-pair cooldown (300s) is active, it blocks BEFORE flip prevention (600s) kicks in, giving false result. Create new instance with `_pair_last_trade` set 700s ago.

### 6. Order Parameters
For each tradeable symbol:
- Fetch `exchangeInfo` → extract `LOT_SIZE.stepSize`, `PRICE_FILTER.tickSize`, `MIN_NOTIONAL`
- Verify `_round_qty()` and `_round_price()` produce valid values
- Test leverage setting via `set_leverage()`

### 7. Algo Order API (SL/TP)
- Place a test SL order with intentionally bad price → expect error code (confirms endpoint works)
- `/fapi/v1/algoOrder` with `algoType=CONDITIONAL`
- Expected: `{'code': -4013, 'msg': 'Price less than min price.'}` = endpoint active

### 8. Position Reconciliation
- `GET /fapi/v2/positionRisk` → count open positions
- Compare with local state
- Log any drift

### 9. DXY Fallback
- Yahoo Finance (expected: 429)
- CoinGecko fallback (expected: OK)
- Both should return price data

### 10. Paper Trade Simulation
Full end-to-end cycle:
1. Open position (LONG BTC @ $62,000)
2. Simulate TP1 hit → verify breakeven SL moved
3. Verify trailing stop activated
4. Simulate trailing SL hit → verify close
5. Check PnL calculation

## Output Format

```
============================================================
🚀 PRE-FLIGHT RESULTS
============================================================
  ✅ API Connectivity: BTC=$62,192 (88ms)
  ✅ Signals: 13/13 passed
  ✅ Safety Rails: 6/6 passed
  ❌ Balance Check: $0 — DEPOSIT REQUIRED
  ...
  Total: 44 | Passed: 43 | Failed: 1
  🟡 1 NON-CRITICAL FAILURES
============================================================
```

## Pass Criteria
- **100% pass** = ready for live
- **Non-critical failures** (balance $0, Yahoo 429) = engine functional, user action needed
- **Critical failures** (signal errors, rail failures) = DO NOT GO LIVE

## Script Location
`~/.hermes/scripts/mona_preflight_test.py`

## Usage
```bash
python3 mona_preflight_test.py        # Full test suite
# Results: ~/.hermes/logs/preflight_report.json
```
