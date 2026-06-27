---
name: openclaw-superagent-framework
description: "OpenClaw Superagent v4.1 — self-improving, self-healing agent framework with 27 tools and 37 skills. Covers reflection engine (learn/auto-fix/propose), watchdog (process monitoring + auto-restart), vault (address/snippet/macro storage), governor (safety rails), HIDS (intrusion detection), skill forge (auto-create skills), and automation/planning tools. Use when integrating self-improvement loops, self-healing processes, or security guardrails into Hermes."
triggers:
  - self-improvement loop
  - self-healing watchdog
  - agent reflection/learning
  - skill forge/creation
  - vault macros
  - governor safety rails
  - intrusion detection
  - OpenClaw
  - Superagent
  - autonomous self-correction
---

# OpenClaw Superagent v4.1 Framework

Self-improving, self-healing agent framework designed as a Hermes skill overlay. 27 tools + 37 skills covering the full autonomous agent lifecycle.

## Architecture

```
openclaw/
├── SKILLS.lock              # Integrity manifest (SHA256 per file)
├── AGENTS.md                # Agent behavior spec
├── SOUL.md                  # Persona/identity
├── IDENTITY.md              # Core identity definition
├── MEMORY.md                # Memory system spec
├── TOOLS.md                 # Tool registry
├── STANDARD.md              # Quality standards
├── HEARTBEAT.md             # Health monitoring
├── DEPLOY.md                # Deployment guide
├── CHANGELOG.md             # Version history
├── INDEX.md                 # Master index
├── panduan.md               # Indonesian user guide
├── tools/                   # 27 Python tools
│   ├── reflection.py        # Self-improvement loop (learn/fix/propose)
│   ├── watchdog.py          # Process monitoring + auto-restart
│   ├── vault.py             # Address/snippet/macro storage (SQLite)
│   ├── skill_integrity.py   # Verify skill file hashes
│   ├── skill_forge.py       # Auto-create new skills
│   ├── skill_market.py      # Skill marketplace
│   ├── governor.py          # Safety rails (spend caps, tx approval)
│   ├── hids.py              # Host intrusion detection
│   ├── memory_engine.py     # Enhanced memory system
│   ├── planner.py           # Task planning + decomposition
│   ├── alerts.py            # Alert system
│   ├── automation.py        # Multi-step workflows
│   ├── triage.py            # Task prioritization
│   ├── content.py           # Content generation
│   ├── dashboard.py         # Dashboard generator
│   ├── voice.py             # Voice capabilities
│   ├── multimodal.py        # Image/video/audio processing
│   ├── eval.py              # Self-evaluation
│   ├── backtest.py          # Trading backtester
│   ├── briefing.py          # Daily briefing generator
│   ├── research_q.py        # Research queue
│   ├── prd.py               # PRD generator
│   ├── scene_prep.py        # Scene preparation
│   ├── mcp_builder.py       # MCP server builder
│   ├── model_registry.py    # Model registry
│   ├── desktop_control.py   # Desktop automation
│   ├── swarm.py             # Multi-agent coordination
│   └── explain.py           # Explanation generator (empty)
├── skills/                  # 37 skill modules
│   ├── m0-m29.md            # 30 module skills
│   ├── x1-x7.md             # 7 extension skills
│   └── hermes/              # Hermes integration
│       ├── SKILL.md         # Main skill definition
│       ├── DISPATCH.md      # Dispatch routing
│       ├── references/      # 15 reference docs
│       └── scripts/         # 11 Python scripts
└── memory/
    └── 2026-05.md           # Historical memory
```

## Key Tools

### 1. Reflection Engine (`tools/reflection.py`)
Self-improvement loop with THREE capabilities and strict safety gates:

- **LEARN** — Scan memory/logs, distill patterns into lessons (stored to memory)
- **AUTO-FIX** — Reversible, non-financial operational issues fixed automatically (only `SAFE_AUTO_ACTIONS`)
- **PROPOSE** — Everything else (skill edits, config changes, fund/rail touches) written as PROPOSAL for operator review. NEVER auto-applied.

**Safety gates:**
- `FROZEN_PATHS` — Files that CANNOT be touched by the loop (SOUL.md, AGENTS.md, governor, vault, reflection.py itself, SKILLS.lock, security refs, HIDS, desktop control, skill market)
- `SAFE_AUTO_ACTIONS` — Only actions that are reversible AND don't move funds
- Self-improve NEVER: signs tx, changes spend cap, regenerates SKILLS.lock, disables governor, or edits itself
- All autonomous actions logged to `~/.hermes/reflection-audit.log`

