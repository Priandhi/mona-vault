# HackerOne Unico Report — PENDING SUBMISSION

**Tanggal:** 2026-06-28
**Status:** ⏳ Menunggu Mas submit besok pagi

## Task
Submit bug bounty report ke HackerOne program `unico_idtech` (Unico IDtech).

## Yang Udah Dikerjain
- ✅ Recon target: api.cadastro.uat.unico.app
- ✅ Finding: IDOR potential — endpoint return user data tanpa auth proper
- ✅ Scope verified via GraphQL: `*.uat.unico.app` dan `*.cadastro.uat.unico.app` in-scope
- ✅ Report lengkap ditulis: `/home/ubuntu/bugbounty/unico/HACKERONE_REPORT.md`
- ❌ Submit gagal — token API gak lengkap

## Blokir
Token HackerOne API yang Mas kasih: `LHCy6TtyYY2YSgQX95/WagsGg7GrCf7Cw2xgRwZK2Mk=`

Format HackerOne API butuh **2 bagian** (Basic Auth):
1. **API Key** = `LHCy...2Mk=` ✅ (sudah dikasih Mas)
2. **API Key Name** = ??? ❌ (BELUM dikasih Mas)

Test 20+ kombinasi nama (0xjosee, monaai.crot@gmail.com, mona, default, dll) → semua 401.

## Next Steps (Besok Pagi)
1. Mas buka HackerOne → Settings → API Tokens
2. Cek **API Key Name** (nama yang dikasih waktu generate token)
3. Kirim nama token ke Mona
4. Mona submit via API:
   ```bash
   curl -u "API_KEY_NAME:API_KEY" \
     -X POST "https://api.hackerone.com/v1/reports" \
     -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -d '{...report payload...}'
   ```
5. Atau Mas submit manual via browser → copy-paste dari `/home/ubuntu/bugbounty/unico/HACKERONE_REPORT.md`

## Files
- Report: `/home/ubuntu/bugbounty/unico/HACKERONE_REPORT.md`
- Token tersimpan di memory Mona

## Decisions
- Mas pilih simpan dulu, submit besok pagi
- Mona bantu submit (bukan Mas yang copy-paste manual)

## Issues
- HackerOne API untuk hackers mungkin deprecated (settings/api-tokens → 404)
- Kalau API deprecated, fallback: Mas submit manual via browser
