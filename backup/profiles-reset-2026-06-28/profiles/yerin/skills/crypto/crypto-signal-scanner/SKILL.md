---
name: crypto-signal-scanner
description: >
  Dual-mode crypto futures signal scanner — momentum (trend+pullback) and reversal (SMC).
  Scans Binance futures pairs, generates signals with chart + explanation, sends to Telegram.
trigger: >
  User asks for crypto signals, trade setups, entry/exit analysis, or "scan" commands.
  Also triggers when building trading bots or signal systems.
---

# Crypto Signal Scanner — Dual Mode

## Architecture

```
Scanner → Analyzer → Chart Generator → Telegram Notifier
   │          │              │                │
  100 pairs  Score ≥70    Simple chart    Topic 387
```

## Two Modes

### 1. MOMENTUM Mode (for trending markets)
- **When**: ADX > 25 + EMA alignment
- **Strategy**: Trend + Pullback entry at EMA20
- **Signals**: EMA crossover, RSI filter, volume, funding rate
- **Best for**: Strong trending tokens (BTC, ETH, SOL)

### 2. REVERSAL Mode (for ranging markets)  
- **When**: ADX < 25 or ranging
- **Strategy**: SMC patterns (OB, FVG, CHoCH)
- **Signals**: Fresh OB, Virgin FVG, liquidity sweep, displacement
- **Best for**: Range-bound tokens at key levels

## Scoring System (0-100)

### Momentum Score:
- Trend strength (EMA alignment): 0-30 pts
- Pullback quality (1-5% from EMA20): 0-30 pts
- Volume confirmation: 0-20 pts
- RSI filter (not overbought/oversold): 0-20 pts
- Funding rate bonus: 0-10 pts

### Reversal Score (SMC):
- MTF alignment: 0-20 pts
- Fresh OBs (H4+H1+M15): 0-25 pts
- Virgin FVGs: 0-20 pts
- CHOCH confirmation: 0-15 pts
- Liquidity sweep + displacement: 0-15 pts
- Smart Money flow: 0-10 pts

## Chart Rules (CRITICAL)

**User preference (2026-06-08):** User wants charts that look like **Binance/TradingView**, not basic matplotlib. User showed Slevensy Scanner Bot chart as reference. Use `mplfinance` library for professional candlestick charts.

**Chart Requirements (TradingView-style):**
- ✅ mplfinance candlestick (green up / red down, with wicks)
- ✅ EMA20 (cyan) & EMA50 (yellow) trend lines
- ✅ Entry (green), SL (red), TP1-3 (cyan dashed) horizontal lines
- ✅ Volume bars below candlestick
- ✅ Current price marker with green label box on right
- ✅ Price labels on RIGHT side (y_on_right=True) — like TradingView
- ✅ Info box (top-left): Entry, SL, TP, Score
- ✅ Reasons box (bottom-right): entry signals
- ✅ Dark theme: bg #1a1a2e, grid #333333
- ✅ Support/Resistance dotted lines with labels
- ❌ NO Order Block zones
- ❌ NO FVG zones
- ❌ NO Liquidity level boxes
- ❌ NO SMC annotations on chart

**Implementation:** Use `mona_chart_pro.py` with `mplfinance` library. NOT `mona_chart_simple.py` (basic matplotlib).

**mplfinance style setup:**
```python
mc = mpf.make_marketcolors(up='#00ff88', down='#ff4444', ...)
style = mpf.make_mpf_style(marketcolors=mc, facecolor='#1a1a2e', y_on_right=True, ...)
```

**Pitfalls:**
- `gridwidth` is NOT a valid kwarg for `mpf.make_mpf_style()` — remove it
- Use tuple colors `(r, g, b, a)` not CSS `rgba()` strings for matplotlib patches
- `matplotlib.use('Agg')` required for headless server
- mplfinance returns `(fig, axes)` tuple — use `returnfig=True`

## Signal Format (Telegram)

User prefers **professional format** with market context, S/R levels, and entry reasoning. Match Slevensy Scanner Bot quality.

**CRITICAL (2026-06-08):** Signal format must be **PLAIN TEXT** — NO markdown bold (`**text**`), NO markdown italic. When `parse_mode=""` is used for Telegram delivery, markdown characters show as literal `**` in the message. User: "data gak lengkap mona gak ada harga gak ada apapun".

