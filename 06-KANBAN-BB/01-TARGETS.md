# 01 — ACTIVE TARGETS
*Managed by: MONA | Recon by: LIORA | Last updated: YYYY-MM-DD*

---

## ⚠️ SCOPE ENFORCEMENT

**SEMUA aktivitas bot HANYA boleh pada target yang terdaftar di file ini.**
Sebelum test, scan, atau recon apapun: verifikasi dulu di sini.

Kalau domain tidak ada di file ini = **OUT OF SCOPE = SKIP**.

---

## TEMPLATE PROGRAM

Copy, isi, lalu tambahkan ke section ACTIVE PROGRAMS:

```markdown
### [PROGRAM-NAME]
- **H1 URL:** https://hackerone.com/[handle]
- **H1 Handle:** [handle] (untuk API calls)
- **Type:** Public / Private / Invite-only
- **Scope In:**
  - `*.domain.com`
  - `api.domain.com`
- **Scope Out:**
  - `blog.domain.com`
  - third-party integrations
- **Asset Types:** Web, API, Mobile (Android/iOS), Cloud
- **Bounty Range:** $XXX – $XXXXX
- **Rate Limit Rule:** [misal: max 10 req/s, no automated scanner]
- **Account Rules:** [izinkan multiple test account? Y/N/UNCLEAR]
- **Special Rules:** [misal: no account creation, no PII exfiltration]
- **Enrolled Date:** YYYY-MM-DD
- **Status:** ACTIVE
- **Notes:** [catatan penting]
```

---

## ACTIVE PROGRAMS

*(Tambahkan program yang sudah enrolled di H1)*

---

## PAUSED / CLOSED

*(Pindahkan program yang tidak aktif ke sini)*

---

## SCOPE CHANGE LOG

| Date | Program | Change | Updated By |
|---|---|---|---|
| YYYY-MM-DD | — | Initial setup | MONA |
