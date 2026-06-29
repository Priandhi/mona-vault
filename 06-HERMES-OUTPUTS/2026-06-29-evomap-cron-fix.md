# EvoMap Cron Fix — 2026-06-29

## Task
Fix 3 EvoMap cron jobs yang failed karena model drift safety skip.

## Root Cause
- Job dibuat pas model global = `deepseek-v4-flash` (murah)
- Model global sekarang = `kr/claude-opus-4.8` (Kiro Opus, mahal)
- Job unpinned → Hermes skip LLM call biar gak kebetulan spend mahal
- Error: `Skipped to prevent unintended spend: global inference config drifted`

## Fix Applied
Update 3 job jadi `no_agent=true` (script-only, zero token spend):
- `4785fcdc764a` evomap-publish (every 120m, deliver=origin)
- `26d89431ba42` evomap-heartbeat-all (every 4m, deliver=local)
- `0815d7125755` evomap-publish-highgdi (every 6h, deliver=local)

## Result
- evomap-publish: 6/6 capsules published ✅ (rate-limit, logrotate, mass-assignment, session-mgmt, jwt, retry-backoff)
- evomap-heartbeat-all: 4/4 nodes online ✅
- evomap-publish-highgdi: 12/12 published ✅ (3 topics × 4 nodes: n1_query_fix, memory_leak_fix, sql_injection_fix)
- Zero token spend (no LLM call needed, script output langsung deliver)

## Decisions
- Pilih `no_agent=true` daripada pin model karena script output udah cukup jelas, LLM step cuma "terjemahin" = buang token
- Deliver `origin` untuk evomap-publish tetep dipertahankan biar Mas dapat notifikasi di chat
- Deliver `local` untuk heartbeat + highgdi (silent, gak spam chat)

## Next Steps
- Monitor next run scheduled (evomap-publish 17:36, highgdi 18:00)
- Kalau ada error baru, cek `~/.hermes/cron/output/<job_id>/` untuk detail
