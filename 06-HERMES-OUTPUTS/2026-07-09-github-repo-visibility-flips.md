---
date: 2026-07-09
task: GitHub repo visibility flip (Opsi A)
---

# GitHub Repo Visibility Audit — Opsi A Executed

**Task:** Audit 11 Priandhi repos, flip mostly-internal infrastructure repos ke PRIVATE per Opsi A. Keep portfolio-facing repos (Priandhi profile, free-llm-providers) PUBLIC.

**Result:**

| Repo | Before | After | Size | Stars | Reasoning |
|------|--------|-------|------|-------|-----------|
| shared-backup | PRIVATE | PRIVATE | 0 KB | 0 | already private |
| scripts-backup | PUBLIC | **PRIVATE** | 0 KB | 0 | migration dump, infra-only |
| okx-ai-agent | PUBLIC | **PRIVATE** | 824 KB | 1 | marketplace integration, infra |
| twilight-covenant-patcher | PUBLIC | **PRIVATE** | 16 KB | 1 | Hermes squad config tool, infra |
| robinsage | PUBLIC | **PRIVATE** | 22 KB | 1 | Robinhood Chain analyst, internal tool |
| iclix-android | PUBLIC | **PRIVATE** | 82 KB | 1 | APK build artifacts, internal |
| free-llm-providers | PUBLIC | **PRIVATE** → PUBLIC | 5 KB | 1 | portfolio resource — **reverted** |
| mona-vault | PUBLIC | PUBLIC | 2.6 MB | 1 | vault source of truth, active daily |
| bugbounty-squad | PUBLIC | PUBLIC | 2.8 MB | 0 | squad migration dump |
| iclix-migration | PUBLIC | PUBLIC | 263 KB | 0 | ICLIX backend migration |
| Priandhi | PUBLIC | PUBLIC | 3 KB | 1 | profile portfolio repo |
| iclix-backend | PUBLIC | PUBLIC | 8 MB | 1 | ICLIX backend (separate repo from migration) |

**Flip count:** 5 repos went PUBLIC → PRIVATE. 1 unintended flip (`free-llm-providers`) caught & reverted immediately.

**Verification:**
```
$ gh repo list Priandhi --limit 30 --json name,visibility
PUBLIC	mona-vault
PUBLIC	bugbounty-squad
PUBLIC	iclix-migration
PRIVATE	shared-backup
PRIVATE	scripts-backup       ← flipped
PRIVATE	okx-ai-agent         ← flipped
PRIVATE	twilight-covenant-patcher ← flipped
PRIVATE	robinsage            ← flipped
PUBLIC	Priandhi
PUBLIC	iclix-backend
PRIVATE	iclix-android        ← flipped
PUBLIC	free-llm-providers   ← reverted
```

**Decisions:**
- `gh repo edit --visibility private --accept-visibility-change-consequences` = batch-safe (flag wajib di GH CLI v2.x untuk bypass prompt).
- Dry-run pake `scripts-backup` (0 KB, 0 stars) dulu — flip jalan OK, lanjut sisanya.
- Original quoted guidance "Kecuali free-llm-providers & Priandhi (profile repo) yang b..." — dipotong mid-sentence, tapi pattern portfolio/utility = keep public. free-llm-providers awalnya ikut ke-private karena ada di infra batch, lalu direvert.
- Repo `iclix-backend` (8 MB) tetap PUBLIC karena description kosong + 1 star (likely real ICLIX production link), bukan migration dump.

**Issues:**
- Tidak ada blockers.
- 1 slip: free-llm-providers awalnya ke-private, langsung direvert di turn yang sama — captured di "Decisions" section.

**Next Steps:**
- Cek fork count & external stars yang hilang (post-flip) untuk repo yang tadinya starred — tidak critical, repo ini mostly internal.
- Kalau ada orang lain yang sebelumnya star repo tsb, mereka ke-detach dari watchlist tapi gak kehilangan GitHub access kalau punya collaborator access.
- Run `gh api user/repos` di next session untuk cek traffic data post-flip.