```
🟢 SYMBOL LONG
━━━━━━━━━━━━━━━━━━━━━━━━━━

Mode: 🚀 MOMENTUM
Score: 90/100 (HIGH)

Entry: $XX.XXXX
Stop Loss: $XX.XXXX
TP1: $XX.XXXX
TP2: $XX.XXXX

Market Data:
• 24h Change: +X.XX%
• Volume: $XXX,XXX,XXX
• Funding: X.XXXX%
• RSI: XX
• EMA20: $XX.XXXX
• EMA50: $XX.XXXX
• Pullback: X.X%

Reasons:
• Reason 1
• Reason 2
• Reason 3

━━━━━━━━━━━━━━━━━━━━━━━━━━
TRADE STATUS: ⏳ WAITING ENTRY

⚠️ DYOR. Bukan financial advice.
Powered by: Mona Dual Mode Scanner v1.0
```

**NEVER use `**bold**` or `*italic*` in signal messages.** Telegram renders them as literal text when parse_mode="" is set.

## Deduplication (CRITICAL — User Corrected 2026-06-08)

**Dedup by TOKEN only, NOT by token+direction.** User: "jangan kirim token yang sama dalam sinyal futures cukup 1 token sekali" — if ETHUSDT was sent as LONG, do NOT also send ETHUSDT SHORT within the cooldown window. One alert per token, period.

**Cooldown: 24 hours** (not 1 hour). Same token should not appear more than once per day.

```python
sent_signals = {}  # persisted to ~/data/sent_signals.json

def _is_signal_sent(self, symbol: str, direction: str = "") -> bool:
    key = symbol  # e.g. "ETHUSDT" — NOT "ETHUSDT_LONG"
    if key in self.sent_signals:
        if time.time() - self.sent_signals[key] < 86400:  # 24h cooldown
            return True
    return False

def _mark_signal_sent(self, symbol: str, direction: str = ""):
    self.sent_signals[symbol] = time.time()
    self._save_sent_signals()
```

**Why not direction-based?** User sees "ETHUSDT LONG" and "ETHUSDT SHORT" in the same feed as spam — same token, conflicting direction. Pick the higher-score one only.

**Pitfall:** The dedup file (`sent_signals.json`) must be persisted to disk. In-memory-only dedup resets on cron restart, causing duplicates. Always load from file on startup, save after each mark.

## Cron Deployment

**CRITICAL (2026-06-08):** User explicitly corrected: "jangan share kesini bos ke topic loh" — NEVER deliver to home channel (DM). ALWAYS deliver to specific topic.

Target: Topic 387 (Futures Trading)
Schedule: */5 * * * * (every 5 minutes)
Delivery: `telegram:-1003899936547:387`

**NEVER use `deliver: "origin"` or `deliver: "telegram"` for signal scanners.** These go to DM. Always use `telegram:CHAT_ID:TOPIC_ID`.

**CRITICAL: no_agent=true for signal scanners** — The script must send signals DIRECTLY via `send_message()`, NOT through an LLM agent. LLM agents truncate/reformat signal data, losing prices and details. User: "data gak lengkap mona gak ada harga gak ada apapun".

```python
# In the scanner script's main() function:
from mona_telegram import send_message, TOPIC_FUTURES

for signal in signals:
    msg = format_signal(signal)  # plain text, no markdown
    send_message(TOPIC_FUTURES, msg, parse_mode="")  # plain text!
    _mark_signal_sent(signal.symbol)
```

**Cron job config:**
```yaml
script: mona_dual_mode_scanner.py
no_agent: true
deliver: "telegram:-1003899936547:387"
```

**Signal Quantity (CRITICAL):** User explicitly said "kasih 1-3 sinyal aja yang potensi" — ONLY send top 1-3 signals per scan cycle, NOT 25. User gets overwhelmed and frustrated with too many signals. Quality over quantity.

Must attach chart image with `MEDIA:/path/to/chart.png`.

## Pitfalls

1. **Division by zero**: Always check `if denominator > 0` before dividing
2. **Rate limits**: Binance allows 200 req/min. Add 0.1s delay between requests
3. **None values**: API may return None. Always check `if data is not None`
4. **Chart matplotlib**: Use `matplotlib.use('Agg')` for headless, use tuple colors not CSS rgba()
5. **Stablecoins**: Skip USDC, BUSD, TUSD, FDUSD, DAI, USDP pairs
6. **Empty klines**: Check `len(klines) >= 50` before analysis
7. **Leverage: ALWAYS MAX per token** — Fetch from `/fapi/v1/leverageBracket`, never hardcode. CAKE=75x, BTC=125x, ETH=100x. See binance-futures-trading skill for details.
8. **Margin: MAX $5 per position** — Hard cap. `qty = ($5 × max_leverage) / entry_price`. User: "margin max 5$ per posisi"
9. **Plain text only** — No markdown `**bold**` or `*italic*` in Telegram messages. Use `parse_mode=""`.
10. **no_agent=true** — Script sends directly, not via LLM agent. LLM truncates signal data.
11. **User is protective of built projects** — When doing VPS cleanup, ALWAYS explain what each file/project is and ask before deleting. User: "takut ada yang miss jelaskan dulu". Never assume a project is "old" or "unused" without checking.

