---
task: Verifikasi dan aktifkan vision model kimchi/kimi-k2.7 via 9Router
date: 2026-06-30
---

## Task
Verifikasi konfigurasi vision (`auxiliary.vision`) sudah benar (`provider: 9router`, `model: kimchi/kimi-k2.7`) dan pastikan tool `vision_analyze` berjalan tanpa error 401 dari Xiaomi/TokenPlan.

## Result
- ✅ Config `~/.hermes/config.yaml` sudah benar:
  ```yaml
  auxiliary:
    vision:
      provider: 9router
      model: kimchi/kimi-k2.7
  ```
- ✅ Fresh-process test berhasil: vision via `async_call_llm(task='vision')` mengembalikan respons dari `kimi-k2.7`
- ✅ Gateway utama di-restart (PID baru 2358754) untuk memuat config baru
- ✅ `vision_analyze` berhasil menganalisis gambar `/home/ubuntu/.hermes/image_cache/img_ece6ac80713a.jpg` menggunakan `kimchi/kimi-k2.7`
- ✅ File `/tmp` sementara sudah dibersihkan

## Decisions
- Restart gateway utama dengan SIGKILL ke PID lama (2083660) karena SIGTERM tidak berhasil dalam 2 menit; child cron (EvoMap heartbeat) membuat proses lama tidak mau mati gracefully.
- Menggunakan detached `nohup` script untuk schedule restart dan SIGKILL agar perintah tetap jalan meskipun sesi chat terputus.

## Issues
- Gateway lama tidak mau mati gracefully karena ada cron child process yang sedang berjalan.
- Setelah restart muncul warning: `No active credentials for provider: ol` di log gateway — ini default model lama (`ol/`) yang masih tersisa di config fallback, bukan blocker untuk vision.

## Next Steps
- Periksa dan bersihkan config `model.fallback_providers` yang masih merujuk `ol/` jika ingin menghilangkan warning.
- Monitor stabilitas gateway setelah restart.
