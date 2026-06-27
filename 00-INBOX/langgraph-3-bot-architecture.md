---
type: concept-note
date: 2026-06-28
session: Arsitektur 3 Bot — LangGraph untuk Bug Bounty + CTF
status: SAVED FOR DISCUSSION
---

# 🧠 LangGraph Architecture — 3 Bot Setup (Concept)

## Core Concept
LangGraph-based multi-agent system: MONA (coordinator) → YUNA (executor) → SOYU (hunter). 
Stateful graph dengan conditional branching buat error handling, retry, dan human-in-the-loop.

## Graph Structure (Proposed)

```
Input (Mas → KANTOR)
  ↓
MONA node: verify scope / strategi / decomposisi
  ↓ Conditional Edge
  ├─ Bug bounty? → YUNA scan
  │                     ↓
  │                     Hasil: 200? → MONA review → tulis report
  │                     Hasil: 403? → retry loop (3x) → fail → SOYU alert
  │                     Hasil: rate limit? → wait → resume
  └─ CTF? → YUNA solve
                           ↓
                        Hasil: flag? → MONA verify → submit
                        Hasil: wrong? → retry (3x) → pivot → SOYU track
```

## Key Features
- Stateful (tiap node tau: attempt_count, last_error, next_node)
- Conditional edges (if 200 → report, if 403 → retry, if rate_limit → wait)
- Human-in-the-loop (native, pause buat Mas approval)
- Checkpoint + resume (kalau crash, bisa lanjut dari exact state)
- Error handling: 3x → auto-pivot → tell Mas

## Agents Roles
| Agent | Role | Node | Model |
|---|---|---|---|
| MONA | Coordinator + Strategist | scope verification, decompos, report | Opus 4.6 |
| YUNA | Executor + Scanner | nuclei, ffuf, subfinder, exploit | Flash |
| SOYU | Hunter + Monitor | alert, CTF track, OSINT | Flash |

## Communication
- Telegram topics (8460 MONA, 8461 YUNA, 8462 SOYU, 8463 KANTOR)
- Shared state via /home/ubuntu/shared/state.graph.json
- Checkpoint: /home/ubuntu/shared/checkpoint/

## Notes
- CrewAI = simpler setup, tapi terbatas (sequential, gak ada retry)
- LangGraph = lebih complex tapi cocok buat CTF/bug bounty (conditional, stateful)
- Hybrid: CrewAI buat standard pipeline, LangGraph buat edge cases
- Mas interested in exploring LangGraph implementation

## Related
- Hermes profiles: yuna → executor, soyu → hunter
- Skill: LangGraph setup (custom nodes + tools)
- Saved to vault for next discussion session