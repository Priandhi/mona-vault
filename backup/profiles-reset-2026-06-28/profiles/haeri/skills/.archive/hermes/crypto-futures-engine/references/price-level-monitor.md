# Price-Level Entry Monitor (VIRTUALUSDT Pattern)

## Architecture

When a signal source (external scanner, manual analysis, MJ9) identifies a setup but price hasn't reached the entry zone yet, deploy a lightweight price monitor that watches for retrace to the FVG/OB zone.

## Files

- `~/.hermes/scripts/virtual_monitor.py` — standalone monitor for VIRTUALUSDT

## Monitor Logic

```
Every 60 seconds:
1. Fetch current price from /fapi/v1/ticker/price
2. Check if price is IN entry zone (FVG zone)
3. If IN zone + bullish confirmation (BOS or RSI<40 + volume spike) → ENTRY ALERT
4. If approaching zone (within 2%) → APPROACH ALERT
5. If below zone → WARNING (SL risk)
6. If above TP1 → TP ALERT
```

## SMC Levels Definition

```python
ENTRY_ZONE_LOW = 0.540   # Bottom of H4 FVG
ENTRY_ZONE_HIGH = 0.558  # Top of H4 FVG
SL_LEVEL = 0.530         # Below structure
TP1 = 0.575              # RR 1:1
TP2 = 0.597              # RR 1:2
TP3 = 0.619              # RR 1:3
```

## Confirmation Signals (5m klines)

- **BOS Bullish** — current price breaks above previous 10-candle high
- **RSI oversold + volume** — RSI < 40 AND volume > 1.5x average
- Either confirmation triggers entry alert

## Alert Cooldown

5-minute cooldown between alerts per type. Prevents spam during volatile retrace.

## Telegram Delivery

Uses same bot token as engine. Alerts to Alpha topic (13) via `send_telegram_alert()`.

## When to Use

- External signal identifies setup but price hasn't reached entry zone
- User manually asks to monitor a specific pair for retrace
- SMC setup is valid but price has already moved (missed by 3-5%)
- Pair is in a clear FVG/OB zone that price may retrace to

## Key Difference from Trading Engine

The monitor does NOT trade — it only alerts. User decides whether to enter manually or let the engine pick it up if the pair is in its scan list. This is intentional: external signals may have different analysis methodology than the engine's 7-layer system.
