---
type: master-kanban
project: bug-bounty
created_at: 2026-06-28
last_updated: 2026-06-28
---

# Bug Bounty — Master Kanban

## Pipeline Overview

```
00-BACKLOG → 01-MONA-REVIEW → 02-YUNA-RECON → 03-YUNA-EXPLOIT → 04-SOYU-MONITOR → 05-REVIEW → 07-DONE
                                                                                    ↓
                                                                              06-BLOCKED
```

## Agent Roles

| Agent | Role | Phase | Topic |
|-------|------|-------|-------|
| **MONA** | Coordinator + Lead Hacker | Scope verify, Review, Report | 8460 🧠 MONA |
| **YUNA** | Executor | Recon, Exploit | 8461 💹 YUNA |
| **SOYU** | Hunter | Monitor, OSINT | 8462 🎯 SOYU |
| **KANTOR** | Shared workspace | Handoff, Status | 8463 🏕️ KANTOR |

## Folder Structure

| Folder | Owner | Purpose |
|--------|-------|---------|
| `00-BACKLOG` | Mas | New targets, pending triage |
| `01-MONA-REVIEW` | MONA | Scope verification, strategy |
| `02-YUNA-RECON` | YUNA | Active recon (nuclei, subfinder, ffuf) |
| `03-YUNA-EXPLOIT` | YUNA | Exploit writing, vuln verification |
| `04-SOYU-MONITOR` | SOYU | OSINT, CVE watch, passive monitoring |
| `05-REVIEW` | MONA | Review findings before report |
| `06-BLOCKED` | Any | Blocked targets (needs Mas input) |
| `07-DONE` | Any | Completed, reported, paid |

## Card Format (YAML Frontmatter)

```yaml
---
type: kanban-card
target: "program-handle"
program_url: "https://hackerone.com/handle"
scope: ["*.example.com"]
phase: backlog
status: pending
assigned_to: null
priority: medium
bounty_range: "low"
attempts: 0
findings: []
errors: []
next_node: "mona_scope_verify"
history: []
---
```

## Workflow Rules

1. **Mas adds target** → `00-BACKLOG` with program URL
2. **MONA picks up** → moves to `01-MONA-REVIEW`, verifies scope via HackerOne GraphQL
3. **MONA hands off to YUNA** → moves to `02-YUNA-RECON`, YUNA runs nuclei+subfinder+ffuf
4. **YUNA finds vuln** → moves to `03-YUNA-EXPLOIT`, writes PoC
5. **YUNA confirms** → moves to `05-REVIEW`, MONA reviews
6. **MONA reports** → moves to `07-DONE`
7. **Blocked?** → `06-BLOCKED` with reason in `errors[]`
8. **SOYU monitors** → `04-SOYU-MONITOR` for passive OSINT on active targets

## LangGraph Integration

Each card = 1 LangGraph state node. The `phase` field drives the graph:

```
backlog → mona_scope_verify → yuna_recon → yuna_exploit → mona_review → done
                                                    ↓
                                              (error) → blocked
```

- **Checkpoint:** `/home/ubuntu/shared/state.graph.json`
- **State schema:** `/home/ubuntu/shared/state_schema.py`
- **Engine:** `/home/ubuntu/shared/langgraph_engine.py`

## Stats

- **Total targets:** 0
- **Active:** 0
- **Done:** 0
- **Blocked:** 0
