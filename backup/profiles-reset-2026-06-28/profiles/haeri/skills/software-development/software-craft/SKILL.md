---
name: software-craft
description: "Software development process and craft — plan mode, spike (throwaway exploration), writing plans, TDD (red-green-refactor), subagent-driven execution, pre-commit code review, and honest review discipline. Class-level methodology skills adapted from obra/superpowers and gsd-build. Trigger when user asks to write a plan, spike an idea, do TDD, execute via subagents, request code review, or review another agent's proposal."
version: 1.0.0
author: Hermes Agent (adapted from obra/superpowers + gsd-build)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, tdd, subagent, code-review, methodology, superpowers, craft]
    replaces: [plan, spike, test-driven-development, requesting-code-review, review-discipline, writing-plans, subagent-driven-development]
---

# Software Craft — Process & Methodology

Class-level umbrella for software development methodology. Each section is a standalone process; together they form a coherent build/test/review flow.

## When to use which

| User says… | Load |
|---|---|
| "Write a plan for this" / "what's the approach" / "let's plan first" | §1 Plan Mode |
| "Spike on this" / "is this even feasible" / "validate before we build" | §2 Spike |
| "Write a detailed plan" / "hand-off ready plan" / "spec this out" | §3 Writing Plans |
| "Write tests first" / "TDD this" / "red-green-refactor" | §4 Test-Driven Development |
| "Use subagents to execute this" / "parallel implementation" / "delegate tasks" | §5 Subagent-Driven Development |
| "Pre-commit review" / "security scan" / "quality gates" | §6 Requesting Code Review |
| "Review this agent's proposal" / "koreksi dulu" / "honest feedback" | §7 Review Discipline |

## §1. Plan Mode (was `plan`)

Plan mode = write the plan, do not execute. Default when user asks "what's the approach" without committing to action. Outputs markdown plan to `.hermes/plans/` with bite-sized tasks, exact paths, complete code.

**Key behaviors:**
- One turn only — no implementation
- Plans must be specific enough that a fresh subagent can execute them
- Save to `.hermes/plans/<date>-<slug>.md`

For full rules: `references/plan.md`

## §2. Spike (was `spike`)

Throwaway exploration. Validate feasibility before committing to a build. Outcomes: "feasible as designed", "feasible with caveats", "not feasible — try alternative", or "need more research".

**Hard rules:**
- Code lives in `spike-<topic>/` — clearly marked throwaway
- Time-box (default: 1 hour)
- No production paths touched
- Capture learnings in `spike-<topic>/README.md`

For full rules: `references/spike.md`

## §3. Writing Plans (was `writing-plans`)

Different from §1 in scope: writing-plans produces HANDOFF-READY plans assuming the implementer has zero context and questionable taste. Used when delegating to a subagent.

**Required sections in any plan:**
- Goal (one paragraph)
- Architecture decisions with rationale
- Files to create/modify (exact paths)
- Code (full snippets, no pseudo-code)
- Verification (tests, manual checks)
- Out-of-scope (what NOT to do)

For full rules: `references/writing-plans.md`

## §4. Test-Driven Development (was `test-driven-development`)

Red-green-refactor. Write the test first. Watch it fail. Write minimal code to pass. Refactor.

**Iron rule:** If you didn't watch the test fail, you don't know if it tests the right thing.

For full rules: `references/test-driven-development.md`

## §5. Subagent-Driven Development (was `subagent-driven-development`)

Execute plans via `delegate_task()` with fresh subagent per task and 2-stage review. Two subagent kinds:
- **Implementer subagent** — does the work
- **Reviewer subagent** — independent quality check

For full rules + context budget + gates taxonomy: `references/subagent-driven-development.md` + `references/context-budget-discipline.md` + `references/gates-taxonomy.md`

## §6. Requesting Code Review (was `requesting-code-review`)

Pre-commit verification pipeline: security scan, baseline-aware quality gates, auto-fix for known-safe patterns, independent reviewer subagent.

**Pipeline stages:**
1. Static scan (bandit, eslint, etc.)
2. Security audit (secrets, injection)
3. Quality gates (coverage, complexity)
4. Auto-fix safe issues
5. Reviewer subagent verdict

For full rules: `references/requesting-code-review.md`

## §7. Review Discipline (was `review-discipline`)

Honest review of proposals from other agents (Claude, GPT, Gemini), blog posts, docs, or external sources.

**Core discipline:** Only flag ACTUAL issues with verified evidence. Never fabricate bugs to look thorough. Own mistakes immediately when wrong.

**Triggers:** "review", "koreksi dulu", "kasih feedback", or whenever the agent is about to claim something is wrong/broken.

For full rules: `references/review-discipline.md`

## How they chain together

```
User wants to build X
  │
  ▼ §1 Plan Mode ────────► short plan
  │
  ▼ §2 Spike ────────────► validate feasibility
  │
  ▼ §3 Writing Plans ────► handoff-ready plan
  │
  ▼ §5 Subagent-Driven ──► implementation
  │     │
  │     ▼ §4 TDD ────────► tests written first
  │     │
  │     ▼ §6 Code Review ► pre-commit check
  │
  ▼ §7 Review Discipline ► if user asks for honest critique
```

## Absorbed Skills (consolidated June 2026)

- `plan` → §1 + `references/plan.md`
- `spike` → §2 + `references/spike.md`
- `writing-plans` → §3 + `references/writing-plans.md`
- `test-driven-development` → §4 + `references/test-driven-development.md`
- `subagent-driven-development` → §5 + `references/subagent-driven-development.md` + `references/context-budget-discipline.md` + `references/gates-taxonomy.md`
- `requesting-code-review` → §6 + `references/requesting-code-review.md`
- `review-discipline` → §7 + `references/review-discipline.md`
