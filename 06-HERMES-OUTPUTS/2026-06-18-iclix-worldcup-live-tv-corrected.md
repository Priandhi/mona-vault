---
type: receipt
date: 2026-06-18
tags:
  - receipt
  - iclix
  - streaming
---

# Receipt: World Cup 2026 Live TV - ICLIX (Corrected)

**Date:** 2026-06-18
**Task:** Cari siaran live Piala Dunia 2026 dari iptv-org/iptv + tambah RTB Brunei ke Live TV di ICLIX web

## Yang Ditest — dari iptv-org

### ✅ VERIFIED WORKING (real video segments)
| Channel | Resolusi | Segmen |
|---------|----------|--------|
| beIN SPORTS XTRA | 1080p ✅ | 3MB/segmen |
| beIN SPORTS XTRA (ES) | 1080p ✅ | bekerja |
| TVRI Nasional | 1080p ✅ | 827KB/segmen |
| TVRI World | 1080p ✅ | bekerja |

### ❌ DEAD/BLOCKED dari iptv-org
| Channel | Alasan |
|---------|--------|
| FIFA+ (all 9 variants) | 404 Wurl / 302 redirect ke Pluto TV (blocked) |
| Fox Sports 1 | Manifest 200, segmen 404/0 bytes |
| Fox Sports 2 | Host not found |
| ESPN Deportes | Timeout |
| Rai Sport HD | Timeout |
| Premier Sports | 403 CloudFront |
| Olympic Channel | 403 Akamai |
| SPOTV / SPOTV2 | Manifest 200, segmen 401 (token needed) |

### ⛔ GEO-BLOCKED dari VPS SG
| Channel | Platform |
|---------|----------|
| RTB Sukmaindera 🇧🇳 | CloudFront 403 (Brunei only?) |
| RTB Aneka 🇧🇳 | CloudFront 403 |

**Catatan:** RTB mungkin WORK untuk Mas di Indonesia — beda geolokasi.

## Yang Ada di LiveTV.jsx (final)

### ⚽ Sports (4 channel)
1. beIN SPORTS XTRA — ✅ confirmed working 1080p
2. beIN SPORTS XTRA (ES) — ✅ confirmed working
3. RTB Sukmaindera 🇧🇳 — 🔴 geo-blocked dari SG, coba dari Indo
4. RTB Aneka 🇧🇳 — 🔴 geo-blocked dari SG, coba dari Indo

### 📺 Nasional (3)
- TVRI Nasional ✅
- TVRI World ✅
- (SCTV, Indosiar via Vidio embed, RCTI/GTV via embed-proxy, ANTV external)

### 🎬 Lainnya (25+ channel)
- Hiburan: Trans7, Trans TV, Garuda TV, MBG TV, dll ✅
- Berita: MetroTV, tvOne, BeritaSatu, BTV ✅
- Lokal: Bandung TV, Banten TV, Padang TV, dll ✅

## File Changed
- `frontend/src/pages/LiveTV.jsx` — Rewritten TV_CHANNELS array
  - REMOVED: 9 dead FIFA+ streams, Fox Sports (segmen kosong), ESPN/Rai/Premier/DAZN/Olympic
  - ADDED: RTB Sukmaindera + RTB Aneka
  - KEPT: beIN XTRA (confirmed working), TVRI, all Indonesian channels
  - Header: "beIN Sports + RTB Brunei (World Cup 2026) + 30+ TV Indonesia & TVRI"

## Deploy
- ✅ Built via Vite
- ✅ PM2 iclix-api restarted (pid 2469815)
- ✅ Tunnel: https://prague-runner-cyber-volumes.trycloudflare.com/

## Next Steps
- Mas coba langsung dari browser:
  - Buka Live TV → ⚽ Sports
  - Coba RTB Sukmaindera & RTB Aneka — mungkin work dari Indo
  - Coba beIN SPORTS XTRA — confirmed working 1080p
- Kalau ada match day, cek apakah beIN/RTB beneran siarin Piala Dunia 2026
