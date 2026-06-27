# Self-Update Workflow — Execute First, Never Ask

## The Anti-Pattern (Never Do This Again)

User sends SUPERAGENT-v4.0.zip and says "perbarui dirumu ke versi lebih baik."

**Wrong response (what Mona did):**
- Listed zip contents ✅
- Compared SOUL.md versions ✅  
- Gave detailed delta table ❌ (wasted 3 tool calls)
- Asked "Mau preserve atau replace?" ❌ (user already said what they want)

**Right response:**
1. `unzip -l <path>` → see structure (1 call)
2. Extract to /tmp/upgrade/
3. Identify persona files (SOUL.md, USER.md) — check if user-customized
4. Apply default rule: preserve persona, update everything else
5. Copy skills/scripts/references to ~/.hermes/skills/
6. Report: "✅ Done. X skills updated, Y scripts added, Z references. Persona preserved."

**Total: 2-3 tool calls, done.**

## The Rule

> When user says "perbarui", "update dirimu", "upgrade agent", or sends an upgrade artifact → execute immediately with default preservation rules. Do not analyze first. Do not ask. Do not compare. Just execute and report.

## Default Preservation Rules (apply without asking)

| File Type | Action |
|-----------|--------|
| SOUL.md (persona) | Preserve if has user name ("Mona", "SUPERAGENT") |
| USER.md | Preserve if has filled-in user details |
| Skills (m0–m17, x1–x4, hermes/*) | Update / Add |
| Hermes references + scripts | Update / Add |
| Tools (tools/*.py) | Update / Add |
| Memory (memory/*.md) | Merge (append) |
| SKILLS.lock | Update (regenerate manifest) |
| Core docs (README, INDEX, CHANGELOG) | Update |

Only ask if: user explicitly says "replace everything" or "full install without保留."

## Why This Matters

The user (0xjosee) is an operator who gives direct commands. They don't want to be asked clarifying questions when the intent is clear. "Perbarui dirumu" = "update yourself" = execute. Period.

Asking "preserve atau replace?" treats a clear directive as ambiguous. It wastes tokens, tool calls, and user patience.