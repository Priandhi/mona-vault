---
type: receipt
date: 2026-06-28
task: Profile Reset & Cleanup
status: COMPLETED
---

# Profile Cleanup — 2026-06-28

## Task
Hapus profil kanban + yerin + haeri. Reset soyu + yuna untuk setting ulang dengan profil baru + SOUL.md baru. Backup semua ke GitHub.

## Result

### Phase 1 — Backup ke GitHub
- Repo: `Priandhi/mona-vault` (PRIVATE)
- Path: `backup/profiles-reset-2026-06-28/`
- Size: 21.7 MB
- Commit: `bac6227`
- Contents:
  - 4 profiles (yerin/haeri/soyu/yuna) — essential files only (excluded logs/sessions/cache/state.db)
  - kanban.db (112KB)
  - vault 07-KANBAN/ (6 files)
  - mona-squad workspace (10 files)
  - 6 scripts (mona-autoheal.py, mona-squad-*.py, mona_futures_engine.py, yerin/haeri-report.py)
  - MANIFEST.json
- Bot tokens preserved in .env files (TELEGRAM_BOT_TOKEN for YUNA + SOYU — akan dipakai ulang)

### Phase 2 — Stop Services
- 5 systemd services disabled: hermes-gateway-yerin/haeri/soyu/yuna/mona-bot
- 6 cron entries removed: Squad Orchestrator, Auto-Heal Monitor (x2), yuna-soft-stop, SOYU Sniper Status, Charon SOYU Status Check

### Phase 3 — Wipe from VPS
| Item | Path | Status |
|------|------|--------|
| Profile yerin | `~/.hermes/profiles/yerin/` | DELETED |
| Profile haeri | `~/.hermes/profiles/haeri/` | DELETED |
| Profile soyu | `~/.hermes/profiles/soyu/` | DELETED |
| Profile yuna | `~/.hermes/profiles/yuna/` | DELETED |
| kanban.db | `~/.hermes/kanban.db` | DELETED (auto-recreates 4KB, will clear on gateway restart) |
| Vault 07-KANBAN | `~/obsidian-vault/07-KANBAN/` | DELETED |
| Mona Squad | `~/mona-workspace/mona-squad/` | DELETED |
| Scripts | `~/.hermes/scripts/` | 9 scripts deleted |

### Phase 4 — Pending (next session)
- [ ] Recreate profile yuna dengan SOUL.md baru
- [ ] Recreate profile soyu dengan SOUL.md baru
- [ ] Bot tokens same: @YunaStrategistBot, @SoyuPhantomBot
- [ ] Config: topic 2905 (YUNA), 2906 (SOYU), model via 9Router
- [ ] Install skills minimal

## Decisions
1. **Backup ke GitHub private repo** — Mas directive: "backup semua ke github aja hapus dari vps". Repo private (Priandhi/mona-vault) jadi aman buat bot tokens.
2. **Exclude junk dari backup** — logs/sessions/cache/state.db excluded (regenerable). Keep SOUL.md, config.yaml, .env, memories, skills, scripts, hooks.
3. **Kanban auto-recreates** — kanban.db deleted but main gateway holds reference, re-creates 4KB empty DB. Will fully clear after gateway restart (not done now per safety protocol).
4. **Bot tokens preserved** — YUNA + SOYU .env backed up. Will reuse same bot tokens (@YunaStrategistBot, @SoyuPhantomBot) when recreating profiles.
5. **mona-workspace** kept (has meridian, charon, crypto-ops, etc.) — only mona-squad subdir deleted.

## Issues
- kanban.db auto-recreates (4KB) — harmless, will clear on gateway restart
- 2 cron jobs still reference "SOYU" in name but were already disabled (deliver=local) — removed

## Next Steps
- Diskusi dengan Mas tentang SOUL.md baru untuk YUNA + SOYU (personality, role, tone)
- Setelah SOUL.md ready: `hermes profile create yuna` + `hermes profile create soyu`
- Configure config.yaml (bot token, topic, model)
- Install skills minimal per profile
- Enable systemd services
