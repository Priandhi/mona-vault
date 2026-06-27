# @zaimiri's "Hermes Agent + Obsidian Vault = AI Brain" — Architecture Reference

Source: https://x.com/zaimiri/status/2062897401724022824
Author: @zaimiri
Date accessed: 2026-06-14
Extraction method: cover image analyzed via vision_analyze (article body requires X login)

## Article Thesis

Stop treating Obsidian as just a "prettier notes app." Use it as the **memory layer for Hermes Agent** — Hermes reads the vault, uses tools, writes back receipts. The vault becomes a co-evolving brain.

## 8 Modules

| # | Module | What it does | Coverage in our setup |
|---|--------|--------------|----------------------|
| 1 | **VAULT** | Plain markdown files (Obsidian format) | ✅ `obsidian-vault/` initialized |
| 2 | **FILESYSTEM + MCP** | Hermes reads/writes vault via filesystem tools | ✅ Built-in to Hermes |
| 3 | **CLAUDE.MD/AGENTS.MD CONTEXT** | Vault protocol injected at session start | ✅ `AGENTS.md` with VAULT MEMORY PROTOCOL |
| 4 | **SKILLS SOPs** | Skills as Standard Operating Procedures | ✅ 80+ skills installed |
| 5 | **CRON JOBS** | Scheduled autonomous tasks | ✅ owntown-watcher, tunnel-url-watcher, etc. |
| 6 | **MORNING BRIEF** | Daily 08:00 cron: read yesterday's receipts → morning summary | ⏳ Planned (see `mona-knowledge-vault` skill) |
| 7 | **INBOX PROCESSOR** | Weekly process `00-INBOX/` → project files | ⏳ Planned |
| 8 | **WEEKLY SYNTHESIS** | Roll up week's receipts → synthesis.md | ⏳ Planned |

**Coverage: 4/8 active, 3/8 partial, 1/8 N/A (built-in to Hermes).**

## 5 Principles

1. **LOCAL FIRST** — no cloud lock-in; vault is plain markdown on VPS
2. **PLAIN TEXT** — markdown, future-proof, greppable, diff-able
3. **EVERY RUN MAKES SYSTEM SMARTER** — receipts accumulate, system learns
4. **RELIABLE LOOP** — PLAN > ACT > CHECK > RECORD (4-phase cycle)
5. **EVERYTHING CONNECTED. NOTHING LOCKED IN.** — links between notes, easy export/migrate

## Why This Pattern Works for Mona

- **Solves context loss** — without vault, every session starts cold. With vault, session start loads relevant context.
- **Solves audit gap** — receipts = proof of what was done, decisions, blockers
- **Solves knowledge decay** — research findings persist in `03-RESEARCH/` forever
- **Solves "what did we do about X"** — git log + receipts = full history
- **Complements (doesn't replace) runtime memory** — vault for detail, memory tool for compressed facts

## Implementation Status (Hye-Jin setup, 2026-06-14)

- ✅ Vault folder structure created
- ✅ Git initialized, `04-WALLET/` git-ignored
- ✅ README.md as vault index
- ✅ AGENTS.md with VAULT MEMORY PROTOCOL
- ✅ First daily note + first receipt written
- ⏳ Per-project files in `02-PROJECTS/` — pending (user to trigger)
- ⏳ GitHub private repo + push — pending (user to provide username)
- ⏳ Obsidian Git plugin setup on mobile — pending
- ⏳ Morning brief cron — pending implementation
- ⏳ Weekly synthesis cron — pending implementation

## What to Replicate from @zaimiri's Stack (TBD)

These are ideas worth trying — not yet implemented:

- **Daily morning brief** — read receipts from 7 days ago, write 1-paragraph morning brief to `01-DAILY/YYYY-MM-DD.md` at 08:00
- **Weekly inbox processing** — Sunday cron: list `00-INBOX/`, ask user which to promote to `02-PROJECTS/`
- **Weekly synthesis** — Sunday 23:00 cron: roll up week's receipts into `01-DAILY/YYYY-W##-synthesis.md`

## Quotes from Cover Image

> "I think Obsidian becomes way more interesting when you stop treating it like a prettier notes app."
> "The vault is where your memory should live."
> "Hermes is the thing that can read that memory, use tools, ..."
> "Loop: PLAN > ACT > CHECK > RECORD"
> "LOCAL VAULT — 100% YOURS"
> "EVERY RUN MAKES YOUR SYSTEM SMARTER"
> "EVERYTHING CONNECTED. NOTHING LOCKED IN."
