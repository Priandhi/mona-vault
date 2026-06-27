# Auto-Trade Execution Mode

## Architecture

```
mona_futures_auto.py
├── PaperTrader class
│   ├── open_position() — Simulate entry
│   ├── check_exit() — Check TP/SL conditions
│   └── get_stats() — Win rate, PnL, ROI
├── AutoTrader class
│   ├── analyze_and_trade() — Main logic
│   ├── monitor_loop() — Continuous scanning
│   └── _calculate_dynamic_leverage() — Signal-based leverage
└── CLI: --mode paper|live --symbols BTCUSDT --interval 30
```

## Paper → Live Workflow

### Step 1: Paper Trade (1-24 hours)
```bash
python3 mona_futures_auto.py --mode paper --interval 30
```

Monitor:
- Win rate > 60%
- No bugs or crashes
- Alerts working correctly
- TP/SL triggering properly

### Step 2: Check Results
```python
# In Python
trader = AutoTrader(config, mode='paper')
stats = trader.get_stats()
print(f"Win rate: {stats['win_rate']}%")
print(f"Total PnL: ${stats['total_pnl']}")
print(f"ROI: {stats['roi']}%")
```

### Step 3: Code Changes Before Live Switch

**CRITICAL — Fix hardcoded balance fallback in AutoTrader:**
```python
# WRONG (hardcoded when no paper trader):
risk_amount = self.paper.balance * self.config.max_position_pct if self.paper else 50 * self.config.max_position_pct

# RIGHT (use live balance cache):
balance = self.paper.balance if self.paper else self._live_balance
risk_amount = balance * self.config.max_position_pct
```

**Add live balance refresh method + `_live_balance` init:**
```python
# In __init__:
self._live_balance = 55.5  # initial estimate, refreshed each cycle

# New method:
async def _refresh_live_balance(self):
    if self.mode != 'live': return
    try:
        import hmac, hashlib, aiohttp
        ts = int(time.time() * 1000)
        query = f'timestamp={ts}'
        sig = hmac.new(self.config.binance_api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        url = f'https://fapi.binance.com/fapi/v2/account?{query}&signature={sig}'
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={'X-MBX-APIKEY': self.config.binance_api_key}) as r:
                if r.status == 200:
                    acc = await r.json()
                    for b in acc.get('assets', []):
                        if b['asset'] == 'USDT':
                            self._live_balance = float(b['availableBalance'])
                            return
    except Exception as e:
        log.warning(f"Balance refresh error: {e}")
```

**Call refresh in monitor_loop (every cycle):**
```python
while self.running:
    await self._refresh_live_balance()
    # ... rest of loop
```

**Update `get_report()` for live mode:**
```python
if not self.paper:
    return f"""📊 <b>Auto-Trade Report (LIVE)</b>
━━━━━━━━━━━━━━━━━━━━━━
💰 <b>Balance:</b> ${self._live_balance:.2f}
📊 <b>Mode:</b> LIVE — Real Money!
📅 <b>Trades today:</b> {self.daily_trades}/{self.config.max_daily_trades}
⚡ <b>Leverage:</b> {self.config.default_leverage}x"""
```

### Step 4: Kill Paper + Start Live
```bash
# Find and kill paper process
ps aux | grep mona_futures | grep -v grep
kill <PID>
```

**Hermes process tracking (PITFALL):**
```python
# WRONG — Hermes rejects nohup:
terminal("nohup python3 mona_futures_auto.py --mode live &")

# RIGHT — use background=true for Hermes to track:
terminal(
    command="cd ~/.hermes/scripts && python3 mona_futures_auto.py --mode live --interval 30",
    background=True,
    notify_on_complete=True
)
```

### Step 5: Update Cron Jobs
Remove paper-trade one-shot cron jobs, keep/update recurring scanner:
```python
cronjob(action='remove', job_id='<paper_status_cron_id>')
cronjob(action='remove', job_id='<switch_to_live_cron_id>')
cronjob(action='update', job_id='<scanner_cron_id>', script='mona_futures_v2_cli.py report')
```

### Step 6: Monitor First Hour
- Check logs for `Live balance: $X.XX` — confirms balance refresh works
- Verify position sizes match real balance (not hardcoded $50)
- Watch first entry alert in Telegram
- Check Binance API for actual order placement

## Selective Entry Rules

### Must Pass ALL Checks:
1. Signal score > 65
2. Min 5/12 signals agree
3. Regime NOT ranging (ADX > 25)
4. VPIN NOT toxic (< 0.7)
5. DXY not adverse
6. Daily trade limit not reached
7. Cooldown period elapsed (15 min)
8. No correlated position open

### Signal Strength → Leverage:
- Score 65-75 → 25x leverage (minimum)
- Score 75-80 → 35x leverage (default)
- Score 80+ → 50x leverage (maximum)

## Alert Format

### Paper Trade Entry:
```
🟢 PAPER TRADE — BTCUSDT
━━━━━━━━━━━━━━━━━━━━━━

📊 Side: LONG
💰 Entry: $60,000.00
📏 Size: $100.00
⚡ Leverage: 35x
🎯 Score: +72.5

TP/SL:
• SL: $59,100.00
• TP1: $60,180.00 (55%)
• TP2: $60,450.00 (30%)
• TP3: $60,900.00 (15%)

💰 Balance: $50.00
📊 Trades today: 1/6
```

### Live Trade Entry:
Same format but without "PAPER" prefix.

### Exit Alert:
```
💰 POSITION CLOSED — BTCUSDT
━━━━━━━━━━━━━━━━━━━━━━

📊 Reason: TP1
💰 PnL: $0.55 (+0.55%)
⚡ Side: LONG
📈 Entry: $60,000.00

💰 Balance: $50.55
📊 Win Rate: 66.7%
```

## Cron Integration

### Status Check (every hour):
```python
cronjob(
    action='create',
    schedule='every 1h',
    prompt='Check paper trade status and report results',
    deliver='telegram:-1003899936547:387'
)
```

### Daily Report (9 AM):
```python
cronjob(
    action='create',
    schedule='0 9 * * *',
    prompt='Generate daily PnL report',
    deliver='telegram:-1003899936547:387'
)
```

## Pitfalls

1. **Paper balance mismatch** — Always initialize PaperTrader with same balance as config
2. **Daily counter reset** — Reset at midnight UTC, not local time
3. **Multiple processes** — Kill ALL instances before restarting: `pkill -f "mona_futures_auto"`
4. **Cooldown timing** — Use `time.time()` not datetime for cooldown calculations
5. **Position size rounding** — Round to 6 decimal places for Binance API compatibility
6. **Leverage setting** — Must call `set_leverage()` before each trade, Binance resets on position close
7. **TP/SL order types** — Use `STOP_MARKET` for SL, `TAKE_PROFIT_MARKET` for TP (not limit orders)
8. **Partial close quantities** — Calculate as: `qty * close_pct`, round to 6 decimals
9. **Exit check frequency** — Check exits every scan interval (30s), not just when scanning for new trades
10. **Alert before execution** — Send entry alert BEFORE placing orders, exit alert AFTER closing
