---
name: "delegate-coding-agents"
description: "Delegate coding tasks to external CLI agents (Claude Code, OpenAI Codex, OpenCode). Hermes orchestrates; the agent is an isolated implementation lane whose diff Hermes reviews. Use when work is multi-file, has clear acceptance criteria, or when user explicitly says 'use claude/codex/opencode'."
tags:
  - coding-agents
  - claude-code
  - codex
  - opencode
  - delegation
  - worktree
  - PTY
---
# External Coding Agent Delegation

> Umbrella for delegating coding work to external CLI agents: Claude Code, OpenAI Codex, and OpenCode. Hermes acts as the orchestrator; the external agent is an isolated implementation lane.

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "claude code", "anthropic coding agent", "use claude" | `references/claude-code/` |
| "codex", "openai codex", "use codex" | `references/codex/` |
| "opencode", "open-source coding agent" | `references/opencode/` |
| "kanban codex lane", "isolated worktree for codex" | `references/kanban-codex-lane/` |

## Architecture

Hermes is the **task owner**. The external agent is an **input lane** only — its output is not a task completion signal, not a trusted reviewer, and not allowed to write durable state. Hermes reviews the diff, runs tests, and writes the handoff.

```
User gives task
   ↓
Hermes plans + delegates to <agent>
   ↓
Agent runs in isolated worktree/branch
   ↓
Hermes reviews diff + reruns tests
   ↓
Hermes accepts / cherry-picks / rejects
   ↓
Hermes writes handoff
```

## When to Delegate vs Do It Yourself

**Delegate when:**
- Multi-file feature work with clear acceptance criteria
- Refactors with bounded diff
- PR reviews
- Mechanical migrations
- Boilerplate generation

**Do it yourself when:**
- One-line fixes
- Investigations where the answer is short
- Config tweaks
- Touches secrets, credentials, or live trading systems
- User just wants a quick answer

## PITFALLS (Universal)

1. **Always set `workdir`** in terminal calls — keep the agent in the right project directory.
2. **Use `--max-turns` in print mode** — prevents runaway loops.
3. **Monitor tmux/PTY sessions** — use `tmux capture-pane` or `process(action='poll')` instead of waiting blindly.
4. **Don't trust self-report** — always inspect the diff and rerun tests from Hermes.
5. **Use `pty=true` for interactive TUI** — Codex, OpenCode, Claude Code interactive modes hang without a PTY.

## Related (not part of this umbrella)

- `autonomous-ai-agents/hermes-agent` — Configure Hermes Agent itself (different scope; the framework that orchestrates THESE agents).
- `kanban-orchestrator`, `kanban-worker` (in devops/) — Kanban task dispatch and worker conventions.

## Topic Pages

- `references/claude-code/SKILL.md` — Claude Code v2.x (Anthropic): print mode, interactive PTY, worktree, hooks
- `references/codex/SKILL.md` — OpenAI Codex CLI: exec mode, worktrees, batch reviews
- `references/opencode/SKILL.md` — OpenCode TUI + CLI: run, interactive, model selection
- `references/kanban-codex-lane/SKILL.md` — Kanban + Codex dual-lane convention with PMB safety constraints
