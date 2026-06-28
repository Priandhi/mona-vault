---
type: architecture-note
date: 2026-06-28
status: PRODUCTION
---

# LangGraph v3 — Bug Bounty Engine (REAL StateGraph)

## Files
- `/home/ubuntu/shared/langgraph_engine_v3.py` — Main engine (StateGraph + conditional edges + MemorySaver)
- `/home/ubuntu/shared/graph_state.py` — TypedDict state schema (GraphState)
- `/home/ubuntu/shared/bb_nodes.py` — 7 node functions (mona_scope, yuna_recon, yuna_exploit, yuna_bypass, mona_review, soyu_archive, mas_approval)
- `/home/ubuntu/shared/telegram_notifier.py` — Notify 3 bot topics per phase
- `/home/ubuntu/shared/kanban_mover.py` — Auto card move between 8 folders
- `/home/ubuntu/shared/tool_executor.py` — subfinder+httpx+ffuf+nuclei wrappers
- `/home/ubuntu/shared/scope_verifier.py` — HackerOne GraphQL (no auth)

## What makes this REAL LangGraph (not v2 stub)
1. `StateGraph(GraphState)` — TypedDict-validated state
2. `add_conditional_edges(source, routing_fn, path_map)` — routing 200/403/429/vuln/no_vuln
3. `MemorySaver()` checkpointer — resume from any node after crash
4. `interrupt_before=["mas_approval"]` — human-in-loop native
5. `app.invoke(state, config={"thread_id": task_id})` — compiled graph, thread-scoped
6. `app.get_state(config)` — inspect current state + next node
7. `app.update_state(config, {"mas_decision": "approve"}, as_node="mas_approval")` — resume after interrupt

## Graph
```
START → mona_scope
  ├─ in_scope → yuna_recon
  ├─ out_scope → soyu_archive (blocked)
  └─ no_program → yuna_recon

yuna_recon
  ├─ alive → yuna_exploit
  ├─ no_alive → soyu_archive (failed)
  └─ rate_limited → wait → yuna_recon (retry)

yuna_exploit
  ├─ vuln_found → mona_review
  ├─ no_vuln → mona_review
  ├─ forbidden → yuna_bypass
  └─ fail_3x → mona_review

yuna_bypass (max 3 retries)
  ├─ alive → yuna_exploit
  ├─ forbidden → yuna_bypass (retry)
  └─ fail_3x → mona_review

mona_review
  ├─ escalate → mas_approval (INTERRUPT)
  └─ done → soyu_archive

mas_approval (paused)
  ├─ approve → soyu_archive
  └─ reject → soyu_archive

soyu_archive → END
```

## CLI
```bash
# Run
python3 /home/ubuntu/shared/langgraph_engine_v3.py \
  --task <name> --target <url> --program <handle> --run

# Status
python3 /home/ubuntu/shared/langgraph_engine_v3.py --status <task_id>

# Resume after Mas approval
python3 /home/ubuntu/shared/langgraph_engine_v3.py \
  --resume <task_id> --decision approve

# Show graph
python3 /home/ubuntu/shared/langgraph_engine_v3.py --graph
```

## Test Results (2026-06-28)
- ✅ Graph compiles with StateGraph + MemorySaver + interrupt_before
- ✅ Unico UAT target: scope verified → recon (2 alive) → exploit (403) → bypass (3x fail) → review → archive (blocked)
- ✅ Local target: no_program → recon (1 alive) → exploit (no vuln) → review → archive
- ✅ Mock vuln state: mona_review correctly routes to `escalate` + sets `needs_mas_approval=True`
- ✅ Conditional edges work: 403 loops to bypass 3x before escalating
- ✅ Telegram notifications fire per phase
- ✅ Kanban cards auto-move between folders

## v2 (OLD STUB) — KEPT AS REFERENCE
- `/home/ubuntu/shared/langgraph_engine_v2_OLD_STUB.py.bak`
- Was a sequential Python loop with `NODES = {"mona": run_mona}` dict
- NO real StateGraph, NO conditional edges, NO MemorySaver, NO interrupt
- DO NOT USE — v3 is the real engine
