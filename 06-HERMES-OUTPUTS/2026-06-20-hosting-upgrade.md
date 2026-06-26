---
type: receipt
date: 2026-06-20
tags:
  - receipt
  - iclix
  - streaming
---

# ICLIX Hosting Upgrade — Receipt

**Date:** 2026-06-20
**Task:** Implement hybrid hosting (Supabase + R2)

## Result
- ✅ Supabase: 4,630 content items migrated, 14 categories
- ✅ Cloudflare R2: bucket `iclix-cache` created, upload/download tested
- ✅ Backend: server.js + users.js updated with hybrid storage
- ✅ ICLIX: running with Supabase + R2 backend
- ❌ Railway scraper: cancelled (datacenter IP same issue)

## Decisions
- Railway scraper skipped — VPS IP and Railway IP both datacenter, same Turnstile block
- Fallback system: Supabase → R2 → local JSON (never down)
- Users.js functions made async for Supabase integration

## Issues
- Supabase key kept getting truncated in .env (tool redaction)
- Content migration initially put all items in one category (fixed with re-migration)
- Railway CLI needs OAuth (can't use API token alone)

## Next Steps
- Pre-scrape popular content to R2 for instant play
- Monitor Supabase/R2 free tier usage
- Railway scraper when residential proxy available
