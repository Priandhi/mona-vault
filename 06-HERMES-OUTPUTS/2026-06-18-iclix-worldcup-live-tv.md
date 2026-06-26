---
type: receipt
date: 2026-06-18
tags:
  - receipt
  - iclix
  - streaming
---

# Receipt: World Cup 2026 Live TV - ICLIX

**Date:** 2026-06-18
**Task:** Cari siaran live Piala Dunia 2026 dari iptv-org/iptv dan tambah ke Live TV di ICLIX web

## Source
- GitHub repo: `iptv-org/iptv` — koleksi 10k+ IPTV channel publik
- Master playlist: `https://iptv-org.github.io/iptv/index.m3u8`

## Yang Ditambahkan (20+ channel olahraga baru)

### 🏆 FIFA+ Official (Piala Dunia 2026)
Semua channel FIFA+ dari iptv-org — official stream FIFA yang FREE:
| Channel | Stream |
|---------|--------|
| FIFA+ English 🇬🇧 | jmp2.uk/plu... |
| FIFA+ US 🇺🇸 | Samsung headend cloudfront |
| FIFA+ Spanish 🇪🇸 | Wurl manifest |
| FIFA+ Portuguese 🇧🇷 | Wurl manifest |
| FIFA+ French 🇫🇷 | Wurl manifest |
| FIFA+ German 🇩🇪 | Wurl manifest |
| FIFA+ Italian 🇮🇹 | Wurl manifest |
| FIFA+ Hisp. America | Wurl manifest |
| FIFA+ Women | Wurl manifest |

### 📺 Sports Broadcasters
- **Fox Sports 1** 🇺🇸 (HD, via cors-proxy → 190.11.225.124)
- **Fox Sports 2** 🇺🇸 (via aynaott)
- **Fox Sports (ARG)** 🇦🇷 (jmp2.uk)
- **beIN SPORTS XTRA** (Amagi, working ✅)
- **beIN SPORTS XTRA (ES)** (cloudfront)
- **ESPN Deportes** 🇺🇸 (thetvapp.to)
- **Rai Sport HD** 🇮🇹 (adriatelekom)
- **Sport TV1** 🇵🇹 (filegear-sg proxy)
- **Sport TV5** 🇵🇹 (filegear-sg proxy)
- **Premier Sports** (Amagi)
- **DAZN Combat** (Rakuten Amagi)
- **Olympic Channel** (Akamai)

## Technical Changes

### File diubah: `frontend/src/pages/LiveTV.jsx`
- **Sebelum:** TV_CHANNELS pake ID pecahan (0, 0.01, 0.1, 0.15, 0.16 → 29)
- **Sesudah:** ID sequential 100+ → 50+ channel total, kategori rapi
- Semua channel FIFA+ & Fox Sports marked `featured: true`
- Header subtitle update: "🏆 FIFA+ Official (siarkan langsung Piala Dunia 2026)"
- Channel count: 30+ → 50+ channel

### Backend: server.js sudah punya `/api/proxy` endpoint
- Manifest rewriting: semua relatif URL dalam .m3u8 di-rewrite jadi `/api/proxy?url=...`
- Sudah support HLS proxy via Express (tidak perlu tambahan)
- CORS sudah allow semua origin

### Deploy
- Frontend built via Vite (870KB JS, 78KB CSS)
- PM2 process: `iclix-api` (id 22) running on port 3000
- Cloudflared tunnel: `https://prague-runner-cyber-volumes.trycloudflare.com`

### Stream Test Results
| Stream | Status |
|--------|--------|
| FIFA+ English (jmp2.uk) | ✅ 200, HLS manifest |
| Fox Sports 1 (cors-proxy) | ✅ 200, HLS manifest |
| beIN SPORTS XTRA (Amagi) | ✅ 200, HLS manifest |

## Decisions
1. **Pilih pake FIFA+ dari iptv-org** daripada cari stream ilegal — FIFA+ official free stream
2. **Proxy via `/api/proxy`** daripada direct URL — biar bisa rewrite HLS manifest untuk relatif path
3. **PM2** daripada background manual — biar auto-restart kalo crash
4. **ID sequential** daripada ID pecahan — lebih rapi dan gampang maintain

## Issues
- FIFA+ channel ini adalah FAST channel 24/7 (FIFA content), bukan dedicated match stream. Mungkin perlu dicek pas match day apakah beneran siaran langsung.
- Fox Sports 1 pake cors-proxy.cooks.fyi (third party) — mungkin lambat atau mati kapan aja.
- beIN SPORTS XTRA confirmed by Mas sebelumnya TIDAK carry World Cup matches.

## Next Steps
- Test langsung di browser Mas: buka Live TV → pilih FIFA+ → check apakah stream jalan
- Kalau ada match day, verifikasi FIFA+ beneran siarin langsung
- Alternatif: cari langsung World Cup 2026 match streams dari sumber lain pas match day

