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
