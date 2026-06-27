# Dual Mode Scanner v2.0 — Production Status

**Built:** 2026-06-08
**Status:** Production-ready, cron job running every 5 minutes

## Architecture

```
mona_dual_mode_v2.py
├── MarketMode detection (ADX + EMA alignment)
├── Momentum mode (trend + pullback to EMA20)
├── Reversal mode (SMC patterns via Dozero engine)
├── Chart generation (matplotlib with SMC annotations)
└── Telegram notification
```

## Key Files

| File | Purpose |
|------|---------|
| `~/.hermes/scripts/mona_dual_mode_v2.py` | Main scanner |
| `~/.hermes/scripts/mona_smc_master_v21.py` | SMC analysis engine |
| `~/.hermes/scripts/mona_signal_generator.py` | Signal + chart generation |
| `~/.hermes/charts/` | Generated chart images |

## Performance Results (2026-06-08)

```
Total signals: 35 (from 100 pairs)
Long signals:  33
Short signals: 2

TOP 5 LONG:
🟢 TAOUSDT:    100/100 — Entry $208.22, SL $202.23, TP1 $214.21
🟢 SOLUSDT:    90/100  — Entry $64.86, SL $63.39, TP1 $66.33
🟢 LINKUSDT:   90/100  — Entry $7.71, SL $7.55, TP1 $7.87
🟢 JTOUSDT:    90/100  — Entry $2.04, SL $1.98, TP1 $2.10
🟢 PENGUUSDT:  90/100  — Entry $0.0148, SL $0.0143, TP1 $0.0153

TOP 2 SHORT:
🔴 BLUAIUSDT:  80/100  — Entry $0.0131, SL $0.0136, TP1 $0.0126
🔴 PORTALUSDT: 80/100  — Entry $0.0646, SL $0.0667, TP1 $0.0625
```

## Momentum Entry Strategy

```python
# For trending markets: enter on pullback to EMA20
bullish = price > ema20 > ema50
bearish = price < ema20 < ema50

# Scoring (100-point scale):
# - Trend strength (EMA alignment): 20-30 pts
# - Pullback quality (1-5% = good): 20-30 pts
# - Volume confirmation: 10-20 pts
# - RSI filter (not overbought/oversold): 20 pts
# - Funding rate bonus: 10 pts

# Entry at EMA20, SL = EMA20 - 1.5*ATR, TP = EMA20 + N*ATR
```

## Cron Job Configuration

```python
# Schedule: every 5 minutes
# Threshold: score ≥ 70/100
# Delivery: Telegram topic (futures)
# Deduplication: 1 hour cooldown per signal
```

## Known Issues

1. **No virgin FVG detection** — All FVGs marked as "tested" (detection too aggressive)
2. **No CHoCH on M15** — Swing detection not finding enough points
3. **R:R ratio** — Our 1:2 vs Dozero.x 1:4 (entry calculation suboptimal)
4. **Onchain flow** — Not implemented yet (needs API key)

## Future Improvements

- [ ] Fix virgin FVG detection
- [ ] Improve CHoCH detection on M15
- [ ] Add onchain flow analysis (whale tracking)
- [ ] Add news integration (crypto events)
- [ ] Add watchlist system
- [ ] Add price alerts
