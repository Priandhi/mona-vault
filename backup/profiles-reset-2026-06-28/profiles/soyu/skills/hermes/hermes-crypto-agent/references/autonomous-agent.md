# Autonomous Agent Architecture

**Created:** June 2026
**Purpose:** Full autonomous trading agent with decision engine, execution sandbox, and goal system

## Components

### 1. Decision Engine (`decision_engine.py`)
- Multi-signal scoring (whale, price, volume, OI, sentiment)
- Confidence-based execution thresholds
- Risk-adjusted position sizing (Kelly Criterion)
- Memory of past decisions and outcomes

### 2. Execution Sandbox (`execution_sandbox.py`)
- Safe transaction execution with limits
- Max $25 per trade, $100/day
- Slippage protection (max 3%)
- Gas estimation and limits
- Error handling and retry

### 3. Goal System (`goal_system.py`)
- Goal creation (daily, weekly, custom)
- Automatic task breakdown
- Progress tracking real-time
- Performance analytics
- Daily goal reset (midnight)

### 4. Autonomous Loop (`autonomous_loop.py`)
- Runs 24/7 monitoring 10 symbols
- Makes decisions setiap 5 menit
- Auto-execute trades tanpa user suruh
- Self-healing kalau error (auto-restart)
- Telegram alerts ke 💎 Alpha topic

### 5. Goal Task Generator (`goal_tasks.py`)
- Auto-generates tasks from goals based on type
- Profit goal → futures trading + airdrop farming + alpha sniping tasks
- Airdrop goal → scan + complete + verify tasks
- CLI: `python3 goal_tasks.py reset` (daily reset), `python3 goal_tasks.py generate <goal_id>`

## Integration with Futures Engine

The autonomous agent integrates with the existing futures engine:
1. **Signal Collection** — Uses same 12 signal generators
2. **Decision Making** — Adds confidence scoring and risk assessment
3. **Execution** — Uses execution sandbox for safe trades
4. **Goal Tracking** — Updates goal progress after each trade (auto-increments profit goal when trade executes)

## Systemd Service

```ini
# ~/.config/systemd/user/mona-autonomous.service
[Unit]
Description=Mona Autonomous Agent - Full Autonomous Trading
After=network.target mona-bot.service
Wants=network.target

[Service]
Type=simple
WorkingDirectory=/home/ubuntu/.hermes/scripts/autonomous_agent
ExecStart=/home/ubuntu/.hermes/hermes-agent/venv/bin/python3 autonomous_loop.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mona-autonomous
Environment=PYTHONUNBUFFERED=1
MemoryMax=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

**PITFALL:** Do NOT add `User=ubuntu` to a `systemctl --user` service — causes `status=216/GROUP`. User-level services run as the logged-in user automatically.

## Daily Goal Reset

Cron job resets daily goals at midnight:
```bash
cd ~/.hermes/scripts/autonomous_agent && python3 goal_tasks.py reset
```

## Safety Limits

- Max single trade: $25
- Max daily volume: $100
- Max daily trades: 20
- Stop loss: 5-10%
- Take profit: 10-20%
- Circuit breaker: 3 consecutive losses → pause 30 min

## Testing

Test script: `test_alpha_hunter.py`
- Simulates whale activity
- Tests decision engine
- Verifies execution sandbox
- Validates goal tracking

## Telegram Integration

- Startup message to 📊 Status topic (15)
- Trade alerts to 💎 Alpha topic (13)
- Goal progress updates
- Status reports every hour
