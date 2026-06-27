# Update Execution Pattern

## The One Rule

> User says "perbarui", "update dirimu", "upgrade", or sends zip → **execute immediately with defaults**. Do not ask.

The session that taught this lesson: 0xjosee sent SUPERAGENT-v4.0.zip and said "perbarui dirumu ke versi lebih baik dan sempurna ini." Mona responded with a long analysis and "Mau preserve atau replace?" — that's the anti-pattern to never repeat.

## Execution Default Checklist

When artifact arrives unprompted:

- [ ] **Extract first**: `unzip -l <path>` → see structure
- [ ] **Detect root folder**: usually named after the framework (openclaw, superagent, hermes-agent)
- [ ] **Read current persona files** (SOUL.md, USER.md, IDENTITY.md) — check for user-specific personalization
- [ ] **Apply standard rules** (see SKILL.md)
- [ ] **Copy skills/scripts/references** to `~/.hermes/skills/`
- [ ] **Preserve persona** unless user explicitly said "replace all"
- [ ] **Report**: "✅ X skills updated, Y scripts added. New: ..."

## Common Artifact Structures

### SUPERAGENT/OpenClaw (openclaw/ root)
```
openclaw/
├── SOUL.md, IDENTITY.md, AGENTS.md, TIME.md, HEARTBEAT.md  (persona + core)
├── skills/m0.md … m17.md, x1.md … x4.md  (skill files)
├── skills/hermes/SKILL.md + references/ + scripts/  (Hermes crypto agent refs)
├── tools/*.py  (Python tools)
├── .env.example, README.md, CHANGELOG.md, INDEX.md, TOOLS.md  (docs)
├── memory/YYYY-MM.md  (memory roll)
└── SKILLS.lock  (integrity manifest — regenerate post-merge)
```

### Hermes Agent source (hermes-agent/ root)
Usually a git clone or source zip — not a skill bundle. Handle differently:
- If it contains `SKILL.md` → treat as skill bundle
- If it's pure source → advise user to use `hermes update` CLI instead

### Flat structure (no root folder)
Single skill or small update. Extract to temp, inspect, then:
- If SKILL.md in root → install as new skill to `~/.hermes/skills/<category>/`
- If just references/scripts → merge into existing skill umbrella

## Preservation Heuristics

| File | Preservation Rule |
|------|------------------|
| `SOUL.md` | Always read current before applying. If contains user name (Mona, SUPERAGENT, etc.) → preserve. Only overwrite if incoming has same persona identity. |
| `USER.md` | Preserve if has filled-in user details. |
| `IDENTITY.md` | Preserve if customized. |
| `AGENTS.md` | Usually safe to update — rules, not persona. |
| `memory/*.md` | Always merge append, never replace. |

## Post-Apply Checklist

After applying an update bundle:

1. `ls ~/.hermes/skills/hermes/` — verify new skills landed
2. If `SKILLS.lock` updated → note it for manifest regeneration
3. Check new scripts: `ls ~/.hermes/skills/hermes/scripts/`
4. Report new capabilities introduced
5. If persona was preserved → note "Persona preserved (Mona 💜)" in summary

## Signs It's a Major Version (v3 → v4 pattern)

- New skill numbers (m14–m17, x4) → skill expansion
- New `tools/` directory → new tooling
- `SKILLS.lock` present → integrity system introduced
- `references/` subdir under skills/hermes → new reference topics
- `governor.md` in references → Spend Governor added
- `.env.example` with 50+ vars → expanded configuration

Major version → assume full capability uplift, report all new features in summary.