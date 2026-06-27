# Autonomous Agent Architecture

Full autonomous trading agent — decision engine + execution sandbox + goal system + self-healing loop.

## Architecture

```
autonomous_agent/
├── decision_engine.py    # Multi-signal scoring + auto-decision
├── execution_sandbox.py  # Safe TX execution with limits
├── goal_system.py        # Goal tracking + task breakdown
├── goal_tasks.py         # Auto-generate tasks from goals + daily reset
├── autonomous_loop.py    # Main 24/7 loop + self-healing + goal integration
└── test_alpha_hunter.py  # Test scenarios
```

## Decision Engine (decision_engine.py)

Multi-signal scoring system that analyzes market data and makes trading decisions.

### Signals
- `whale_activity` — Whale buy/sell ratio (weight: 25%)
- `price_action` — Price change 1h/24h (weight: 20%)
- `volume` — Volume vs average (weight: 15%)
- `sentiment` — Funding rate, fear/greed (weight: 10%)
- `on_chain` — OI change, liquidations (weight: 15%)
- `social` — Twitter/Telegram mentions (weight: 10%)
- `technical` — RSI, MACD, etc (weight: 5%)

### Decision Flow
1. Collect signals from multiple sources
2. Weight and combine signals (-100 to +100)
3. Calculate confidence (0-1) based on signal agreement
4. Determine action: BUY/SELL/HOLD/WATCH/SKIP
5. Calculate position size using Kelly Criterion
6. Set stop loss and take profit based on volatility

### Confidence Thresholds
- > 0.65 → Execute trade
- 0.4-0.65 → Watch (alert only)
- < 0.4 → Skip

### Position Sizing (Kelly Criterion)
```python
win_prob = confidence
odds = 2.0  # Assume 2:1 reward/risk
kelly = (odds * win_prob - (1 - win_prob)) / odds
kelly *= 0.25  # Quarter Kelly for safety
position = base + (max - base) * kelly
```

## Execution Sandbox (execution_sandbox.py)

Safe transaction execution with limits and protection.

### Limits
- Max single tx: $25
- Max daily volume: $100
- Max daily count: 20
- Min tx: $1
- Max slippage: 3%
- Max gas: $5

### Safety Checks
1. Check transaction limits
2. Check token blacklist
3. Estimate gas cost
4. Set slippage protection
5. Execute with retry
6. Log transaction

## Goal Oriented System (goal_system.py)

Makes the autonomous agent work towards specific targets instead of just reacting to signals.

### Architecture
```
goal_system.py
├── GoalManager — create/track/archive goals
├── Goal — id, title, target_value, current_value, status, tasks[]
├── Task — id, title, status, progress, result
└── GoalType — DAILY, WEEKLY, CUSTOM
```

### Data Flow
1. User (or cron) creates goal: "Earn $100 today"
2. `goal_tasks.py generate <goal_id>` creates tasks:
   - Futures Trading ($50 target)
   - Airdrop Farming ($30 target)
   - Alpha Sniping ($20 target)
3. Autonomous agent updates progress after each trade
4. Daily reset cron archives completed goals, creates new daily target

### Integration with Autonomous Loop
- `autonomous_loop.py` imports `GoalManager`
- After successful trade → `update_goal_progress()` + `update_task()`
- Startup message shows active goals
- Hourly status update includes goal progress
- Daily reset cron: `0 0 * * *` → `goal_tasks.py reset`

### File Layout
```
~/.hermes/memory/goals/
├── active_goals.json    # Current goals
└── archive/             # Completed/failed goals (timestamped)
```

### Key Patterns
- Tasks auto-generated based on goal type (profit/airdrop/generic)
- Progress tracked as dollar amount vs target
- Task status: PENDING → IN_PROGRESS → COMPLETED/FAILED
- Goals auto-complete when `current_value >= target_value`

## Autonomous Loop (autonomous_loop.py)

Main 24/7 loop that ties everything together.

### Flow
1. Initialize: DecisionEngine + ExecutionSandbox + GoalManager
2. Monitor watchlist (10 symbols)
3. Collect signals for each symbol (with 0.5s rate limit between)
4. Make decisions based on goal context
5. Execute trades if confident (confidence >= 0.65)
6. Update goal progress after successful trades
7. Report to Telegram (trades → Alpha, status → Status)
8. Sleep 5 minutes between cycles
9. Status update every hour (includes goal progress)

### Self-Healing
- Catches all exceptions
- Sends error alert to Telegram
- Waits 30 seconds
- Recreates agent instance
- Restarts monitoring loop

### Telegram Integration
- Trade alerts → 💎 Alpha topic (13)
- Status updates → 📊 Status topic (15)
- Startup → 📊 Status topic (15)

## Systemd Service

```ini
# ~/.config/systemd/user/mona-autonomous.service
[Unit]
Description=Mona Autonomous Agent
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/ubuntu/.hermes/scripts/autonomous_agent
ExecStart=/home/ubuntu/.hermes/hermes-agent/venv/bin/python3 autonomous_loop.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

**PITFALL:** Do NOT add `User=ubuntu` to `systemctl --user` service — causes `status=216/GROUP`. The `--user` flag already implies the current user.

## Testing

Run `test_alpha_hunter.py` to verify:
1. Strong whale signal → BUY @ 80% confidence, $6.38 size
2. Weak signal → WATCH (no trade, 0% confidence)
3. Position sizing with Kelly Criterion
4. Risk scoring (25/100 for strong signals)

Run `test_goal_system.py` to verify:
1. Goal creation with target and deadline
2. Task generation (3 tasks for profit goal)
3. Progress tracking ($35 → $65 → $100)
4. Task status transitions (PENDING → IN_PROGRESS → COMPLETED)
5. Report formatting for Telegram
