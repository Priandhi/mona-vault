# High Leverage Position Sizing

## The Problem
With small accounts ($50), traders often use high leverage (25-75x) to make meaningful profits.
But if position size is too large, one bad trade wipes the account.

## The Solution: Risk-Based Position Sizing

### Formula
```
size_usdt = risk_amount / stop_distance_pct
```

Where:
- `risk_amount = balance * max_position_pct` (e.g., $50 * 0.03 = $1.50)
- `stop_distance_pct = (atr * sl_atr_mult) / price` (e.g., 1.5%)

### Example Calculation
Balance: $50
Risk: 3% ($1.50)
ATR: $750 (BTC)
Price: $60,000
SL multiplier: 1.5

```
stop_distance = $750 * 1.5 = $1,125
stop_distance_pct = $1,125 / $60,000 = 1.875%
size_usdt = $1.50 / 0.01875 = $80
```

So with 35x leverage, you'd open an $80 position (not $50 * 35 = $1,750!).

### Why This Works
- Risk is always $1.50 regardless of leverage
- Higher leverage → tighter SL → smaller position
- Lower leverage → wider SL → larger position
- Both have same dollar risk

### Alternative: Margin-Based Sizing (Hexa YUNA preference)

When user wants **fixed margin per trade** (predictable $X notional regardless of SL), use margin-based:

```python
def calculate_position_size_margin_based(margin_usd, leverage, entry):
    notional = margin_usd * leverage
    qty = notional / entry
    return qty, notional
```

**When to choose each:**
- **Risk-based:** Professional risk management, consistent dollar risk per trade. Default for serious systems.
- **Margin-based:** Fixed budgets, predictable per-trade cost, simpler mental model. YUNA dozero uses this ($90 margin × 20x = $1,800 notional).

Risk-based is theoretically superior (constant $ risk) but margin-based is more intuitive for small accounts where the user wants to know "this trade costs me $X margin". Ask user before switching.

## Dynamic Leverage

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

Example:
- Score 85 → 50x leverage
- Score 75 → 37x leverage
- Score 65 → 25x leverage

## Liquidation Safety: Leverage × SL Math Rule (CRITICAL)

**Lesson (YUNA 2026-06-17):** High leverage and tight SL are mathematically incompatible. You CANNOT use 75x leverage with a 4% SL — the position liquidates BEFORE the SL triggers.

### The Math
- Liquidation distance (isolated, no fees) ≈ 1 / leverage
- 20x lev → liquidation at ~5% price move
- 50x lev → liquidation at ~2% price move
- 75x lev → liquidation at ~1.3% price move

**The SL must be SMALLER than the liquidation distance** — otherwise the position blows up before the SL has a chance to trigger.

**With 80% safety buffer:** `SL_max = 0.8 / leverage`

### Reference Table

| Leverage | Liq distance | Max safe SL (80% buffer) | 4% SL works? |
|----------|--------------|--------------------------|--------------|
| 10x | 10% | 8.0% | ✅ (4% << 8%) |
| 20x | 5% | 4.0% | ✅ (exactly at limit) |
| 25x | 4% | 3.2% | ❌ (SL too wide) |
| 30x | 3.3% | 2.7% | ❌ |
| 50x | 2% | 1.6% | ❌ (any SL > 1.6% liquidates) |
| 75x | 1.3% | 1.1% | ❌ (any SL > 1.1% liquidates) |

### Mandatory Pre-Trade Validation Function

Add this to any leveraged trading engine. Call before placing any order:

```python
def validate_leverage_sl(leverage: int, sl_pct: float) -> bool:
    """Liquidation safety check.
    Liquidation distance ≈ 1/leverage (isolated, no fees).
    80% safety buffer = SL must be < 0.8 × liq_distance.
    Raises ValueError if SL is too wide for the leverage.
    """
    if leverage <= 0:
        raise ValueError(f"Invalid leverage: {leverage}")
    liq_distance = (1.0 / leverage) * 0.8   # 80% safety buffer
    if sl_pct >= liq_distance:
        raise ValueError(
            f"REJECTED: SL {sl_pct*100:.1f}% not safe for {leverage}x leverage. "
            f"Max safe SL: {liq_distance*100:.1f}%"
        )
    return True
```

**Use:** `validate_leverage_sl(20, 0.04)` → OK. `validate_leverage_sl(50, 0.04)` → raises ValueError.

### Why This Matters in Practice

**The 75x trap:** A scanner finds a 15m signal with 4% SL. Engineer thinks "let me use Binance max 75x for higher ROI." But 75x liquidates at 1.3% — the position explodes LONG before the SL triggers. Result: -100% loss on margin instead of the intended -4% loss.

**The 20x sweet spot:** With 20x leverage, you can use a 4% SL and have a 1% buffer before liquidation. This is the highest leverage that's mathematically safe with a typical 4% SL.

**Applies to ALL leveraged setups:** Binance Futures, Bybit, OKX, dYdX, Hyperliquid, GMX, etc. The math is the same everywhere.

## Common Mistakes

1. **Using balance * leverage as position size**
   - Wrong: $50 * 35x = $1,750 position
   - Right: $1.50 / 1.5% = $100 position

2. **Fixed percentage without ATR adjustment**
   - Wrong: Always 2% of balance
   - Right: risk_amount / (ATR-based SL distance)

3. **Not capping max position**
   - Always cap at: balance * max_position_pct * leverage
   - Prevents accidental oversized positions

4. **Ignoring funding rate impact**
   - High leverage = higher funding rate impact
   - Factor into risk calculation

## Config Template (Small Account)

```python
# Risk Management
max_position_pct = 0.03        # 3% risk per trade
max_total_exposure = 0.09      # 9% max total
max_drawdown_pct = 0.07        # 7% daily drawdown → pause
default_leverage = 35
max_leverage = 50

# Dynamic Leverage
dynamic_lev_min = 25
dynamic_lev_max = 50
dynamic_lev_threshold = 80

# TP/SL (Quick Profits)
sl_atr_mult = 1.5              # Tight SL
tp1_risk_reward = 1.2          # TP1 = 1.2x risk
tp2_risk_reward = 2.0          # TP2 = 2x risk
tp3_risk_reward = 3.0          # TP3 = 3x risk
tp1_close_pct = 0.55           # Close 55% at TP1
tp2_close_pct = 0.30           # Close 30% at TP2
tp3_close_pct = 0.15           # Close 15% at TP3
```
