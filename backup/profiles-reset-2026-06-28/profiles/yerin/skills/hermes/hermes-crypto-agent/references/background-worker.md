# Background Worker — 24/7 Task Executor Architecture

## Overview

MonA's background worker processes tasks from a SQLite queue 24/7, even when user isn't chatting. Each task has steps, checkpoints, retry logic, and progress reporting to Telegram.

**Key principle:** Worker = autonomous agent that GRINDS. User = operator who monitors results + gives direction.

## Architecture

```
User (Telegram) → Bot (mona_bot.py) → Task Queue (SQLite)
                                              ↓
                            Worker (mona_worker.py) → Execute → Report (Telegram)
```

### Files

| File | Location | Purpose |
|------|----------|---------|
| `mona_worker_db.py` | `~/.hermes/scripts/` | Database layer: CRUD, status, history |
| `mona_worker.py` | `~/.hermes/scripts/` | Worker service: poll queue, execute, report |
| `mona_worker.db` | `~/.hermes/scripts/` | SQLite database (auto-created) |
| systemd: `mona-worker.service` | `/etc/systemd/system/` | Auto-start service |

### Database Schema

```sql
-- Main task table
tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'general',  -- airdrop, alpha, general, nft, mining
    status TEXT DEFAULT 'pending',    -- pending, running, waiting_input, completed, failed
    priority INTEGER DEFAULT 5,       -- lower = higher priority
    steps_json TEXT DEFAULT '[]',     -- [{name, action}, ...]
    current_step INTEGER DEFAULT 0,
    checkpoint_json TEXT DEFAULT '{}', -- accumulated results per step
    result_json TEXT DEFAULT '{}',
    error_log TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    input_needed TEXT,                -- what input is blocking this task
    created_at, started_at, completed_at, updated_at
)

-- Audit trail
task_history (id, task_id, action, details, timestamp)

-- User-provided inputs
task_inputs (id, task_id, input_key, input_value, received_at)
```

## Task Lifecycle

```
pending → running → completed
    ↓         ↓
waiting_input  failed → (retry) → pending
    ↓
pending (after input received)
```

1. **Add task** — via bot command or code
2. **Worker picks up** — highest priority, oldest first
3. **Execute steps** — sequential, checkpoint after each
4. **Need input?** — status=waiting_input, notify user
5. **Error?** — retry up to max_retries, then fail
6. **Complete** — report results to Telegram

## Task Categories & Executors

Each category maps to an executor function in `mona_worker.py`:

- **`airdrop`** → `execute_airdrop_grind()` — research, check eligibility, execute social tasks, verify, report
- **`alpha`** → `execute_alpha_research()` — web search, analyze, report to Alpha topic
- **`general`** → `execute_generic()` — step-by-step execution with checkpoints
- **Custom** — add new executor, register in `route_task()` dict

### Adding a New Executor

```python
def execute_my_category(task):
    """Execute custom task type"""
    checkpoint = json.loads(task["checkpoint_json"])
    steps = json.loads(task["steps_json"])

    for i in range(task["current_step"], len(steps)):
        step = steps[i]
        # ... do work ...
        checkpoint[step_name] = result
        update_task_step(task["id"], i + 1, checkpoint)

        if needs_input:
            request_input(task["id"], "description of what's needed")
            return "waiting_input"

    update_task_status(task["id"], "completed")
    return "completed"

# Register in route_task():
executors = {
    "airdrop": execute_airdrop_grind,
    "alpha": execute_alpha_research,
    "my_category": execute_my_category,  # ← add here
}
```

## Bot Commands (in topic 📝 Laporan Garapan)

| Command | Description |
|---------|-------------|
| `task add [judul]` | Add new task to queue |
| `task status` | Queue statistics |
| `task list` | Active tasks (pending/running/waiting) |
| `task detail [id]` | Full task details with steps |
| `task retry [id]` | Retry a failed task |
| `laporan` | Completed tasks report |
| `help` | Show all commands |

## Systemd Service

```ini
# /etc/systemd/system/mona-worker.service
[Unit]
Description=Mona Background Worker — 24/7 Task Executor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/ubuntu/mona-workspace
ExecStart=/usr/bin/python3 -u /home/ubuntu/.hermes/scripts/mona_worker.py
Restart=always
RestartSec=10
Environment=HOME=/home/ubuntu

[Install]
WantedBy=multi-user.target
```

**Critical:** Always use `python3 -u` (unbuffered) for systemd services. Without it, `journalctl` shows nothing until buffer flush.

## Progress Reporting

Worker reports to Telegram at each step:
- `⏳ TASK #N — [████░░░░░░] 40% — Step name`
- `✅ TASK #N COMPLETED — Results: ...`
- `❌ TASK #N FAILED — Error: ...`
- `🔔 INPUT NEEDED — Task #N needs: ...`

Reports go to the topic that matches the task category (or 📝 Laporan Garapan by default).

## Pitfalls

- **SQLite permissions**: Worker runs as root (systemd), but user scripts run as ubuntu. Fix: `chmod 666 mona_worker.db` or use shared path with proper ownership.
- **Poll interval**: Default 10s. Too fast = CPU waste. Too slow = delayed response. 10s is good for interactive use.
- **Max concurrent**: Currently 1 task at a time. Increase carefully — parallel tasks need wallet rotation to avoid nonce conflicts on EVM.
- **Input timeout**: Tasks in `waiting_input` stay forever. Consider adding a timeout (e.g., 24h) to auto-fail stale tasks.
- **Step granularity**: Too fine = spammy reports. Too coarse = no visibility. Aim for 3-7 steps per task.
- **hermes_tools NOT available**: Worker runs as standalone Python. Can't import `from hermes_tools import web_search`. Use `urllib` or `curl` directly. For tasks needing Hermes tools, use `no_agent=False` cron jobs instead.
