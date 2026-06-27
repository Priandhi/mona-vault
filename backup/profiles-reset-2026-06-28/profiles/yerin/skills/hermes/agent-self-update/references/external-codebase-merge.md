# External Codebase Merge Pattern

When user sends a zip that's a SKILL/TOOL bundle (not a Hermes core update), use this workflow.

## Key Principle
"Jangan ada yang dihapus, ambil yang belum punya" — NEVER remove existing capabilities. Only ADD.

## Step-by-Step

### 1. Backup
```bash
BACKUP_DIR="~/.hermes/backup_pre_merge_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r ~/.hermes/scripts "$BACKUP_DIR/"
cp -r ~/.hermes/skills "$BACKUP_DIR/"
cp ~/.hermes/config.yaml "$BACKUP_DIR/"
```

### 2. Extract & Analyze
```bash
cd /tmp && mkdir merge_work && cd merge_work
unzip -o <artifact.zip>
find . -type f | wc -l  # actual file count
# Check SKILLS.lock vs actual — lock may reference more files than zip contains
```

### 3. Identify Overlaps
```bash
# Compare new tools with existing
ls ~/.hermes/scripts/mona_*.py  # existing
ls /tmp/merge_work/*/tools/*.py  # new
# Look for functional overlaps (bridge_engine.py vs mona_bridge.py)
```

### 4. Copy Tools (preserving existing)
```bash
mkdir -p ~/.hermes/scripts/openclaw_tools
cp /tmp/merge_work/*/tools/*.py ~/.hermes/scripts/openclaw_tools/
# Remove irrelevant tools (desktop_control.py for server)
echo "# Superagent Tools" > ~/.hermes/scripts/openclaw_tools/__init__.py
```

### 5. Copy Skills (preserving existing)
```bash
mkdir -p ~/.hermes/skills/openclaw
cp /tmp/merge_work/*/skills/*.md ~/.hermes/skills/openclaw/
# Copy sub-skill references/scripts
cp -r /tmp/merge_work/*/skills/hermes ~/.hermes/skills/openclaw/
```

### 6. Smoke Test
```bash
cd ~/.hermes/scripts/openclaw_tools
for f in *.py; do
    [ "$f" = "__init__.py" ] && continue
    python3 -c "import sys; sys.path.insert(0,'.'); import ${f%.py}; print('${f%.py}: OK')" 2>&1
done
```

### 7. Report
Summary format:
- X new tools added (list names)
- Y new skills added (list names)
- Z references added
- 0 existing files modified
- Backup location

## Common Pitfalls

1. **Partial zips** — SKILLS.lock may reference 112 files but zip only has 28. The lock is the FULL package manifest.

2. **Import path issues** — New tools may use relative imports (`from .swap_engine import`). Fix to absolute: `from openclaw_tools.swap_engine import`.

3. **Class name conflicts** — Two files with same class name but different implementations. Check with `grep "^class " *.py` before merging.

4. **User correction: "jangan ada yang dihapus"** — If overlap exists, keep BOTH. Prefix new ones if needed.

5. **Don't register as Hermes tools** — These are Python modules loaded by scripts, not Hermes tool functions. No config.yaml changes needed.

## Real Example: Superagent v4.1 → Mona (June 2026)

Result:
- 27 new tools (watchdog, reflection, vault, governor, HIDS, automation, planner, alerts, triage, briefing, memory_engine, research_q, eval, backtest, dashboard, skill_integrity, skill_forge, skill_market, mcp_builder, model_registry, prd, content, voice, multimodal, scene_prep, humanizer, swarm, explain)
- 55 new skills (m0-m29, x1-x7, hermes integration)
- All existing Mona capabilities preserved
- Backup: ~/.hermes/backup_pre_merge_20260607_094319/
