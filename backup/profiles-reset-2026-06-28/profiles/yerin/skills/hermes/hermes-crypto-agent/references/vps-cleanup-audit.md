# VPS Cleanup Audit Reference

## When to Run
- Monthly maintenance
- After merging external codebases (like SUPERAGENT v4.0)
- When disk usage > 70%
- When skill count > 100

## Audit Steps

### 1. Check Disk Usage
```bash
df -h /                          # Overall disk
du -sh ~/.hermes/*/              # .hermes breakdown
du -sh ~/mona-workspace/*/       # Workspace breakdown
```

### 2. Clean Logs
```bash
# Truncate huge logs
truncate -s 0 ~/.hermes/logs/gateway-exit-diag.log  # Can grow 100MB+
rm -f ~/.hermes/logs/agent.log.{1,2,3}
rm -f ~/.hermes/logs/errors.log.{1,2}
```

### 3. Remove Irrelevant Skills
Categories safe to remove on Linux VPS for crypto-focused user:
- `apple/` — macOS only (apple-notes, apple-reminders, findmy, imessage, macos-computer-use)
- `creative/` — ascii-video, baoyu-*, comfyui, touchdesigner, manim-video, p5js, popular-web-designs, pretext, songwriting
- `research/` — research-paper-writing (1.5MB!)
- `productivity/` — powerpoint (1.2MB!), notion, linear, airtable, teams-meeting-pipeline
- `mlops/` — llama-cpp, obliteratus, vllm, audiocraft, segment-anything, dspy, lm-evaluation-harness, weights-and-biases
- `gaming/` — minecraft-modpack-server, pokemon-player
- `red-teaming/` — godmode
- Misc: obsidian, himalaya, blogwatcher, llm-wiki, polymarket, xurl, yuanbao, openhue, jupyter-live-kernel

### 4. Remove Duplicate/Stub Scripts
Check for:
- Tiny stubs (< 500 bytes): `whale_monitor.py`, `whale_tracker.py`, `full_intel.py`
- Removed features: `pumpfun_sniper.py` (if PumpFun disabled)
- Superseded scanners: `mona_alpha_scan.py`, `mona_alpha_scan_report.py`, `mona_alpha_intel.py` (if replaced by smart scanner)
- `sa_*` overlaps: `sa_monitoring.py` (superseded by `sa_monitoring_advanced.py`), `sa_browser_engine.py` (overlaps `mona_browser.py`), etc.
- Duplicate real-time scanners: `mona_base_realtime_scanner.py` vs `mona_base_launchpad_scanner.py` (check if one supersedes the other)

### 5. Clean Python Cache
```bash
find ~/.hermes/venv-*/ -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find ~/.hermes/venv-*/ -name "*.pyc" -delete 2>/dev/null
```

### 6. Remove Empty Parent Directories
```bash
find ~/.hermes/skills/ -type d -empty -delete 2>/dev/null
```

### 7. After External Codebase Merge
1. Prefix new scripts (e.g. `sa_` for SUPERAGENT)
2. Check overlaps with existing `mona_*` scripts
3. Remove duplicates
4. Update SKILL.md to reflect changes

## Expected Results
- Skills: ~50 (from 107 original)
- Scripts: ~34 (from 46 original)
- Logs: ~5MB (from 132MB original)
- Total savings: ~300MB+
