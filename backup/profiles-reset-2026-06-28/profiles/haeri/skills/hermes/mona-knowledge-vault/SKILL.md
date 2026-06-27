---
name: mona-knowledge-vault
description: Persistent markdown knowledge vault for Mona — Obsidian-style local-first memory layer with Git version control, session-start context loading, task-end receipt writing, and multi-device sync. Use when initializing a vault, when user asks to "setup memory", "catat ini", "jangan lupa", or when starting/completing any task that should leave an audit trail. Trigger also on phrases like "vault", "obsidian", "knowledge base", "second brain", "knowledge management" in the context of agent memory.
when_to_use:
  - User asks to setup Obsidian vault / knowledge base / second brain
  - User says "catat" / "jangan lupa" / "inget" in context of persistent notes
  - Session starts (read 01-DAILY + 02-PROJECTS + 05-HERMES-OUTPUTS + 06-KANBAN for context)
  - Task completes (write receipt to 05-HERMES-OUTPUTS/YYYY-MM-DD-[task].md + update kanban)
  - User shares insight worth preserving in 03-RESEARCH/
  - Project status changes (update 02-PROJECTS/[project].md)
  - User gives new task (route to correct agent kanban + add to BACKLOG)
  - User says "kanban" / "task board" / "agent board" / names YUNA/SOYU/YERIN/HAERI
version: 1.1.0
---

# Mona Knowledge Vault

> Local-first persistent memory layer for Mona. Markdown + Git + Obsidian. Lives at `/home/ubuntu/obsidian-vault/` on the VPS. Architecture inspired by @zaimiri's "Hermes Agent + Obsidian Vault = AI Brain" pattern.

## What This Skill Covers

The vault is **NOT** the runtime `memory` tool (which is small, structured, char-limited). It's a **plain-markdown knowledge layer** — readable in Obsidian, syncable via Git, fully owned by the user. Use both layers together:

| Layer | Tool | Size | Purpose |
|-------|------|------|---------|
| Runtime memory | `memory` tool (user/memory) | ~1.4KB each | Compact facts, preferences, corrections |
| **Knowledge vault** | **This skill (Obsidian-style markdown)** | **Unlimited** | **Detailed notes, receipts, research, projects** |

The vault does NOT replace the memory tool. The memory tool captures the *essence*; the vault captures the *full context*.

## When to Write to the Vault

- ✅ Task completes → write receipt (see "Receipt Format" below)
- ✅ Project status changes → update `02-PROJECTS/[project].md`
- ✅ Research finding / exploit attempt / new tool → write `03-RESEARCH/[topic].md`
- ✅ Random idea / quick thought → dump to `00-INBOX/`
- ✅ End of day → update `01-DAILY/YYYY-MM-DD.md`
- ❌ Don't write secrets (use 04-WALLET/ which is git-ignored, NOT receipts)
- ❌ Don't dump large data blobs (use a subfolder or external link)

## Vault Folder Structure (Canonical)

```
/home/ubuntu/obsidian-vault/
├── .git/                          (Git repo, branch: main)
├── .gitignore                     (04-WALLET/ excluded + editor noise)
├── README.md                      (vault index — purpose, folders, agent rules)
├── AGENTS.md                      (user-level context + VAULT MEMORY PROTOCOL)
├── 00-INBOX/                      (📥 quick captures, .gitkeep)
│   └── YYYY-MM-DD-idea.md
├── 01-DAILY/                      (📅 one .md per day)
│   └── YYYY-MM-DD.md
├── 02-PROJECTS/                   (📋 one .md per active project)
│   ├── iclix.md
│   ├── owntown-bot.md
│   ├── mining.md
│   ├── 21+-subproject.md
│   └── mona-vault.md
├── 03-RESEARCH/                   (🔍 findings, exploit attempts)
│   └── [topic].md
├── 04-WALLET/                     (⚠️ SENSITIVE — git-ignored, NEVER push)
│   └── README.md (warns about git-ignore)
├── 05-HERMES-OUTPUTS/             (📜 receipts — audit trail)
│   └── YYYY-MM-DD-[task-name].md
└── 06-KANBAN/                     (📋 5-agent coordination board — see Kanban section)
    ├── README.md                  (kanban index + workflow)
    ├── master-kanban.md           (MONA coordinator view)
    ├── yuna-trading.md            (YUNA — The Strategist: trading/LP)
    ├── soyu-sniper.md             (SOYU — The Phantom: sniper/alpha)
    ├── yerin-mining.md            (YERIN — The Grinder: mining)
    └── haeri-airdrop.md           (HAERI — The Collector: airdrop/NFT)
```

