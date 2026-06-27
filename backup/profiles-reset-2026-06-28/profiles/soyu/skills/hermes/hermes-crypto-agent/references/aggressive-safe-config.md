# Aggressive-Safe Mode Configuration

**Created:** June 2026
**Purpose:** Balance between aggressive returns and capital protection for small accounts ($50-60)

## Philosophy

User wants "aggressive tapi tetap aman dan cuan" — higher risk per trade but stricter signal requirements. The key insight: **higher risk per trade (5%) with higher signal bar (min score 50, min 4 signals)** produces better results than lower risk (4%) with lower signal bar (min score 40, min 3 signals).

## Settings

```python
# Signal Thresholds (SELECTIVE — Quality Entries)
min_score_to_trade = 40        # Raised from 35 (Jun7) — higher quality entries
min_signals_agree = 3          # 3 signals agreeing is solid enough

# Risk Management (AGGRESSIVE BUT SAFE)
max_position_pct = 0.05        # 5% risk per trade ($2.75 on $55)
max_total_exposure = 0.12      # 12% max total ($6.60) — reduced from 15% (Jun7)
max_drawdown_pct = 0.08        # 8% daily drawdown → pause ($4.40)
max_simultaneous_positions = 3 # Max 3 positions at once (Jun7, was unlimited)
balance_reserve_pct = 0.20     # Always keep 20% balance free — $11 (Jun7, NEW)
default_leverage = 35          # 35x default (safer than 50x)
max_leverage = 50              # 50x max (was 75x — too risky)

# Dynamic Leverage (SMART)
# Score 50-60: 20x leverage
# Score 60-70: 30x leverage
# Score 70-80: 40x leverage
# Score 80+:   50x leverage
dynamic_lev_min = 20
dynamic_lev_max = 50
dynamic_lev_threshold = 80

# Trade Limits (SELECTIVE)
max_daily_trades = 5           # Max 5 trades/day (was 8)
min_time_between_trades_sec = 900  # 15 min cooldown (was 10)

# Stop Loss (TIGHT — Protect Capital)
sl_atr_mult = 1.2              # Tighter SL (was 1.5)
trailing_atr_multiplier = 1.5  # Tighter trailing (was 2.0)

# Take Profit (AGGRESSIVE — Lock Profits)
tp1_risk_reward = 1.5          # TP1 = 1.5x risk (was 1.0)
tp2_risk_reward = 2.5          # TP2 = 2.5x risk (was 2.0)
tp3_risk_reward = 4.0          # TP3 = 4x risk (was 3.5)
tp1_close_pct = 0.40           # Close 40% at TP1 (was 50%)
tp2_close_pct = 0.35           # Close 35% at TP2 (was 30%)
tp3_close_pct = 0.25           # Close 25% at TP3 (runner)

# Symbols (TOP 10 ONLY — More Focus)
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT',
           'DOGEUSDT', 'ADAUSDT', 'AVAXUSDT', 'SUIUSDT', 'ARBUSDT']

# Scan Settings
scan_interval_sec = 90         # 90 seconds (was 120)
balance_check_interval_sec = 300  # 5 minutes

# Profit Targets
daily_target_usd = 8.0         # $8/day target (realistic)
weekly_target_usd = 50.0       # $50/week target
```

## Why This Works

### Aggressive:
- Risk 5% = position lebih gede ($2.75 vs $2.22)
- TP 1.5x/2.5x/4x = profit target lebih tinggi
- Scan 90 detik = lebih cepat detect peluang
- Max 3 posisi = fokus pada best setups

### Safe:
- Min score 40 = hanya trade signal yang layak
- Min signals 3 = butuh konfirmasi
- Max leverage 50x = gak terlalu ekstrem
- **Balance reserve 20%** = selalu ada $11 bebas untuk opportunity baru
- **Max 3 positions** = gak over-commit modal
- Drawdown 8% = proteksi modal lebih ketat
- Tighter SL = cut loss lebih cepat

## Guard System (June 2026)

Three guards enforced BEFORE every entry in `analyze_and_trade()`:

