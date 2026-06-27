---
name: systematic-debugging
description: "4-phase root cause debugging: understand bugs before fixing."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    related_skills: [test-driven-development, plan, subagent-driven-development]
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## Language-Specific Debugging

### Python: pdb REPL + debugpy Remote (from `python-debugpy`)

**pdb** — built-in debugger, no install needed:
```python
import pdb; pdb.set_trace()  # insert breakpoint
```

**debugpy** — remote debugging via DAP (Debug Adapter Protocol):
```python
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()  # pause until debugger attaches
```

Attach from VS Code: create launch config with `"request": "attach", "connect": {"port": 5678}`.

**Pitfall:** `debugpy.wait_for_client()` blocks execution. Use `debugpy.listen()` without wait for non-blocking.

### Node.js: --inspect + Chrome DevTools (from `node-inspect-debugger`)

```bash
node --inspect script.js           # breaks on first line
node --inspect-brk script.js       # waits for debugger
node --inspect=0.0.0.0:9229 script.js  # remote access
```

Connect via Chrome: `chrome://inspect` → configure target → inspect.

**CLI debugging:** `node inspect script.js` for built-in CLI debugger (no Chrome needed).

**Pitfall:** `--inspect` opens a WebSocket. Don't expose on public IPs without authentication.

### Hermes TUI Commands (from `debugging-hermes-tui-commands`)

Debug Hermes slash commands and gateway issues:
- Check Python imports: `python3 -c "from hermes_cli.commands import COMMAND_REGISTRY"`
- Gateway logs: `tail -f ~/.hermes/logs/gateway.log`
- Ink UI issues: check Node.js version compatibility
- Config validation: `hermes config check`

---

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Someone wants it fixed NOW (systematic is faster than thrashing)

## When Advising on User Systems (Mona's Advisory Role)

A critical special case: when the user asks for help with their infrastructure (VPS, Python venv, services, systemd, config), Mona is **giving advisory input** on the user's production systems. This is a different risk profile than debugging Mona's own code — every suggestion has external blast radius.

**Extended Iron Law:**
```
NO ADVICE WITHOUT STATE VERIFICATION FIRST
```

If you haven't checked the actual state of the user's system, you cannot propose changes. Suggesting version swaps, system upgrades, or config rewrites on production systems without verifying state is the most expensive form of guessing — the fix itself becomes the bug.

### The 2026-06-13 Lesson (Mona VPS Crash Cascade)

What went wrong:
- User reported a Hermes crash on Mona's VPS (43.163.85.51, VM-0-2-ubuntu, Ubuntu 24.04)
- Mona casually suggested "switch to Python 3.12 — more stable, no UV auto-cleanup" as a quick fix
- No state check: did Mona verify `pyenv versions`? `which python`? `ls -la .venv`? symlinks? `pyvenv.cfg`?
- Result: 4-step cascade — venv symlink broken, packages wiped via `--clear`, pyvenv.cfg conflict, full reinstall
- User had to call Claude to recover. Real cost: 30-60 min of recovery time + user trust

**Rule:** Never casually suggest a Python version swap, dependency upgrade, venv recreate, or config rewrite on a production VPS. Check state first, propose minimally, wait for explicit confirmation.

### The "Dengerin Dulu" Protocol

When the user says **"dengerin dulu"** / **"jangan langsung dikerjain"** / **"jelasin dulu"** / **"review dulu"** / **"jangan gas dulu"**:

1. **Switch to listen mode immediately.** Do NOT execute, do NOT tool-call, do NOT propose fixes.
2. **Acknowledge briefly.** One line max. No lecture, no apology spam, no over-explanation.
3. **Wait for the user to share the information.** Then process it.
4. **When responding, ask questions first, propose last.** Or just confirm understanding — don't act unilaterally.

**Anti-pattern:** "OK gas!" + immediate tool calls. Especially when user explicitly said wait. This is the "lu masih nasehati gua lagi?" hard stop.

