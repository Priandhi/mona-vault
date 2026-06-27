# Telegram Alert Integration for Autonomous Engines

## Overview

Autonomous trading engines should send Telegram alerts ONLY on trade events (open/close). Not periodic status, not scan summaries, not balance reports.

## Setup

### Find Group Chat ID

From `~/.hermes/config.yaml`:
```yaml
telegram:
  allowed_chats: '-1003899936547'  # This is the group chat ID
```

### Environment Variables

```python
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '-1003899936547')  # From config
TELEGRAM_FUTURES_TOPIC = '387'  # 📈 Futures topic thread ID
```

### Alert Function

```python
def send_telegram_alert(message: str):
    """Send alert to Telegram Futures topic. Only for real trade events."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = json.dumps({
            'chat_id': TELEGRAM_CHAT_ID,
            'message_thread_id': int(TELEGRAM_FUTURES_TOPIC),
            'text': message,
            'parse_mode': 'HTML',
        }).encode()
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log.warning(f"Telegram alert failed: {e}")
```

## Alert Templates

### Trade Opened
```python
send_telegram_alert(
    f"🟢 <b>TRADE OPENED</b>\n"
    f"━━━━━━━━━━━━━━━\n"
    f"Pair: <b>{symbol}</b>\n"
    f"Side: <b>{side}</b>\n"
    f"Entry: <code>{price:.4f}</code>\n"
    f"SL: <code>{sl_price:.4f}</code>\n"
    f"TP1: <code>{tp1_price:.4f}</code>\n"
    f"TP2: <code>{tp2_price:.4f}</code>\n"
    f"Leverage: {leverage}x\n"
    f"Score: {score:.1f}\n"
    f"Regime: {regime.value}\n"
    f"Size: ${size_usdt:.2f}"
)
```

### Trade Closed
```python
icon = "✅" if pnl_pct > 0 else "❌"
send_telegram_alert(
    f"{icon} <b>TRADE CLOSED</b>\n"
    f"━━━━━━━━━━━━━━━\n"
    f"Pair: <b>{symbol}</b>\n"
    f"Side: <b>{pos_data['side']}</b>\n"
    f"Entry: <code>{pos_data['entry_price']:.4f}</code>\n"
    f"Exit: <code>{exit_type}</code>\n"
    f"PnL: <b>{pnl_pct:+.2f}%</b>\n"
    f"MFE: {mfe:.1f}% | MAE: {mae:.1f}%\n"
    f"Score: {pos_data.get('score', 0):.1f}"
)
```

## Trade Execution Notifications (FILLED vs LIMIT PLACED)

**Hexa user feedback (2026-06-17):** "harusnya kasih detail kalau limit order biar gak salah paham". The label `✅ EXECUTED` is too ambiguous — it can mean either "position opened" or "limit order placed in the book". Hexa got confused thinking SYNUSDT was an open position when it was just a limit order. **Always distinguish:**

- `✅ FILLED` — position is open, show actual entry price
- `⏳ LIMIT PLACED (waiting fill)` — order is in the order book but NOT filled, show limit price + warning
- `❌ FAILED` — order did not place at all

### Correct Execution Alert Templates

**Filled (position open):**
```python
send_telegram_alert(
    f"✅ FILLED — {symbol}\n"
    f"━━━━━━━━━━━━━━━\n"
    f"Direction: {direction}\n"
    f"Entry: ${actual_fill_price:.4f}\n"
    f"Qty: {qty:.4f}\n"
    f"SL: ${sl:.4f}\n"
    f"TP1: ${tp1:.4f} | TP2: ${tp2:.4f}\n"
    f"Order ID: {order_id}"
)
```

**Limit placed (order in book, waiting for fill):**
```python
send_telegram_alert(
    f"⏳ LIMIT PLACED (waiting fill) — {symbol}\n"
    f"━━━━━━━━━━━━━━━\n"
    f"Direction: {direction}\n"
    f"Signal entry: ${signal_entry:.4f}\n"
    f"Limit price: ${limit_price:.4f}\n"
    f"⚠️ Posisi BELUM terbuka — nunggu market nyentuh limit\n"
    f"Qty: {qty:.4f}\n"
    f"SL: ${sl:.4f}\n"
    f"TP1: ${tp1:.4f} | TP2: ${tp2:.4f}\n"
    f"Order ID: {order_id}"
)
```

### Implementation Pattern (executor → notifier contract)

The executor must pass a `filled` flag to the notifier:

```python
result = execute_trade(...)  # result['filled'] = True/False, result['limit_price'] = float
send_execution(
    symbol=result["symbol"],
    direction=result["direction"],
    entry=result["entry"],
    qty=result["quantity"],
    sl=result["sl"], tp1=result["tp1"], tp2=result["tp2"],
    success=result["success"],
    order_id=result.get("order_id", ""),
    error=result.get("error", ""),
    filled=result.get("filled", True),       # ← key field
    limit_price=result.get("limit_price", 0),  # ← only if not filled
)
```

**Default `filled=True` for backward compat** (market orders are always filled at submission). The notifier picks the right label from the `filled` flag.

**Do NOT alert just "EXECUTED"** — Hexa will read it as "position opened" and act on it. The distinction matters because the user might cancel a limit order that's still pending, and the notif should make that state clear.

## Where to Place Alerts

1. `_execute_trade()` — after trade registration, before evolution update
2. `_close_position()` — after journal exit, before position removal

## What NOT to Alert

- ❌ Scan summaries ("Scanned 30 pairs, no opportunities")
- ❌ Balance updates ("Balance: $53.46")
- ❌ Position monitoring ("LINK still holding")
- ❌ Engine status ("Engine running, 30 pairs")
- ❌ Circuit breaker warnings (log only)
- ❌ Evolution cycles (log only)

## Auto-Start on IP Unban

When Binance IP gets banned, create a cron job that checks every 5 minutes:

```python
# ~/.hermes/scripts/auto_start_engine.py
def check_ip_status():
    params = {'timestamp': int(time.time() * 1000)}
    qs = urllib.parse.urlencode(params)
    sig = hmac.new(api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = f"https://fapi.binance.com/fapi/v2/account?{qs}&signature={sig}"
    req = urllib.request.Request(url, headers={'X-MBX-APIKEY': api_key})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        balance = float(data.get('totalWalletBalance', 0))
        return True, balance
    except urllib.error.HTTPError as e:
        return False, 0
    except:
        return False, 0

if __name__ == '__main__':
    if is_engine_running():
        exit(0)
    ok, balance = check_ip_status()
    if ok:
        start_engine()
```

Set as cron: `cronjob(schedule="every 5m", script="auto_start_engine.py", no_agent=True)`
Kill cron after engine starts to avoid duplicate processes.
