---
name: "code-debugging"
description: "Connect debuggers to running code: Python (debugpy/DAP), Node.js (--inspect/CDP), plus the systematic 4-phase debugging methodology that should drive both. Use when pdb/print isn't enough, when debugging async or multi-process code, or when the user wants root cause analysis."
tags:
  - debugging
  - python
  - node
  - pdb
  - debugpy
  - chrome-devtools
  - DAP
---
# Code Debugging Tools

> Connect debuggers to running code: Python via debugpy (DAP), Node.js via --inspect, and the systematic debugging methodology that should drive both.

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "python debugger", "pdb", "breakpoint in python", "debugpy" | `references/python-debugpy/` |
| "node debugger", "chrome devtools for node", "inspect" | `references/node-inspect-debugger/` |
| "debug systematically", "root cause", "hypothesis-driven" | `references/systematic-debugging/` |

## Methodology First

Before reaching for a debugger, apply `systematic-debugging`:
1. Reproduce the bug.
2. Form a hypothesis about the cause.
3. Test the hypothesis with a print/log or a single breakpoint.
4. If wrong, reformulate. If right, fix and verify.

The debugger tools here are for when print/log isn't enough — usually async code, race conditions, or complex object state.

## Topic Pages

- `references/python-debugpy/SKILL.md` — Python: pdb REPL + debugpy remote (DAP)
- `references/node-inspect-debugger/SKILL.md` — Node.js: --inspect + Chrome DevTools Protocol CLI
- `references/systematic-debugging/SKILL.md` — 4-phase root cause debugging: understand bugs before fixing
