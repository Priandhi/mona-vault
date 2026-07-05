# Bug Bounty — 3rd Target Selection (Senin 06 Jul 2026)

## 📋 Context
- WOT (Wallet on Telegram): 3 report submitted, awaiting triage (1-7 business days)
- Urban Dictionary: PAUSED, gak bisa submit sampai reopen
- Unico: skipped (APK required)
- 75 enrolled programs di H1 → filter web-only → 16 realistic candidates → top 3 by scope quality

## 🎯 Top 3 Candidates

### 🥇 1. Greenhouse (app.greenhouse.io) — RECOMMENDED
- **Scope**: 14 URL scopes (app/boards/api/onboarding/support subdomains)
- **Liveness**: ✅ all accessible 302 (redirect to sign_in — normal SaaS auth flow)
- **Type**: Enterprise ATS (Applicant Tracking System) SaaS
- **Bug surface**:
  - Account takeover via sign_in flow
  - `api.greenhouse.io` — REST API surface, IDOR/BOLA candidates
  - Job board cross-tenant data leak (boards.greenhouse.io hosts career pages for many companies)
  - `onboarding.greenhouse.io` — employee onboarding flow (authz complexity)
  - `support.greenhouse.io` — support ticketing (potentially Zendesk-backed)
- **Bounty range estimate**: $500-$5k (medium-large)
- **Pros**: Enterprise SaaS = business logic bugs (less saturated than pure web XSS)
- **Cons**: Auth required, gak banyak unauthenticated surface

### 🥈 2. Algolia (www.algolia.com)
- **Scope**: 4 URL scopes (www.algolia.com, dashboard.algolia.com, *.algolia.net, *.algolianet.com)
- **Liveness**: 
  - www.algolia.com: ✅ 200 (295KB, Cloudflare)
  - dashboard.algolia.com: ✅ 301 → sign_in
  - *.algolia.net: ❌ DNS fail
  - *.algolianet.com: ❌ DNS fail
- **Type**: Search-as-a-Service API
- **Bug surface**:
  - dashboard.algolia.com = main target (auth-only, account takeover)
  - API surface (skip — user-controlled indexes internal)
- **Bounty range estimate**: $200-$2k (mature, numerous pro hunters)
- **Pros**: Clear single-target focus, well-disclosed reward tiers
- **Cons**: Mature program, banyak pro hunters, scope kecil

### 🥉 3. Vimeo (*.vimeo.com, *.vhx.tv, *.magisto.com, *.livestream.com)
- **Scope**: 36 URL scopes (multi-domain)
- **Liveness**:
  - www.vimeo.com: ✅ 301 → vimeo.com
  - developer.vimeo.com: ✅ 200 (14KB, Cloudflare)
  - upload.vimeo.com: ❌ DNS fail
  - help.vimeo.com: ✅ 302 → Zendesk
  - www.vhx.tv: ✅ 301 → vimeo.com/ott
- **Type**: Video platform (UGC surface — massive)
- **Bug surface**:
  - Video upload cross-tenant exposure (IDOR on video_id)
  - VHX.tv OTT platform (subscription video, auth/IDOR candidates)
  - Magisto.com (video editing legacy)
  - Livestream.com (acquired by Vimeo)
- **Bounty range estimate**: $500-$10k (large, mature)
- **Pros**: Massive scope, big reward potential
- **Cons**: VERY mature, Vimeo security team sophisticated, banyak top-100 hunters

## 🚀 Recommendation

**Greenhouse** = realistic next target buat squad. Alasan:
1. ✅ Enterprise SaaS = business logic bugs (less competition vs pure XSS/SQLi)
2. ✅ Auth flow sign_in = potential auth bypass / session fixation
3. ✅ API endpoint (api.greenhouse.io) = IDOR/BOLA potential (HR data exposure = high impact)
4. ✅ Cross-tenant job board (boards.greenhouse.io) = tenant isolation testing
5. ✅ 14 scopes cukup luas buat 2-bot squad (LIORA + ZQYA)
6. ⚠️ Auth required — perlu sign-up free account (ATS trial di Greenhouse.io)

## 📅 Next Steps
1. Setup free trial account di Greenhouse (LIORA: signup via email verify flow)
2. Dispatch LIORA Phase 5: deep recon `app.greenhouse.io` + `api.greenhouse.io` (collect endpoints, JS bundles)
3. Dispatch ZQYA: post-recon, target IDOR/BOLA di `api.greenhouse.io/v1/*` endpoints
4. Tunggu hasil + evaluate findings sebelum submit

## 📝 References
- H1 program: https://hackerone.com/greenhouse
- Scope via GraphQL (public, no auth needed)
- Squad SOP V4: bug-bounty-squad skill references/sop-v4.md