### Folder Purposes

| Folder | Purpose | Read Frequency | Write Frequency |
|--------|---------|----------------|-----------------|
| `00-INBOX/` | Quick captures, ideas, links | Per session start (skim) | Multiple per session |
| `01-DAILY/` | Daily journal — what happened today | **Every session start (load context)** | End of day |
| `02-PROJECTS/` | Per-project status, decisions, blockers | Per relevant request | Per project update |
| `03-RESEARCH/` | Findings, exploit attempts, new tools | Per research question | Per new finding |
| `04-WALLET/` | Wallet addresses, keypair paths (LOCAL ONLY) | Per crypto op | Per new wallet |
| `05-HERMES-OUTPUTS/` | Task receipts (audit trail) | **Per task start (check prior)** | **Every task completion** |
| `06-KANBAN/` | 5-agent task board (MONA/YUNA/SOYU/YERIN/HAERI) | **Every session start (load board)** | **On every task state change** |

## Vault Memory Protocol (MANDATORY)

> This is the core operational discipline. Implemented via `AGENTS.md` injection so it loads on every session.

### Session Start (Read)
1. Read `01-DAILY/` — find latest file (load context)
2. Read `02-PROJECTS/` — load projects relevant to user's request
3. Read `05-HERMES-OUTPUTS/` — check latest 2-3 receipts for prior task continuity
4. If 00-INBOX/ has unprocessed items, surface them to user

### During Session
- Project state changes → update `02-PROJECTS/[project].md`
- Research/learning emerges → write `03-RESEARCH/[topic].md`
- Quick idea/thought → `00-INBOX/YYYY-MM-DD-[slug].md`

### Task End (Write Receipt)
Every completed task → write `05-HERMES-OUTPUTS/YYYY-MM-DD-[task-name].md` using the **Receipt Format** below. This is non-negotiable.

### End of Day
- Update `01-DAILY/YYYY-MM-DD.md` with summary
- `git add -A && git commit -m "vault: YYYY-MM-DD daily"`

## Multi-Agent Kanban System (06-KANBAN/)

> Operational coordination board. Lives in vault at `06-KANBAN/`. Established 2026-06-14.

### The 5 Agents

These are **role identifiers for Mona's execution modes**, not separate sub-agents. When a task lands, Mona decides which role-mode to use and updates the corresponding board.

| Agent | Codename | Role | Skill Stack (existing skills to invoke) |
|-------|----------|------|------------------------------------------|
| **MONA** | The Architect | Coordinator, owns `master-kanban.md`, routes tasks | All skills (orchestrator) |
| **YUNA** | The Strategist | Trading, LP, OOR alerts, PnL | `meridian-dlmm-agent`, `binance-futures-trading`, `crypto-futures-engine` |
| **SOYU** | The Phantom | Sniper, alpha signals, fast entry/exit | `charon-sniper-bot`, `solana-sniper-bot`, `alpha-hunter-new-token-discovery`, `crypto-signal-scanner` |
| **YERIN** | The Grinder | Mining ops, hashrate, payouts | `vps-mining-setup`, `gpu-cloud-mining`, `pm2-process-health` |
| **HAERI** | The Collector | Airdrops, NFT mint, multi-wallet | `galxe-reverse-engineering`, future NFT tracking, `hermes-crypto-agent` |

### Kanban File Layout

```
06-KANBAN/
├── README.md            # Kanban index + workflow + agent roster
├── master-kanban.md     # MONA's high-level coordination view (8-15 tasks)
├── yuna-trading.md      # YUNA's board
├── soyu-sniper.md       # SOYU's board
├── yerin-mining.md      # YERIN's board
└── haeri-airdrop.md     # HAERI's board
```

