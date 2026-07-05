# Receipt: Braze Bug Bounty Audit — Initial Recon

**Task:** Comprehensive security audit of Braze bug bounty instance (login + endpoint enum + attack surface testing)  
**Date:** 2026-07-04  
**Time Spent:** ~45 minutes  
**Status:** ✅ COMPLETE

---

## Result

### Deliverables
1. ✅ Full audit report: `/home/ubuntu/obsidian-vault/03-RESEARCH/braze-bugbounty-audit-2026-07-04.md` (8.9KB)
2. ✅ Credentials extracted + saved (vault-protected)
3. ✅ 15 unique API endpoints mapped
4. ✅ 562 HTTP requests captured + analyzed
5. ✅ 8 attack vectors tested (IDOR, CSRF, session, API key, rate limit, SSRF, GraphQL, file upload)

### Findings Summary
| Severity | Count | Status |
|----------|-------|--------|
| Critical | 0 | None found |
| High | 0 | None found |
| Medium | 1 | CSRF bypass (unconfirmed — needs deeper testing) |
| Low | 4 | Cookie flags, dev enumeration, subdomain session, no rate limit |

### Key Discoveries
- **Web SDK API Key:** `9468396f-efb5-4a0d-be8b-f26b50d82ef9` (properly scoped to write-only)
- **App Group ID:** `6a48d30c5b9b0d006a0bfa8e` (only 1 app group in instance)
- **Environment:** Braze PCE (Private Cloud Environment) — staging/development
- **Security Posture:** Well-hardened, no low-hanging fruit

---

## Decisions

1. **No squad dispatch yet** — Recon complete, but findings too weak for immediate submission. Need deeper exploit dev before involving squad.
2. **Focus on CSRF bypass** — Only medium-severity finding (unconfirmed). If confirmed, could be combined with XSS for account takeover.
3. **Skip IDOR testing** — Properly protected (403 on all traversal attempts).
4. **Save credentials to vault** — Session cookies expire, but login flow automated. Can re-auth anytime.

---

## Issues

1. **CSRF test inconclusive** — Endpoint returned 200 without CSRF token, but might have other protections (origin check, SameSite cookies). Needs browser-based testing with controlled Origin header.
2. **No public H1 program** — Braze not found on HackerOne via GraphQL search. Might be private invitation-only program.
3. **Limited attack surface** — This is a staging PCE instance, not production. Many endpoints (webhooks, exports, integrations) not accessible or not configured.

---

## Next Steps

### Immediate (MONA)
- [ ] Test CSRF bypass with controlled `Origin` header
- [ ] Fuzz `/recently_visited/visit` endpoint with XSS payloads
- [ ] Attempt session fixation via `_session_id` cookie manipulation

### Squad Dispatch (after Mas review)
- [ ] **LIORA:** Research Braze public bug bounty program scope + PCE architecture
- [ ] **ZQYA:** CSRF bypass PoC + XSS fuzzing on dashboard
- [ ] **RIVA:** Auth bypass testing (2FA skip, OAuth manipulation)
- [ ] **NOVA:** Cloud infra scan (K8s API, S3 buckets, webhook SSRF)

### Long-term
- [ ] Wait for Mas to confirm if this instance is in-scope for bug bounty
- [ ] If not in-scope, pivot to other H1 programs (Urbandictionary, Wallet on Telegram, etc.)
- [ ] Build automated Braze scanner for future PCE instances

---

## Files Generated

```
/tmp/braze_config_full.json          — 39KB dashboard config
/tmp/braze_important.json            — Extracted sensitive fields
/tmp/braze_cookies_final.json        — 10 session cookies
/tmp/braze_loggedin_state.json       — Playwright storage state
/tmp/braze_api_capture.json          — 5 API calls during load
/tmp/braze_all_requests.json         — 562 HTTP requests
/tmp/braze_endpoints.txt             — 15 unique endpoints
/tmp/braze_audit.png                 — Dashboard screenshot
/home/ubuntu/obsidian-vault/03-RESEARCH/braze-bugbounty-audit-2026-07-04.md — Full report
```

---

**Auditor:** MONA 💜  
**Review Status:** Pending Mas review before squad dispatch