## Market Context Integration

Signals are more powerful when combined with macro context. Run these modules alongside the signal scanner:

- **Fear & Greed Index** — contrarian signal (extreme fear = buy, extreme greed = sell)
- **BTC Dominance** — BTC.D rising = avoid alts, falling = altcoin season
- **Onchain Flow** — BTC/ETH price, volume, DeFi TVL, whale transactions
- **News** — trending coins, top gainers/losers

See `references/market-context-modules.md` for API endpoints and interpretation.

## Auto SL/TP Manager

When placing LIMIT orders, SL/TP cannot be placed immediately (no position yet). Use a background process to monitor fills and auto-protect.

See `references/auto-sltp-manager.md` for implementation.

## Watchlist & Price Alerts

Persistent coin monitoring with price alerts. Store in JSON, check on each scan cycle.

See `references/watchlist-price-alerts.md` for implementation.

## Critical Pitfall: State File Race Condition

**Problem:** When the auto SL/TP manager is killed (SIGTERM), its signal handler calls `save_state()`. If the in-memory `monitored_orders` dict is empty (e.g., manager just restarted and hasn't loaded yet), it overwrites the state file with `{}`, erasing all registered orders.

**Sequence that causes data loss:**
1. Write 3 orders to `sl_tp_monitor.json`
2. Kill old manager process → signal handler fires → saves empty `{}` to file
3. New manager starts → reads empty file → 0 orders loaded

**Fix:** Only save state if there are orders to save:

```python
def signal_handler(sig, frame):
    log.info("Shutting down Auto SL/TP Manager...")
    if monitored_orders:  # DON'T overwrite with empty dict
        save_state()
    sys.exit(0)
```

**Deployment sequence (safe restart):**
1. Kill old manager (it will save empty state)
2. Write order data to file AFTER kill completes
3. Start new manager (reads non-empty file)

```bash
pkill -f auto_sl_tp_manager
sleep 2  # wait for clean shutdown
python3 -c "...write orders to file..."
python3 scripts/auto_sl_tp_manager.py &  # start new
```

**PITFALL:** The `save_state()` race condition also affects other daemon scripts. Always check `if data_dict:` before saving state on shutdown. This pattern applies to ANY daemon that persists state to JSON.

## ALL Report Cron Jobs: no_agent=true (CRITICAL, June 2026)

Market context, news, onchain, dashboard, daily reports — ALL must use `no_agent: true` with `script` field. LLM agents truncate/reformat output, losing prices and details. User: "data gak lengkap mona gak ada harga gak ada apapun".

Pattern:
```python
cronjob(action='update', job_id=..., no_agent=True, script='mona_xxx.py')
```

After creating/updating, run immediately:
```python
cronjob(action='run', job_id=...)
```

Cron jobs at `0 */N * * *` only fire at top of hour. If created at 10:35 with `0 */6 * * *`, next run = 12:00. Use `cronjob(action='run')` for immediate first execution.

## Files

- `mona_dual_mode_scanner.py` — Main scanner engine (momentum + reversal)
- `mona_chart_pro.py` — Professional TradingView-style chart (mplfinance) ← PREFERRED
- `mona_chart_simple.py` — Simple candlestick chart (basic matplotlib) ← FALLBACK
- `mona_dual_pro.py` — Combined scanner + pro chart + output
- `mona_dual_simple.py` — Combined scanner + simple chart + output
- `mona_scanner_notifier.py` — Telegram sender
- `mona_signal_scanner.py` — SMC-based scanner (reversal mode only)
- `mona_signal_generator.py` — Signal generator with chart + explanation
- `mona_market_context.py` — Fear & Greed, BTC dominance, top movers
- `mona_news.py` — Trending coins, top gainers/losers
- `mona_onchain.py` — BTC/ETH price, DeFi TVL, whale transactions
- `mona_watchlist.py` — Watchlist & price alerts
- `mona_auto_sltp.py` — Auto SL/TP manager (background process)
- `mona_dashboard.py` — All-in-one report (market + signals + watchlist + onchain)
