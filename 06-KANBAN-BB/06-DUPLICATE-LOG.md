# 06 — DUPLICATE LOG
*Managed by: MONA | Wajib dicek sebelum test apapun*

---

## TUJUAN

Mencegah bot re-test bug yang sudah:
1. Pernah ditemukan tim ini (internal)
2. Terbukti duplikat dengan laporan H1 yang sudah ada

**Kapan cek file ini:**
- MONA: sebelum process entry dari `04-CONFIRMED-FINDINGS.md`
- Semua bot: sebelum claim item dari `02-RECON-QUEUE.md`

Kalau kombinasi [domain + endpoint + bug class] sudah ada di sini = **SKIP**.

---

## FORMAT ENTRY

```markdown
## [LOG-YYYY-MM-DD-NNN] — [Deskripsi Singkat]
- **Reported By Bot:** ZQYA / RIVA / NOVA
- **Check Date:** YYYY-MM-DD
- **Target:** https://domain.com/endpoint?param=
- **Bug Class:** [type]
- **Duplicate Of:**
  - Internal: [FINDING-ID] / [H1 Report #XXXXXXX]
  - Atau: "Similar finding in program history"
- **Reason:** [kenapa ini duplikat — same endpoint, same param, same class]
- **Lesson:** [apa yang bisa dihindari agar tidak re-test hal serupa]
```

---

## DUPLICATE ENTRIES

*(MONA tulis setiap kali temukan duplikat)*

---

## PATTERNS — JANGAN TEST LAGI

Ringkasan pola yang sudah di-test dan duplikat/tidak worth it:

| Domain | Endpoint | Bug Class | Notes | Date |
|---|---|---|---|---|
