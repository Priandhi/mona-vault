# Self-Update & External Codebase Merge

## The One Rule

> User says "perbarui", "update dirimu", "upgrade", or sends zip → **execute immediately with defaults**. Do not ask.

## Execution Default Checklist

When artifact arrives unprompted:

- [ ] **Extract first**: `unzip -l <path>` → see structure
- [ ] **Detect root folder**: usually named after the framework (openclaw, superagent, hermes-agent)
- [ ] **Read current persona files** (SOUL.md, USER.md, IDENTITY.md) — check for user-specific personalization
- [ ] **Apply standard rules** (preserve persona, update skills/scripts/references)
- [ ] **Copy skills/scripts/references** to `~/.hermes/skills/`
- [ ] **Preserve persona** unless user explicitly said "replace all"
- [ ] **Report**: "✅ X skills updated, Y scripts added. New: ..."

## Preservation Heuristics

| File | Rule |
|------|------|
| `SOUL.md` | Read current before applying. If has user name/personalization → preserve. |
| `USER.md` | Preserve if has filled-in user details. |
| `IDENTITY.md` | Preserve if customized. |
| `AGENTS.md` | Usually safe to update — rules, not persona. |
| `memory/*.md` | Always merge append, never replace. |

## External Codebase Merge (non-Hermes bundles)

Key principle: "Jangan ada yang dihapus, ambil yang belum punya" — NEVER remove existing. Only ADD.

1. **Backup** — `cp -r ~/.hermes/scripts ~/.hermes/skills ~/.hermes/config.yaml /backup/`
2. **Extract & analyze** — `unzip -l`, count actual files vs SKILLS.lock manifest
3. **Identify overlaps** — `grep "^class " *.py` for conflicts
4. **Copy tools** — new tools to `~/.hermes/scripts/<prefix>_tools/`
5. **Copy skills** — new skills to `~/.hermes/skills/<framework>/`
6. **Smoke test** — `python3 -c "import tool_name; print('OK')"`
7. **Report** — what was ADDED, not what changed

**PITFALL:** Zip files may contain SKILLS.lock referencing 112 files but only 28 in the actual zip. The lock is the FULL package manifest.

**PITFALL:** Use `sa_` prefix for merged scripts to avoid conflicts with existing `mona_` scripts.

## Git Source Update

When Hermes was installed from git clone:

```bash
cd ~/.hermes/hermes-agent
git stash && git pull origin main
pip install -e .
hermes --version  # verify
hermes gateway restart  # REQUIRED — old gateway runs old code
```

**PITFALL:** Gateway process keeps running old code in memory. MUST restart after update.

## Post-Apply Verification

1. `ls ~/.hermes/skills/hermes/` — verify new skills landed
2. Check new scripts: `ls ~/.hermes/scripts/`
3. Report new capabilities introduced
4. If persona was preserved → note in summary