### 2. Watchdog (`tools/watchdog.py`)
Process monitoring with auto-restart:

```python
@dataclass
class WatchedProcess:
    name: str
    check_fn: Callable[[], bool]    # Returns True if alive
    restart_fn: Callable[[], None]  # Restarts the process
    max_restarts_per_hour: int = 5
```

- `shell_check(pgrep_pattern)` — Check if process is alive via pgrep
- Rate-limited restarts (max N/hour) to prevent restart loops
- Only monitors processes OPERATOR explicitly registers in config
- Aligned with `SAFE_AUTO_ACTIONS` x4 (restart_crashed_process)

### 3. Vault (`tools/vault.py`)
SQLite-backed storage for addresses, snippets, commands, and macros:

```python
vault.put("wallet kerja", "0x...", kind="address")
vault.resolve_address("wallet kerja")  # → "0x..."
vault.add_macro("morning routine", ["check balance", "scan market", "report"])
```

- Address validation (EVM 0x... / base58 Solana)
- Macro workflows (multi-step named sequences)
- FROZEN — self-improve loop cannot edit vault (prevents address swap attack)

### 4. Governor (`tools/governor.py`)
Safety rails for agent actions:
- Spend caps per transaction and per day
- Transaction approval flow (auto-approve small, operator-confirm large)
- Fund movement restrictions

### 5. HIDS (`tools/hids.py`)
Host-based Intrusion Detection:
- File integrity monitoring
- Unauthorized access detection
- Anomaly alerting

### 6. Skill Integrity (`tools/skill_integrity.py`)
Verify skill files match SHA256 hashes in SKILLS.lock:
- Detect corrupted or tampered skills
- Alert on integrity violations
- Prevent execution of modified skills without re-signing

### 7. Skill Forge (`tools/skill_forge.py`)
Auto-create new skills from observed patterns:
- Analyze repeated task sequences
- Extract reusable procedures
- Generate SKILL.md with frontmatter

## Integration with Hermes

### As Skills
Each tool can be wrapped as a Hermes skill with:
- `SKILL.md` — Trigger conditions, usage instructions
- `scripts/` — Python implementations
- `references/` — API docs, patterns

### As Background Services
- Watchdog → systemd service or cron health check
- Reflection → periodic cron job (every 6-24h)
- HIDS → continuous monitoring daemon

### As Cron Jobs
```
# Reflection cycle — every 6h
cronjob(schedule="0 */6 * * *", prompt="Run reflection: scan recent logs, learn patterns, propose improvements")

# Watchdog check — every 5min
cronjob(schedule="*/5 * * * *", prompt="Check watched processes, restart any that crashed")

# Integrity check — every 1h
cronjob(schedule="0 * * * *", prompt="Verify SKILLS.lock integrity, alert if mismatches found")
```

## Skill Modules (m0-m29, x1-x7)

The 30 module skills (m0-m29) cover progressive capability levels:
- **m0-m5**: Basic operations (file management, web search, terminal, memory)
- **m6-m10**: Intermediate (crypto ops, browser automation, DeFi)
- **m11-m15**: Advanced (multi-chain, sniping, MEV, airdrops)
- **m16-m20**: Expert (governance, security audit, cross-chain bridge)
- **m21-m25**: Master (autonomous trading, portfolio management, risk)
- **m26-m29**: Transcendent (self-improvement, multi-agent, ecosystem)

The 7 extension skills (x1-x7) cover:
- **x1**: Custom tool creation
- **x2**: Plugin development
- **x3**: Platform integration
- **x4**: Security hardening
- **x5**: Performance optimization
- **x6**: Multi-modal operations
- **x7**: Ecosystem orchestration

## Security Model

```
FROZEN_PATHS (cannot be edited by self-improve loop):
├── SOUL.md, AGENTS.md, USER.md
├── governor.md, governor.py
├── security.md, mev.py
├── skill_integrity.py, reflection.py
├── SKILLS.lock
├── x4.md (security hardening)
├── watchdog.py, vault.py
├── model_registry.py, planner.py
├── swarm.py, automation.py, skill_forge.py
├── hids.py, desktop_control.py, skill_market.py
└── (v4.1 additions — OS/firewall/desktop/marketplace = attack surface)
```

## Tool Import & Directory Structure (Critical)

