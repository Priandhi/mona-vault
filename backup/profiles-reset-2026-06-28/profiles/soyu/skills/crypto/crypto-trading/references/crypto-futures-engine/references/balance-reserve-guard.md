# Balance Reserve Guard Pattern

Protects small accounts ($50-55) from deploying 100% of capital. Keeps reserve for high-conviction entries and prevents over-correlated positions.

## Config Parameters

### Aggressive Mode (for disposable capital)
```python
balance_reserve_pct: float = 0.20     # Always keep 20% free
max_simultaneous_positions: int = 3   # Hard cap on concurrent positions
max_total_exposure: float = 0.12      # 12% max total
max_position_pct: float = 0.05        # 5% risk per trade
default_leverage: int = 35
max_leverage: int = 50
```

### Conservative Mode (for critical/survival capital)
```python
balance_reserve_pct: float = 0.25     # Always keep 25% free
max_simultaneous_positions: int = 2   # Hard cap — fewer positions
max_total_exposure: float = 0.08      # 8% max total
max_position_pct: float = 0.03        # 3% risk per trade
default_leverage: int = 20
max_leverage: int = 30
```

**When to use conservative:** User expresses financial desperation ("buat makan istri", "bayar hutang", "last balance"). This is NOT gambling money — it's family survival money.

## Implementation

Add to `analyze_and_trade()` method, AFTER daily limit and cooldown checks, BEFORE signal analysis:

```python
# ── Balance Reserve Guard ──
balance = self.paper.balance if self.paper else self._live_balance
if balance > 0:
    reserve = balance * config.balance_reserve_pct
    
    if self.mode == 'live':
        # Fetch real-time account state from Binance
        acc = await signed_request('/fapi/v2/account')
        total_balance = sum(float(a['balance']) for a in acc.get('assets', []) if a['asset'] == 'USDT')
        available = float(acc.get('availableBalance', 0))
        active_positions = len([p for p in acc.get('positions', []) if float(p.get('positionAmt', 0)) != 0])
        
        # Guard 1: Max positions
        if active_positions >= config.max_simultaneous_positions:
            log.info(f"Max positions reached ({active_positions}/{config.max_simultaneous_positions})")
            return
        
        # Guard 2: Balance reserve
        if available < reserve:
            log.info(f"Balance reserve guard: available ${available:.2f} < reserve ${reserve:.2f}")
            return

# Position sizing uses USABLE balance (after reserve)
usable_balance = balance - reserve
if usable_balance <= 0:
    log.info(f"No usable balance (reserve: ${reserve:.2f})")
    continue
risk_amount = usable_balance * config.max_position_pct
```

## Why This Matters

Without guards:
- $54 balance → 4 positions deploy $53 → $0.48 available
- All LONG → market dip hits ALL positions
- No room for contrarian entries
- Strong signal appears but can't execute

With guards:
- Max 2-3 positions → capital preserved
- 20-25% reserve ($11-13.50) → room for high-conviction setups
- Position sizing based on usable balance → smaller, safer positions

## Real-World Examples

### Aggressive ($54, disposable)
Balance: $54.07
Reserve: $54.07 × 0.20 = $10.81
Usable: $54.07 - $10.81 = $43.26
Risk per trade: $43.26 × 0.05 = $2.16

### Conservative ($54, survival money)
Balance: $54.07
Reserve: $54.07 × 0.25 = $13.52
Usable: $54.07 - $13.52 = $40.55
Risk per trade: $40.55 × 0.03 = $1.22

With 20x leverage and 1.0% SL distance:
Position size = $1.22 / 0.01 = $122 (much safer than aggressive $216)
