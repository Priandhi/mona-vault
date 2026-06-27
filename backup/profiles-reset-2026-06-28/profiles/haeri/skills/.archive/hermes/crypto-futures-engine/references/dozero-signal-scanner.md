# DOZERO.X Signal Scanner — Full-Market Coverage

## Problem
Trading engine scans only 30-100 pairs. VIRTUALUSDT had 80/100 SMC setup but wasn't in the list. User said: "solid tapi gak kasih aku sinyal" (solid but didn't give me the signal).

## Solution
Standalone scanner process that monitors ALL top 100 pairs independently.

## Architecture
```
dozero_scanner.py (standalone, NOT part of trading engine)
├── get_top_symbols() — batch fetch ALL tickers, filter by volume
├── DozeroSignalScanner
│   ├── scan_all() — iterate top 100, run SMC analysis
│   ├── _analyze_symbol() — fetch H1/H4/D klines, run DOZERO.X
│   └── format_signal() — Telegram-ready alert with entry/SL/TP
└── main() — loop with configurable interval
```

## Key Design Decisions

1. **Separate process from trading engine** — Engine needs speed (limited pairs). Scanner needs thoroughness (all pairs).
2. **Signal-only, no trading** — Alerts to Telegram. User decides whether to enter manually or add to engine.
3. **1-hour cooldown per pair** — Don't spam the same setup.
4. **Threshold 75+** — Same as DOZERO.X SMC engine. Lower would flood with noise.
5. **Alerts to Alpha topic (13)** — Separate from Futures trading topic (387).

## API Cost
- 1 batch call for all tickers
- ~3 calls per pair × 100 pairs = ~300 calls per cycle
- At 50 req/min rate limit: ~6 minutes per cycle
- Safe for 300s (5 min) interval — cycle finishes before next starts

## Running
```bash
# One-shot scan
python3 dozero_scanner.py --once --threshold 75

# Continuous monitoring
python3 dozero_scanner.py --interval 300 --threshold 75

# Custom topic
python3 dozero_scanner.py --interval 300 --threshold 75 --topic 13
```

## Telegram Chat ID
Default: `-1003899936547` (from `TELEGRAM_CHAT_ID` env or hardcoded fallback).
Topic 13 = 💎 Alpha topic.

## Production Results (2026-06-07)
- Scanned 100 pairs in ~30 seconds
- Found 3 setups: MRVLUSDT (75), OPGUSDT (75), 1000BONKUSDT (80)
- VIRTUALUSDT scored 65 (below threshold) — MJ9 uses lower threshold
- Alerts delivered to Telegram Alpha topic
