---
type: project
status: complete
priority: medium
tags:
  - project
  - iclix
  - hosting
---
# ICLIX Hosting Upgrade Plan
> Created: 2026-06-20
> Status: PLANNING (belum eksekusi)

---

## 1. TUJUAN

Upgrade ICLIX dari single-VPS ke hybrid architecture:
- **VPS** tetap jadi server utama (Express backend)
- **Supabase** ganti database (PostgreSQL vs JSON files)
- **Cloudflare R2** ganti video cache (object storage vs local disk)
- **Railway** tambah scraper service (resolve m3u8 dari IP berbeda)

**Hasil yang diharapkan:**
- Database lebih reliable, bisa query complex
- Video cache lebih cepat (CDN vs local disk)
- Scraper lebih luas (bisa resolve dari IP berbeda)
- VPS lebih enteng (kurang ~2-3GB storage)

---

## 2. ARSITEKTUR

```
User → Cloudflare CDN → VPS (ICLIX server utama)
                              │
                    ┌─────────┼─────────┐
                    ↓         ↓         ↓
              ┌─────────┐ ┌─────┐ ┌─────────┐
              │Supabase │ │ R2  │ │ Railway │
              │Database │ │Cache│ │Scraper  │
              └─────────┘ └─────┘ └─────────┘
```

---

## 3. SUPABASE — DATABASE

### 3.1 Tables

**users**
- id (UUID, primary key)
- username (unique, varchar 50)
- email (unique)
- password_hash
- display_name
- avatar_url
- vip (JSONB: tier, plan, expires)
- auth_provider (local/google/phone)
- created_at, updated_at

**content**
- id (serial, primary key)
- tmdb_id (integer, not null)
- type (varchar 10: movie/tv/anime)
- title (varchar 500)
- overview (text)
- poster_path, backdrop_path
- vote_average (decimal)
- genre_ids (integer array)
- category (varchar 50)
- release_date
- UNIQUE(tmdb_id, type)

**stream_cache**
- id (serial, primary key)
- tmdb_id (integer)
- type (varchar 10)
- season (integer, nullable)
- episode (integer, nullable)
- m3u8_url (text)
- source (varchar 50: vidlink/vidsrc/animasu)
- referer (text)
- headers (JSONB)
- expires_at (timestamp)
- scraped_at (timestamp)
- UNIQUE(tmdb_id, type, season, episode, source)

**scrape_queue**
- id (serial, primary key)
- tmdb_id, type, season, episode
- priority (integer, default 0)
- status (varchar 20: pending/processing/done/failed)
- attempts (integer, default 0)
- created_at, processed_at

### 3.2 Data Migration

- users.json → users table
- content-db.json → content table (5,401 items)
- scraped_streams.json → stream_cache table

### 3.3 Fallback Strategy

Pattern: try Supabase first, fallback to local JSON file.
Kalau Supabase down, ICLIX tetap jalan pakai local cache.

---

## 4. CLOUDFLARE R2 — VIDEO CACHE

### 4.1 Bucket Structure

```
iclix-cache/
├── streams/           # m3u8 cache metadata (JSON)
│   ├── movie/603.json
│   └── tv/1396/1/1.json
├── thumbnails/        # Episode thumbnails
│   ├── movie/603.jpg
│   └── tv/1396/1/1.jpg
└── content/           # Content posters/backdrops
    ├── posters/603.jpg
    └── backdrops/603.jpg
```

### 4.2 Integration

- S3-compatible API (AWS SDK)
- Upload resolved m3u8 + metadata
- Download on play request
- CacheControl headers for CDN caching

### 4.3 Fallback Strategy

Pattern: R2 → local disk → scrape fresh.
Kalau R2 down, fallback ke local cache di VPS.

---

## 5. RAILWAY — SCRAPER SERVICE

### 5.1 Service Structure

