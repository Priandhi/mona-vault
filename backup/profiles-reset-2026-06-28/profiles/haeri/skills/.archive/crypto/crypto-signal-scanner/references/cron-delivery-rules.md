# Cron Delivery Rules — Topic Routing & no_agent

## Critical Rule

**NEVER deliver cron output to home channel (DM).** User correction (2026-06-08): "jangan share kesini bos ke topic loh".

## Wrong (sends to DM)
```yaml
deliver: "origin"     # ← Goes to home channel (DM)
deliver: "telegram"   # ← Goes to home channel (DM)
```

## Correct (sends to specific topic)
```yaml
deliver: "telegram:-1003899936547:387"  # ← Futures Trading topic
deliver: "telegram:-1003899936547:13"   # ← Alpha topic
deliver: "telegram:-1003899936547:10"   # ← Garapan topic
deliver: "telegram:-1003899936547:15"   # ← Logs topic
deliver: "telegram:-1003899936547:17"   # ← Research topic
```

## Topic Map (Mona Ai Group)
```
Topic 10 — 📝 Laporan Garapan
Topic 13 — 💎 Alpha
Topic 15 — 📚 Logs
Topic 17 — 🔬 Research
Topic 387 — 📈 Futures Trading
```

## no_agent=true for Signal Scanners (CRITICAL)

**When deploying signal scanners as cron jobs, ALWAYS set `no_agent: true`.**

Why: LLM agents truncate/reformat signal data, losing prices and details. User: "data gak lengkap mona gak ada harga gak ada apapun".

**Pattern:**
1. Script sends signals DIRECTLY via `send_message(TOPIC_FUTURES, msg, parse_mode="")`
2. Cron job runs script with `no_agent: true` (script IS the job, no LLM processing)
3. If no signals found, script outputs nothing (silent)

**Example cron config:**
```yaml
name: mona-dual-mode-scanner
script: mona_dual_mode_scanner.py
no_agent: true
schedule: "*/5 * * * *"
deliver: "telegram:-1003899936547:387"
```

**Example script main():**
```python
from mona_telegram import send_message, TOPIC_FUTURES

async def main():
    signals = await scanner.scan()
    if signals:
        for signal in signals[:3]:  # MAX 3
            msg = format_signal(signal)  # PLAIN TEXT, no markdown
            send_message(TOPIC_FUTURES, msg, parse_mode="")
            _mark_signal_sent(signal.symbol)
    # If no signals, print nothing = silent
```

## How to Fix Existing Jobs

```bash
# List all cron jobs
hermes cron list

# Update delivery to topic
hermes cron update JOB_ID --deliver "telegram:-1003899936547:387"
```

Or via cronjob tool:
```python
cronjob(action='update', job_id='xxx', deliver='telegram:-1003899936547:387', no_agent=True, script='scanner.py')
```

## Rule of Thumb

- **Scanners/Signals** → Topic 387 (Futures Trading), no_agent=true
- **Alpha/New tokens** → Topic 13 (Alpha)
- **Reports/Summaries** → Topic 10 (Garapan)
- **System logs** → Topic 15 (Logs)
- **Research** → Topic 17 (Research)
- **NEVER** → origin / telegram (home channel = DM)
