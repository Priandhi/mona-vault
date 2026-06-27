# Self-Evolving Agent Pattern

Architecture Mona yang bikin dia makin pintar setiap hari tanpa disuruh.

## Components

### 1. Lesson Store (SQLite)
Database: `~/.hermes/scripts/mona_lessons.db`

Tables:
- `lessons` — Learned lessons with category, impact, confidence, usage tracking
- `evaluations` — Task outcome scores (1-10) with criteria breakdown
- `patterns` — Detected recurring patterns (success, error, feedback)
- `feedback` — User corrections, preferences, praise
- `metrics` — Performance metrics over time
- `prompt_versions` — A/B testing for prompt improvements

### 2. Evaluation Engine
Score task outcomes on 5 criteria:
- Speed (15%) — How fast was completion
- Accuracy (30%) — Was result correct
- Completeness (25%) — Was everything done
- User Satisfaction (20%) — Did user like it
- Efficiency (10%) — Resource usage (gas, API calls)

Auto-extract lessons from weaknesses (score ≤ 4).

### 3. Reflection System
On failure → classify error type → generate insight + action:
- `api_error` → Need retry logic and fallbacks
- `timeout` → Need better timeout handling
- `auth_error` → Need token refresh
- `rate_limit` → Need throttling
- `validation_error` → Need input validation

On success → identify success factors → reinforce.

### 4. Pattern Detector
Analyze recent data for:
- Recurring errors (same task type, same weakness)
- Task type success rates (which areas need improvement)
- Time-based patterns (when tasks succeed/fail)
- User feedback patterns (recurring corrections)

### 5. Feedback Loop
User feedback → Lesson:
- `feedback salah [apa] → [benar]` → High-confidence correction lesson
- `feedback suka [apa]` → Reinforce related lessons (confidence +5%)
- `feedback prefer [preference]` → Preference lesson (95% confidence)

### 6. Memory Compaction
- Remove unused, low-confidence lessons
- Consolidate frequently-applied but unsuccessful lessons
- Clean old metrics (>90 days)

## Bot Commands (Topic 📚 Logs)

```
evolve status      — Evolution dashboard
evolve score       — Task score trends (30-day)
evolve lessons     — Recent lessons learned
evolve patterns    — Detected patterns
evolve feedback    — Pending feedback
evolve maintain    — Run maintenance
```

Feedback (any topic):
```
feedback salah [apa] → [benar]   — Koreksi Mona
feedback suka [apa]              — Reinforce behavior
feedback prefer [preference]     — Set preference
```

## Integration with Worker

Worker calls `auto_evaluate_task()` after each task:
```python
from mona_evolution_commands import auto_evaluate_task

result = auto_evaluate_task(
    task_id=task['id'],
    task_type=task['category'],
    task_title=task['title'],
    outcome={'status': 'completed', 'verified': True},
    error=None
)
# result['evaluation']['score'] = 1-10
# result['evaluation']['lessons_extracted'] = [lesson_ids]
```

## Key Files

```
~/.hermes/scripts/mona_lessons_db.py         — Database layer
~/.hermes/scripts/mona_evolution.py          — Core engine (6 components)
~/.hermes/scripts/mona_evolution_commands.py — Bot integration
~/.hermes/scripts/mona_lessons.db            — SQLite database
```

## Anti-Patterns

- **Don't evaluate every single micro-action.** Evaluate at task completion level.
- **Don't over-compact.** Lessons need time to prove their value (at least 10 applications).
- **Don't auto-apply high-impact changes without user confirmation.** Low/medium impact → auto. High/critical → suggest to user first.
- **Don't store raw error traces in lessons.** Store the classified error type + insight, not the full stack trace.
