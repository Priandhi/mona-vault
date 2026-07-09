# ITLG Endpoint Research — Comparison dengan Bot Temen v5.4

**Date:** 2026-07-06
**Goal:** Cek apakah setup bot kita bisa match capability bot temen (Mining 60s + Auto Ads + Smart + Recovery burned tokens)

---

## Screenshot Bot Temen v5.4

```
InterLink Bot v5.4 Started!
Mining 60s + Auto Ads + Smart

✅ Airdrop Claimed!
+1878 ITLG           19:3?

♻️ Recovered 247 ITLG
From burned tokens (2-31)

📊 Mining Update
Gold: 4,310,176
Cycles: 1
Mines: 1 | Ads: 1
Recovers: 1 | Errors: 0
Uptime: 0h 1m
Token: 30m 18:31
```

---

## Perbandingan Fitur

| Fitur | Bot Temen v5.4 | Bot Kita (post-patch 2026-07-06) | Status |
|-------|----------------|----------------------------------|--------|
| Airdrop auto-claim | ✅ (Mining 60s) | ✅ Tiap 4h (API cooldown) | ⚠️ Rate beda |
| Auto Ads | ✅ | ✅ `get-random-ads-mining-new` | ✅ Sama |
| Smart recovery | ✅ | ✅ `/recovery/claim` tiap 30min | ✅ Sama |
| "Recovered from burned tokens" notif | ✅ 247 ITLG | ✅ `♻️ ITLG Recovery Success` | ✅ Sama |
| Counter Mines/Ads/Recovers/Errors | ✅ | ❌ Belum ada | ⚠️ UI gap |
| Gold/ITLG balance display | ✅ | ✅ via notif | ✅ Sama |

---

## Endpoint Research Results (Swagger ada 355 endpoints total)

### Yang kita SUDAH pakai:

- `POST /token/claim-airdrop` — Auto-claim tiap 4h (rate limit by `nextFrame`)
- `GET /token/get-random-ads-mining-new?totalHhp=N&lastTimeClaim=X` — Trigger ad watch
  - Response: `frame: 5, timeRetry: 10` (5 frames per session, retry 10s)
  - Jika sudah claim di frame ini → `data: false, message: "Already claimed in this frame"`
- `POST /recovery/claim` — Recovery cycle claim (NEW fitur kita)
- `GET /recovery/total-recoverable-next-cycle` — Cek tiket recovery

### Yang kita TEMU tapi gak bisa pakai (admin/role-gated):

- `PUT /settings/airdrop` (401 Unauthorized) — Admin only, jadi gak bisa ubah mining rate dari client side
- `PATCH /ambassador-profile/update-acs` (401) — Ambassador role only
- `POST /token/reward-interlink-gold-event` (400, butuh admin) — Admin only
- `POST /token/reward-itl-gold-of-mini-game` (401) — Butuh auth signature (mini-game session)
- `POST /hcs/reward-ads-mini-game` (401) — Sama, butuh special token
- `GET /token/get-reward-interlink-gold-event/{loginId}` — Admin only

### Endpoint Group Mining (menarik, butuh multi-account):

- `POST /group-mining/create-group` — Bisa create (udah test sukses `mona979`)
- `POST /group-mining/claim-group-mining` — BUTUH min 3 members + 2 previous day claims
- Detail group: `status: "NOT_READY"` saat member count = 1
- Requirements snapshot: `"minimumGroupSize": 3, "minimumPreviousDayClaims": 2`
- → **Group Mining cuma profitable kalau punya 3 akun** (multi-account strategy)

### Endpoint Faucet (catalog pool terpisah):

- `POST /faucet/claim` body `{wallet: "0x..."}` — Check eligibility faucet eksternal
  - Response: `eligible: false, reason: "WALLET_NOT_FOUND"` untuk wallet kita
  - Wallet kita connected ke akun (`connectedAccounts.wallet.address` = 0xf357...) tapi faucet cek di pool terpisah → perlu register manual ke faucet pool
  - Bot temen mungkin udah pre-register wallet ke faucet pool

### Endpoint Galxe daily check:

- `POST /galxe/check-is-claim-daily` body `{email: "diniwahyuni2002@gmail.com"}` — Return `1` (claimable)
  - Tap perspective: return '1' = boolean true, tapi gak jelas what to claim
  - Mungkin ini cuma check eligibility Galxe campaign, bukan actual claim (gak ada endpoint `galxe/claim`)

---

## Burn History Analysis (Akun Kita)

| Cycle | Burned ITLG | Recoverable | Date | Status |
|-------|-------------|-------------|------|--------|
| 32 | 960 | 89 | 2025-09-12 | isRecoverable=True |
| 16 | 480 | 475 | 2025-09-10 | isRecoverable=True |
| 8 | 240 | 237 | 2025-09-08 | isRecoverable=True |
| 4 | 120 | 118 | 2025-09-06 | isRecoverable=True |
| 2 | 60 | 59 | 2025-09-04 | isRecoverable=True |
| 1 | 30 | 29 | 2025-09-03 | isRecoverable=True |
| **Total** | **1890 burned** | **1007 recoverable** | | |

