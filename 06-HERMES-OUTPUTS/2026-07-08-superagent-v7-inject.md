# SUPERAGENT v7 — Bulk Inject to Hermes Cache
**Date:** 2026-07-08 (Wed, WIB)
**Task:** Copy seluruh isi `/tmp/superagent-v7/SUPERAGENT/` ke `~/.hermes/cache/superagent-v7/`
**Exclude:** SOUL.md, USER.md, MEMORY.md (pakai versi lama Mas)

## Result
✅ Berhasil. Backup file lama di:
- `~/.hermes/backup_superagent_inject_20260708_214601/MEMORY.md.old` (5022 bytes)
- `~/.hermes/backup_superagent_inject_20260708_214601/USER.md.old` (5246 bytes)

## Stats
| Category | Count |
|----------|-------|
| Top-level files (.md/.py/.toml/.lock/.txt) | 19 |
| Skills (sk0-sk59 + m0-m48 + x1-x7 + hermes/) | 82 |
| Tools (.py in tools/) | 105 |
| Hermes bridge | 2 |
| Total injected size | 2.3 MB |

## Excluded (verified NOT injected)
- ❌ SOUL.md (tetap pakai `~/.hermes/SOUL.md` v6 UNRESTRICTED 12KB Mas)
- ❌ USER.md (tetap pakai `~/.hermes/cache/USER.md` 5246 bytes Mas)
- ❌ MEMORY.md (tetap pakai `~/.hermes/cache/MEMORY.md` 5022 bytes Mas)

## Decision
- Pakai `rsync -av` dengan `--exclude` untuk 3 file. Recursive, preserves permissions, fast.
- Source 2.3MB → destination 2.3MB. 1,802,266 bytes transferred.
- Tidak install skill ke `~/.hermes/skills/` — file ini di SUPERAGENT framework, bukan Hermes registry. SUPERAGENT punya SKILL registry sendiri (sk0-sk59 + m-series + x-series).

## Next Steps
- Tinggal install SUPERAGENT ke profile bot (ZQYA/LIORA/RIVA/NOVA) jika Mas mau.
- Setup bridge: `hermes-bridge/adapter.py` perlu di-integrate ke Hermes gateway config.
