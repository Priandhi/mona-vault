```
Date     : 2026-06-17
Agent    : HAERI — The Collector
Task     : Pause 2 cronjob airdrop sistem (belum ada airdrop bagus per Hexa)
Airdrop  : N/A (paused)
Action   : Commented out 2 cron entries di crontab sistem:
             - mona_airdrop_scanner.py (tiap 5 jam)
             - mona_airdrop_auto_pipeline.py (tiap 3 jam)
           Backup crontab asli: /tmp/crontab.backup-20260617-160907.txt
           Paused lines ditambahkan di akhir crontab dengan prefix comment
           untuk gampang di-resume (uncomment saja).
Wallet   : N/A
Result   : ✅ 2 cron airdrop paused, no instance masih jalan
Deadline : N/A (pause indefinite, sampai ada airdrop bagus)
Next     : Kalau resume, fix dulu ImportError `now_wib` di mona_airdrop_scanner.py
           sebelum uncomment cron line-nya.
           Rollback cmd: `crontab /tmp/crontab.backup-20260617-160907.txt`
```

**Issues ditemukan:**
- `mona_airdrop_scanner.py` broken: `ImportError: cannot import name 'now_wib' from 'mona_telegram'`
  - Ini salah satu alasan airdrop scanner kosong/gak ada hasil bagus
  - Perlu di-fix sebelum scanner di-resume