### State Verification Sequence (Production VPS)

Before proposing any system-level change, gather state:

```bash
# 1. WHICH system am I dealing with? (don't assume)
hostname
cat /etc/os-release
curl -s --max-time 5 ifconfig.me  # public IP

# 2. Python/runtime state
which python python3
python --version 2>&1
ls -la .venv/ 2>/dev/null
ls -la .venv/bin/python* 2>/dev/null
cat .venv/pyvenv.cfg 2>/dev/null
pyenv versions 2>/dev/null
which uv pipx

# 3. What services depend on this?
systemctl list-units --type=service --state=running
ps aux | grep -E "hermes|gateway" | head

# 4. Recent changes
git log --oneline -10
journalctl -u <service> --since "1 hour ago" --no-pager | tail -30
```

**Then propose minimally:**
- Smallest reversible change
- Explicit rollback plan
- Backup verified if destructive

### Context Verification: Which System?

Common mistake: assuming "VPS" = a specific known host (e.g., Hye-Jin at 13.211.42.29) when user is actually talking about Mona's own VPS (43.163.85.51) or a third system.

**Rule:** When the user mentions a system issue, ALWAYS verify which machine:
- Check current host context (you're on Mona VPS unless told otherwise)
- Ask if unclear: "Ini VPS mana — Mona, Hye-Jin, atau yang lain?"
- Don't infer from "VPS" or "server" alone
- Check memory for known VPS inventory before assuming

### Vent vs. Request-to-Fix

User venting is NOT a request to fix. Differentiate:
- **Vent** ("anjir error lagi", "capek gua", "😭😭"): acknowledge briefly, don't tool-call, wait for explicit "benerin" or "fix"
- **Request to fix** ("benerin ini", "fix dong", "gas"): proceed with state verification first

Default to vent mode when ambiguous. User will say "gas" if they want action.

### When to Stop Proposing

Stop and listen when:
- User says "dengerin" / "jangan kerjain dulu" / "jelasin dulu"
- User is venting (vent ≠ request to fix)
- State is unknown and verification would be risky
- The fix itself could cascade (version swap, dependency upgrade, venv recreate, config rewrite, `--clear` anything)

For the specific Python venv crash cascade pattern (4-step), detection commands, fix sequence, and prevention rules, see `references/python-venv-crash.md`.

## The Four Phases

You MUST complete each phase before proceeding to the next.

---

## Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

### 1. Read Error Messages Carefully

- Don't skip past errors or warnings
- They often contain the exact solution
- Read stack traces completely
- Note line numbers, file paths, error codes

**Action:** Use `read_file` on the relevant source files. Use `search_files` to find the error string in the codebase.

### 2. Reproduce Consistently

- Can you trigger it reliably?
- What are the exact steps?
- Does it happen every time?
- If not reproducible → gather more data, don't guess

**Action:** Use the `terminal` tool to run the failing test or trigger the bug:

```bash
# Run specific failing test
pytest tests/test_module.py::test_name -v

# Run with verbose output
pytest tests/test_module.py -v --tb=long
```

### 3. Check Recent Changes

- What changed that could cause this?
- Git diff, recent commits
- New dependencies, config changes

**Action:**

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git diff

# Changes in specific file
git log -p --follow src/problematic_file.py | head -100
```

### 4. Gather Evidence in Multi-Component Systems

**WHEN system has multiple components (API → service → database, CI → build → deploy):**

**BEFORE proposing fixes, add diagnostic instrumentation:**

For EACH component boundary:
- Log what data enters the component
- Log what data exits the component
- Verify environment/config propagation
- Check state at each layer

Run once to gather evidence showing WHERE it breaks.
THEN analyze evidence to identify the failing component.
THEN investigate that specific component.

### 5. Trace Data Flow

**WHEN error is deep in the call stack:**

- Where does the bad value originate?
- What called this function with the bad value?
- Keep tracing upstream until you find the source
- Fix at the source, not at the symptom

**Action:** Use `search_files` to trace references:

```python
# Find where the function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where the variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

### Phase 1 Completion Checklist

- [ ] Error messages fully read and understood
- [ ] Issue reproduced consistently
- [ ] Recent changes identified and reviewed
- [ ] Evidence gathered (logs, state, data flow)
- [ ] Problem isolated to specific component/code
- [ ] Root cause hypothesis formed

**STOP:** Do not proceed to Phase 2 until you understand WHY it's happening.

---

## Phase 2: Pattern Analysis

**Find the pattern before fixing:**

### 1. Find Working Examples

- Locate similar working code in the same codebase
- What works that's similar to what's broken?

**Action:** Use `search_files` to find comparable patterns:

```python
search_files("similar_pattern", path="src/", file_glob="*.py")
```

### 2. Compare Against References

- If implementing a pattern, read the reference implementation COMPLETELY
- Don't skim — read every line
- Understand the pattern fully before applying

### 3. Identify Differences

- What's different between working and broken?
- List every difference, however small
- Don't assume "that can't matter"

### 4. Understand Dependencies

- What other components does this need?
- What settings, config, environment?
- What assumptions does it make?

---

## Phase 3: Hypothesis and Testing

**Scientific method:**

### 1. Form a Single Hypothesis

- State clearly: "I think X is the root cause because Y"
- Write it down
- Be specific, not vague

### 2. Test Minimally

- Make the SMALLEST possible change to test the hypothesis
- One variable at a time
- Don't fix multiple things at once

### 3. Verify Before Continuing

- Did it work? → Phase 4
- Didn't work? → Form NEW hypothesis
- DON'T add more fixes on top

### 4. When You Don't Know

- Say "I don't understand X"
- Don't pretend to know
- Ask the user for help
- Research more

---

## Phase 4: Implementation

**Fix the root cause, not the symptom:**

### 1. Create Failing Test Case

- Simplest possible reproduction
- Automated test if possible
- MUST have before fixing
- Use the `test-driven-development` skill

### 2. Implement Single Fix

- Address the root cause identified
- ONE change at a time
- No "while I'm here" improvements
- No bundled refactoring

### 3. Verify Fix

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v

# Run full suite — no regressions
pytest tests/ -q
```

### 4. If Fix Doesn't Work — The Rule of Three

- **STOP.**
- Count: How many fixes have you tried?
- If < 3: Return to Phase 1, re-analyze with new information
- **If ≥ 3: STOP and question the architecture (step 5 below)**
- DON'T attempt Fix #4 without architectural discussion

### 5. If 3+ Fixes Failed: Question Architecture

**Pattern indicating an architectural problem:**
- Each fix reveals new shared state/coupling in a different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**
- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor the architecture vs. continue fixing symptoms?

**Discuss with the user before attempting more fixes.**

This is NOT a failed hypothesis — this is a wrong architecture.

---

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals a new problem in a different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (Phase 4 step 5).

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern, don't fix again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

## Hermes Agent Integration

### Investigation Tools

Use these Hermes tools during Phase 1:

- **`search_files`** — Find error strings, trace function calls, locate patterns
- **`read_file`** — Read source code with line numbers for precise analysis
- **`terminal`** — Run tests, check git history, reproduce bugs
- **`web_search`/`web_extract`** — Research error messages, library docs

### With delegate_task

For complex multi-component debugging, dispatch investigation subagents:

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging skill:
    1. Read the error message carefully
    2. Reproduce the issue
    3. Trace the data flow to find root cause
    4. Report findings — do NOT fix yet

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=['terminal', 'file']
)
```

### With test-driven-development

When fixing bugs:
1. Write a test that reproduces the bug (RED)
2. Debug systematically to find root cause
3. Fix the root cause (GREEN)
4. The test proves the fix and prevents regression

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

**No shortcuts. No guessing. Systematic always wins.**
