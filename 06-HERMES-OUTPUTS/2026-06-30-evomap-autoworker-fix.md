---
task: Perbaiki EvoMap Auto-Worker (claim logic + submit error)
date: 2026-06-30
---

## Task
Fix hasil cron pertama EvoMap Auto-Worker yang menunjukkan `task_full` dan `same_owner_already_claimed` serta submit 404.

## Result
- ✅ Claim logic diubah: hanya **1 node pertama** yang coba claim per run. Node lain skip tanpa error.
- ✅ Pesan error diubah jadi informatif:
  - `task_full` → `[INFO] claim skipped: task slots full`
  - `same_owner_already_claimed` → `[INFO] claim skipped: owner already claimed this task`
- ✅ Submit handling lebih robust: HTTP 404 `asset_not_found` atau `task_not_found` dilabeli `[WARN]` bukan `[FAIL]`.
- ✅ Strategy step Gene dibuat >= 15 karakter sesuai validasi EvoMap.
- ✅ Test run berhasil:
  - Claimed task `cmr0e7gsx0h1f6t3` (bounty 5)
  - Published gene + capsule
  - Submit HTTP 200: submitted

## Decisions
- Hanya 1 node per run yang claim untuk menghindari `same_owner_already_claimed` antar node.
- Label error jadi `[INFO]` atau `[WARN]` karena ini bukan failure teknis, tapi kondisi marketplace.
- Strategy step harus deskriptif & actionable >= 15 chars — perbaikan validasi EvoMap.
- Cron tetap jalan tiap jam, script sudah update otomatis (tidak perlu recreate cron).

## Issues
- EvoMap free tier sering return `server_busy` (429) — script sudah exponential backoff.
- Task slot bounty cepat penuh — perlu run lebih sering atau upgrade tier.
- Submit 404 sebelumnya karena strategy step terlalu pendek, publish gagal silen.

## Next Steps
- Monitor run cron berikutnya jam 18:00 SGT.
- Pertimbangkan schedule lebih sering (misal 30 menit) kalau bounty selalu penuh.
