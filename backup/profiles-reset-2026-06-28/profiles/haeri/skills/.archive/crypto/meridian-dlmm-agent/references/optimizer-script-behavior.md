# Meridian Optimizer Script Behavior

## Two Scripts

| Script | Flags | Data Source | Output |
|--------|-------|-------------|--------|
| `meridian_screening_tracker.py` | `--parse`, `--analyze`, `--report` | PM2 agent logs (`logs/agent-YYYY-MM-DD.log`) | `screening_tracker.json` |
| `meridian_optimizer.py` | `--collect`, `--analyze`, `--report` | PM2 agent logs + existing tracker data | `optimizer_tracker.json`, `optimization_report.json` |

Both live at `~/.hermes/scripts/`. The screening_tracker is the primary tool; the optimizer is an alternate that adds a `--collect` step.

## `meridian_optimizer.py` Report Format

```json
{
  "ready": true,              // ← MISLEADING: just means analysis completed
  "timestamp": "...",
  "analysis_summary": {
    "total_cycles": 65,
    "deploy_rate": 0.0,       // ← KEY METRIC for threshold direction
    "passed_pools": [],
    "rejection_breakdown": {
      "bot_filter": 77,
      "safety_block": 42
    }
  },
  "optimal_thresholds": {     // ← The suggested values
    "maxBotHoldersPct": 30,
    "minFeeActiveTvlRatio": 0.025,
    ...
  },
  "confidence": "high",       // ← Also misleading with low deploy rate
  "recommendation": "Continue DRY RUN — need more data"  // ← Contradicts ready:true
}
```

## Known Quirks

### 1. "ready" flag contradiction
The report sets `ready: true` even when recommending "Continue DRY RUN". The flag means "analysis completed" not "ready for LIVE". Always check `deploy_rate` and `recommendation` fields too.

### 2. Stale "current" values
The analysis compares against values stored in tracker data (from rejection time), not from live `user-config.json`. If config changed during data collection, the "current" values will be wrong. Always verify:
```bash
python3 -c "import json; c=json.load(open('user-config.json')); print({k:c[k] for k in ['maxBotHoldersPct','minFeeActiveTvlRatio','minHolders','minMcap']})"
```

### 3. Threshold direction logic
The optimizer uses a simple heuristic that may not match actual needs:
- Bot filter rejections high → suggest INCREASING maxBotHoldersPct (relaxing)
- Safety block rejections high → suggest DECREASING minFeeActiveTvlRatio (relaxing)

But if the tracker data was collected at DIFFERENT thresholds than current config, the direction can be inverted. Always cross-check:
- Low deploy rate (< 10%) → thresholds should RELAX (more permissive)
- High deploy rate (> 30%) with bad pools → thresholds should TIGHTEN

### 4. No wallet-size awareness
The optimizer doesn't consider wallet balance. A 0.364 SOL wallet has different optimal thresholds than a 10 SOL wallet. Always apply the wallet-appropriate values from `references/screening-optimization.md` rather than raw optimizer output.

## Safe Application Workflow

1. Run optimizer: `--collect` → `--analyze` → `--report`
2. Read the report's `optimal_thresholds`
3. Compare report's "current" values vs actual `user-config.json` — if they differ, the data is stale
4. Cross-reference with `references/screening-optimization.md` threshold sensitivity data
5. Verify direction makes sense for current deploy rate
6. Apply changes manually (don't auto-apply)
7. `pm2 restart meridian` and verify new thresholds in PM2 logs