Each agent board has 4 states (identical to master):

```
## 📋 BACKLOG           (queued, not started)
## 🔄 IN PROGRESS       (currently being worked on)
## 👀 PENDING REVIEW    (done but needs user review)
## ✅ DONE               (closed — date appended)
```

### Task Format

```
- [ ] [AGENT] Deskripsi task — deadline jika ada      (open)
- [x] [AGENT] Task selesai — 2026-MM-DD               (closed)
```

### Task Lifecycle (Ties Everything Together)

This is the FULL workflow when user gives a task. Touches multiple vault files in sequence.

```
1. User gives task
   ↓
2. MONA decides agent → add to BACKLOG of [agent].md AND master-kanban.md
   ↓
3. State transition: BACKLOG → 🔄 IN PROGRESS
   ↓
4. Execute (use the agent's skill stack)
   ↓
5. During: update 02-PROJECTS/[project].md if state changes
   ↓
6. Done → state transition: 🔄 IN PROGRESS → ✅ DONE
   - Add date to entry: `- [x] [AGENT] task — 2026-06-14`
   - Remove from 🔄 IN PROGRESS
   - Move to ✅ DONE
   - Update master-kanban.md (same transition)
   ↓
7. Write receipt to 05-HERMES-OUTPUTS/YYYY-MM-DD-[task].md
   ↓
8. Update 01-DAILY/YYYY-MM-DD.md (running log)
   ↓
9. git add -A && git commit -m "vault: 2026-MM-DD [task] — DONE"
```

### Routing Decision (How MONA Picks the Agent)

Quick heuristic for picking the right board:

| User says... | Route to |
|--------------|----------|
| "trading" / "LP" / "futures" / "PnL" / "OOR" / "Meridian" | YUNA |
| "snipe" / "alpha" / "launch" / "signal" / "pump" / "new token" | SOYU |
| "mining" / "hashrate" / "rig" / "payout" / "RandomX" / "Juno" | YERIN |
| "airdrop" / "claim" / "NFT" / "mint" / "eligibility" | HAERI |
| "setup X" / "bikin Y" / "fix Z" / "audit" (no specific domain) | MONA (self) |

When ambiguous → default to MONA (self), then ask user if still unclear.

### Master-Kanban Size Discipline

Don't let master-kanban grow unbounded. Master is the **coordinator view** — only show:
- High-level agent tasks (1-3 per agent max in IN PROGRESS)
- Cross-agent blockers
- Recently completed (last 3-5 per agent)
- Anything user needs visibility on

Granular work happens on agent boards. Master is the dashboard.

## Receipt Format (Established 2026-06-14)

Every task gets a receipt. Format: **Task | Result | Decisions | Issues | Next Steps**

```markdown
# Receipt: YYYY-MM-DD-[task-name].md

## Task
[One-sentence description of what was done]

## Result
[What was accomplished. Files created, commands run, outputs.]

## Decisions
[Key choices made + reasoning. "Chose X over Y because Z."]

## Issues
[Problems encountered. Bugs. Blockers. Workarounds applied.]

## Next Steps
[Bulleted checklist of follow-ups. Empty list = task closed.]
```

Full template: `templates/receipt-template.md`

## Initialization Procedure (First-Time Setup)

If `/home/ubuntu/obsidian-vault/` doesn't exist, run the 6-step bootstrap:

