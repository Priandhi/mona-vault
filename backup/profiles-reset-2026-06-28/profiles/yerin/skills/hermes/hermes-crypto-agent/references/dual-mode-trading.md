# Dual-Mode Trading System (Scalper / Sniper)

Architecture for Mona Autonomous Engine v3.1 — two distinct trading modes with auto-switching.

## When to use

- Engine is scanning but finding 0 opportunities (consecutive empty scans)
- Market has high momentum/volatility but DOZERO.X confluence is too strict
- User wants both high-frequency scalping AND high-conviction sniping from same engine

## Architecture

```
┌─────────────────────────────────────┐
│         _scan_and_trade()           │
│  ┌──────────┐    ┌───────────────┐  │
│  │ _determine_mode()              │  │
│  │  FNG < 20 or > 80 → SCALPER   │  │
│  │  3+ empty scans → SCALPER     │  │
│  │  else → SNIPER                │  │
│  └──────────┘    └───────────────┘  │
│         │               │           │
│    ┌────▼────┐    ┌─────▼─────┐    │
│    │ SCALPER │    │  SNIPER   │    │
│    │ Mode    │    │  Mode     │    │
│    └────┬────┘    └─────┬─────┘    │
│         │               │           │
│  Momentum Scanner  Full 7-Layer    │
│  1 API call all    DOZERO.X SMC    │
│  tickers → top 15  Debate+CG+Mem   │
│  → quick TA        Score ≥ 75      │
│  Score ≥ 55        4+ signals      │
│  2+ signals        Full debate     │
│  No debate                          │
│  120s interval     300s interval   │
└─────────────────────────────────────┘
```

## Config structure (in CONSERVATIVE_CONFIG)

```python
'mode': 'auto',  # 'auto', 'scalper', 'sniper'
'scalper': {
    'min_score': 55,
    'min_signals': 2,
    'max_positions': 3,
    'risk_per_trade_pct': 0.02,   # Smaller size per trade
    'leverage_base': 15,
    'leverage_min': 10,
    'leverage_max': 25,
    'sl_atr_mult': 1.0,          # Tighter SL
    'tp1_pct': 0.008,            # 0.8% TP1
    'tp2_pct': 0.015,            # 1.5% TP2
    'trailing_activation_r': 1.0,
    'trailing_atr_mult': 0.3,
    'max_daily_trades': 8,
    'cooldown_after_loss_sec': 300,
    'scan_interval': 120,        # 2 min between scans
},
'sniper': {
    'min_score': 75,
    'min_signals': 4,
    'max_positions': 2,
    'risk_per_trade_pct': 0.03,
    'leverage_base': 20,
    'leverage_min': 15,
    'leverage_max': 30,
    'sl_atr_mult': 1.5,
    'tp1_close_pct': 0.25,
    'tp2_close_pct': 0.25,
    'trailing_activation_r': 2.0,
    'trailing_atr_mult': 0.5,
    'max_daily_trades': 4,
    'cooldown_after_loss_sec': 600,
    'scan_interval': 300,
},
```

## Momentum Scanner (mona_momentum.py)

Fast pre-filter for scalper mode. ONE API call for ALL tickers.

**Flow:**
1. `GET /fapi/v1/ticker/24hr` — all 650+ tickers in single call (cached 30s)
2. Filter: volume > $5M, change > 1.5%, skip stablecoins/leveraged
3. Sort by absolute change, take top 15
4. For each: fetch 5m klines (RSI 14) + 15m klines (EMA 9/21 cross)
5. Composite score: RSI + momentum + EMA position + volume spike + EMA cross
6. Return ranked candidates (score 0-100)

**Signals counted for scalper:**
- RSI < 65 (LONG) or > 35 (SHORT)
- EMA 9/21 cross detected
- Volume ratio > 1.5x
- 24h change > 3% in trade direction

**PITFALL:** EMA cross detection needs `prev_ema_9` and `prev_ema_21` from `closes[:-1]`. Typo `prev_21` instead of `prev_ema_21` crashes the scanner. Always verify variable names.

## Auto-switch logic

```python
def _determine_mode(self) -> str:
    # Switch max every 10 minutes (prevent flapping)
    if time.time() - self._mode_switch_ts < 600:
        return self._active_mode
    
    fng = get_fear_greed_cached()['value']
    
    if fng < 20 or fng > 80:
        return 'scalper'  # Extreme sentiment = momentum plays
    elif no_positions and self._consecutive_empty_scans >= 3:
        return 'scalper'  # Sniper finding nothing, try scalper
    else:
        return 'sniper'
```

## Scalper trade execution differences

- **Leverage:** Fixed from config (15x base), adjusts DOWN for high volatility
- **SL/TP:** Pre-calculated from momentum data (tight: 1.0 ATR SL, 0.8%/1.5% TP)
- **No debate:** Speed over deliberation — momentum fades fast
- **No DOZERO.X:** Momentum scanner replaces structural analysis
- **Telegram alert:** Shows `[SCALPER]` or `[SNIPER]` tag with ⚡/🎯 icon

## Dynamic scan interval

```python
# In main loop:
mode_key = self._active_mode
scan_interval = self.config.get(mode_key, {}).get('scan_interval', 300)
await asyncio.sleep(scan_interval)
```

## Key metrics from first live run (June 2026)

- Momentum scan: 650 tickers → 153 filtered → 15 candidates → 10 scored ≥ 50
- First trade: BLESSUSDT LONG score=75, entry 0.005991, lev=15x, SL=0.005873, TP1=0.006039
- Result: TP1 hit (+0.8%), SL moved to breakeven, remaining closed at breakeven
- Auto-switch triggered by FNG=12 (Extreme Fear) → SCALPER mode

## When NOT to use scalper mode

- Low volatility, ranging market (FNG 30-70, no momentum)
- When user wants high-conviction only (set mode='sniper' manually)
- When balance is very low and each trade must count (sniper's 75+ threshold safer)
