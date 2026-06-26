---
type: receipt
date: 2026-06-27
tags:
  - receipt
---

# Task: c0mpute Worker Modal Setup

## Task
Setup c0mpute.ai worker node di Modal GPU (A10G) pakai token `cwt_uRxM9JQ4...`.

## Result
- ✅ Token verified via `npx @c0mpute/worker`
- ✅ Modal app deployed + worker connected ke orchestrator
- ✅ Worker registered: vision, tools, thinking, uncensored — 19.7 tok/s
- ❌ Gak ada jobs → GPU nganggur → waste credit

## Decisions
- Mas decided to **hapus + stop** karena gak ada jobs
- Skill disimpan buat referensi kalo nanti ada jobs beneran
- Base image: `debian_slim` with Node 22 via NodeSource

## Issues
- write_file ngeredact token → harus fix manual pake patch
- Layer pull lama di first run (~400MB debian_slim)
- Modal `run` vs `deploy` punya image beda
- node:22-bookworm-slim gak punya Python → Modal runner gagal

## Next Steps
- None — task closed by Mas