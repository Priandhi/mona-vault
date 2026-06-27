# Self-Evolving Agent — Architecture Reference

> Module: `mona_evolution.py` + `mona_evolution_commands.py` + `mona_lessons_db.py`

## Architecture

```
Task Selesai → Evaluation Engine (score 1-10)
     ↓
Score rendah? → Reflection System (analyze failure)
     ↓
Extract lesson → Lesson Store (SQLite)
     ↓
Pattern Detector → Find recurring patterns
     ↓
Next task → Read lessons → Execute better
```

## Components

### 1. Evaluation Engine
Scores tasks on 5 weighted criteria:
- Speed (15%): How fast completed
- Accuracy (30%): Was result correct
- Completeness (25%): Was everything done
- User Satisfaction (20%): Did user like it
- Efficiency (10%): Resource usage (gas, API calls)

Score 1-10. Low scores auto-generate lessons.

### 2. Reflection System
Classifies errors into types:
- `timeout` → Add timeout handling
- `auth_error` → Implement token refresh
- `rate_limit` → Add throttling
- `validation_error` → Better input validation
- `api_error` → Retry logic + fallbacks

Each error type has template lessons that get stored.

### 3. Pattern Detector
Detects:
- **Error patterns**: Recurring low scores in specific task types
- **Success patterns**: High performance to reinforce
- **Feedback patterns**: Multiple similar user corrections
- **Time patterns**: When tasks succeed/fail most

Runs every 10th task.

### 4. Feedback Loop
User commands (any topic):
- `feedback salah [apa] → [benar]` → Correction (confidence 0.9)
- `feedback suka [apa]` → Praise (reinforce related lessons +0.05)
- `feedback prefer [preference]` → Preference (confidence 0.95)

### 5. Memory Compaction
- Remove unused, low-confidence lessons (0 applications, confidence < 0.5)
- Consolidate frequently-applied but unsuccessful lessons
- Keep active, high-confidence lessons

### 6. Lesson Store (SQLite)

```sql
CREATE TABLE lessons (
    id INTEGER PRIMARY KEY,
    category TEXT,        -- 'task', 'error', 'feedback', 'preference'
    subcategory TEXT,     -- 'wallet', 'alpha', 'airdrop', 'browser', 'nft'
    lesson TEXT,          -- The actual lesson text
    context TEXT,         -- JSON with original context
    impact TEXT,          -- 'critical', 'high', 'medium', 'low'
    confidence REAL,      -- 0.0 to 1.0
    source TEXT,          -- Where lesson came from
    times_applied INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    last_applied TIMESTAMP
);
```

## Bot Commands (Topic 📚 Logs)

| Command | Description |
|---------|-------------|
| `evolve status` | Full evolution dashboard |
| `evolve score` | Task score trends (30 days) |
| `evolve lessons` | Recent lessons learned |
| `evolve patterns` | Detected patterns |
| `evolve feedback` | Pending feedback |
| `evolve maintain` | Run maintenance |
| `evolve compact` | Compact old data |

## Auto-Evaluation Hook

Called from worker after each task:
```python
from mona_evolution_commands import auto_evaluate_task
result = auto_evaluate_task(task_id, task_type, title, outcome, error=error)
```

Alerts on Telegram:
- Score ≤ 3 → 🔴 Low Score Alert with weaknesses
- Score ≥ 9 → 🟢 High Score with strengths

## Integration Points

- Worker calls `auto_evaluate_task()` after each completed/failed task
- Bot routes `feedback` and `evolve` commands to Logs handler
- Smart router detects `evolve` and `feedback` prefixes from any topic
- Pattern detector runs every 10th task (lightweight)

## Pitfalls

1. **Lesson confidence**: Start at 0.7, increase with successful applications, decrease with failures
2. **User corrections**: High confidence (0.9) because user explicitly told you
3. **Don't over-learn**: Not every failure needs a lesson. Check if lesson already exists before creating duplicate
4. **Compaction timing**: Run during low-activity periods, not during active grinding
