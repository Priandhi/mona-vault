---
name: kanban
description: "Hermes Kanban — multi-agent task board with orchestrator and worker roles. Class-level umbrella covering the Kanban lifecycle, role-specific playbooks (orchestrator decomposition + worker execution), task state machine, recovery actions, and integration with hermes-* profiles. Trigger when user mentions Kanban, asks to use Kanban for multi-agent work, mentions dispatching workers, or discusses task routing/decomposition."
version: 1.0.0
author: Hermes Agent
license: MIT
environments: [kanban]
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, worker, task-board, dispatch, decompose]
    replaces: [kanban-orchestrator, kanban-worker]
---

# Hermes Kanban

Hermes Kanban is a multi-agent task board where one **orchestrator** profile decomposes work and dispatches cards to **worker** profiles. Each card runs as a fresh agent process with its own skills, model, and workspace.

## Two roles, two sections

| If you're playing… | Read |
|---|---|
| **Orchestrator** — decomposes work, routes cards to specialists | §1 |
| **Worker** — executes a single assigned card | §2 |

Both roles share the same lifecycle (orient → work → heartbeat → block/complete). The core lifecycle is auto-injected into every kanban process via the `KANBAN_GUIDANCE` system-prompt block; this umbrella is the deeper detail.

## §1. Orchestrator (was `kanban-orchestrator`)

### Profiles are user-configured — not a fixed roster

Hermes setups vary widely. Some users run a single profile; some run a small fleet (`docker-worker`, `cron-worker`); some run a curated specialist team. There is **no default specialist roster** — the orchestrator skill does not know what profiles exist on this machine.

The dispatcher silently fails to spawn unknown assignee names. So a card assigned to `researcher` on a setup that only has `docker-worker` just sits in `ready` forever.

**Step 0: discover available profiles before planning.**
- `hermes profile list` — prints the table of profiles configured on this machine
- `kanban_list(assignee="<some-name>")` — sanity-check a single name
- Just ask the user

### When to use the board (vs. just doing the work)

Create Kanban tasks when any of these are true:
1. Multiple specialists are needed (research + analysis + writing = 3 profiles)
2. The work should survive a crash or restart
3. The user might want to interject (human-in-the-loop)
4. Multiple subtasks can run in parallel (fan-out for speed)
5. Review / iteration is expected
6. The audit trail matters

If none apply — it's a small one-shot reasoning task — use `delegate_task` instead or answer the user directly.

### The anti-temptation rules

The orchestrator's job is to **decompose and route**, never to do the work. If you find yourself about to call a tool that mutates state in a domain you assigned to a card, stop and write a card instead.

### Decomposition patterns

**Pattern A — Specialist fan-out:**
```
Card 1: research → researcher
Card 2: implementation → docker-worker
Card 3: review → reviewer
```

**Pattern B — Sub-task chain:**
```
Card 1: scaffold (worker-A)
Card 2: implement (worker-B, blocks on 1)
Card 3: test (worker-C, blocks on 2)
```

**Pattern C — Judge loop:**
- Worker does the work, judge evaluates, loop until goal met
- Use for "translate the README" or "keep going until X is true"
- Write explicit acceptance criteria — "Translate every section to French; no English remains" > "Translate the README"

For full rules + pitfalls + recovery actions: `references/orchestrator.md`

## §2. Worker (was `kanban-worker`)

### Workspace handling

Your workspace kind determines how you should behave inside `$HERMES_KANBAN_WORKSPACE`:

| Kind | What it is | How to work |
|---|---|---|
| `scratch` | Fresh tmp dir, yours alone | Read/write freely; it gets GC'd when the task is archived. |
| `dir:<path>` | Shared persistent directory | Other runs will read what you write. Treat it like long-lived state. |
| `worktree` | Git worktree at the resolved path | If `.git` doesn't exist, run `git worktree add <path> ${HERMES_KANBAN_BRANCH:-wt/$HERMES_KANBAN_TASK}` first, then commit work here. |

### Tenant isolation

If `$HERMES_TENANT` is set, prefix memory entries with the tenant so context doesn't leak: `business-a: Acme is our biggest customer` not `Acme is our biggest customer`.

### Good summary + metadata shapes

The `kanban_complete(summary=..., metadata=...)` handoff is how downstream workers read what you did.

**Coding task:**
```python
kanban_complete(
    summary="shipped rate limiter — token bucket, keys on user_id with IP fallback, 14 tests pass",
    metadata={
        "changed_files": ["rate_limiter.py", "tests/test_rate_limiter.py"],
        "tests_run": 14,
        "tests_passed": 14,
        "decisions": ["user_id primary, IP fallback for unauthenticated requests"],
    },
)
```

### Things workers should NEVER do

- Call `clarify` to ask the user a question — you're running headless, it will time out. Use `kanban_comment` + `kanban_block` instead.
- Modify files outside `$HERMES_KANBAN_WORKSPACE` unless the task body says to.
- Create follow-up tasks assigned to yourself — assign to the right specialist.
- Complete a task you didn't actually finish. Block it instead.

For full rules + pitfalls: `references/worker.md`

## Recovery actions (both roles)

When a worker profile keeps crashing, hallucinating, or getting blocked:

1. **Reclaim** (`hermes kanban reclaim <task_id>`) — abort and reset to `ready`
2. **Reassign** (`hermes kanban reassign <task_id> <new-profile> --reclaim`) — switch profile
3. **Change profile model** — edit profile config, then Reclaim to retry

Hallucination warnings appear when `kanban_complete(created_cards=[...])` references card ids that don't exist or weren't created by the worker's profile — the gate blocks the completion.

## CLI fallback (for human operators)

Every tool has a CLI equivalent:
- `kanban_show` ↔ `hermes kanban show <id> --json`
- `kanban_complete` ↔ `hermes kanban complete <id> --summary "..." --metadata '{...}'`
- `kanban_block` ↔ `hermes kanban block <id> "reason"`
- `kanban_create` ↔ `hermes kanban create "title" --assignee <profile> [--parent <id>]`

## Absorbed Skills (consolidated June 2026)

- `kanban-orchestrator` → §1 + `references/orchestrator.md`
- `kanban-worker` → §2 + `references/worker.md`
