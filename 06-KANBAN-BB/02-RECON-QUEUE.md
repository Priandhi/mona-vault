# 02 — RECON QUEUE
*Input: LIORA, NOVA (cron) | Output: ZQYA, RIVA, NOVA | Manager: all bots*

---

## TAG → BOT ROUTING

| Tag | Bot | Jenis Temuan |
|---|---|---|
| `[#injection]` | **ZQYA** | SQLi, XSS, SSRF, SSTI, XXE, deserialization |
| `[#server-side]` | **ZQYA** | HTTP smuggling, race condition, request pollution |
| `[#cache]` | **ZQYA** | Cache poisoning, cache deception |
| `[#traversal]` | **ZQYA** | Path traversal, LFI |
| `[#auth]` | **RIVA** | Login bypass, password reset, MFA, session |
| `[#authz]` | **RIVA** | Authorization issues, BFLA |
| `[#idor]` | **RIVA** | Object-level authorization, BOLA |
| `[#jwt]` | **RIVA** | JWT misconfig, alg confusion, none attack |
| `[#oauth]` | **RIVA** | OAuth redirect, PKCE, state CSRF |
| `[#cloud]` | **NOVA** | S3/IAM/Azure/GCP misconfiguration |
| `[#mobile]` | **NOVA** | APK static analysis, deeplink, intent |
| `[#takeover]` | **NOVA** | Subdomain takeover candidate |
| `[#automation]` | **NOVA** | Cron pipeline output untuk verify |
| `[#credential]` | **MONA** | Leaked API key, secret — CRITICAL, direct |

Satu temuan bisa punya lebih dari satu tag.

---

## FORMAT ENTRY

```markdown
## [RECON-YYYY-MM-DD-NNN] — [Title Singkat]
- **Discovered:** YYYY-MM-DD HH:MM
- **Source:** subfinder / ct-logs / js-analysis / github-dorking / nuclei / paste-site / manual
- **Target:** https://exact-url.domain.com/path?param=
- **Type:** subdomain / api-endpoint / leaked-secret / exposed-service / mobile-endpoint / s3-bucket
- **Tag:** [#tag1] [#tag2]
- **Priority:** HIGH / MEDIUM / LOW
- **Tech Stack:** (jika diketahui — nginx, express, spring, dll)
- **Notes:** [context penting untuk bot yang handle]
- **Claimed by:** — (bot yang claim isi ini)
- **Status:** QUEUED
```

---

## 🔴 HIGH PRIORITY

*(Entry dengan Priority: HIGH)*

---

## 🟡 MEDIUM PRIORITY

*(Entry dengan Priority: MEDIUM)*

---

## 🟢 LOW PRIORITY

*(Entry dengan Priority: LOW)*

---

## ✅ CLAIMED / DONE

*(Bot yang claim pindah entry ke 03-EXPLOIT-INPROGRESS.md
dan update Claimed by + Status di sini)*
