---
name: "kanban-dispatch"
description: "Multi-agent Kanban task dispatch: orchestrator polls a board, workers claim and execute tasks, results are reconciled to the master board. Use when setting up a task queue, dispatching parallel work, or running a long-lived worker process."
tags:
  - kanban
  - task-queue
  - dispatch
  - orchestrator
  - worker
  - subagent
---
# Kanban Task Dispatch

> Multi-agent task board for the soyu profile. The orchestrator/worker pair runs the dispatch loop, queues tasks, and routes work to sub-agents (YUNA, SOYU, YERIN, HAERI, MONA).

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "start kanban", "dispatch loop", "task queue" | `references/kanban-orchestrator/` |
| "pick up task", "claim work", "worker loop" | `references/kanban-worker/` |

## Architecture

```
[ orchestrator ] -- polls task board --> [ worker ] -- runs task --> reports back
       ^                                                           |
       |                                                           v
       +----------------- task state (master board) <-------------+
```

The orchestrator is the single source of truth for which task is in flight. The worker grabs a task, executes it, and writes the result back. The board state is SQLite or the Obsidian vault (`06-KANBAN/`).

## Topic Pages

- `references/kanban-orchestrator/SKILL.md` — Orchestrator loop, board schema, task routing
- `references/kanban-worker/SKILL.md` — Worker loop, sub-agent invocation, completion handoff

## Related

- `delegate-coding-agents` (in autonomous-ai-agents/) — for delegating specific task implementations to Claude/Codex
- `mona-knowledge-vault` (in hermes/) — vault-based Kanban (`06-KANBAN/master-kanban.md`)
- `pm2-process-health` (in process-ops/) — for keeping the orchestrator service alive