```bash
# STEP 1 — Folder structure
mkdir -p /home/ubuntu/obsidian-vault/{00-INBOX,01-DAILY,02-PROJECTS,03-RESEARCH,04-WALLET,05-HERMES-OUTPUTS}

# STEP 2 — Git init + .gitignore (exclude 04-WALLET/)
cd /home/ubuntu/obsidian-vault
git init -b main
git config user.email "Mona@hermes-agent.local"
git config user.name "Mona"
# Write .gitignore with: 04-WALLET/, .DS_Store, .obsidian/workspace.json, *.swp

# STEP 3 — README.md (vault index — see templates/vault-readme-template.md)
# STEP 4 — AGENTS.md (VAULT MEMORY PROTOCOL — see templates/agents-md-vault-snippet.md)
# STEP 5 — 01-DAILY/YYYY-MM-DD.md (first daily entry)

# STEP 6 — Commit
git add -A
git commit -m "init: obsidian vault memory system"

# OPTIONAL: Preserve empty folder structure in Git
touch 00-INBOX/.gitkeep 02-PROJECTS/.gitkeep 03-RESEARCH/.gitkeep 05-HERMES-OUTPUTS/.gitkeep
git add -A
git commit -m "chore: add .gitkeep to preserve empty folder structure"

# IMMEDIATELY write first receipt (proof-of-concept + sets standard)
# File: 05-HERMES-OUTPUTS/YYYY-MM-DD-init-vault.md
git add -A
git commit -m "vault: YYYY-MM-DD init receipt"
```

## Git Workflow

### Sensitive Folders — Always Git-Ignored
- `04-WALLET/` is in `.gitignore` because it contains wallet addresses, keypair paths, and secret references
- Even if the folder is "just addresses" (public on-chain data), keeping it git-ignored enforces a discipline: **never accidentally push sensitive paths**
- Verify with: `git check-ignore -v 04-WALLET/` → should print `.gitignore:2:04-WALLET/   04-WALLET/`

### Empty Folders — `.gitkeep` Pattern
Git doesn't track empty folders. To preserve the 6-folder structure across clones:
```bash
# Add .gitkeep to every empty folder EXCEPT git-ignored ones
touch 00-INBOX/.gitkeep 02-PROJECTS/.gitkeep 03-RESEARCH/.gitkeep 05-HERMES-OUTPUTS/.gitkeep
# 04-WALLET/ excluded because it's git-ignored
# 01-DAILY/ will always have today's file, so no .gitkeep needed
```

### Commit Message Conventions
```
init: obsidian vault memory system
chore: add .gitkeep to preserve empty folder structure
vault: 2026-06-14 init receipt
vault: 2026-06-14 iclix-anime-scraper-fix
vault: 2026-06-14 daily
```

### Branch Strategy
- Single `main` branch for personal vault (no PRs, no feature branches)
- For collaboration, branch per major refactor — but typical use is solo

## Sync to GitHub (Recommended)

```bash
# 1. Create private repo on github.com (do NOT init with README/.gitignore)
# 2. Add remote
cd /home/ubuntu/obsidian-vault
git remote add origin git@github.com:<username>/mona-vault.git

# 3. Push
git push -u origin main
```

Use SSH key (not HTTPS token) — generate one with `ssh-keygen -t ed25519 -C "Mona@hermes-agent.local" -f ~/.ssh/github_mona_vault`, add public key to GitHub Settings > SSH.

**REPO MUST BE PRIVATE** — vault contains personal notes, project details, wallet references.

## Sync Options (Pick One)

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **GitHub private repo** | Versioned, free, multi-device | Cloud dependency | Most users |
| **Obsidian Git plugin** | Edit in Obsidian app, auto-sync | Requires Obsidian app setup | Mobile editing |
| **Syncthing** | P2P, no cloud, offline | No version history | Paranoid / offline-first |
| **None (local only)** | Maximum privacy | Single device | High-sensitivity |

## Agent Integration Points

### AGENTS.md (user-level)
The `AGENTS.md` file at `/home/ubuntu/AGENTS.md` contains a `## VAULT MEMORY PROTOCOL` section that gets auto-injected into every session. When initializing a vault, add this section. Template: `templates/agents-md-vault-snippet.md`.

### Daily Note Auto-Update (Cron Job)
Per @zaimiri's "MORNING BRIEF" module: a cron job that reads yesterday's receipts and writes a morning brief to `01-DAILY/`. Pattern (TBD — see Next Steps):

```python
# cron: 0 8 * * * → run daily at 08:00 local
# 1. Read 05-HERMES-OUTPUTS/ of yesterday
# 2. Summarize key outcomes
# 3. Append to 01-DAILY/YYYY-MM-DD.md
# 4. git add -A && git commit
```

