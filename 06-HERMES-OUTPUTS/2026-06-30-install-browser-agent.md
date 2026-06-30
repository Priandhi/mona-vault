---
task: Install browser-agent skill di VPS
date: 2026-06-30
---

## Task
Install skill `browser-agent` (CloakBrowser + extension controller + Playwright agent) ke VPS sesuai TUTORIAL.md.

## Result
- ✅ Skill di-extract ke `~/.hermes/skills/browser-agent/`
- ✅ Venv dibuat: `~/.venvs/browser-agent/`
- ✅ Dependencies terinstall: `cloakbrowser 0.4.5`, `playwright 1.61.0`, `anthropic 0.113.0`
- ✅ CloakBrowser binary pre-downloaded: `~/.cloakbrowser/chromium-146.0.7680.177.5/chrome`
- ✅ Xvfb + fonts sudah terinstall
- ✅ Env variables ditambahkan ke `~/.bashrc`
- ✅ Xvfb starter script: `~/.hermes/scripts/xvfb-start.sh`
- ✅ Skill didaftarkan di `skills.external_dirs` Hermes config
- ✅ `hermes skills list` menunjukkan `browser-agent` enabled
- ✅ Test dasar (headless CloakBrowser ke bot.sannysoft.com) berhasil — title "Antibot"
- ✅ Test extension (MetaMask dari Chrome Web Store) berhasil:
  - MetaMask v13.33.0.0 di-download dan di-cache
  - Extension loaded dan ready
  - Navigasi ke app.uniswap.org berhasil

## Decisions
- Pakai venv terpisah (`~/.venvs/browser-agent`) karena PEP 668 — gak pakai `--break-system-packages`.
- `CLOAKBROWSER_AUTO_UPDATE=false` supaya binary tidak update diam-diam di VPS produksi.
- Profile persisten di `~/.agent/browser-profile` dan cache ekstensi di `~/.agent/ext-cache`.
- Xvfb di-start manual via helper script, display `:99`.
- Daftarkan skill via `external_dirs` di Hermes config biar skill terdeteksi.

## Issues
- `cloaktest` CLI tidak tersedia; diganti dengan `python -m cloakbrowser`.
- `wait_for_extension()` tidak menerima `timeout` argumen — API beda sedikit dari tutorial, sudah disesuaikan.
- Warning CloakBrowser soal Windows fonts muncul tapi tidak fatal; Linux fonts sudah cukup.

## Next Steps
- Untuk pakai skill, aktifkan DISPLAY `:99` dulu (`source ~/.bashrc` atau `bash ~/.hermes/scripts/xvfb-start.sh`).
- Bisa mulai eksperimen dengan `examples/connect_uniswap.py` kalau ada wallet burner.
- Pertimbangkan install Windows fonts jika butuh spoof Windows fingerprint (opsional).
