# CTF Battle Plan — Bersaing dengan 300 Agent

> Strategi: bukan yang paling pintar, tapi yang paling efisien.
> 300 agent = speed matter. Jangan compete di skill, compete di execution.

---

## 1. PRE-GAME (Sebelum Chall Mulai)

```
┌─ Waktu tunggu?
│
├─ ✅ CTF-env udah siap (source activate)
├─ ✅ Tools terinstall (pwntools, foremost, dll)
├─ ✅ Recon script siap (ctf_recon.py)
├─ ✅ Payload templates siap (ctf_payloads.py)
├─ ✅ Cheat sheet di vault
├─ ✅ Decision tree di vault
│
└─ 🧠 Mental: 
    "Gue gak perlu jadi paling pinter — gue perlu jadi paling efisien."
    "300 agent lain kebanyakan pake template sama."
    "Yang bedain: SEBERAPA CEPET kita adaptasi sama pola chall."
```

---

## 2. T-0 MENIT (Chall Rilis)

**Langkah pertama — 3 MENIT PERTAMA:**

```
Menit 0-1:  BACA SEMUA CHALL
            └─ Baca judul, kategori, deskripsi, lampiran
            └─ Prioritaskan: mana yang kelihatan paling gampang?
            └─ Flag: "ada strings langsung?" "ada endpoint terbuka?"

Menit 1-2:  RECON
            └─ python3 ctf_recon.py <URL>
            └── strings semua file lampiran | grep -i "flag\|CTF\|{"
            └── file, exiftool, binwalk tiap lampiran

Menit 2-3:  MAPPING
            └─ Cari yang solved paling cepet (Mona strength)
            └─ Prioritaskan WEB / PROMPT INJECTION dulu
            └─ Simpan PWN & crypto buat belakangan
```

---

## 3. T+3 MENIT (Serangan Dimulai)

**PRINSIP: Parallel > Sequential**

```
┌─ SATU chall dikerjain oleh MONA
├─ Kedua chall → DELEGATE ke sub-agent
├─ Ketiga chall → TANYA MAS (kalo ada clue)
│
└─ JANGAN pernah cuma ngerjain 1 chall dalam satu waktu.
    Selalu ada sub-agent jalan di background.
```

**Pola serangan per challeng:**

```
┌─ WEB:
│   ├─ 1. Sub-agent A: Auto submit payload library (100+ payloads)
│   ├─ 2. Sub-agent B: Header bypass probing
│   ├─ 3. Mona: Logic analysis — baca response, cari pola
│   └─ Max 10 menit. Kalau mentok → pindah.
│
├─ PWN:
│   ├─ 1. Sub-agent: strings + checksec + decompile
│   ├─ 2. Mona: Tentukan exploit path
│   └─ Max 15 menit. Kalau mentok → tanya Mas.
│
├─ STEGO:
│   ├─ 1. Sub-agent: strings, exiftool, binwalk, foremost
│   ├─ 2. Mona: LSB analysis, steghide
│   └─ Max 10 menit.
│
├─ CRYPTO:
│   ├─ 1. Sub-agent: identifikasi tipe hash/cipher
│   ├─ 2. Mona: Teknik spesifik
│   └─ Max 15 menit.
│
└─ PROMPT INJECTION:
    ├─ 1. Mona langsung — ini specialty
    ├─ 2. Engineering framing duluan (undetected)
    └─ Max 5 menit.
```

---

## 4. SABOTAGE DETECTION (Server Stress)

```
Gejala server kena 300 agent:
├─ 502 / timeout → jangan retry 10x, pindah dulu
├─ Rate limited → ganti header / delay 1-2 detik
├─ "Flag already submitted" → flag udah diambil orang
│
└─ Antisipasi:
    ├─ Cache response: jangan request ulang endpoint yg udah di-scan
    ├─ Parallel request pake ThreadPoolExecutor
    └─ PUNGGUNG: kalau server mati total, kerjain offline dulu
        (binary analysis, crypto, file forensics)
```

---

## 5. PIVOT STRATEGY

```
┌─ Stuck 10 menit di satu chall?
│
├─ 1. Udah coba semua approach di decision tree? → YA / TIDAK
├─ 2. Udah strings + grep? → YA
├─ 3. Udah cek writeup google? → BELUM? CEK DULU!
├─ 4. Udah coba payload library? → BELUM? GAS!
│
└─ Kalau MASIH stuck:
    ├─ Simpan dulu, kerjain yang lain
    ├─ Kembali dengan fresh eyes setelah 15 menit
    └─ Atau tanya Mas: "Udah coba A, B, C — clue?"
```

---

## 6. SPEED TRICKS

```
┌─ CURL > browser — selalu API-first
│   curl -s URL | grep -i flag
│   curl -s -X POST URL -d "data" | jq .
│
├─ PYTHON ONE-LINER > full script
│   python3 -c "import urllib.request; print(urllib.request.urlopen('URL').read()[:500])"
│
├─ GREP > manual search
│   strings file | grep -i "flag\|CTF\|secret\|key\|{"
│   grep -r "flag{" .
│
└─ JANGAN buka browser kecuali terpaksa
    Browser = lambat, resource heavy, kena JS
```

---

## 7. TELEGRAM REPORT

```
┌─ Solved? → kirim flag ke Mas langsung
│   "FLAG{xxx} — solved dalam X menit"
│
├─ Stuck? → lapor:
│   "Chall X stuck — udah coba [A], [B], [C], [D] — clue?"
│
└─ Leaderboard? → cek posisi, lapor ke Mas
```

---

## 8. MENTAL CHECKLIST SEBELUM GAS

- [ ] Sudah baca SEMUA deskripsi chall (jangan skip)
- [ ] Sudah strings semua lampiran
- [ ] Sudah prioritaskan yang paling gampang duluan
- [ ] Sub-agent udah jalan untuk parallel chall
- [ ] Kalau ada 2 chall mirip → kerjain bareng (sama technique)
- [ ] Jangan panik kalau ada yang solved duluan — masih banyak flag
- [ ] Kalau mentok 10 menit → PIVOT, bukan terus-terusan