### Weekly Synthesis (Cron Job)
Per @zaimiri's "WEEKLY SYNTHESIS" module: cron that rolls up week's receipts into a `01-DAILY/YYYY-W##-synthesis.md`. Pattern (TBD).

## Pitfalls

### Don't Use `write_file` for Vault Files
Use `write_file` only when creating a brand-new file. For updating existing files, use `patch()` to avoid accidental overwrite. Same lesson as SOUL.md.

### Don't Commit 04-WALLET/
The folder is git-ignored for a reason. Never override with `git add -f 04-WALLET/`. If you need to reference a wallet in a receipt, reference by name (e.g., "main Solana wallet") and link the actual address only from `04-WALLET/README.md`.

### Don't Skip Receipts
"Receipt is a one-time thing" is a lie. The protocol only stays alive if EVERY task gets a receipt. The first receipt (`init-vault.md`) sets the standard — but the second, third, and tenth receipts are what make the system actually useful.

### Don't Duplicate the Runtime Memory
The vault is for DETAILED notes. The runtime `memory` tool is for COMPRESSED facts. If something fits in 100 chars (e.g., "user prefers concise responses"), put it in the memory tool, NOT the vault. If it needs 500+ chars of context, put it in the vault.

### Don't Create Per-Task Folders
Don't add `06-EXPLOITS/`, `07-CLIENTS/`, `08-MISC/` for one-off tasks. The 6-folder structure is fixed. Put task-specific files in `03-RESEARCH/` or `02-PROJECTS/` with a descriptive name. (Exception: `06-KANBAN/` is the 7th folder — added 2026-06-14 for agent coordination, not per-task content.)

### 04-WALLET/ Doesn't Show in `git status --ignored` When Empty
The folder is local-only and git-ignored. To verify it's properly ignored:
```bash
git check-ignore -v 04-WALLET/
# → .gitignore:2:04-WALLET/   04-WALLET/
```

### AGENTS.md Lives in TWO Places — Keep in Sync
The `VAULT MEMORY PROTOCOL` + `KANBAN PROTOCOL` sections live in:
- `/home/ubuntu/AGENTS.md` (canonical — auto-injected into every session by Hermes)
- `/home/ubuntu/obsidian-vault/AGENTS.md` (vault copy — for self-documentation, kept in Git)

**Pitfall:** Updating only one location causes protocol drift. Future sessions will load stale protocol.

**Fix:** After every AGENTS.md update:
```bash
cp /home/ubuntu/AGENTS.md /home/ubuntu/obsidian-vault/AGENTS.md
cd /home/ubuntu/obsidian-vault && git add AGENTS.md && git commit -m "vault: AGENTS.md sync"
```

Or use the helper script at `scripts/sync-agents-md.sh` which does the copy + diff + commit in one step.

### Kanban Updates Bloat Commits If Done Per-State-Change
Every state transition (BACKLOG → IN PROGRESS → DONE) is technically a commit-worthy event, but committing each one creates noise. **Batch:** edit the kanban file across multiple transitions, then commit once at task completion. Receipt gets the detailed timeline; kanban gets the final state.

### Bootstrap the Protocol by Following It
When introducing a new protocol (vault, kanban, etc.), the FIRST task under the new protocol should be **the setup of the protocol itself**. E.g., vault init task → first receipt = vault init receipt. This proves the workflow works and sets the standard for future tasks. Don't defer the first receipt to "later" — write it immediately as proof-of-concept.

## Architecture Inspiration — @zaimiri

Source: https://x.com/zaimiri/status/2062897401724022824 (article body requires X login; cover image analyzed via vision)

