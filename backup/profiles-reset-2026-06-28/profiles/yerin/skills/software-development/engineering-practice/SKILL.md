---
name: engineering-practice
description: >-
  Engineering practice umbrella: planning (write actionable markdown plans), spiking (throwaway experiments
  to validate ideas before build), test-driven development (RED-GREEN-REFACTOR), systematic debugging
  (4-phase root cause analysis), requesting code review (pre-commit review with security scan + auto-fix),
  and review discipline (honest technical feedback — never fabricate bugs). Trigger when the user wants
  to plan, spike, write tests first, debug a tricky bug, request a review, or evaluate another agent's
  technical claim.
triggers:
  - plan
  - spike
  - tdd
  - test driven
  - red green refactor
  - debug
  - debugging
  - bug investigation
  - code review
  - request review
  - review discipline
  - honest review
  - koreksi
  - koreksi dulu
---

# Engineering Practice

This is the umbrella for engineering workflow practices. The 6 sibling skills
(`plan`, `spike`, `test-driven-development`, `systematic-debugging`,
`requesting-code-review`, `review-discipline`) have been absorbed as references;
this SKILL.md captures the cross-cutting discipline and links to per-practice detail.

## Class-level capabilities

| Practice | Reference | When to use |
|----------|-----------|-------------|
| **Plan** | `references/plan-absorbed.md` | User wants a plan instead of execution. Write actionable markdown to `.hermes/plans/` |
| **Spike** | `references/spike-absorbed.md` | Throwaway experiment to validate an idea before building |
| **TDD** | `references/test-driven-development-absorbed.md` | RED-GREEN-REFACTOR cycle, tests first, never modify a failing test to make it pass |
| **Debugging** | `references/systematic-debugging-absorbed.md` | 4-phase root cause debugging: understand bug before fixing |
| **Request review** | `references/requesting-code-review-absorbed.md` | Pre-commit review: security scan, quality gates, auto-fix |
| **Review discipline** | `references/review-discipline-absorbed.md` | Honest technical feedback: only flag REAL bugs, never fabricate to look thorough |

## The flow

These practices form a natural sequence:

1. **Plan** (when scope is unclear) → write `.hermes/plans/<name>.md` with bite-sized tasks
2. **Spike** (when approach is unclear) → throwaway code to validate the idea
3. **TDD** (when implementing) → write failing test, make it pass, refactor
4. **Debug** (when stuck) → 4-phase root cause: reproduce, isolate, hypothesize, fix
5. **Request review** (before merge) → security scan + auto-fix + quality gates
6. **Review discipline** (always, especially when reviewing) → only flag real issues with evidence

## Cross-cutting principles

### Plan mode (entry point)

When the user asks for a plan (not execution), this is the entry practice. The plan should be:
- Bite-sized tasks (each task a single session)
- Exact paths and code (no "implement X" handwaving)
- Saved to `.hermes/plans/` inside the workspace
- Linked to other practices (TDD, debugging, review) as appropriate

### The "honest" rule (applies to all)

From `review-discipline`:
- Only flag what you can VERIFY (trace the code, run the scenario)
- If wrong, own it FAST
- Never invent bugs to look thorough

This applies to debugging too: don't claim "X is the bug" without evidence.

### TDD anti-patterns (avoid)

From `test-driven-development`:
- Never modify a failing test to make it pass (defeats the whole point)
- Never write tests after the implementation
- If you can't write a failing test first, the design isn't testable — refactor

### Debugging anti-patterns (avoid)

From `systematic-debugging`:
- Don't guess-and-check random fixes
- Don't add try/except to silence the error
- Don't "fix" the symptom without finding the root cause

## Absorbed skills (June 2026 consolidation)

The following skills were merged into this umbrella. Their full SKILL.md content is preserved as references.

- `plan` → `references/plan-absorbed.md`
- `spike` → `references/spike-absorbed.md`
- `test-driven-development` → `references/test-driven-development-absorbed.md`
- `systematic-debugging` → `references/systematic-debugging-absorbed.md` (plus `references/python-venv-crash.md` case study)
- `requesting-code-review` → `references/requesting-code-review-absorbed.md`
- `review-discipline` → `references/review-discipline-absorbed.md`
