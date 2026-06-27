# MACD Histogram Alert Format

Based on professional crypto bot screenshot analysis (2026-06-04).

## Original Format
```
📊 MACD HISTOGRAM ALERT 📊
📉 BTC Dominance: 56.5%

3-Month MACD Histogram Cross
🟡 Turning Neutral 🟡

Following a series of bullish signals, the 3-month MACD 
histogram for the total crypto market capitalization (TOTAL) 
has crossed the zero line and is now neutral.

BTC 🔴 WEAKENING (Macd: 0.037)
ETH 🟢 STRENGTHENING (Macd: 0.037)
SOL 🟢 STRENGTHENING (Macd: 0.037)
BNB 🔴 WEAKENING (Macd: 0.037)
XRP 🔴 WEAKENING (Macd: 0.037)

Timeframe: 3M
Feb 16, 2025 14:00:00 UTC
Mar 01, 2025 14:00:00 UTC
```

## Key Patterns

1. **Header with emojis** — `📊 [TYPE] ALERT 📊`
2. **Market context** — Key metric (BTC Dominance)
3. **Bold title** — Indicator + Timeframe
4. **Signal emoji** — 🟡 for neutral
5. **Plain English** — Explanation of signal
6. **Coin list** — Each with color emoji + status + value
7. **Footer** — Timeframe + timestamps

## Telegram Implementation

```python
def format_macd_alert(coins, timeframe, timestamps):
    lines = [
        "📊 *MACD HISTOGRAM ALERT* 📊",
        "",
        f"*{timeframe} MACD Histogram Cross*",
        "🟡 *Turning Neutral* 🟡",
        "",
        "The MACD histogram has crossed the zero line.",
        ""
    ]
    
    for coin in coins:
        emoji = '🟢' if coin['signal'] == 'STRENGTHENING' else '🔴'
        lines.append(f"{coin['symbol']} {emoji} {coin['signal']} (Macd: {coin['value']})")
    
    lines.extend([
        "",
        f"Timeframe: {timeframe}",
        *[ts for ts in timestamps]
    ])
    
    return "\n".join(lines)
```

## Source
Analyzed from professional crypto bot screenshot (img_91366603cf47.jpg, 116x1259px, Telegram dark mode).
