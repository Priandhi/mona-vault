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

### [RECON-2026-07-05-NOVA-001] — Urban Dictionary CT log subdomain enumeration (13 NEW hosts)
- **Discovered:** 2026-07-05 03:55 UTC
- **Source:** crt.sh CT log query (`*.urbandictionary.com`, 1706 entries, 32 unique subdomains, of which 13 not previously probed)
- **Type:** subdomain (verification needed for takeover / misconfig potential)
- **Tag:** [#automation] [#takeover]
- **Priority:** MEDIUM-LOW
- **Tech Stack:** Likely mixed: CloudFront CDN, Shopify, GitLab Pages, auth-service front-ends (inferred from DNS probes)
- **Notes:**
  - Discovered during UD-NOVA-V3 recon. Subdomains newly identified (not in initial probe list of 15 hosts):
    - `account.urbandictionary.com`
    - `adops.urbandictionary.com`
    - `ads.urbandictionary.com`
    - `blog.urbandictionary.com`
    - `email.urbandictionary.com`
    - `forms.urbandictionary.com`
    - `go.urbandictionary.com`
    - `mcp.urbandictionary.com`
    - `my.urbandictionary.com`
    - `orders.urbandictionary.com`
    - `secure.urbandictionary.com`
    - `tos.urbandictionary.com`
    - `tun.urbandictionary.com`
    - `www42.urbandictionary.com` and `www93.urbandictionary.com` (likely old front-ends)
  - Higher-value targets: `secure.urbandictionary.com`, `account.urbandictionary.com`, `orders.urbandictionary.com` — authn/authn/e-commerce fronts.
  - `mcp.urbandictionary.com` — unusual host (Model Context Protocol? or internal)
  - LIORA: probe each — HEAD probe, CNAME chain, takeover fingerprint. Pay special attention to attack-surface outliers:
    - `mcp` (uncommon service name)
    - `secure` and `account` (authn/elevated surface)
    - `forms`, `email` (form-handling, possible auth0 or sendgrid integration)
- **Claimed by:** —
- **Status:** QUEUED

### [RECON-2026-07-05-NOVA-002] — Urban Dictionary S3 bucket watch ( WEEKLY-CRON trigger)
- **Discovered:** 2026-07-05 03:55 UTC
- **Source:** manual probe (NOVA)
- **Type:** exposed-service (S3 bucket monitoring)
- **Tag:** [#cloud] [#automation]
- **Priority:** LOW (post-hoc monitoring item)
- **Notes:**
  - Bucket `urbandictionary-assets-staging` (us-east-1) confirmed anon-ListBucket (FINDING-20260705-001). Last upload was 2019-08-12.
  - RECOMMENDED CRON: weekly poll of `?max-keys=1&prefix=assets/` — if `<LastModified>` of latest key changes (new file dropped), alert immediately. New uploads to this bucket mean a developer is using it again and may inadvertently drop secrets.
  - Also watch for HTTP status change 200→403 (bucket got locked down — finding closed).
- **Claimed by:** —
- **Status:** QUEUED (NOVA cron pipeline)

---

## ✅ CLAIMED / DONE

*(Bot yang claim pindah entry ke 03-EXPLOIT-INPROGRESS.md
dan update Claimed by + Status di sini)*
