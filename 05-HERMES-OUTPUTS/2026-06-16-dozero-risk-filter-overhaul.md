# Receipt: Dozero.X Post-Mortem BANK/INX/AR + Risk Filter Overhaul

**Date:** 2026-06-16
**Agent:** YUNA — The Strategist
**Task:** Investigate loss cause + apply B+C fix (close losers + rewrite risk filters)
**Mas:** Hexa (@0xjosee)

## Posisi
**Closed (manual market close):**
- BANKUSDT LONG — realized -$269.68
- INXUSDT LONG — realized -$86.11
- ARUSDT LONG — realized -$87.26
- **Total realized loss: -$443.05**

**Active positions after fix:** 7 (BANK/INX/AR removed)

## PnL
- Pre-fix day uPnL: -$363.49 (mostly from BANK/INX/AR)
- Realized (closed): -$443.05
- Post-close current uPnL: +$104.81 (7 positions)
- Net day (realized + unrealized): -$338.24

## Result

### ✅ Closed
All 3 loss positions manually closed via market order with reduceOnly=true.

### ✅ Risk Filter Overhaul Applied

**File: `config/settings.py`**
- `MAX_MARGIN_PER_TRADE`: 100.0 → **5.0** (20x reduction, matches user rule)
- `MIN_PRICE_USD`: 0 → **0.05** (skip dust tokens)
- `MIN_SL_DISTANCE_PCT`: 0 → **0.02** (2% min SL — was 1.2% allowed)
- `MAX_SL_DISTANCE_PCT`: 0 → **0.08** (8% max SL)
- `MIN_VOLUME_USDT`: 500K → **2M** (4x stricter, skip thin liquidity)
- Added `LEVERAGE_TIERS` dict:
  - high (≥$10): 50x max (BTC/ETH/SOL)
  - mid  (≥$1):  25x max (BNB/LINK/AVAX)
  - low  (≥$0.10): 15x max (ADA/XRP/DOGE)
  - dust (<$0.10): REJECTED

**File: `engine/risk.py`**
- `build_trade_plan()` — added 3 new checks:
  1. SL distance < 2% → reject (would be 50x wipeout)
  2. SL distance > 8% → reject (illiquid stops)
  3. Price < $0.05 → reject (dust token)
- `_get_leverage_cap_for_price(price)` — new helper
- Pass `current_price` to enable filters (was None)
- Float epsilon (1e-6) on SL boundary checks (2.0% == 2.0% should pass)

**File: `engine/executor.py`**
- `_get_leverage_for_symbol()` — new method, returns min(binance_max, tier_cap)
- `_emergency_close()` — new method, market-close if SL fails
- Replaced 5-order SL/TP block with **1 SL + 1 Main TP only** (testnet limit fix)
- SL placement: 3 retry attempts with auto-widen (1.5x) on -2021
- If all 3 SL attempts fail → **EMERGENCY CLOSE** (no unprotected positions)
- Main TP at TP2 level (2R target) instead of TP3 (3R)
- `calculate_position_size()` now takes `leverage` param (use tier-capped, not max)

**File: `config/connection.py`**
- Added `market_order()` method (was missing, needed for emergency close)

**File: `engine/core.py`**
- `build_trade_plan()` call now passes `current_price` for price-tier filter

### ✅ Verified
- All modules import cleanly
- Test suite: BANK (1.85% SL, $0.04) → REJECTED ✅
- Test suite: INX (1.2% SL, $0.008) → REJECTED ✅
- Test suite: AR (1.23% SL, $2.12) → REJECTED ✅
- Test suite: BTC (3% SL, $100k) → PASSED ✅
- Test suite: ADA (3% SL, $0.50, low tier) → PASSED ✅
- PM2 restarted, new volume threshold 2M active (498 pairs vs 525 before)
- No syntax/import errors in logs

## Decisions

1. **Hard cap margin $5** — matches Hexa's user rule. $100 was 20x oversize.
2. **Tiered leverage** — micro-caps can't handle 50x even with valid signals.
3. **Min SL 2%** — protects against "tight SL + high leverage" wipeout (BANK was 1.85% SL with 50x = 92% loss potential).
4. **1 SL + 1 Main TP** — testnet max stop order limit is ~2-3 per symbol. Trying 5 = guaranteed failure. Mainnet also has limits (usually 10/symbol, but new symbols vary).
5. **Emergency close on SL fail** — Hexa's #1 rule: "unprotected position = worse than small loss".
6. **Price < $0.05 = reject** — dust tokens have wide spreads, manipulation risk, and "lottery ticket" volatility.

## Issues

1. **Mainnet API keys still 401** — `~/mona-workspace/vault/.binance_keys` expired/revoked. Not auto-fixed (needs Hexa action).
2. **BANK/INX/AR losses realized** — -$443.05 already booked in testnet.
3. **Dozero auto cycle runs every 30 min** — won't see new trades until next signal + cooldown release.

## Next Steps

- [ ] **Binance mainnet API key rotation** (Hexa needs to do this from Binance UI)
- [ ] Monitor 2-3 days with new filters, validate WR stays > 50%
- [ ] When WR stable > 55% for 5 days + max DD < 10% → consider mainnet
- [ ] Backtest new filter config on historical data
- [ ] Update binance-futures-trading skill with lessons learned
- [ ] Consider adding position-level stop loss (not just entry SL) — manage open positions

## Related Files

- `/home/ubuntu/dozero/config/settings.py` — config overhaul
- `/home/ubuntu/dozero/engine/risk.py` — validation filters + leverage helper
- `/home/ubuntu/dozero/engine/executor.py` — 1 SL + 1 Main TP + emergency close
- `/home/ubuntu/dozero/engine/core.py` — pass current_price to risk
- `/home/ubuntu/dozero/config/connection.py` — added market_order
- `/home/ubuntu/dozero/data/traded.json` — cooldown tracker (still tracking 9 symbols)
- `/home/ubuntu/dozero/logs/auto.log` — execution logs (1,666 -4045 errors now should drop to ~0)
