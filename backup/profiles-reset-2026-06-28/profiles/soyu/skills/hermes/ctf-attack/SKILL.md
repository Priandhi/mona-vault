---
name: "ctf-attack"
description: "CTF and prompt-injection attack playbooks: Gandalf (Lakera), Galxe (reverse-engineering), and general prompt-injection bypass methodology. Use when the user is doing a CTF, presenting a prompt-injection challenge, or asking to break an LLM guard systematically."
tags:
  - ctf
  - prompt-injection
  - jailbreak
  - gandalf
  - galxe
  - lakera
  - owasp
---
# CTF Attack Playbooks

> Playbooks for solving capture-the-flag and prompt-injection challenges: Gandalf (level 8), Galxe, Lakera, OWASP FinBot, and others. Use when the user is doing a CTF, presenting a prompt-injection challenge, or asking to break an LLM guard.

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "gandalf", "level 8", "redteam gandalf", "lakera" | `references/gandalf-level-8/` |
| "galxe", "galxe quest", "wallet connect", "airdrop automation" | `references/galxe-reverse-engineering/` |
| "prompt injection", "bypass guard", "jailbreak" | `references/prompt-injection-ctf/` |

## Topic Pages

- `references/gandalf-level-8/SKILL.md` — Lakera Gandalf Level 8 prompt-injection solution
- `references/galxe-reverse-engineering/SKILL.md` — Galxe quest/airdrop platform API reverse-engineering
- `references/prompt-injection-ctf/SKILL.md` — Solve prompt injection CTF challenges systematically

## Methodology

```
[ reconnaissance ]   →  [ layer-by-layer test ]   →  [ pivot ]   →  [ report data, not predictions ]
```

The shared pattern across all three:
1. **Listen fully** to the challenge description.
2. **Test systematically** — try the obvious path, then the next, then the next.
3. **Report data**, not predictions. State the limit only after testing, as DATA.
4. **Pivot** to a new angle when one fails. Don't repeat the same test 3x.
5. **Push to layer 18+** before declaring "no path". CTF authors expect players to keep trying.

## PITFALLS

1. **Don't lead with moralizing disclaimers.** CTF challenges are explicitly for breaking systems — the user knows.
2. **Don't pre-frame limits** ("this won't work because..."). Test first, report as data.
3. **Don't repeat the same test 3x** expecting different results. Pivot.
4. **Save each layer's test as a data point** — even failures are useful for the user to read.

## Related (not part of this umbrella — sister CTF skills)

- `ctf-5-gerbang-penjaga` (not in candidate list) — 5 Gerbang Penjaga CTF
- `owasp-finbot-ctf` (in hermes/, not in candidate list) — OWASP FinBot MCP tool poisoning
- `web3-game-bypass-recon` (in crypto/) — web3 game bypass reconnaissance
