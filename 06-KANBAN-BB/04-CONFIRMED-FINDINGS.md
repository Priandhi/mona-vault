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