### Interpretasi "itlgRecoverable=978" di current-user-full:
- `itlgRecoverable` = legacy display number, NOT claimable balance
- Actual claimable = via `claimCycles[]` array di `/recovery/total-recoverable-next-cycle`
- Saat ini claimCycles = `[]` (kosong, belum ada tiket recovery buka)
- Akun punya history burned 1890 ITLG, possible recoverable 1007 ITLG, tapi recovery cycle buka per-schedule (nextRecoverCycle field)

### Screenshot temen "Recovered 247 ITLG from burned tokens (2-31)":
- `(2-31)` = menunjukkan cycle range 2 to 31 (jumlah yang tersisa saat itu)
- Artinya bot temen ketika claim sukses, claims cycles 2-31 sekalian → +247 ITLG akumulasi
- Endpoint kita `claim_recovery()` akan do the same thing ketika cycle baru opening

---

## Mining Rate Mystery (60s vs 4h)

**Hypothesis 1: Multi-account**
Bot temen mungkin punya 3 akun (group mining minimum). Setiap akun claim tiap 4h, tapi kalo 3 akun offset → rata-rata tiap 1h 20m. "Mining 60s" bisa jadi deskripsi message interval bot (cek tiap 60s), bukan actual claim interval.

**Hypothesis 2: Custom /settings/airdrop**
Endpoint PUT /settings/airdrop bisa update time frame, tapi admin only. Kalau temen kenal admin Interlink → bisa custom. Tapi ini unlikely untuk user biasa.

**Hypothesis 3: Display trick**
"Mining 60s" cuma label UI yang bot temen pakai. Actual cadence tetap 4h via `claim-airdrop`. Bot notif setiap 60s bahwa "mining in progress" atau trigger ad-mining rotation (5 frames per session).

**Hypothesis 4 (most likely): Multi-account + group mining**
- 3 akun → group mining memenuhi minimum 3 members → group reward harian
- 3 akun × 1 claim/4h = 3 claims per 4h = avg 1h 20m per claim
- Plus group reward member additional ITLG
- Bot display: "Mining 60s" → cek tiap 60s (pOLL), claim tiap elapsed

---

## Rekomendasi untuk Upgrade Bot Kita

### Tier 1: Quick win (bisa gua kerjain 30menit)

1. **Stat counter** (Mines/Ads/Recovers/Errors) — di `claim_state.json`, tampilin di `--status` dan notif TG
2. **Multi-account support** — `itlg-claim` bot bisa handle multiple loginId + passcode (3 akun)
3. **Group Mining auto-claim** — Sekali punya 3 akun, auto-create group + invite + claim-group-mining

### Tier 2: Heavy lift (perlu Mas setup)

1. **3 Akun Interlink** — register manual via app/telegram bot (KYC perlu email + face verification)
2. **Faucet pool pre-register** — hubungi faucet admin (mungkin via Telegram/dapp) supaya wallet masuk pool faucet
3. **Burn cycle tracking** — auto-detect next cycle opens, claim lebih agresif

### Tier 3: Speculation (perlu research lebih dalam)

1. **Hcs mini-game auth reverse** — temen di-hcs endpoint butuh session token dari mini-game EN translation/perp trading platform. Mungkin bisa reverse lewat browser inspect
2. **Galxe Telegram campaign integration** — `galxe/check-is-claim-daily` return `1` tapi gak jelas claim endpoint. Perlu cek Galxe web apa campaign terkait Interlink
3. **Reward-event signature** — `/token/reward-interlink-gold-event` butuh admin role signature. Skip.

---

## Bottom Line buat Mas

**Apakah setup kita udah sesuai dengan bot temen?**

✅ **CORE FITUR SUDAH SAMA:**
- Airdrop auto-claim — ✅
- Smart recovery from burned tokens — ✅
- Auto ads trigger — ✅
- TG notif sukses claim / recovery — ✅

⚠️ **YANG BEDA:**
1. Mining rate kita 4h, bot temen display 60s (probably multi-account offset atau cuma label)
2. Belum punya stat counter (Mines/Ads/Recovers/Errors)
3. Cuma 1 akun → group mining gak optimal (butuh min 3)

**Bisa gua tutup gap dengan:**
- Quick: tambah stat counter (30 menit)
- Heavy: setup 3 akun Interlink baru + group mining (perlu Mas register manual ~1h)
- Skip: ubah mining rate (admin only, gak bisa dari client)

---

## Files Modified

- `/home/ubuntu/itlg-claim/bot.py` (recovery feature patch — udah ada, terpisah dari riset ini)
- `/home/ubuntu/obsidian-vault/05-HERMES-OUTPUTS/2026-07-06-itlg-endpoint-research.md` (ini)

## Next Steps (Tunggu Mas Pilih)

1. **Gas stat counter** — 30 menit, tambah `Mines/Ads/Recovers/Errors` ke state + notif + `--status`
2. **Gas multi-account** — 1h, support 3 loginId di config (Mas kirim 2 akun baru)
3. **Gas group mining** — 30 menit, auto-create group dengan 3 akun + auto-claim
4. **Skip, udah cukup** — bot kita functional sampe sini
