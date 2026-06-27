# Screening Tracker Data Structure

File: `~/mona-workspace/meridian/screening_data/screening_tracker.json`

## Top-level structure

```json
{
  "cycles": [...],      // Array of cycle records
  "candidates": [...],  // Array of candidate records
  "stats": []           // Usually empty
}
```

## Cycle record

```json
{
  "timestamp": "2026-06-10T04:45:02.657Z",
  "candidates": [],         // Pool names evaluated this cycle
  "deploy": null,           // null if no deploy, or deploy object (see below)
  "reject_reason": null,    // Why cycle didn't deploy
  "best_candidate": null    // Best candidate name
}
```

### Deploy object (when cycle deploys)

```json
{
  "pool": "GO-SOL",
  "amount": 0.15,
  "timestamp": "2026-06-08T16:45:02.643Z"
}
```

## Candidate record (bot_filter rejection)

```json
{
  "pool": "CHANCE-SOL",
  "bot_pct": 43.39,
  "max_bot_pct": 40,          // Threshold AT REJECTION TIME (config drift!)
  "rejected_by": "bot_filter",
  "timestamp": "2026-06-10T04:00:01.501Z"
}
```

## Candidate record (safety_block rejection)

```json
{
  "pool": "unknown",            // Sometimes pool name missing
  "fee_tvl_actual": 0.0,       // Actual fee/TVL ratio
  "fee_tvl_threshold": 0.025,  // Configured minFeeActiveTvlRatio at rejection time
  "rejected_by": "safety_block",
  "reason": "Pool fee/active-TVL 0% is below configured minFeeActiveTvlRatio 0.025%.",
  "timestamp": "2026-06-10T04:00:01.501Z"
}
```

## Key fields for analysis

| Field | Present in | Notes |
|---|---|---|
| `pool` | Both | Pool name (e.g. "GO-SOL"). Sometimes "unknown" for safety_block |
| `bot_pct` | bot_filter | Actual bot holder percentage |
| `max_bot_pct` | bot_filter | Config threshold AT rejection time — may differ from current config! |
| `fee_tvl_actual` | safety_block | Actual fee/active-TVL ratio (percentage) |
| `fee_tvl_threshold` | safety_block | Configured minFeeActiveTvlRatio at rejection time |
| `reason` | safety_block | Human-readable rejection reason |
| `rejected_by` | Both | "bot_filter" or "safety_block" |
| `timestamp` | Both | ISO 8601 UTC |

## Config drift detection

The `max_bot_pct` field records the threshold **at rejection time**, not the current config. If user-config.json says `maxBotHoldersPct: 40` but tracker data shows `max_bot_pct: 25`, the running Meridian process used the old threshold for those rejections.

**Detection:** Count distinct `max_bot_pct` values:
```python
from collections import Counter
thresholds = Counter(c.get('max_bot_pct') for c in candidates if c.get('rejected_by') == 'bot_filter')
print(thresholds)  # e.g., {25: 68, 30: 134, 35: 64, 40: 8}
```

Multiple threshold values = config changed during data collection. Data from old thresholds is still useful for simulation but doesn't reflect current behavior.

## Analysis workflow

```bash
# 1. Parse PM2 logs into tracker JSON
python3 ~/.hermes/scripts/meridian_screening_tracker.py --parse

# 2. Compute statistics
python3 ~/.hermes/scripts/meridian_screening_tracker.py --analyze

# 3. Print summary report
python3 ~/.hermes/scripts/meridian_screening_tracker.py --report
```

For deeper analysis, read `screening_tracker.json` directly with Python — the built-in report is a summary only.

## Threshold simulation

To test what-if scenarios:
```python
# Bot filter: how many would pass at different thresholds?
bot_filtered = [c for c in candidates if c.get('rejected_by') == 'bot_filter']
bot_pcts = [c['bot_pct'] for c in bot_filtered if c.get('bot_pct')]
for t in [40, 42, 44, 46, 48, 50]:
    would_pass = sum(1 for p in bot_pcts if p <= t)
    print(f"At {t}%: {would_pass}/{len(bot_pcts)} pass ({would_pass/len(bot_pcts)*100:.0f}%)")

# Safety block: how many would pass at different thresholds?
safety = [c for c in candidates if c.get('rejected_by') == 'safety_block']
fee_actuals = [c['fee_tvl_actual'] for c in safety if c.get('fee_tvl_actual') is not None]
for t in [0.005, 0.01, 0.015, 0.02, 0.03]:
    would_pass = sum(1 for f in fee_actuals if f >= t)
    print(f"At {t}%: {would_pass}/{len(fee_actuals)} pass")
```
