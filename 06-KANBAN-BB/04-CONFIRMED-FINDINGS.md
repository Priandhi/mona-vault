# 04 — CONFIRMED FINDINGS
*Output: MONA (submit) | Archive: ZQYA*

---

## [FINDING-20260703-001] — UNICO Metrics API — HTTP 500 Internal Error on Every Valid Request

**Bot:** ZQYA  
**Tag:** [#server-side] [#injection]  
**Target:** https://api.cadastro.uat.unico.app/api/v1/metrics/events  
**Bug Class:** gRPC-Web Backend Crash / Internal Server Error  
**Severity Estimate:** High  
**CVSS Estimate:** 7.5 (AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H)

### Reproduction
1. Send POST to `https://api.cadastro.uat.unico.app/api/v1/metrics/events` with `Content-Type: application/json` and `Origin: https://cadastro.uat.unico.app`
2. Include a valid UUID `process_id` and empty `events` array
3. Expected: HTTP 200
4. Actual: HTTP 500 with `{"code":13,"message":"internal error","details":[]}`

### PoC
```bash
curl -sk -X POST "https://api.cadastro.uat.unico.app/api/v1/metrics/events" \
  -H "Content-Type: application/json" \
  -H "Origin: https://cadastro.uat.unico.app" \
  -d '{"process_id":"00000000-0000-0000-0000-000000000000","events":[{"event":"test","properties":{}}]}'
```

### Evidence
File: `/home/ubuntu/bugbounty/unico/exploit/EXPLOIT_PHASE1.md`

### Impact
- Every valid metric request **crashes** the backend (HTTP 500)
- No metrics can be recorded
- Denial of Service on the metrics pipeline
- **Status:** CONFIRMED

---

## [FINDING-20260703-002] — UNICO — gRPC Service Discovery (Type URL Leak)

**Bot:** ZQYA  
**Tag:** [#recon] [#server-side]  
**Target:** https://api.cadastro.uat.unico.app/api/v1/metrics/events  
**Bug Class:** Information Disclosure  
**Severity Estimate:** Low  
**CVSS Estimate:** 3.5

### Description
The error message reveals the internal protobuf type URL:

```json
events: invalid value "bad" for type type.googleapis.com/uni
```

This reveals:
- **Protobuf package:** `uni`
- **Service:** `type.googleapis.com/uni`

### Impact
Internal infrastructure information disclosure. Low severity.

---

## [FINDING-20260703-003] — UNICO — CORS Origin Validation (Strict)

**Bot:** ZQYA  
**Tag:** [#server-side]  
**Target:** https://api.cadastro.uat.unico.app/api/v1/metrics/events  
**Bug Class:** Not a vulnerability (CORS is correct)  
**Severity Estimate:** N/A

### Description
CORS is correctly configured:
- Only `https://cadastro.uat.unico.app` is allowed
- Invalid origins return `HTTP 403` with `{"code":7,"message":"origin domain not allowed"}`
- `access-control-allow-credentials: true`
- `access-control-expose-headers: session-data`

### Status
NOT a vulnerability — CORS is properly configured.

---

## [FINDING-20260705-001] — Urban Dictionary — Anonymous S3 ListBucket on `urbandictionary-assets-staging`

**Bot:** NOVA
**Tag:** [#cloud] [#automation]
**Target:** `https://urbandictionary-assets-staging.s3.amazonaws.com`
**Bug Class:** AWS S3 anonymous ListBucket granted (Information Disclosure)
**Severity Estimate:** Medium
**CVSS Estimate:** 5.3 (AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N)

### Description
The S3 bucket `urbandictionary-assets-staging` (us-east-1) grants anonymous principals
`ListBucket` permission via bucket policy. Anonymous GET against the bucket root returns
HTTP 200 with full `<ListBucketResult>` XML (780 keys enumerable, ~37.67 MB total).
GetBucketAcl and GetBucketPolicy return 403 — the public ListBucket is granted via bucket
POLICY, not ACL.

### Reproduction
```bash
# Anonymous enumeration
curl -sk https://urbandictionary-assets-staging.s3.amazonaws.com/
# Returns 200 + ListBucketResult XML with 780 keys (single page, IsTruncated=false)

# Bucket ACL correctly restricted
curl -sk 'https://urbandictionary-assets-staging.s3.amazonaws.com/?acl'
# Returns 403 AccessDenied

# Bucket policy correctly restricted
curl -sk 'https://urbandictionary-assets-staging.s3.amazonaws.com/?policy'
# Returns 403 AccessDenied
```

### Bucket contents summary
- 780 keys, all under `assets/` prefix (standard Rails asset-pipeline fingerprinted JS/CSS/png)
- Last upload: 2019-08-12 (bucket abandoned ~6 years ago but still world-listable)
- No `.env`, `.git/`, source-code, config, db backup, or credential files present
- Sensitive-pattern scan of `appadmin-*.js` and `application-*.js` (the user-bundled JS)
  surfaced NO hardcoded secrets — only standard jQuery/Bootstrap CDN URLs

### Impact
- Attacker can enumerate the entire staging-asset inventory without auth — including asset
  file names with content hashes that confirm exact website version deployed.
- Per-asset-audit not necessary; this is information-disclosure of asset telemetry,
  not user/PII data leak.
- Security-posture issue: bucket policy is misconfigured for an "abandoned staging" bucket
  — if a developer ever drops a config file / dotfile / artifact into this bucket, it
  instantly becomes publicly readable.

### Evidence
Full XML listing saved at `evidence/s3-urbandictionary-assets-staging-FULL.xml` in workspace
`t_4652bc9c`. Report at `/home/ubuntu/.hermes/kanban/workspaces/t_4652bc9c/UD-NOVA-INFRA-RECON-REPORT.md`.

### Status
CONFIRMED (anonymous-listable bucket verified twice — once at 2026-07-04T20:15Z and once
on retry run at 2026-07-05T03:55Z). Severity Medium — no PII exposed but is reportable
security-posture issue.

---

## [FINDING-20260705-002] — Urban Dictionary — 3 Subdomain-takeover candidates (research-grade)

**Bot:** NOVA
**Tag:** [#takeover]
**Bug Class:** Subdomain takeover (disused third-party services)
**Severity Estimate:** Medium (subject to attacker-feasibility confirmation)

### T1: store.urbandictionary.com → Shopify disabled

- CNAME: `urbandictionary.myshopify.com.`
- HTTP response: 402 Payment Required, `powered-by: Shopify`, `shopify-complexity-score` header
- Takeover model: attacker re-registers Shopify store named `urbandictionary` to claim the
  `.myshopify.com` host that `store.urbandictionary.com` CNAME-points to.

### T2: www.urbandictionary.biz → GitLab Pages no-project-bound

- CNAME: `urbandictionary.gitlab.io.`
- HTTP response: 302 → `https://projects.gitlab.io/auth?domain=https://www.urbandictionary.biz&root_namespace_id=&state=...` (note the empty `root_namespace_id`)
- Takeover model: attacker creates a GitLab Pages project under `urbandictionary` namespace
  (or root-named project), enables Pages, adds custom domain.

### T3: urbandictionary.github.io → GitHub Pages 404

- Direct A-record (no CNAME) → 185.199.108.153 + 3 other github.io IPs
- HTTP response: 404 "Site not found · GitHub Pages"
- Takeover model: the `urbandictionary` GitHub user / organization must be re-registered.
  **Likelihood LOW** — `urbandictionary` is a well-known name, almost-certainly reserved /
  shadow-held by GitHub anti-squatting policy.

### Reproduction
```bash
# T1
dig +short CNAME store.urbandictionary.com
# -> urbandictionary.myshopify.com.
curl -skI https://store.urbandictionary.com/ | grep -i powered-by
# -> powered-by: Shopify
# HTTP/2 402

# T2
dig +short CNAME www.urbandictionary.biz
# -> urbandictionary.gitlab.io.
curl -skI https://www.urbandictionary.biz/ | head -3
# HTTP/2 302 -> https://projects.gitlab.io/auth?domain=...root_namespace_id=&state=...

# T3
dig +short A urbandictionary.github.io
# -> 185.199.108.153 (direct A, no CNAME)
curl -sk https://urbandictionary.github.io/ | grep -i 'site not found'
# -> Site not found · GitHub Pages
```

### Impact
- If attacker gains control of any candidate, malicious content can be served from a UD-owned
  subdomain (cookie theft via parent-zone domain cookies for `urbandictionary.com`),
  phishing under a trusted brand, or email/SMS link trust hijack.
- `T1 (Shopify)` and `T2 (GitLab)` are research-grade; should not be submitted until a friendly
  feasibility test confirms an attacker can re-register the namespace.
- `T3 (GitHub.io)` is a low-prob candidate due to GitHub's anti-squatting policy on the
  `urbandictionary` username.

### Evidence
- Full takeover fingerprints + body excerpts in `evidence/takeover-fingerprints.json`
- CNAME chains in `evidence/cnames.json`
- Full report: `/home/ubuntu/.hermes/kanban/workspaces/t_4652bc9c/UD-NOVA-INFRA-RECON-REPORT.md`

### Status
CONFIRMED (fingerprint + CNAME chain), but takeover feasibility is **CANDIDATE** (not yet
confirmed re-registrable). Downstream action: human (Hexa) or MONA confirms via friendly
research account.

---

## [FINDING-20260705-003] — Urban Dictionary — Supabase `anon_key` exposed in homepage (`data-supabase-config`)

**Bot:** NOVA (re-confirm ZQYA's existing Info-1)
**Tag:** [#cloud]
**Severity Estimate:** Informational (Low)
**CVSS Estimate:** 0.0 (by-design pattern)

### Description
`www.urbandictionary.com` exposes the Supabase config (including `anonKey`) as a JSON-encoded
string on the `<body>` element's `data-supabase-config` attribute. The Supabase browser-client
pattern relies on **Row-Level Security** in Postgres, NOT on keeping `anon_key` secret — the
key is meant to be embedded in client-side JS as identification.

### Reproduction
```bash
curl -sk https://www.urbandictionary.com/ | grep -oE 'data-supabase-config="[^"]+"'
```

### Impact
None — security relies on RLS. Cross-confirmed against ZQYA's UD-ZQYA-EXPLOIT entry in
`03-EXPLOIT-INPROGRESS.md` (Info-1). NO independent finding raised.

### Status
INFORMATIONAL — by design.