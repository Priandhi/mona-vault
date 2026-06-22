# Receipt: 2026-06-21 — Squad System Overhaul + YUNA Fix

**Task:** Perbaiki seluruh squad system (cleanup 9Router, fix YUNA config, simplify orchestrator, stop idle gateways)

## Yang Dilakukan

### 1. 9Router Cleanup
- Hapus **Unimodel (GE)** provider dari DB (DEAD — quota exhausted)
- Backup DB tetap aman

### 2. YUNA Profile Fix
- `custom_providers.api_key` diperbaiki dari **YAML array** (3 keys termasuk 2 om- sampah) jadi **single string**
- YUNA profile sekarang pakai 9Router + TokenRouter M3 key yang bener

### 3. Dozero Scanner Fix
- **clear cooldown** — 257 pairs dalam strike-cooldown di-reset
- **signalled.json format** — diperbaiki dari array `[]` jadi object `{"signalled":[]}` 
- **Restart PM2** — sekarang lagi scan fresh (ETHUSDT, BNBUSDT, dll)

### 4. Cross-Agent Orchestrator Simplified (v3)
- **Dari 7 rules → 2 rules** (cuma YUNA↔SOYU yang aktif)
- **Timeout guard 25 detik** — auto-kill kalo ngelag
- **Rate limit 60 detik** — gak spam
- **File cache** — baca signals.log/traded.json sekali, bukan 4 kali
- **First-run dedup** — gak spam pas pertama jalan
- CPU spike 98.5% solved ✅

### 5. YERIN + HAERI Gateway Stopped
- Hemat ~60MB RAM
- Tapi profil dan skrip masih ada — gampang start lagi kapan aja

### 6. Cron Jobs Cleanup
- Hapus 4 cron jobs mati: YERIN Mining Status, HAERI Airdrop Status, Mona Airdrop Scanner, Airdrop find

## Hasil

|Area|Before|After|
|---|---|---|
|9Router|Unimodel DEAD di DB ✅|Dihapus bersih|
|YUNA config|custom_providers broken (array) ✅|Single key bener|
|Dozero scanner|Saturated (257 cooldown) ✅|Fresh scan, 0 cooldown|
|Orchestrator|7 rules, 98% CPU ✅|2 rules, timeout 25s, gak bakal ngelag|
|YERIN/HAERI|Gateway nyala (~60MB) ✅|Stopped, profil tetap ada|
|Cron jobs|4 job paused nyampah ✅|Dihapus|
|RAM available|~772 MB ✅|~667 MB (beda tipis karena Dozero lagi scan aktif + session lagi jalan)|

## Decisions

1. **YERIN/HAERI gateway di-stop** — mining & airdrop lagi gak ada yang dikerjain, mending hemat RAM. Kalau nanti ada peluang, tinggal `systemctl --user start hermes-gateway-yerin`
2. **Cross-agent disederhanain** — 5 dari 7 rules refer ke YERIN/HAERI yang lagi nganggur. Mubazir.
3. **9Router Unimodel dihapus** — udah mati dari 2026-06-18, gak bakal balik

## Issues

- Masih **swap 1.4 GB / 3.9 GB** — ada memory pressure. Kalau semua service jalan bareng bisa makin berat.
- **Dozero masih testnet**, WR perlu dimonitor beberapa hari ke depan sebelum consider mainnet.

## Next Steps

1. [ ] SOYU daily PnL report cron — biar Charon results keliatan
2. [ ] YUNA WR tracker setelah 3-7 hari data terkumpul
3. [ ] Kalau Dozero WR stabil >55%, siapin mainnet migration
