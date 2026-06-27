# Dual-Mode Trading System (Scalper + Sniper)

## Architecture

The dual-mode system adds a momentum pre-filter layer on top of the existing confluence engine. Two operational modes with automatic switching based on market conditions.

## Files

- `mona_momentum.py` — MomentumScanner class: batch ticker fetch, volume/price filter, RSI/EMA analysis, composite scoring
- `mona_autonomous.py` — AutonomousEngine with `_scan_and_trade()` → `_determine_mode()` → `_scan_scalper()` / `_scan_sniper()`

## Mode Config

```python
'scalper': {
    'min_score': 55,           # Lower threshold for momentum
    'min_signals': 2,          # Fewer signals required
    'max_positions': 3,        # More concurrent positions
    'risk_per_trade_pct': 0.09,  # ~$5 risk on $55 balance
    'leverage_base': 25,       # Higher leverage (auto-fallback if pair doesn't support)
    'leverage_min': 20,
    'leverage_max': 40,
    'sl_atr_mult': 1.0,       # Tighter SL
    'tp1_pct': 0.008,          # 0.8% TP1
    'tp2_pct': 0.015,          # 1.5% TP2
    'scan_interval': 120,      # 2 min between scans
    'max_daily_trades': 8,
    'cooldown_after_loss_sec': 300,
},
'sniper': {
    'min_score': 75,
    'min_signals': 4,
    'max_positions': 2,
    'risk_per_trade_pct': 0.03,
    'leverage_base': 20,
    'sl_atr_mult': 1.5,
    'scan_interval': 300,
}
```

**IMPORTANT:** Scalper config is MODE-SPECIFIC and must NOT be overwritten by evolved config. See pitfall #118 in SKILL.md.

## Auto-Switch Triggers

| Condition | Mode | Reason |
|-----------|------|--------|
| FNG < 20 | Scalper | Extreme Fear = volatile momentum |
| FNG > 80 | Scalper | Extreme Greed = pump chasing |
| 3+ empty sniper scans | Scalper | No structural setups, try momentum |
| Normal market | Sniper | Wait for high-conviction confluence |

Switch cooldown: 10 minutes to prevent oscillation.

## MomentumScanner Scan Flow

1. `GET /fapi/v1/ticker/24hr` — ONE call for ALL 650+ tickers (cache 30s)
2. Filter: volume > $5M, abs(change) > 1.5%, exclude stablecoins/leveraged
3. Sort by abs(change), take top 15
4. For each candidate: fetch 5m klines (30 candles) + 15m klines (30 candles)
5. Calculate: RSI(14), EMA(9), EMA(21), volume ratio, ATR
6. Composite momentum score (0-100): bias from RSI + momentum + EMA position + volume spike
7. Return candidates with score ≥ 50

## Scalper Entry Evaluation

Unlike Sniper (which uses 12-signal composite + DOZERO.X SMC + debate), Scalper uses fast 4-signal check:

1. **RSI** — LONG if RSI < 65, SHORT if RSI > 35
2. **EMA cross** — EMA9 crossed EMA21 recently
3. **Volume spike** — volume_ratio > 1.5x
4. **Price momentum** — 24h change > 3% in trade direction

Need 2+ signals to enter. No debate, no SMC, no CoinGlass — speed over precision.

## Scalper SL/TP

Pre-calculated from ATR% of 5m klines:
- SL = price ± (ATR% × sl_atr_mult)
- TP1 = price ± 0.8% (fixed percentage)
- TP2 = price ± 1.5% (fixed percentage)

Tighter than Sniper because scalps target quick moves.

## Production Results (2026-06-07)

- Engine started, FNG=12 → auto-switched to Scalper
- Momentum scan: 650 tickers → 157 filtered → 15 candidates → 9 evaluated
- Entry: BLESSUSDT LONG @ 0.005991, score=75, regime=BREAKOUT
- SL placed @ 0.005873, TP1 placed @ 0.006039
- Total API calls for scan: ~35 (vs 180+ for full sniper scan)

### Scalper Entry Modes (v3.1)

The scalper now has TWO entry modes based on score:

| Score | Entry Type | Action |
|-------|-----------|--------|
| ≥ 80 + strong momentum (>5% change) | TABRAK (market buy) | Immediate execution |
| 65-79 | LIMIT ORDER | Place limit 0.3% below current, expires in 5 min |
| < 65 | WAIT | Not strong enough, skip |

This prevents chasing pumps at market price while still capturing strong momentum moves.

## Key Learnings

1. BLESSUSDT requires integer qty (step=1) — hardcoded list missed it, dynamic fetch fixed it
2. TP2 fails with -4130 when TP1 already placed with closePosition=true — expected behavior
3. Momentum scanner finds candidates that sniper mode misses (because sniper is too strict for ranging/volatile markets)
4. 120s scan interval for scalper catches more opportunities than 300s sniper interval
5. **Trailing SL NoneType bug** — `trailing_sl` can be None when `max()`/`min()` is called on synced positions. Always guard: `if pos['trailing_sl'] is None: pos['trailing_sl'] = new_trail else: max(...)`. See pitfall #114 in SKILL.md.
6. **Notional minimum on scalper entries** — With small balance ($55), scalper entries on cheap tokens (HOMEUSDT @ $0.05) can fail with -4164 "notional must be no smaller than 5". Check `qty * price >= 5` before sending.
7. **Consecutive empty scans counter** — Initialize `_consecutive_empty_scans = 0` in `__init__`. Increment on empty scan, reset to 0 on trade. Used by `_determine_mode()` to switch from Sniper to Scalper after 3+ empty scans.
8. **Parallel scanner + engine = best coverage** — DOZERO.X scanner found MRVLUSDT (75), OPGUSDT (75), 1000BONKUSDT (80), EWYUSDT (80) while engine was in Scalper mode. User gets both momentum trades AND structural signals.
9. **Leverage auto-detection is MANDATORY** — SKYAIUSDT max 10x, HUSDT max 10x. Engine tried 25x → failed silently → entry rejected. Always use `set_leverage_auto()` which tries descending values. See pitfall #116.
10. **Evolved config overwrites scalper settings** — The evolution engine's `_apply_evolved_config()` was reverting scalper risk (9%→3%) and leverage (25x→20x). Fix: save/restore mode-specific configs. See pitfall #118.
11. **Entry retry on "exceeded maximum"** — When position too large for leverage, retry at 50% then 25% size. Catches edge cases where leverage fallback still produces too-large positions.
12. **Position verification after entry** — Always verify position exists on Binance before placing SL/TP. Prevents phantom entries with orphaned SL/TP orders.
13. **Never trade while debugging** — User rule: "lu kalau lagi proses benerin fix bug atau apa jangan entry dulu jirr". Kill engine before fixing, restart only after all fixes verified.

## Parallel Scanner Architecture

Run the trading engine AND a standalone signal scanner in parallel for maximum coverage:

```
Trading Engine (mona_autonomous.py)     Signal Scanner (dozero_scanner.py)
├── Scalper mode: momentum plays        ├── Full SMC analysis on 100 pairs
├── Sniper mode: confluence setups      ├── Alerts only (no trading)
├── 30-100 pairs (fast)                 ├── 100 pairs (thorough)
└── Executes trades                     └── User decides
```

The engine catches momentum (Scalper) and high-conviction confluence (Sniper). The scanner catches structural setups across the full market. Together they cover both fast-moving momentum plays and slow-building SMC setups.