```
iclix-scraper/
├── server.js          # Express API (receive scrape jobs)
├── resolvers/
│   ├── vidlink.js     # VidLink resolver
│   ├── vidsrc.js      # VidSrc chain resolver
│   └── animasu.js     # Animasu resolver
├── package.json
└── railway.toml
```

### 5.2 API Endpoints

- POST /scrape — resolve m3u8 untuk konten
- GET /health — health check

### 5.3 Integration

VPS backend → Railway scraper → resolve m3u8 → cache ke R2 + local

### 5.4 Cron Job

Auto-scrape top 100 konten populer tiap 6 jam.

---

## 6. BACKEND INTEGRATION

### 6.1 File yang perlu di-update

```
/home/ubuntu/iclix/backend/
├── server.js              # Tambah Supabase + R2 client
├── services/
│   ├── supabase-client.js # BARU
│   ├── r2-client.js       # BARU
│   └── railway-client.js  # BARU
└── cache/                 # Tetap ada sebagai fallback
```

### 6.2 Backward Compatibility

Semua endpoint tetap ada, response format sama.
Yang berubah cuma SOURCE data. Frontend ga perlu diubah.

---

## 7. IMPLEMENTATION ORDER

### Phase 1: Setup External Services (Tanpa ganggu ICLIX)
1. Supabase: buat project + tables
2. R2: buat bucket + API keys
3. Railway: buat project + deploy scraper

### Phase 2: Testing Koneksi (Tanpa ganggu ICLIX)
4. Test Supabase connection dari terminal
5. Test R2 upload/download dari terminal
6. Test Railway scraper dari terminal

### Phase 3: Data Migration (Tanpa ganggu ICLIX)
7. Migrate users.json → Supabase
8. Migrate content-db.json → Supabase
9. Migrate scraped_streams.json → R2

### Phase 4: Backend Integration (RISIKO)
10. Backup server.js (git commit)
11. Tambah Supabase + R2 client
12. Update endpoints (dengan fallback)
13. Test ICLIX masih jalan

### Phase 5: Scraper Integration
14. Connect VPS → Railway scraper
15. Setup auto-scrape cron
16. Verify instant play works

### Phase 6: Cleanup
17. Remove local JSON files (setelah confirm OK)
18. Remove local cache (setelah confirm OK)
19. Verify VPS storage turun

---

## 8. ROLLBACK PLAN

Kalau ada masalah di Phase 4:
- git stash / git checkout server.js
- pm2 restart iclix-api
- ICLIX balik ke mode lama (JSON files)
- Data di Supabase/R2 tetap aman

---

## 9. ESTIMASI

- Phase 1-2: 30 menit (setup + testing)
- Phase 3: 30 menit (data migration)
- Phase 4: 45 menit (backend integration)
- Phase 5: 30 menit (scraper integration)
- Phase 6: 15 menit (cleanup)
- **Total: ~2.5 jam**

---

## 10. YANG DIBUTUHKAN DARI MAS

1. **Supabase account** — daftar di supabase.com, buat project, kirim:
   - Project URL
   - Anon Key (public)
   - Service Role Key (private)

2. **Railway account** — daftar di railway.app, kirim:
   - API Token

3. **Cloudflare API Token** — Mas udah punya account, kirim:
   - API Token (yang bisa edit R2)
   - Account ID

---

## 11. COST

- Supabase: **$0** (gratis tier)
- R2: **$0** (10GB gratis)
- Railway: **$0** ($5 credit gratis/bulan)
- Cloudflare CDN: **$0** (gratis)
- **Total: $0**

---

## 12. RISIKO & MITIGASI

| Risiko | Impact | Mitigasi |
|--------|--------|----------|
| Supabase down | ICLIX tetap jalan (local fallback) | Fallback ke JSON files |
| R2 down | Video cache miss, re-scrape | Fallback ke local cache |
| Railway habis credit | Scraper mati | Scrape dari VPS (existing) |
| Integrasi bug | ICLIX down sementara | Git rollback + pm2 restart |
| Free tier limit | Feature degrade | Monitor usage, upgrade kalau perlu |
