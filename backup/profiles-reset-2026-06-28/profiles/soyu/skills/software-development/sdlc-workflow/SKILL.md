---
name: "sdlc-workflow"
description: "End-to-end software development workflow: plan (no execution), spike (validate), writing-plans (output plan), code, requesting-code-review (pre-commit gates), subagent-driven-development (delegate & ship). One entry point for the full planning-to-shipment cycle."
tags:
  - sdlc
  - planning
  - spike
  - code-review
  - subagent
  - delegate-task
  - TDD
---
# Software Development Workflow

> Umbrella for the planning → review → execution phases of software development. Five narrow skills that should be loaded as one class.

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "plan", "write a plan", "no execution yet", "save to .hermes/plans" | `references/plan/` |
| "spike", "throwaway experiment", "validate idea" | `references/spike/` |
| "write implementation plan", "bite-sized tasks", "code stubs" | `references/writing-plans/` |
| "code review", "pre-commit", "security scan", "quality gates" | `references/requesting-code-review/` |
| "execute plan", "subagent", "delegate_task", "2-stage review" | `references/subagent-driven-development/` |

## The SDLC Cycle

```
[ plan / writing-plans ]   →  [ spike ]   →  [ code ]   →  [ requesting-code-review ]   →  [ subagent-driven-development ]
   (no execution)              (validate)      (build)         (verify)                            (delegate & ship)
```

`plan` and `writing-plans` look similar but are subtly different:
- `plan` — Hermes-internal: write a plan to `.hermes/plans/`, no code execution, used by the plan-mode slash command.
- `writing-plans` — Generic: write an implementation plan with bite-sized tasks, paths, and code stubs. Output is the plan itself, ready to be handed to a subagent.

`spike` is for throwaway experiments: prove something is feasible before committing to an architecture.

`requesting-code-review` is for the "is this ready to ship?" check — security, quality gates, auto-fix.

`subagent-driven-development` is for executing a plan via `delegate_task` subagents with 2-stage review (writer subagent + reviewer subagent).

## PITFALLS

1. **Don't mix `plan` with `writing-plans` in one session.** Pick one. `plan` is for Hermes's plan mode; `writing-plans` is for ad-hoc planning that ends with delegating to a coding agent.
2. **Always `spike` before non-trivial architecture decisions.** A 30-minute spike beats 3 hours of wrong direction.
3. **Don't skip `requesting-code-review`.** It's the last line of defense before code hits a branch.

## Topic Pages

- `references/plan/SKILL.md` — Plan mode: write markdown plan to .hermes/plans/
- `references/spike/SKILL.md` — Throwaway experiments to validate an idea
- `references/writing-plans/SKILL.md` — Write implementation plans with bite-sized tasks
- `references/requesting-code-review/SKILL.md` — Pre-commit review: security scan, quality gates
- `references/subagent-driven-development/SKILL.md` — Execute plans via delegate_task subagents

## Related

- `delegate-coding-agents` (autonomous-ai-agents/) — for delegating to Claude Code / Codex / OpenCode
- `code-debugging` (software-development/) — for the "what's wrong with this code?" phase
- `requesting-code-review` ↔ `review-discipline` — review-discipline is a meta-skill about honest review; requesting-code-review is the operational pre-commit hook
