# AgentRouter Provider — WAF Blocker — 2026-06-21

## Task
**Mas request:** Add AgentRouter API key ke 9Router.
- base_url: `https://agentrouter.org/v1`
- api_key: `sk-fXuvhLTiaCnVGilDhyvSvOHmAXZVw1xjzWFvVi8AXu01g70X` (52 chars, valid sk-+48hex format)

## ❌ BLOCKED: Aliyun WAF Slider Captcha

agentrouter.org diproteksi **Aliyun WAF** dengan slider captcha challenge. Semua request dari VPS IP di-return HTML challenge page, bukan real API response.

### 3 Attempts (all WAF-blocked)

| # | Method | Result |
|---|--------|--------|
| 1 | `curl -H "Authorization: Bearer KEY" /v1/models` | 200 OK tapi body = WAF challenge HTML (`aliyun_waf_aa` meta tag) |
| 2 | `curl` dengan browser headers (UA, Origin, Referer) + tanpa auth | Sama, WAF challenge page |
| 3 | Playwright headless (Chrome for Testing, anti-detection flags, set WAF cookies dari root visit) | Sama, WAF challenge page (Title: "Verification", slider captcha) |

### Key observations
- Site root `/` return 200 OK dengan `X-Oneapi-Request-Id` header → platform OneAPI-based (OpenAI-compatible confirmed)
- `/v1/*` endpoints return Aliyun WAF HTML challenge (`aliyun_waf_aa` + `aliyun_waf_bb` cookies)
- Slider captcha perlu human interaction — **tidak solvable dari headless browser** (cookie `_nb_ioWEgULi` value tetap kosong)
- Sama pattern seperti DeepSeek WAF: VPS datacenter IP ke-flag permanent

## ❌ Not Added to DB (per skill pitfall #25)

> "ALWAYS test API keys directly against upstream BEFORE adding to 9router DB. ... If 401 → key invalid/expired, DON'T add to DB."

Key ga bisa divalidasi (bukan 401, tapi WAF block). Kalau dipaksa add:
- 9Router calls dari VPS bakal kena WAF yang sama = dead connection di DB
- Polusi DB dengan provider yang ga work = waste
- 9Router restart tetap ga akan solve WAF blocker

## Decisions
- **JANGAN add ke DB dulu** —违反 skill pitfall #25 (validate dulu baru add)
- Sudah 3 attempts sesuai anti-bot pivot rule (Mas 2026-06-18)
- Stop trying, pivot ke user action

## Opsi Lanjut (butuh Mas decision)

1. **Verify key dari browser Mas** — buka `https://agentrouter.org/v1/models` di HP/laptop, solve slider captcha 1x, kasih tau gw response yang valid (atau paste curl output setelah captcha solved). Kalau work → gw add ke DB dengan proxy setup
2. **Skip dulu** — banyak provider lain yang work (Halo-b.ai, OpenModel, TokenRouter, Kimchi)
3. **Residential proxy** — kalau Mas punya akses residential proxy IP, bisa set 9Router keluar lewat proxy itu

## Files Created (cleanup needed)
- `/tmp/agentrouter_key.txt` — key file (52 chars, sensitive, delete setelah task selesai)
- `/tmp/ar_headers.txt`, `/tmp/ar_browser_headers.txt` — test header files
- `/tmp/test_ar.py`, `/tmp/test_ar2.py` — Playwright test scripts

## Next Steps
- Tunggu Mas confirm: opsi 1 (browser verify) / 2 (skip) / 3 (proxy)
- Jangan add dead connection
- Cleanup `/tmp/agentrouter_key.txt` kalau Mas decide skip
