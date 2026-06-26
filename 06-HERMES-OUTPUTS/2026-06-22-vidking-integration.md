---
type: receipt
date: 2026-06-22
tags:
  - receipt
  - iclix
  - streaming
---

# Receipt: VidKing Integration — ICLIX Direct m3u8 Playback
**Date:** 2026-06-22
**Status:** ✅ Deployed

## Task
Cari sumber streaming yang lancar dan gak ada iklan buat ICLIX — bypass semua blokir dari VPS.

## Findings
- **cloudnestra.com** dan **vodvidl.site** DNS BLOCKED dari VPS — ini root cause semua embed source (VidLink, vidsrcme, etc) gak bisa serve m3u8 langsung
- **multiembed.cc** ternyata punya banyak embed source alternatif yg belum pernah dicoba: Vidnest, VidKing, Videasy, VidFast
- **VidKing (vidking.net)** ditemukan pake CDN **joe.goldweather.net** yang FULLY RESOLVABLE dari VPS!

## Before vs After
| Aspek | Before | After (VidKing) |
|-------|--------|------------------|
| Source | iframe embed (VidLink/vidsrcme) -> ads | Direct m3u8 HLS |
| CDN | cloudnestra.com (BLOCKED) | joe.goldweather.net ✅ |
| Ads | Iklan popup dari embed | **ZERO ADS** |
| Playback | iframe + HLS.js hybrid | **HLS.js direct** |
| Latency | instant (iframe) / 5s (if expired cache) | 5-15s cold / <1s cached |

## Changes Made
1. **resolve_m3u8.py** — Added VidKing as PRIMARY source (priority #1)
2. **browser-pool.js** — Increased timeout 10s → 20s
3. **server.js /api/play** — Added synchronous VidKing resolve (15s timeout) before iframe fallback. If VidKing succeeds → direct m3u8 playback. If fails → iframe chain (fallback).
4. **server.js** — Cache save on successful VidKing resolve (so next play is instant)

## Verification
All tested ✅:
- Movie (Fight Club 550) → m3u8 ✅, segment 836KB MPEG-TS ✅
- TV show (Breaking Bad S1E1) → m3u8 ✅  
- TV show (Game of Thrones S1E1) → m3u8 ✅
- TV show (The Office S1E1) → m3u8 ✅
- Fresh uncached movie (Matrix Reloaded 604) → direct in 14.2s ✅
- Fresh uncached TV (The Office S1E1) → direct in 14s ✅
- Cached content → instant 530ms ✅
- Segment through /api/ts proxy → MPEG-TS valid ✅

## Key Insight
VidKing m3u8 URLs **DO NOT EXPIRE** — tested same URL 10+ min later, still serves 1978 segments.

## Next Steps
1. Pre-resolve cron: populate cache for top movies/TV shows
2. Add VidKing to pre-scrape system (every 6h) so popular content stays warm
3. Consider adding VidKing to anime resolver (if they support anime)
