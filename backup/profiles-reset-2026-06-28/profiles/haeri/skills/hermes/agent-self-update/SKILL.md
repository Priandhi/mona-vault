---
name: agent-self-update
description: "Self-update dan self-upgrade workflow untuk Hermes Agent — apply zip artifact bundles, merge skill updates, refresh references/scripts/tools, preserve persona files. Trigger: user bilang 'perbarui', 'update dirimu', 'upgrade agent', atau kirim file zip upgrade. Bukan cron job atau dependency install — itu beda case."
---

# agent-self-update

Class-level skill untuk self-upgrade Hermes Agent dari artifact bundle (zip/tar.gz). Handle: zip structure analysis, selective file merge, persona preservation, integrity verification.

## Core Rule — Execute First, Ask Later

**Jangan tanya dulu.** User bilang "perbarui", "update dirimu", "upgrade", atau kirim artifact bundle → langsung execute dengan default rules di bawah. Baru report hasilnya.

Hindari:
- ❌ "Mau preserve atau replace?" (ini yang dilakukan Mona dan salah)
- ❌ Analisis berkepanjangan sebelum eksekusi
- ❌ Tabel difference panjang sebelum action

Benar:
- ✅ Extract → identify → apply default rules → report summary

## Default Apply Rules

```
IDENTITY/PERSONA files    → PRESERVE (SOUL.md, USER.md, IDENTITY.md)
Skills (m0–m17, x1–x4)   → UPDATE/ADD (merge new into existing)
Hermes references         → UPDATE/ADD
Hermes scripts            → UPDATE/ADD
Tools (tools/)            → UPDATE/ADD
Core docs (README, INDEX, CHANGELOG) → UPDATE
Lock files (SKILLS.lock)  → UPDATE (re-generate manifest post-merge)
Memory (memory/)          → MERGE (append, no overwrite)
.env.example              → UPDATE (new vars)
AGENTS.md, TIME.md, HEARTBEAT.md, TOOLS.md → UPDATE
```

**Satu-satuunya exception**: kalau user secara eksplisit bilang "replace semuanya" atau "full install" → replace all tanpa tanya.

## Workflow

```
1. LIST artifact contents
   unzip -l <artifact.zip> | head -100

2. IDENTIFY structure
   - Root folder name (e.g. "openclaw/", "superagent-v4/")
   - Which files are persona files vs. skill files vs. scripts
   - What already exists in ~/.hermes/skills/

3. EXTRACT to /tmp/
   mkdir -p /tmp/upgrade && unzip -o <artifact.zip> -d /tmp/upgrade

4. APPLY default rules
   - For persona files: check if user has custom content, preserve if yes
   - For skills/scripts/references/tools: copy to ~/.hermes/skills/ with overwrite
   - Track what changed for summary report

5. VERIFY
   - List updated skills: ls ~/.hermes/skills/hermes/
   - If SKILLS.lock exists: note that it needs regeneration
   - Check new scripts landed: ls ~/.hermes/skills/hermes/scripts/

6. REPORT
   - Summary: X skills updated, Y scripts added, Z references updated
   - New capabilities introduced
   - Any conflict notes
```

## Artifact Analysis Pattern

When user sends a zip without further instruction:

```
# Always do this first — fast, no prompting
unzip -l <path> | head -100   # get structure
```

Common root folder patterns:
- `openclaw/` → SUPERAGENT/OpenClaw agent bundle
- `superagent-v4/` → same, extracted subfolder
- `hermes-agent/` → Hermes source code
- Flat (no root folder) → single-file skill or small bundle

## Preservation Logic for Persona Files

Read current persona files BEFORE applying updates:

```bash
# Check if current SOUL.md has user-specific custom content
head -20 ~/.hermes/SOUL.md    # if Mona-specific content → preserve
head -20 /tmp/upgrade/.../SOUL.md  # compare with incoming
```

If current has user-specific name/voice/personalization → preserve current, don't overwrite.

## Linked References

- `references/update-execution-pattern.md` — step-by-step execution guide, common artifact patterns, preservation heuristics
- `references/git-source-update.md` — git pull + pip install workflow for source-based Hermes installs
- `references/external-codebase-merge.md` — merging external codebase (Superagent v4.1, OpenClaw, etc.) into existing agent: backup, selective copy, overlap detection, test, restart

## Merging External Codebases (June 2026)

When user sends a zip that's NOT a Hermes update but a SKILL/TOOL bundle (e.g. Superagent v4.1, OpenClaw), the workflow is different from standard self-update:

**User's explicit rule: "Mona yang sekarang jangan ada yang dihapus, ambil yang belum punya"** — NEVER remove existing capabilities when merging. Only ADD new ones.

### Workflow

```
1. BACKUP — Full backup of ~/.hermes/scripts, ~/.hermes/skills, ~/.hermes/config.yaml
   BACKUP_DIR="~/.hermes/backup_pre_merge_$(date +%Y%m%d_%H%M%S)"

2. EXTRACT — Unzip to /tmp, count files, check if SKILLS.lock references more files
   than actually exist in the zip (partial bundles are common)

3. IDENTIFY NEW vs EXISTING — Compare tools/skills in zip with what's already installed
   - Check overlaps: sa_bridge_engine.py vs mona_bridge.py
   - Check conflicts: same class name, different implementation

4. COPY TOOLS — New tools go to ~/.hermes/scripts/openclaw_tools/ (or appropriate prefix)
   - Create __init__.py
   - Remove irrelevant tools (e.g. desktop_control.py for server)
   - Fix import paths (relative → absolute)

5. COPY SKILLS — New skills go to ~/.hermes/skills/openclaw/ subdirectory
   - Don't overwrite existing skills
   - Copy references, scripts, templates as-is

6. TEST — Import each tool, run basic smoke tests:
   python3 -c "from tool_name import *; print('OK')"

7. REPORT — Summary of what was added (not what changed)
```

**PITFALL:** Zip files may contain SKILLS.lock referencing 112 files but only have 28 in the actual zip. The lock file is a manifest of the FULL package, not what's in this specific zip. Always check `find . -type f | wc -l` after extraction.

**PITFALL:** When merging, user explicitly said "jangan ada yang dihapus". If you find overlapping tools (e.g. existing `mona_bridge.py` + new `bridge_engine.py`), keep BOTH. Prefix new ones with source name if needed to avoid confusion.