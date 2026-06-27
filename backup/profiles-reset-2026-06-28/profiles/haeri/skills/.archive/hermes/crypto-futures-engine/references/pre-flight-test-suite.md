# Pre-Flight Test Suite

Run BEFORE live trading. Every test must pass. One critical failure = NO LIVE.

## Location
`~/.hermes/scripts/mona_preflight_test.py`

## Usage
```bash
python3 mona_preflight_test.py          # Run all tests
python3 mona_preflight_test.py --fix    # Run + auto-fix
```

## 14 Tests Covered
1. **API Connectivity** — Binance Futures REST reachable, BTC price valid
2. **API Authentication** — Signed endpoints work (balance, positions)
3. **Balance Check** — USDT balance ≥ $40 minimum
4. **All 13 Signals** — Each signal generator returns valid data (OI, Funding, CVD, Taker, OrderFlow, Basis, Structure, VolProfile, FearGreed, DXY, XExchange, Liquidation, SMC)
5. **Safety Rails** — Per-pair cooldown, flip prevention, hourly limit, min balance, circuit breaker, position sizing
6. **Order Parameters** — LOT_SIZE, PRICE_FILTER, MIN_NOTIONAL filters valid for each symbol
7. **Algo Order API** — SL/TP endpoint responds (not 404)
8. **Position Reconciliation** — Can read open positions from Binance
9. **DXY Fallback** — Yahoo → CoinGecko → Binance BTC proxy chain works
10. **Rate Limiter** — Blocks after N requests
11. **Telegram Alerts** — Can send to topic
12. **Full Engine Scan** — End-to-end scan produces valid results
13. **Cron Jobs** — Scanner + daily report active
14. **Paper Trade Simulation** — Full cycle: open → TP1 → breakeven SL → trailing → close

## Exit Codes
- `0` = All pass (or non-critical failures only, e.g. balance $0)
- `2` = Critical failures — DO NOT GO LIVE

## Report
Saved to `~/.hermes/logs/preflight_report.json`

## PITFALLS

### Flip prevention test must isolate from per-pair cooldown
Per-pair cooldown (300s) fires BEFORE flip prevention (600s) in `_check_safety_rails()`. To test flip prevention independently:
- Create a fresh RiskEngine (no prior trades)
- Set `_pair_last_trade[sym]` to 700s ago (past per-pair cooldown)
- Set `_pair_last_side[sym]` to opposite direction
- Then `_check_safety_rails` will hit the flip check

### DXY signal method name
In `signals.py`, the method is `dxy()` not `dxy_signal()`. The gather call uses `self.dxy(symbol)`.

### Balance check is non-critical
Balance $0 means "deposit required" — engine is still functional, just can't trade. Pre-flight exits 0 (not 2) when only balance check fails.

### SMC Confluence often returns score=0
DOZERO.X SMC threshold is 50 — most scans won't trigger it. This is expected. SMC only fires on strong multi-confluence setups (MTF alignment + Virgin FVG + Sweep + Displacement).
