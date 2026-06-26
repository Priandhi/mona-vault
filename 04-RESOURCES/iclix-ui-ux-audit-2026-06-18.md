# ICLIX UI/UX Audit — 2026-06-18

## Status: Audit Complete, Pending Execution
User: "bagus simpen dulu, kita bahas apalagi? jangan kerja dulu nanti sekalian semua aja kalau udah siap semua"

---

## ✅ YANG UDAH BAGUS

### 1. Struktur halaman lengkap (25 pages)
- Film, Serial TV, Drama Asia, Live TV, Anime, Film Indonesia
- VIP, Trending, Genre, Country, Year, Search
- Legal pages (About, Terms, Privacy, FAQ)

### 2. Movie detail page keren
- Poster, rating, tahun, durasi, sutradara
- Cast dengan foto aktor (scrollable)
- Trailer section (4+ trailers, Play No Ads)
- "Film Serupa" (similar films)
- Tombol "Tonton Sekarang" + "Info Lengkap"

### 3. Search berfungsi
- Grid layout, 19 hasil relevan untuk "avengers"
- Rating, tahun, VIP badge di setiap card

### 4. Dark theme + Netflix-like layout
- Hero banner dengan auto-carousel
- Horizontal content carousels
- Red accent (ICLIX brand #e50914)
- Side menu dengan kategori lengkap

### 5. Komponen modular
- VideoPlayer.jsx (auto-failover, 7 sources)
- MovieCard.jsx, MediaCard.jsx
- HeroBanner.jsx, AuthModal.jsx
- VipBadge.jsx, Navbar.jsx, Footer.jsx

---

## ⚠️ YANG PERLU DIPERBAIKI

### 🔴 BUG/CRITICAL (P1)

#### 1. Rating 0.0 di hero banner
- Film baru (Spider-Man: Brand New Day, The Boys) muncul rating `0.0`
- **Fix**: Sembunyikan rating kalau TMDB belum ada rating

#### 2. Content duplikat
- Film yang sama muncul di 3-4 section (VIP, Originals, Trending)
- **Fix**: Deduplicate per section, logic "jangan tampilkan film yang sudah ada di section atas"

#### 3. Placeholder kosong
- Beberapa section ada card kosong/tanpa poster
- **Fix**: Jangan render card kosong, atau fallback poster

### 🟡 DESIGN/UX (P2)

#### 4. Text kecil & kontras kurang
- Rating numbers terlalu kecil
- Tahun di card susah dibaca
- **Fix**: Perbesar font rating, pakai warna kuning/emas untuk angka rating (seperti TMDB stars)

#### 5. Carousel arrows kurang jelas
- Left/right scroll arrows terlalu subtle
- **Fix**: Perbesar, tambah hover effect, atau pakai dot indicators

#### 6. App download "SOON"
- Footer masih tulis "SOON" untuk Google Play & App Store
- **Fix**: Hapus dulu sampai app ready, atau ganti "Coming 2026"

#### 7. Section headers kurang menonjol
- "Pilihan Untukmu", "ICLIX Originals" dll blend dengan background
- **Fix**: Perbesar font, kasih subtle underline/glow

### 🟢 FEATURE BARU (P3)

#### 8. ❌ Personalisasi rekomendasi
- Netflix punya "Because You Watched X"
- ICLIX belum punya watch history → rekomendasi

#### 9. ❌ Continue Watching
- Netflix punya "Continue Watching" row
- ICLIX perlu simpan progress di localStorage/backend

#### 10. ❌ Hover preview
- Netflix: hover card → expand + play trailer clip
- ICLIX: hover → nothing (card statis)

#### 11. ❌ Trailer auto-play di hero
- Netflix: hero banner auto-play trailer muted
- ICLIX: hero = static image

#### 12. ❌ Subtitle indicator
- Gak ada badge "Sub Indo" di card
- User gak tau film mana yang ada subtitle Indonesia

#### 13. ❌ Watchlist button di card
- Ada halaman Watchlist tapi gak ada tombol "Tambah" di card
- User harus buka detail dulu

---

## 📊 PRIORITAS PERBAIKAN

| Prioritas | Item | Effort | Status |
|-----------|------|--------|--------|
| 🔴 P1 | Fix rating 0.0 (sembunyikan kalau kosong) | 5 menit | Pending |
| 🔴 P1 | Content deduplication per section | 30 menit | Pending |
| 🔴 P1 | Remove empty card placeholders | 15 menit | Pending |
| 🟡 P2 | Perbesar rating text + warna kuning | 15 menit | Pending |
| 🟡 P2 | Tambah "Sub Indo" badge di card | 30 menit | Pending |
| 🟡 P2 | Watchlist button di card | 1 jam | Pending |
| 🟡 P2 | "Continue Watching" row | 2 jam | Pending |
| 🟢 P3 | Hover preview (expand card) | 3 jam | Pending |
| 🟢 P3 | Hero trailer auto-play | 2 jam | Pending |
| 🟢 P3 | Personalized rekomendasi | 5 jam | Pending |

---

## 🔍 TECH STACK NOTES

### Frontend Components
- 25 pages in `/home/ubuntu/iclix/frontend/src/pages/`
- 11 components in `/home/ubuntu/iclix/frontend/src/components/`
- TMDB API for metadata (en-US)
- HLS.js for video playback

### Backend Services
- `/home/ubuntu/iclix/backend/`
- PM2 process: `iclix-api`
- Cache: `backend/cache/scraped_streams.json` (6h TTL)
- Server health: `/api/server-health`
- Pre-scrape: `backend/services/pre-scrape.js`

### Video Sources (7 alive)
1. VidLink.pro (primary)
2. Vidsrc.to
3. vsembed.ru (fastest 243ms)
4. Vidsrc.in
5. MultiEmbed.cc
6. Vidsrc.pm
7. Rivestream.live

### NEW: VidSrc Chain Scraper (discovered today)
- vidsrc.to → vsembed.ru → cloudnestra.com → m3u8
- Pure HTTP request, no browser needed
- Saved to: `03-RESEARCH/iclix-video-resolver-research.md`

---

## 📋 NEXT STEPS

1. **Discuss with Mas**: Apa lagi yang perlu dibahas sebelum eksekusi?
2. **Bundle semua perbaikan**: Eksekusi P1+P2+P3 sekaligus
3. **Test end-to-end**: Pastikan video playback, search, detail page semua work
4. **Deploy**: `npm run build` → `pm2 restart iclix-api`

---

## Related Files
- `/home/ubuntu/obsidian-vault/03-RESEARCH/iclix-video-resolver-research.md` — Video resolver research
- `/home/ubuntu/obsidian-vault/02-PROJECTS/iclix.md` — ICLIX project file
- `/home/ubuntu/iclix/frontend/src/components/` — Frontend components
- `/home/ubuntu/iclix/backend/services/` — Backend services
