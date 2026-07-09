# ITLG Recovery (Burned Cycle) Feature — Added

**Date:** 2026-07-06
**Task:** Tambah fitur auto-recovery burned ITLG cycles ke `itlg-claim` bot
**Status:** ✅ DONE — tested, no crash, systemd service active

## Task

Akun dino (loginId 0008811) punya `itlgRecoverable: 978` di field display. Author bot feb-frmn bilang fitur itu "ada tapi belum di-claim". Minta gua cari endpoint recovery yang sebenarnya + patch bot supaya auto-claim.

## Result

### Discovery: OpenAPI Swagger Spec Exposed

`https://prod.interlinklabs.ai/api-docs-json` → 355 endpoint publik (OpenAPI 3.0.0). Recovery tag punya 6 endpoint:

| Method | Path | Function |
|--------|------|----------|
| **POST** | **/api/v1/recovery/claim** | **claim one burn ticket** |
| GET | /api/v1/recovery/my | history (isRecoverable flag) |
| GET | /api/v1/recovery/my-referral | referral recovery |
| GET | /api/v1/recovery/history-recovered | recovered history |
| GET | /api/v1/recovery/total-recoverable | total stats |
| GET | /api/v1/recovery/total-recoverable-next-cycle | **yang dipakai buat claim** — return `claimCycles[]` |

Plus tag BurnTransaction (4 GET history) + MigrateVitlg (vITLG → on-chain migration, butuh role upgrade NO_ROLE).

### Bagaimana Recovery Bekerja (after live test)

1. **Backend Interlink pakai "ticket-based recovery system":**
   - Setiap burn cycle punya pool tiket limited
   - Tiket untuk cycle tertentu hanya bisa di-claim pada "recovery window" yang dijadwalkan (visible di field `nextRecoverCycle`)
   - `claimCycles` = transaksi yang eligible untuk di-claim SEKARANG
   - Kalau `claimCycles: []` = gak ada yang bisa di-claim (waiting next cycle)

2. **POST /recovery/claim schema:**
   - Body WAJIB `{"transactionId": "BURN-{loginId}-{policyVersion}-{cycleNumber}-{YYYYMMDD"}`
   - Swagger spec schema `ClaimRecoverDto` kelihatan kosong (`properties: {}`) tapi backend tetap validasi field name
   - Field name salah (burnTransactionId, txId, id) → "Invalid burn transactionId or not recoverable"
   - Field benar + tiket habis → "No available ticket (unused/failed) for this cycle to claim"
   - Field benar + tiket valid → 200/201 (belum sempat test happy path)

### Akun dino status live:
```
itlgRecoverable: 978  (display-only legacy, virtual total burns)
burnedCycles: 63       (off-chain DB record of past burns)
totalRecovered: 29     (1 ticket cycle 1 already claimed: BURN-0008811-v1-1-20250903)
canRecover: false       (current window tidak punya tiket eligible)
claimCycles: []         (kosong = nothing claimable right now)
```

Burn histories accessible via `GET /burn-histories/my`:
- Cycle 32: BURN-0008811-v1-32-20250912, amount 960 ITLG, totalRecoverable 89
- Cycle 16: BURN-0008811-v1-16-20250910, amount 480 ITLG, totalRecoverable 475
- Cycle 8: BURN-0008811-v1-8-20250908, amount 240 ITLG, totalRecoverable 237

### Patch bot.py (+106 lines)

Lokasi sisipan: antara `claim_airdrop` dan `get_rates`.

Fungsi baru:
- `get_recovery_next_cycle(token, device_id)` — GET /recovery/total-recoverable-next-cycle → claimCycles
- `claim_recovery(token, device_id, transaction_id)` — POST /recovery/claim {transactionId}
- `send_recovery_notif(cfg, recovered, balance_after)` — TG notif ♻️ ke topic 10832
- `check_and_recover(cfg, token)` — entry point: cek tiket, loop claim per tiket, hitung delta balance, kirim notif

Integrasi:
- `run_once()`: panggil `check_and_recover` SEBELUM `attempt_claim`
- `run_loop()`: panggil `check_and_recover` di startup, sebelum tiap `attempt_claim`, DAN setiap 30 menit (tiket bisa open antara window claim 4 jam)

