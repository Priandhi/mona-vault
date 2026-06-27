# Workspace Hygiene / Cleanup Recipe

Discovery commands to run before any deletion. Always run first — never delete based on assumptions.

## Full Discovery Scan

```bash
# 1. Empty files and empty skeleton directories
find ~/mona-workspace/ -type f -empty 2>/dev/null
find ~/mona-workspace/ -type d -empty 2>/dev/null

# 2. Hermes runtime sizes (logs, sessions — safe to clean)
du -sh ~/.hermes/logs/
du -sh ~/.hermes/sessions/
du -sh ~/.hermes/cache/

# 3. Old backup files
ls -lt ~/.hermes/*.bak* 2>/dev/null

# 4. API key locations in .env (output is always masked)
grep -E "API_KEY|OPENAI|ANTHROPIC|TELELMAMA|OLLAMA" ~/.hermes/.env 2>/dev/null | sed 's/=.*/=***/g'
```

## Safe Delete Targets (Operator Data, Zero Risk)

```bash
# Empty skeleton dirs in workspace
find ~/mona-workspace/ -type d -empty -delete

# Old backup files in ~/.hermes/
rm -f ~/.hermes/auth.json.bak.*
rm -f ~/.hermes/config.yaml.bak.*

# Hermes logs (runtime noise, recreated on next run)
rm -rf ~/.hermes/logs/*

# Hermes sessions (chat history only)
rm -rf ~/.hermes/sessions/*
```

## NEVER Delete

- `~/.hermes/memories/MEMORY.md` — user said "jangan hilangkan memori"
- `~/.hermes/memories/USER.md`
- `~/.hermes/skills/` — skill definitions
- `~/.hermes/state.db`, `kanban.db` — operational state
- `vault/` contents in workspace — secrets

## API Key Rotation (Comment-Out, Don't Delete)

```bash
# In ~/.hermes/.env, comment out exhausted key:
# OPENROUTER_API_KEY=sk-or-v1-oldkey   ← add # prefix, preserve for reference

# Add new key on next line:
# OPENROUTER_API_KEY=sk-or-v1-newkey
```

## Typical Findings on a Mature Workspace

| Finding | Typical Size | Action |
|---------|-------------|--------|
| Empty skeleton dirs | 0 | Delete |
| `*.bak.*` old backups | < 1MB | Delete |
| `~/.hermes/logs/` | 50–100MB | Clean |
| `~/.hermes/sessions/` | 1–10MB | Clean |
| `cache/` JSON files | 1–5MB | Skip unless stale |

## Hermes Skills Cleanup (Irrelevant Skills)

Hermes ships with 100+ bundled skills across all categories. On a **crypto-focused Linux VPS**, many are irrelevant and waste load time.

**Safe to remove (category-level):**
- `apple/*` — macOS only (apple-notes, apple-reminders, findmy, imessage, macos-computer-use)
- `creative/*` — user is crypto-focused, not creative (ascii-video, baoyu-*, comfyui, touchdesigner-mcp, manim-video, p5js, popular-web-designs, pretext, songwriting-and-ai-music)
- `research/*` — academic (research-paper-writing 1.5MB!)
- `productivity/*` — office tools (powerpoint 1.2MB!, notion, linear, airtable, teams-meeting-pipeline)
- `mlops/*` — ML training (llama-cpp, obliteratus, vllm, audiocraft, segment-anything, dspy, weights-and-biases)
- `gaming/*` — minecraft, pokemon
- `red-teaming/*` — godmode jailbreak

**Individual skills safe to remove:**
- `obsidian`, `himalaya`, `xurl`, `openhue`, `jupyter-live-kernel`, `blogwatcher`, `llm-wiki`, `polymarket`, `yuanbao`

**How to clean:**
```bash
# Remove by category
rm -rf ~/.hermes/skills/apple/ ~/.hermes/skills/creative/ ~/.hermes/skills/research/
rm -rf ~/.hermes/skills/productivity/ ~/.hermes/skills/mlops/ ~/.hermes/skills/gaming/
rm -rf ~/.hermes/skills/red-teaming/

# Remove individual skills (search first — they may be nested)
find ~/.hermes/skills/ -type d -name "obsidian" -exec rm -rf {} + 2>/dev/null
find ~/.hermes/skills/ -type d -name "himalaya" -exec rm -rf {} + 2>/dev/null

# Clean empty parent dirs
find ~/.hermes/skills/ -type d -empty -delete 2>/dev/null

# Verify
find ~/.hermes/skills/ -name "SKILL.md" | wc -l  # expect ~49 from 107
```

**Typical savings:** ~7MB skills + faster skill loading

## Scripts Deduplication

After merging external skillsets (e.g. SUPERAGENT v4.0), scripts accumulate duplicates. Clean pattern:

