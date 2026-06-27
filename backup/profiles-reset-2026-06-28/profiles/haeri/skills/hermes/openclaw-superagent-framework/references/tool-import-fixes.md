# OpenClaw Tool Import Fixes & Test Results

## Test Date: 2026-06-07

## Problem 1: Flat Copy Breaks Tools

Tools use `Path(__file__).resolve().parent.parent` to find project root. Flat copy to `openclaw_tools/` makes ROOT point to wrong directory.

**Fix:** Create proper directory structure:
```bash
mkdir -p ~/.hermes/scripts/openclaw/{tools,skills}
cp openclaw_tools/*.py openclaw/tools/
```

## Problem 2: Dataclass NoneType Error

When using `importlib.util.spec_from_file_location`, dataclass decorators fail with:
```
AttributeError: 'NoneType' object has no attribute '__dict__'
```

**Root cause:** Module not registered in `sys.modules` before `exec_module()`. Python's dataclass decorator accesses `sys.modules[cls.__module__].__dict__` for field resolution.

**Fix:**
```python
spec = importlib.util.spec_from_file_location('module_name', 'path.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['module_name'] = mod  # Register FIRST
spec.loader.exec_module(mod)      # Then execute
```

## Problem 3: Wrong Class Names

Naive assumptions about class names fail. Verified exports:
- `automation.py` → `AutomationEngine` (NOT `Automation`)
- `vault.py` → `Vault` (no-arg constructor, auto-creates SQLite)
- `hids.py` → `HIDS(sources, rules, ...)` (needs args)
- `skill_forge.py` → `draft_skill()`, `forge_proposal()` (module functions, not classes)

## Problem 4: Governor Not Standalone

`governor.py` doesn't exist as a standalone file. Governor logic is embedded in `reflection.py` via `FROZEN_PATHS` and `SAFE_AUTO_ACTIONS`.

## Verified Test Results (2026-06-07)

```
13/13 PASS
✅ watchdog    — Watchdog + WatchedProcess + shell_check/shell_restart
✅ reflection  — is_frozen, _audit, FROZEN_PATHS (21 items), SAFE_AUTO_ACTIONS (7 items)
✅ vault       — Vault() SQLite at ~/.hermes/vault.db, put/get/list/remove/resolve_address
✅ hids        — HIDS(sources, rules) + watch/process_line
✅ governor    — Embedded in reflection.py (FROZEN_PATHS protects critical files)
✅ skill_forge — draft_skill() + forge_proposal()
✅ automation  — AutomationEngine class
✅ model_registry — ModelRegistry + ModelConfig
✅ memory_engine  — MemoryEngine + Memory
✅ backtest    — backtest() + BacktestResult + Trade
✅ alerts      — AlertEngine + Rule
✅ triage      — Message + Triaged
✅ briefing    — BriefingSection + already_ran_today()
```

## Key Safety Gates

```python
FROZEN_PATHS = {
    "SOUL.md", "AGENTS.md", "USER.md",
    "skills/hermes/references/governor.md", "skills/hermes/scripts/governor.py",
    "skills/hermes/scripts/mev.py", "skills/hermes/references/security.md",
    "tools/skill_integrity.py", "tools/reflection.py", "SKILLS.lock",
    "skills/x4.md", "tools/watchdog.py", "tools/vault.py", "tools/model_registry.py",
    "tools/planner.py", "tools/swarm.py", "tools/automation.py", "tools/skill_forge.py",
    "tools/hids.py", "tools/desktop_control.py", "tools/skill_market.py",
}

SAFE_AUTO_ACTIONS = {
    "retry_with_fallback_rpc",
    "rotate_rpc",
    "switch_llm_provider",
    "restart_crashed_process",
    "clear_cache",
    "requote",
    "backoff_and_retry",
}
```

## Vault DB Schema

```sql
CREATE TABLE entries (label TEXT PRIMARY KEY, kind TEXT, value TEXT, tags TEXT DEFAULT '');
CREATE TABLE macros (name TEXT PRIMARY KEY, steps TEXT, note TEXT DEFAULT '');
```

Address validation regex: `^(0x[0-9a-fA-F]{40}|[1-9A-HJ-NP-Za-km-z]{32,44})$` (EVM + base58)