### 1. Balance Reserve Guard
```python
reserve = balance * 0.20  # Always keep 20% free
if available < reserve:
    skip  # Don't entry
```
Prevents over-committing. With $54 balance, always keeps ~$11 free.

### 2. Max Positions Guard
```python
active_positions = count_positions_with_amt_nonzero()
if active_positions >= 3:
    skip  # Max 3 positions
```
Prevents concentration risk. Forces quality over quantity.

### 3. Usable Balance for Sizing
```python
usable_balance = balance - reserve  # 80% of balance
risk_amount = usable_balance * 0.05  # 5% of usable
```
Position size calculated from usable balance, not total balance.

### 4. Error Detection Fix
```python
# WRONG: Binance doesn't return {'error': ...}
if 'error' not in result:  # ← WRONG

# CORRECT: Check for orderId
if 'error' not in result and 'orderId' in result:  # ← CORRECT
```

**PITFALL:** Binance returns `{'code': -1022, 'msg': '...'}` on error, NOT `{'error': '...'}`. Always check for `'orderId' in result` to confirm success.

## Expected Returns

From $55.50 balance:
- Daily target: $8 (14.4% daily return)
- Weekly target: $50 (90% weekly return)
- Monthly target: $200 (360% monthly return)

**Note:** These are TARGETS, not guarantees. Actual returns depend on market conditions and signal quality.

## Comparison with Other Modes

| Setting | Conservative | Aggressive-Safe | Pure Aggressive |
|---|---|---|---|
| Risk/Trade | 3% | 5% | 6% |
| Min Score | 60 | 40 | 35 |
| Min Signals | 5 | 3 | 3 |
| Max Positions | 2 | 3 | 5 |
| Balance Reserve | 30% | 20% | 10% |
| Max Leverage | 35x | 50x | 75x |
| Max Trades/Day | 3 | 5 | 8 |
| Drawdown | 5% | 8% | 10% |
| Daily Target | $3 | $8 | $15 |

## Implementation

Config file: `~/.hermes/scripts/mona_futures_v2/config.py`
Auto-trade: `~/.hermes/scripts/mona_futures_auto.py --mode live --interval 90`

## Signal Tuning (Critical for Aggressive-Safe)

### OI Divergence
- Price < -0.3% and OI > +1.5% → LONG (score = min(50, oi_chg * 10))
- Price > +0.3% and OI < -1.5% → SHORT
- Price < -0.1% and OI > +0.5% → Mild LONG (score = min(25, oi_chg * 8))

### Funding Rate
- Rate > 0.008% → SHORT (score = -min(50, rate * 300))
- Rate < -0.008% → LONG (score = min(50, abs(rate) * 300))
- Rate > 0.003% → Mild SHORT (score = -min(25, rate * 200))

### Taker Volume
- Buy > 65% → STRONG_LONG (score = min(80, (buy_pct - 50) * 3))
- Buy < 35% → STRONG_SHORT
- Buy > 53% → LONG (score = (buy_pct - 50) * 2.5)

### FearGreed
- F&G ≤ 15 → score 90 (STRONG_LONG)
- F&G ≤ 25 → score 70 (STRONG_LONG)
- F&G ≥ 85 → score -90 (STRONG_SHORT)
- F&G ≥ 75 → score -70 (STRONG_SHORT)

### OrderFlow (CAPPED)
- Imbalance > 2 → LONG (score = min(50, (imbalance - 1) * 15))
- Imbalance < 0.5 → SHORT (score = -min(50, (1/imbalance - 1) * 15))

### Volume Profile
- POC > 0.3% → LONG (score += 25)
- VWAP > 0.2% → LONG (score += 15)

### Composite Calculation (CRITICAL)
```python
# ONLY count active signals (non-zero)
for s in signals:
    w = weights.get(s.name, 5)
    if abs(s.score) > 0:
        weighted_score += s.score * (w / 100)
        total_weight += w

composite = (weighted_score / total_weight * 100) if total_weight > 0 else 0
```
