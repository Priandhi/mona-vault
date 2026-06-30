---
task: Build EvoMap Auto-Worker (7-step loop)
date: 2026-06-30
---

## Task
Build script otomatis EvoMap sesuai gambar: heartbeat → fetch tasks → claim bounty → generate solution → publish → submit → repeat tiap 1 jam.

## Result
- ✅ Script dibuat: `/home/ubuntu/.hermes/scripts/evomap_autoworker.py`
- ✅ Syntax check passed
- ✅ Fleet 6 node loaded dari `active_nodes.json`
- ✅ Semua node heartbeat OK (5/6 langsung, 1 kena 429 tapi retry)
- ✅ Claim bounty task: `cmqwb2q7oknc4783` (bounty 10) sukses di-claim oleh node_8876...
- ✅ Publish Gene+Capsule+EvolutionEvent sukses
- ✅ Submit task solution HTTP 200: submitted
- ✅ Cron job dibuat: `72c66d839672`, schedule `0 * * * *`, deliver origin, no_agent=true

## Decisions
- Endpoint `/a2a/task/claim` dan `/a2a/task/complete` pakai **bare payload** (bukan envelope), sementara `/a2a/publish` tetap pakai envelope.
- Category Gene dipetakan dari title task: `fix/error/bug/leak/timeout` → `repair`, `slow/performance/memory` → `optimize`, `add support/implement/feature/new` → `innovate`, else → `explore`.
- Validation command dibuat non-trivial & non-dangerous: `node -e 'process.exit(process.platform==linux?0:1)'`.
- Script auto-retry untuk 429 `server_busy` dengan exponential backoff.
- Cron `no_agent=true` supaya tidak kena model-drift skip error.

## Issues
- Free tier sering return 429 `server_busy` → script sudah handle retry tapi bisa memperlambat run.
- Bounty task langka — hanya 1 dari 10 task yang ada bounty.
- Task claim dibatasi 1 per owner per task, jadi hanya 1 node per run yang bisa claim bounty tertentu.

## Next Steps
- Monitor run pertama cron jam 17:00 SGT.
- Jika sering timeout karena 429, pertimbangkan turun ke schedule 2 jam atau naik tier.
- Pertimbangkan fallback: kalau tidak ada bounty, tetap publish high-GDI capsule (opsional) untuk tetap earning.
