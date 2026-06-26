---
type: receipt
date: 2026-06-15
tags:
  - receipt
---

# 2026-06-15 — Smart Router Setup

## Task
Setup auto-model-switching rules for Mona. User chose "Simple" (rules-based, no external infra).

## Result
**✅ Smart Router skill created and verified**

Skill: `~/.hermes/skills/hermes/mona-smart-router/SKILL.md`

## Routing Rules (verified)
| Task type | Model | Verified |
|---|---|---|
| Casual chat, default | `tokenrouter/MiniMax-M3` | ✅ M3 identity confirmed |
| Deep debugging, audit, planning | `zyloo/claude-opus-4-6` | ✅ Opus 4.6 identity confirmed |
| Bulk, monitoring, scraper | `orcarouter/deepseek/deepseek-v4-flash` | ✅ Reasoning mode, functional |
| Mid-complexity, classification | `orcarouter/anthropic/claude-haiku-4.5` | ✅ Claude Haiku confirmed |

## Decision Flow
```
1. HIGH STAKES → Opus
2. DEEP REASONING → Opus
3. BULK/REPEAT → Deepseek
4. MID COMPLEXITY → Haiku
5. ELSE → MiniMax-M3
```

## Decisions
- **Simple rules over Auto Router** — User concerned about "gak mau ada eror terus". Rules-based = no external infra = no single point of failure.
- **Deepseek quirk** — Spent all 100 tokens on reasoning for "what model are you?" prompt. Need higher max_tokens (200+) for it to give final answer. Documented in skill.
- **M3 wraps in <think> tags** — TokenRouter returns `<think>...</think>` wrapper, need to strip. Documented in skill.

## Issues
None. All 4 models route correctly through 9Router with their respective prefixes.

## Next Steps
1. **Start using it** — At next session, Mona can suggest model switch per task
2. **Customize rules** — User can override anytime ("rule: trading → Opus")
3. **Monitor usage** — Track model usage in 9Router's `usageHistory` table
4. **Test edge cases** — Try ambiguous tasks to see if rule picks right model

## Files
- `~/.hermes/skills/hermes/mona-smart-router/SKILL.md` (new)