**Identify duplicates:**
```bash
# Tiny stubs (< 500 bytes) — usually abandoned
find ~/.hermes/scripts/ -name "*.py" -size -500c

# Overlapping functionality (manual review needed)
ls ~/.hermes/scripts/mona_alpha_*.py  # multiple alpha scanners
ls ~/.hermes/scripts/sa_*.py          # superagent scripts vs mona_ equivalents
```

**Safe to remove:**
- Stubs: `whale_monitor.py`, `whale_tracker.py`, `full_intel.py` (200-300 bytes each)
- Superseded: old scanner variants when a smarter version exists
- Feature removed: e.g. `pumpfun_sniper.py` after PumpFun was disabled
- Duplicates: `sa_monitoring.py` (basic) when `sa_monitoring_advanced.py` exists
- Overlaps: `sa_browser_engine.py` when `mona_browser.py` already handles it

**Before deleting, verify no cron job references the script:**
```bash
# Check cron jobs for script references
grep -r "script_name" ~/.hermes/cron/ 2>/dev/null
```

## VPS-Level Cleanup (Beyond Workspace)

When disk usage is high (>60%), scan the entire home directory for cleanup targets.

### Discovery Commands

```bash
# Disk overview
df -h /
du -sh /home/ubuntu/* 2>/dev/null | sort -rh | head -15

# /tmp pip cache (often 1-2GB after multiple installs)
du -sh /tmp/pip-unpack-* 2>/dev/null

# Old Python venvs
du -sh ~/.hermes/venv-* 2>/dev/null

# Old projects (check if still active!)
du -sh ~/freellmapi ~/FinceptTerminal ~/mona ~/TradingAgents 2>/dev/null

# Browser cache
du -sh ~/.hermes/browser-data 2>/dev/null

# Logs (system + hermes)
du -sh /var/log ~/.hermes/logs 2>/dev/null

# Node modules (can be reinstalled)
find /home/ubuntu -name "node_modules" -maxdepth 4 -type d 2>/dev/null

# Old installers in Downloads
ls -lhS ~/Downloads/ 2>/dev/null
```

### Safe to Delete Without Asking

```bash
# /tmp pip cache (~1.6GB typically)
rm -rf /tmp/pip-unpack-*

# Old installers
rm -f ~/Downloads/*.deb ~/Downloads/*.rpm

# Browser cache (cookies lost, but recreated on next login)
rm -rf ~/.hermes/browser-data

# Old hermes logs
rm -rf ~/.hermes/logs/*
```

### MUST ASK FIRST (User Protective of Projects!)

**CRITICAL LESSON (2026-06-08):** User is protective of projects they built. When showing cleanup candidates, ALWAYS explain what each project IS and whether it's still active BEFORE proposing deletion. User: "kalau di hapus kekurangan nya apa takut ada yang miss jelaskan dulu".

```bash
# Check if project is still referenced
grep -rl "project_name" ~/.hermes/scripts/ 2>/dev/null
grep -rl "project_name" ~/.hermes/cron/ 2>/dev/null
ps aux | grep project_name | grep -v grep

# Check if venv is still used
grep -rl "venv-name" ~/.hermes/scripts/ 2>/dev/null
```

**Discovery checklist for each project:**
1. What IS this project? (README, package.json, main files)
2. Is it running? (ps aux)
3. Is it referenced by any script or cron job?
4. What breaks if we delete it?

**Present as categorized table:**
```
✅ AMAN DIHAPUS (Xmb): description
⚠️ TANYA DULU: description + what it does
❌ JANGAN HAPUS: description + why it's important
```

### Typical VPS Savings

| Target | Typical Size | Risk |
|--------|-------------|------|
| /tmp/pip-unpack-* | 1-2GB | Zero |
| venv-headroom (unused) | 500MB | Low (reinstallable) |
| Old projects (freellmapi, etc.) | 500MB-1GB | Medium (ask first) |
| browser-data | 300MB | Low (cookies lost) |
| Old Grass/DEB installers | 40MB | Zero |
| hermes/logs | 100-200MB | Zero |

**Typical total savings: 2-5GB** on a mature VPS.

The `gateway-exit-diag.log` can grow to 100MB+ on long-running instances:
```bash
# Truncate (keeps file handle valid for running processes)
truncate -s 0 ~/.hermes/logs/gateway-exit-diag.log

# Delete old rotations
rm -f ~/.hermes/logs/agent.log.{1,2,3,4,5}
rm -f ~/.hermes/logs/errors.log.{1,2,3,4,5}

# Clean pycache in venvs
find ~/.hermes/venv-*/ -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find ~/.hermes/venv-*/ -name "*.pyc" -delete 2>/dev/null
```