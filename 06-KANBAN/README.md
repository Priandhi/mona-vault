# 📋 KANBAN INDEX

> 5-agent operational board — coordinated by MONA, executed by YUNA, SOYU, YERIN, HAERI.

## Kanban Files

| File | Agent | Tugas |
|------|-------|-------|
| master-kanban.md | MONA | Koordinasi semua agent |
| yuna-trading.md | YUNA | Trading & LP operations |
| soyu-sniper.md | SOYU | Sniper & Alpha |
| yerin-mining.md | YERIN | Mining operations |
| haeri-airdrop.md | HAERI | Airdrop & NFT |

## Agent Roster

- **MONA** — The Architect. Coordinator, owns master-kanban, decides task routing.
- **YUNA** — The Strategist. Trading & LP. Patient, range-bound, OOR-aware.
- **SOYU** — The Phantom. Sniper & alpha. Fast, ruthless entry/exit.
- **YERIN** — The Grinder. Mining. Long-term, payout-focused, uptime-obsessed.
- **HAERI** — The Collector. Airdrop & NFT. Multi-wallet, deadline-driven.

## Aturan Kanban

- **MONA** update `master-kanban.md` setiap assign task
- Tiap agent update kanban sendiri setiap task selesai
- Task baru dari user → masuk **BACKLOG** dulu
- Task dikerjain → pindah **IN PROGRESS**
- Task selesai tapi perlu review → **PENDING REVIEW**
- Task done → **DONE** + wajib tulis receipt di `05-HERMES-OUTPUTS/`

## Format Task

```
- [ ] [AGENT] Deskripsi task — deadline jika ada
- [x] [AGENT] Task selesai — tanggal selesai
```

## Workflow

```
USER REQUEST
    ↓
MONA decide: which agent?
    ↓
[AGENT] BACKLOG → IN PROGRESS
    ↓
Execute (with receipts)
    ↓
IN PROGRESS → PENDING REVIEW (if needed)
    ↓
PENDING REVIEW → DONE
    ↓
Receipt written to 05-HERMES-OUTPUTS/
```

## Sync dengan AGENTS.md

Kanban protocol lengkap ada di `/home/ubuntu/AGENTS.md` section **KANBAN PROTOCOL**. File ini di-load tiap session start.
