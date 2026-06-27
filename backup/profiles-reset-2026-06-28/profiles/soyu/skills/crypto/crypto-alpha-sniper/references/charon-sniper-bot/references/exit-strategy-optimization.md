# Exit Strategy Optimization — Real Data Analysis (Jun8)

## Observed Token Behavior (Charon Signals)

3 tokens tracked over 20 minutes in DRY RUN:

| Token | Peak PnL | PnL Range | Hold Time | Holders | MCap |
|---|---|---|---|---|---|
| LIFE | +18.6% | +10% to +18% | 20m | 1,670 | $215K |
| FIN | +18.5% | +11% to +18% | 20m | 1,187 | $188K |
| GO | +18.6% | +13% to +18% | 17m | 2,208 | $689K |

**Key observations:**
- All 3 peaked at ~+18-19% (consistent)
- PnL highly volatile: bounces 8-10% within 2 minutes
- Fast pumps: reached peak in 5-10 minutes
- Hold time to peak: 5-10 minutes

## Old Config vs New Config Performance

### Old Config (BROKEN — actively losing money):
```
breakEven:    trigger +10%, lock +2%
partialExit:  trigger +25%, sell 40%
trailing:     trigger +20%, drop -8%
```

**What actually happened:**
1. Price hits +10% → break-even triggers → locks SL at +2%
2. Price continues to +18% peak (break-even doesn't help — already locked)
3. Price drops from +18% to +1.9% → break-even sells at +1.9%
4. Trailing NEVER activates (peak +18% < trigger +20%)
5. Partial exit NEVER activates (peak +18% < trigger +25%)
6. **Net profit: +1.9% per trade** ❌

### New Config (OPTIMAL — data-driven):
```
breakEven:    trigger +15%, lock +5%
partialExit:  trigger +12%, sell 35%
trailing:     trigger +12%, drop -8%
```

**What SHOULD happen:**
1. Price hits +12% → partial exit triggers → sell 35%, lock 0.0048 SOL profit
2. Price hits +15% → break-even triggers → lock SL at +5%
3. Price peaks at +18%, drops -8% from peak → trailing sells at ~+10%
4. **Net profit: 35% × 12% + 65% × 10% = +10.7% per trade** ✅

**5.6x more profit with data-driven config.**

## Exit Checker Flow (position-manager.js)

```
1. Max hold time → (no price needed, runs FIRST)
2. Emergency SL → sell all
3. Normal SL → sell all
4. Break-even → LOCK only (doesn't sell) → if locked AND below lock level → sell
5. Partial exit → sell portion (35%), keep rest
6. TP → sell all (only if trailing disabled)
7. Trailing → sell all (peak >= trigger AND drop >= -dropPct)
```

**Critical ordering:** Break-even is checked BEFORE partial exit. If break-even triggers too early (e.g., +10%), it locks at +2%, and the position gets sold at +2% before partial exit can trigger. This is why break-even trigger must be HIGHER than partial exit trigger.

## Config Tuning Rules

1. **Trailing trigger ≈ 60-70% of observed average peak**
   - Average peak +18% → trigger +12%
   
2. **Partial exit trigger ≈ trailing trigger** (same level)
   - Lock some profit as soon as trailing activates
   
3. **Break-even trigger > partial exit trigger**
   - Let partial exit fire first, then protect remaining with break-even
   
4. **Break-even lock ≈ 30-40% of trailing trigger**
   - Trigger +15% → lock +5% (33% of trigger)
   
5. **Slippage ≥ 5% for micro-caps**
   - Solana micro-cap liquidity is thin
   - 3.5% = frequent swap failures
   
6. **Emergency SL ≥ -30% for Solana**
   - Slippage during crash can be 10-20%
   - Emergency at -25% with 15% slippage = actual -40% loss
