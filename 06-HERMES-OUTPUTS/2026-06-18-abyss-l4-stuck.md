---
type: receipt
date: 2026-06-18
tags:
  - receipt
  - ctf
---

# ABYSS CTF — L4 Stuck Report

**Date**: 2026-06-18
**Agent**: MONA (Hermes)
**Task**: Solve ABYSS L4 "The Double Agent" (Web Exploitation)

## Task
Solve L4 of ABYSS CTF (cftarena.duckdns.org). The challenge requires:
- GET /api/agent
- Custom header `X-Agent-ID: ???`
- Custom header `User-Agent: ???`

## Result
**L4 NOT solved.** 700+ header combinations tried. Stuck.

## Decisions
1. Tried SEED + 20+ transformations (md5, sha1, base64, ROT13, etc) — all failed
2. Tried L1/L2/L3 hashes and flags as headers — failed
3. Tried L4 narrative acrostics (TANTL, Tdaosttwktp, etc) — failed
4. Tried pattern variations from "The double agent only speaks..." — failed
5. Tried ECHO (L10) interrogation for L4 password — ECHO gave "NHPP" but invalid
6. Tried path traversal — server blocks with "Nice try." custom error
7. Tried HTTP method probing — different errors for GET/OPTIONS/PUT
8. Tried SQL/NoSQL injection — no effect
9. Tried 365+ agent names from /api/leaderboard — all denied

## Issues
- **L4 server is a black box** that returns same "Access denied. Identity verification failed." for ALL inputs
- **No response length/timing difference** between correct and wrong credentials
- **Path traversal filter is robust** (URL-encoded, double-encoded all blocked)
- **ECHO LLM** at L10 is responsive but doesn't leak L4 password
- **/api/leaderboard** is open and shows 365+ agents, only 1 solved all 10

## Key Findings
- **/api/leaderboard**: Open, no auth, returns full leaderboard data
- **L7, L10, L6 solvable INDEPENDENTLY** of L4 (multiple solvers: solver, kodok, Platypus, Agent)
- **L5, L8, L9 require L4** (no agent solved them without L4)
- **HermesSolver** solved all 10 levels in ~20 minutes (first_finish 1781680247 - started 1781679057)
- **L4 page** has L10 chat box script that sends `level: 10` always
- **L4 server** is Python BaseHTTP/0.6 Python/3.10.12 behind Caddy

## Next Steps
1. Apply Kernel-Exploit-Dojo mindset (saved to vault)
2. Identify L4 PRIMITIVE (what server actually checks) before brute force
3. Try L7, L10, L6 in parallel — they may give clue for L4
4. If still stuck, ask Mas for direct hint
5. Move on to other projects if ABYSS proves too hard

## Status
- L1, L2, L3: ✅ solved
- L4, L5, L6, L7, L8, L9, L10: ❌ unsolved
- Time spent on L4 alone: ~3-4 hours
- Lesson: **Stop brute-forcing, start reconning**
