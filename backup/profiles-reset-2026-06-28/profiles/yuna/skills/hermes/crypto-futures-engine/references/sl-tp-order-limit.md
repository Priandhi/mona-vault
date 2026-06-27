# SL/TP Order Limit (-4045) — Detailed Post-Mortem

**Session origin:** Dozero.X 2026-06-16 (Hexa trading account)
**Severity:** CRITICAL — 3 unprotected positions hit -256% / -110% / -85% ROE
**Status:** Fix shipped, verified, Dozero testnet running with new filters

## The Failure Mode

When a strategy places more stop orders per symbol than Binance allows, the API returns:

```json
{
  "code": -4045,
  "msg": "Reach max stop order limit."
}
```

**Per-symbol stop order limits (Binance Futures):**
- **Testnet:** ~2-3 stop orders/symbol (very tight — easy to hit)
- **Mainnet:** typically 10-20 stop orders/symbol, but **new listings often start at 2-3**
- **Conditional orders in general:** Some symbols have per-account caps regardless

The dangerous part: this is a SILENT failure in a noisy way. Strategies often log "SL placement failed" and continue without a stop. The position then runs unprotected.

## Dozero's Original Anti-Pattern

The executor placed **5 stop orders per position**:
1. SL (STOP_MARKET, close_position=true)
2. TP1 (TAKE_PROFIT_MARKET, 30% qty, close_position=false)
3. TP2 (TAKE_PROFIT_MARKET, 30% qty, close_position=false)
4. TP3 (TAKE_PROFIT_MARKET, 40% qty, close_position=false)
5. Main TP (TAKE_PROFIT_MARKET, close_position=true)

On testnet, all 5 failed. Realized -$443.05 in BANK/INX/AR over 90 minutes of floating losses.

## The Fix (4 changes, all required)

### 1. Single SL + Single Main TP

```python
# Place 1 SL (STOP_MARKET, close_position=true) + 1 Main TP (TAKE_PROFIT_MARKET, close_position=true)
# Main TP = TP2 (2R target) — conservative, fewer orders
```

### 2. SL Retry + Widen Logic (3 attempts)

```python
for attempt in range(3):
    sl_order = algo_order(symbol, side, trigger_price=sl_price,
                          order_type="STOP_MARKET", close_position=True)
    if not sl_order.get("_error"):
        sl_placed = True
        break
    if sl_order.get("code") == -4130:  # Already exists = protected
        sl_placed = True
        break
    if sl_order.get("code") == -2021:  # Would immediately trigger
        # Widen by 1.5x each attempt
        sl_price = entry * (1 - pct_to_sl * (1.5 ** (attempt + 1)))
        if abs(sl_price - entry) / entry > 0.08:  # Cap at 8% from entry
            break
```

### 3. Emergency Close on SL Failure

```python
if not sl_placed:
    # Market close the position immediately
    market_order(symbol, close_side, qty, reduce_only=True)
    return  # Abort trade
```

**Why this matters:** Unprotected position = guaranteed loss. A small realized loss (-$5) is always better than a runaway floating loss (-$200+). This is Hexa's #1 hard rule.

### 4. Filter Signals Before They Reach the Executor

| Filter | Value | Why |
|---|---|---|
| Min price | $0.05 | Dust tokens = wide spreads + manipulation |
| Min SL distance | 2% | 1% SL + 50x leverage = 50% loss on first candle |
| Max SL distance | 8% | Wider = illiquid stops, slippage nightmare |
| Min 24h volume | $2M | $500k pairs have 1-2 minute liquidation cascades |
| Leverage cap | Tiered by price | See below |

## Leverage Tier Table

| Price Tier | Range | Max Leverage | Why |
|---|---|---|---|
| high | ≥ $10 | 50x | BTC/ETH/SOL — proven liquidity, tight spreads |
| mid | ≥ $1 | 25x | BNB/LINK/AVAX — decent liquidity, 1-2 pip spread |
| low | ≥ $0.10 | 15x | ADA/XRP/DOGE — wider spreads, more volatility |
| dust | < $0.10 | REJECTED | No bid at SL level during cascade |

**Effective formula:** `effective_leverage = min(binance_max_lev, tier_cap)`

## Float Boundary Gotcha

When validating SL distance with `if sl_distance_pct < MIN_SL_DISTANCE_PCT`, exact-boundary signals (2.00% == 2.00%) get rejected due to float precision. **Always use 1e-6 epsilon:**

```python
# ❌ WRONG — rejects exact boundary
if sl_distance_pct < MIN_SL_DISTANCE_PCT:
    return None  # Rejects 2.0% SL!

# ✅ CORRECT — allows boundary
if sl_distance_pct < MIN_SL_DISTANCE_PCT - 1e-6:
    return None
```

## Verification

```bash
# Quick smoke test
cd /home/ubuntu/dozero
python3 -c "
import sys; sys.path.insert(0, '.')
from engine.risk import RiskEngine
re = RiskEngine()
plan = re.build_trade_plan('BANKUSDT', 'LONG', 0.0432, 0.0424, score=76, grade='B', current_price=0.0432)
assert plan is None, 'BANK should be rejected'
plan = re.build_trade_plan('AVAXUSDT', 'LONG', 5.0, 4.85, score=85, grade='A', current_price=5.0)
assert plan is not None, 'AVAX should pass'
print('✅ Filter logic working')
"

# Full test suite (re-runnable)
python3 ~/.hermes/profiles/yuna/skills/crypto/binance-futures-trading/scripts/sl_tp_filter_test.py
```

## Testnet vs Mainnet — Key Differences

| Aspect | Testnet | Mainnet |
|---|---|---|
| Max stop orders/symbol | ~2-3 | 10-20 (new listings lower) |
| Auto-liquidation | No (positions float forever) | Yes (positions get MC'd) |
| Balance | Fake USDT (5k typical) | Real money |
| Realized PnL matters? | For learning, not money | For survival |

**Implication:** Testnet positions can hit -1000% ROE without closing. This is GOOD for emergency close testing (you see the unprotected damage), but BAD for understanding what mainnet would do (mainnet auto-liquidates at ~5-10% margin remaining).

## When to Apply This Pattern

Any Binance Futures strategy that:
- Places more than 1 stop order per position
- Trades on testnet (limits are tightest)
- Has 13+ confirmation checks that might pass exotic signals
- Doesn't have an emergency close path

## Dozero Files Changed (reference implementation)

- `dozero/config/settings.py` — added `LEVERAGE_TIERS`, `MIN_PRICE_USD`, `MIN_SL_DISTANCE_PCT`, `MAX_SL_DISTANCE_PCT`, raised `MIN_VOLUME_USDT` to $2M
- `dozero/engine/risk.py` — `build_trade_plan()` with 3 new filter checks + `_get_leverage_cap_for_price()` helper
- `dozero/engine/executor.py` — 1 SL + 1 Main TP only, SL retry with widen, `_emergency_close()` method
- `dozero/config/connection.py` — added `market_order()` for emergency close
- `dozero/engine/core.py` — pass `current_price` to `build_trade_plan()`

## See Also

- `binance-futures-trading` SKILL.md → "SL/TP Order Limit & Emergency Close" section (high-level rules)
- `scripts/sl_tp_filter_test.py` — re-runnable test suite
- Vault receipt: `obsidian-vault/05-HERMES-OUTPUTS/2026-06-16-dozero-risk-filter-overhaul.md`