### 8 Modules (from article)
1. **VAULT** — markdown files (this is `00-INBOX/` + `01-DAILY/` + `02-PROJECTS/`)
2. **FILESYSTEM + MCP** — Hermes reads/writes vault via filesystem tool
3. **CLAUDE.MD/AGENTS.MD CONTEXT** — vault protocol injected via `AGENTS.md`
4. **SKILLS SOPs** — skills as Standard Operating Procedures (we have 80+)
5. **CRON JOBS** — scheduled tasks (owntown-watcher, tunnel-watchdog, etc.)
6. **MORNING BRIEF** — daily 08:00 cron → read yesterday's receipts → morning brief
7. **INBOX PROCESSOR** — process `00-INBOX/` weekly into projects
8. **WEEKLY SYNTHESIS** — roll up week's receipts into synthesis

### 5 Principles (from article)
1. **LOCAL FIRST** — no cloud lock-in
2. **PLAIN TEXT** — markdown, future-proof
3. **EVERY RUN MAKES SYSTEM SMARTER** — receipts accumulate, system learns
4. **RELIABLE LOOP** — PLAN > ACT > CHECK > RECORD
5. **EVERYTHING CONNECTED. NOTHING LOCKED IN.**

Coverage status: 4/8 modules active (VAULT ✅, FILESYSTEM+MCP ✅, AGENTS.MD ✅, CRON ✅, SKILLS ✅). 3/8 partial (MORNING BRIEF ⏳, INBOX PROCESSOR ⏳, WEEKLY SYNTHESIS ⏳). 0/8 missing.

Full reference: `references/zaimiri-architecture.md`

## Quick Commands

```bash
# Read vault state
ls /home/ubuntu/obsidian-vault/
cat /home/ubuntu/obsidian-vault/01-DAILY/$(date +%Y-%m-%d).md
cat /home/ubuntu/obsidian-vault/AGENTS.md | sed -n '/## VAULT MEMORY/,/^## /p'

# Add project file
touch /home/ubuntu/obsidian-vault/02-PROJECTS/newproject.md
# ... edit ...
cd /home/ubuntu/obsidian-vault && git add -A && git commit -m "vault: 02-PROJECTS/newproject"

# Add receipt
touch /home/ubuntu/obsidian-vault/05-HERMES-OUTPUTS/$(date +%Y-%m-%d)-[task].md
# ... fill in format ...
cd /home/ubuntu/obsidian-vault && git add -A && git commit -m "vault: $(date +%Y-%m-%d) [task]"

# Daily note
touch /home/ubuntu/obsidian-vault/01-DAILY/$(date +%Y-%m-%d).md
# ... fill in ...
cd /home/ubuntu/obsidian-vault && git add -A && git commit -m "vault: $(date +%Y-%m-%d) daily"

# Verify git-ignore working
git -C /home/ubuntu/obsidian-vault check-ignore -v 04-WALLET/
```

## Linked Files

- `references/zaimiri-architecture.md` — @zaimiri's article: full module/principle breakdown from cover image
- `references/kanban-roles.md` — Detailed skill stacks per agent (YUNA/SOYU/YERIN/HAERI) — load when routing a task
- `templates/receipt-template.md` — copy-paste starter for task receipts
- `templates/vault-readme-template.md` — copy-paste starter for new vault `README.md`
- `templates/agents-md-vault-snippet.md` — VAULT MEMORY PROTOCOL section to inject into `AGENTS.md`
- `templates/agents-md-kanban-snippet.md` — KANBAN PROTOCOL section to inject into `AGENTS.md`
- `templates/gitignore-template.md` — copy-paste starter for new vault `.gitignore`
- `templates/kanban-board-template.md` — copy-paste starter for new agent kanban board
- `scripts/sync-agents-md.sh` — sync root AGENTS.md → vault AGENTS.md + auto-commit

## Related Skills

- `mona-enhanced-memory` — runtime `memory` tool (complement, not replacement)
- `operator-workspace-bootstrap` — broader workspace folder structure pattern
- `pm2-process-health` — cron jobs that auto-update vault (morning brief, weekly synthesis)
- `mona-command-center` — could integrate vault writes into Telegram bot commands
- `meridian-dlmm-agent` — YUNA's primary trading skill
- `charon-sniper-bot` — SOYU's primary sniper skill
- `vps-mining-setup` — YERIN's primary mining skill
- `galxe-reverse-engineering` — HAERI's primary airdrop skill
