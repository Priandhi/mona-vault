---
type: receipt
date: 2026-06-17
tags:
  - receipt
  - iclix
  - streaming
---

# Receipt — Obscura: Ganti Playwright Scraper
**Date:** 2026-06-17
**Task:** Ganti Python Playwright scraper dengan Obscura (Rust headless browser) untuk ICLIX backend

## What Changed
**Before:** scraper.js spawns Python + Playwright + Chromium (~200MB) for EACH embed source
**After:** scraper.js uses hybrid approach:
1. **Obscura CDP (PM2 service)** — lightweight Rust binary, ~10MB RAM, 48MB binary
2. **Playwright fallback** — hanya untuk VidLink (Next.js RSC streaming tidak kompatibel dengan Obscura V8)

## Files Modified
- `/home/ubuntu/iclix/backend/services/scraper.js` — Full rewrite: Obscura CDP (puppeteer-core) + Playwright fallback
- New PM2 process: `obscura-cdp` (id 16) — `obscura serve --port 9222 --stealth`

## Architecture
```
┌─ Request ──→ scraper.js ──→ VidLink? ──yes──→ Playwright (Python)
                               no
                                ↓
                          Obscura CDP (ws://127.0.0.1:9222)
                          ─ puppeteer-core connects here
                          ─ 5 sources in parallel
                          ─ Stealth mode enabled
```

## Results
- ✅ VidLink (Playwright) — STILL WORKS (movies + TV series)
- ✅ Obscura CDP — RUNNING (port 9222, 10MB RAM, instant startup)
- ✅ PM2 startup configured (auto-restart on boot)
- ✅ Frontend loads with no errors
- ✅ Memory savings: Chromium (~200MB) → Obscura (~10MB) = **~190MB saved per request**
- ✅ No Python spawning overhead for non-VidLink sources

## Why VidLink still needs Playwright
VidLink uses Next.js App Router with RSC (React Server Components) streaming. Obscura's V8 watchdog terminates synchronous overruns, preventing full RSC rendering. This is a known limitation of standalone V8 vs Chromium's Blink engine.

## Future Improvements
- If Obscura adds support for Next.js RSC / streaming, we can eliminate Playwright entirely
- Obscura v0.1.8 — masih early, updates mungkin akan fix ini