Human-like jitter:
- 30-120s sebelum claim-airdrop (existing)
- 5-15s sebelum tiap recovery claim (baru)

### Test end-to-end:

1. **Syntax check:** `python -c py_compile` → OK
2. **Systemd restart:** `itlg-claim.service` active (running), PID berubah, no error log
3. **`--once` test:** jalan tanpa crash, output "ℹ️ No recovery tickets available right now." + "ℹ️ Next claim in 01h 52m 14s"
4. **Direct function test:**
   - `get_recovery_next_cycle` balikin `[]` (sesuai ekspektasi — current cycle belum ada tiket)
   - `check_and_recover` return `(token, 0)` — token tetap valid, total_recovered 0
   - `send_recovery_notif(cfg, 42, 116)` kirim test notif TG (reply 200 implied — no exception)
5. **Systemd fresh OTP login:** bot detek token backup expired → trigger OTP → 1 menit 37 detik OTP masuk → login ulang → dashboard muncul → recovery check → no tiket → masuk loop normal. **Zero crash.**

## Decisions

1. **Pakai endpoint resmi Interlink API**, bukan RPC blockchain. Cloudflare blok semua IP VPS ke `evm.test-net.interlinklabs.ai` (CF block IP level, bukan anti-bot challenge). Jadi blockchain approach gak feasible dari VPS ini. API prod.interlinklabs.ai accessible.

2. **Hook di `run_once` + `run_loop`**, bukan cron baru. Alasan:
   - `itlg-claim.service` udah jalan 24/7 — tinggal sisipkan
   - Bot author tetap happy (ga ada systemd baru yang penting dijaga)
   - Interval tetap 30 menit di loop (bukan tiap poll 10s — lebih sopan)
   - Claim recovery dijeda tiap attempt pakai jitter 5-15s (human-like)

3. **Tidak hapus logic lama `itlgRecoverable` di dashboard.** Field itu tetap berguna sebagai info display (total burn legacy). Tidak ada di-claim-claim pragmatic fungsinya.

4. **Notif format terpisah dari claim-airdrop**:
   - `✅ ITLG Claim Success` untuk airdrop 4h
   - `♻️ ITLG Recovery Success` untuk recovery burned cycle

## Issues

- **Happy path belum sempat di-test** (claim berhasil dengan tiket valid). Requires waiting cycle window reset (might be days). Bot akan auto-trigger saat tiket muncul.
- **Bot systemd memakai token backup yang expired** karena gua buat test lokal. Bot deteksi → login OTP sendiri → tetap jalan. Sanity check untuk auto-recovery OTP.
- **Field `ClaimRecoverDto` di Swagger spec kosong** (`properties: {}` tapi backend tetap validasi). Bug dokumentasi Interlink, bukan masalah kita. Hard-coded di bot kita.

## Next Steps

- **Observe** bot jalan 24-48 jam. Lihat log + notif TG di topic 10832 saat tiket muncul.
- **Ticket recovery cycle schedule:** belum diketahui pasti. Tampaknya related ke `nextRecoverCycle: 4` di user data — mungkin cycle 4, 8, 12, dst (every 4 cycles?). Akan terdeteksi otomatis saat tiket keluar.
- **Migrate vITLG:** endpoint butuh role upgrade (NO_ROLE error) — forwarding tidak di-implement karena belum eligible. Skip.
- **Backup `bot.py` ke Git** supaya Mas bisa re-deploy kalo VPS rusak.

## Files Modified

- `/home/ubuntu/itlg-claim/bot.py` — +106 lines (706 → 812)
  - 4 functions baru: `get_recovery_next_cycle`, `claim_recovery`, `send_recovery_notif`, `check_and_recover`
  - Hook di `run_once` (line 673) + `run_loop` startup + claim attempt + 30-min interval check

## Verification Checklist

- [x] Syntax OK (py_compile)
- [x] Systemd service active running after patch
- [x] `--once` test: no crash, expected output
- [x] Direct function test: `check_and_recover` returns (token, 0) safely
- [x] TG notif function callable (no exception)
- [x] Token auto-refresh via refresh token (di get_session)
- [x] OTP auto-login path masih kerja
- [ ] Happy path claim (waiting cycle window — observation mode)
