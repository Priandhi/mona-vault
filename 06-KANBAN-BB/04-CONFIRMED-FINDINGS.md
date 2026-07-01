# 04 — CONFIRMED FINDINGS
*Input: ZQYA, RIVA, NOVA | Output: MONA (scoring + submit)*

---

## DEFINITION OF READY

**MONA tidak akan proses entry yang tidak memenuhi semua checklist ini:**

- ✅ Bug Class spesifik (bukan hanya "vulnerability found")
- ✅ Target URL exact (bukan hanya domain)
- ✅ Reproduction steps yang bisa diikuti orang lain tanpa context tambahan
- ✅ PoC konkret (payload / raw request / command output)
- ✅ Evidence (response snippet / screenshot description / tool output)
- ✅ Impact statement yang spesifik dan quantifiable
- ✅ Severity estimate
- ✅ Untuk RIVA: account setup documented + policy compliance note
- ✅ Evidence file path: `/home/ubuntu/shared/bugbounty/evidence/[FINDING-ID]/`
- ✅ H1 Program handle (untuk MONA tahu submit ke program yang mana)

Entry yang tidak lengkap akan dikembalikan dengan flag **[REPRO-INCOMPLETE]** ke bot asal.

---

## FORMAT ENTRY STANDAR

```markdown
## [FINDING-YYYY-MM-DD-NNN] — [Vulnerability Title]
- **Bot:** ZQYA / RIVA / NOVA
- **H1 Program:** [program handle dari 01-TARGETS.md]
- **Tag:** [#tag1] [#tag2]
- **Target:** https://exact-url.domain.com/api/v1/endpoint?param=
- **Bug Class:** SQLi / IDOR / SSRF / S3-public / dll
- **Severity Estimate:** Critical / High / Medium / Low
- **CVSS Estimate:** X.X (vector kalau sudah tau)
- **Account Setup:** (RIVA) User A: xxx / User B: yyy / Policy: MULTI-OK
- **Reproduction:**
  1. [Step pertama — spesifik, pakai URL/value nyata]
  2. [Step berikutnya]
  3. Expected: [apa yang seharusnya terjadi]
  4. Actual: [apa yang benar-benar terjadi]
- **PoC:**
  ```
  [payload / raw HTTP request / command]
  ```
- **Evidence:**
  ```
  [response snippet / tool output / grep result]
  ```
  File: /home/ubuntu/shared/bugbounty/evidence/[FINDING-ID]/
- **Impact:**
  [Konkret — "attacker dapat X dengan cara Y, menghasilkan Z"]
- **MONA Notes:** — (MONA isi saat review)
- **Status:** CONFIRMED
```

---

## PENDING MONA REVIEW

*(Bot tulis entry baru di sini. MONA scan section ini.)*

---

## MONA — PROCESSING

*(MONA pindahkan ke sini saat sedang di-score dan di-review)*

---

## PROCESSED — PINDAH KE 05-SUBMITTED

| Finding ID | Title | Submit Date | H1 Report ID |
|---|---|---|---|