Tools MUST live in `openclaw/tools/*.py` — NOT flat-copied. They use `Path(__file__).resolve().parent.parent` to find the project root. Correct structure:

```
~/.hermes/scripts/openclaw/
├── tools/           ← all 27 .py files here
├── skills/          ← m0-m29.md, x1-x7.md, hermes/
└── (optional root files: AGENTS.md, SOUL.md, etc.)
```

### Python Import Pattern (dataclass fix)

When using `importlib.util.spec_from_file_location`, dataclass-based tools fail with `'NoneType' object has no attribute '__dict__'` if module isn't registered in `sys.modules` BEFORE execution:

```python
import importlib.util, sys

spec = importlib.util.spec_from_file_location('automation', 'tools/automation.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['automation'] = mod  # MUST register BEFORE exec
spec.loader.exec_module(mod)
```

### Verified Tool APIs (tested v4.1)

| Tool | Class/Function | Constructor | Key Methods |
|------|---------------|-------------|-------------|
| watchdog.py | `Watchdog`, `WatchedProcess` | `Watchdog()` | `.watch()`, `.tick()`, `.bot_heartbeat_alive()`, `shell_check()`, `shell_restart()` |
| reflection.py | module-level functions | N/A | `is_frozen()`, `_audit()`, `FROZEN_PATHS`, `SAFE_AUTO_ACTIONS` |
| vault.py | `Vault` | `Vault(db_path)` | `.put()`, `.get()`, `.list()`, `.remove()`, `.resolve_address()`, `.add_macro()`, `.get_macro()`, `.list_macros()` |
| hids.py | `HIDS` | `HIDS(sources, rules, allowlist, block_ttl, backend, alert_cb)` | `.watch()`, `.process_line()` |
| automation.py | `AutomationEngine` | — | Multi-step workflow execution |
| skill_forge.py | module-level functions | N/A | `draft_skill()`, `forge_proposal()` |
| model_registry.py | `ModelRegistry`, `ModelConfig` | — | LLM provider management |
| memory_engine.py | `MemoryEngine`, `Memory` | — | Enhanced memory CRUD |
| backtest.py | `BacktestResult`, `Trade` | — | `backtest()` function |
| alerts.py | `AlertEngine`, `Rule` | — | Alert rule matching |
| triage.py | `Message`, `Triaged` | — | Message prioritization |
| briefing.py | `BriefingSection` | — | `already_ran_today()`, daily briefing |

### Testing Approach (Verified 2026-06-07)

When testing tools, do NOT guess function names. Check actual exports first:

```python
import importlib.util, sys, inspect

spec = importlib.util.spec_from_file_location('toolname', 'tools/toolname.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['toolname'] = mod  # REQUIRED for dataclass tools
spec.loader.exec_module(mod)

# Then inspect:
classes = [n for n in dir(mod) if not n.startswith('_') and isinstance(getattr(mod, n), type)]
funcs = [n for n in dir(mod) if not n.startswith('_') and callable(getattr(mod, n)) and not isinstance(getattr(mod, n), type)]
```

Common mistakes:
- `vault.resolve()` → doesn't exist. Use `Vault()` then `.get()`, `.list()`, `.put()`
- `HIDS()` → requires `sources` and `rules` args (can be empty lists for testing)
- `automation.Automation()` → class is `AutomationEngine`, not `Automation`
- `reflection.reflect()` → doesn't exist. Use `is_frozen()`, `_audit()`, read `FROZEN_PATHS`/`SAFE_AUTO_ACTIONS`

### Vault SQLite Location

Default: `~/.hermes/vault.db` (override via `HERMES_VAULT_DB` env var). Auto-creates on first use.

## Pitfalls

1. **Self-improve loop MUST NOT edit FROZEN_PATHS** — Attempting to write = exception. Changes only via proposal + operator regenerating SKILLS.lock manually.
2. **Watchdog only monitors operator-registered processes** — Not from arbitrary input. Prevents attacker registering malicious restart targets.
3. **Vault is FROZEN** — If self-improve could edit vault, it could swap "wallet kerja" to attacker address = serious attack vector.
4. **Governor spend caps are hard limits** — Not advisory. Agent cannot override without operator approval.
5. **SKILLS.lock integrity** — Always verify before executing skills. Tampered skills = potential code injection.
6. **Reflection proposals are NEVER auto-applied** — Even if they look safe. Operator must review and approve. The only exception is `SAFE_AUTO_ACTIONS` which are pre-approved reversible actions.
