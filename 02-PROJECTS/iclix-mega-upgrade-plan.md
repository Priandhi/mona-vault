# ICLIX MEGA UPGRADE — Execution Plan

## Status: IN PROGRESS — Pre-Scrape Running
Last updated: 2026-06-19
User confirmed all decisions, "habis ini kita kerjakan semua"

---

## 📋 USER DECISIONS (FINAL)

1. **Content sources**: Netflix, WeTV, Viu, iQIYI mirrors
2. **Subtitle**: Auto-generate (like IDLIX)
3. **Focus**: Drama Asia + Anime dulu (instant play)
4. **Trailer**: Manual play, banner full HD no bugs
5. **Analytics**: Gak perlu dulu
6. **Design**: Premium, clean, no alay/emoji
7. **Reference**: IDLIX style (2 screenshots analyzed)

---

## 🎯 EXECUTION ORDER

### PHASE 1: VIDEO RESOLVER ENGINE (Foundation)
> Ini dasar dari semuanya — tanpa ini, video gak bisa play

**Step 1.1: Build VidSrc Chain Scraper**
- [ ] Create `backend/services/vidsrc-resolver.js`
- [ ] Implement chain: vidsrc.to → vsembed.ru → cloudnestra.com → m3u8
- [ ] Add error handling & timeout
- [ ] Test with 10+ movies

**Step 1.2: Build Multi-Source Resolver**
- [ ] Create `backend/services/multi-source-resolver.js`
- [ ] Source 1: VidSrc chain (primary)
- [ ] Source 2: Netflix mirror (net22.cc or similar)
- [ ] Source 3: WeTV/Viu/iQIYI mirrors
- [ ] Auto-failover between sources

**Step 1.3: Build Subtitle Auto-Generator**
- [ ] Research IDLIX subtitle method
- [ ] Create `backend/services/subtitle-generator.js`
- [ ] Support: Indonesian subtitles
- [ ] Format: SRT/VTT

**Step 1.4: Cache System**
- [ ] Create `backend/cache/resolved-urls.json`
- [ ] TTL: 6 hours (same as current)
- [ ] Pre-resolve popular content

---

### PHASE 2: CONTENT DATABASE (Drama Asia + Anime Focus)
> Database konten yang fokus Drama Asia + Anime

**Step 2.1: TMDB Content Fetcher**
- [ ] Create `backend/services/content-fetcher.js`
- [ ] Fetch Drama Asia: Korea, China, Jepang, Thailand
- [ ] Fetch Anime (top rated + popular)
- [ ] Filter: rating > 7.0, recent releases

**Step 2.2: Content Database**
- [ ] Create `backend/data/content-db.json`
- [ ] Structure: movies, tv-shows, anime
- [ ] Include: TMDB ID, title, backdrop, poster, metadata
- [ ] Pre-fetch top 500 Drama Asia + top 500 Anime

**Step 2.3: Pre-Resolve Popular Content**
- [ ] Create `backend/services/pre-resolver.js`
- [ ] Run daily cron: resolve top 100 content
- [ ] Cache m3u8 URLs for instant play

---

### PHASE 3: FRONTEND UPGRADE (IDLIX-Style Premium Design)
> Upgrade UI sesuai reference IDLIX

**Step 3.1: Hero Banner Upgrade**
- [ ] Update `HeroBanner.jsx`
- [ ] Full HD backdrop (TMDB original size)
- [ ] Manual play trailer button (not auto-play)
- [ ] Genre tags (pill-shaped)
- [ ] Metadata bar: Year · Seasons · ★ Rating · Country · Language
- [ ] Status badge: ONGOING/ENDED
- [ ] Action buttons: Simpan · Favorit · Trailer · Bagikan
- [ ] Production logos (white monochrome)

**Step 3.2: Episode List Upgrade**
- [ ] Update `TVDetail.jsx` & `AnimeDetail.jsx`
- [ ] 2-column grid layout
- [ ] Episode cards with thumbnail
- [ ] Thumbnail overlays: S01E01, date, rating, duration
- [ ] Episode title + description (truncated)
- [ ] Season selector dropdown
- [ ] Sort controls (Terlama/Terbaru)

**Step 3.3: Card Design Upgrade**
- [ ] Update `MovieCard.jsx` & `MediaCard.jsx`
- [ ] Rating in gold (#f5c518)
- [ ] Status badges (ONGOING/ENDED/NEW)
- [ ] Clean typography hierarchy
- [ ] Proper spacing

**Step 3.4: Video Player Integration**
- [ ] Update `VideoPlayer.jsx`
- [ ] Use new multi-source resolver
- [ ] Instant play (no iframe loading delay)
- [ ] Subtitle support (auto-generated)
- [ ] Quality selector (if available)

**Step 3.5: Search & Filter**
- [ ] Update `SearchResults.jsx`
- [ ] Add filters: Year, Rating, Genre, Country
- [ ] Sort: Terbaru, Terpopuler, Rating

**Step 3.6: Bug Fixes (from audit)**
- [ ] Fix rating 0.0 (hide if vote_count=0)
- [ ] Content deduplication
- [ ] Remove empty card placeholders
- [ ] Fix carousel arrows visibility

---

### PHASE 4: BACKEND API UPDATES
> API endpoints untuk support frontend baru

**Step 4.1: New Endpoints**
- [ ] `GET /api/content/drama-asia` — Drama Asia list
- [ ] `GET /api/content/anime` — Anime list
- [ ] `GET /api/resolve/:type/:id` — Resolve video URL
- [ ] `GET /api/subtitle/:type/:id` — Get subtitle
- [ ] `GET /api/content/:type/:id/episodes` — Episode list

**Step 4.2: Update Existing Endpoints**
- [ ] Update `/api/stream/instant/:type/:id` — Use new resolver
- [ ] Update `/api/tmdb/*` — Add production companies

---

### PHASE 5: TESTING & DEPLOYMENT
> Pastikan semua work sebelum deploy

**Step 5.1: Unit Testing**
- [ ] Test video resolver (10+ movies, 10+ TV shows)
- [ ] Test subtitle generator
- [ ] Test content fetcher
- [ ] Test API endpoints

**Step 5.2: Integration Testing**
- [ ] Test full flow: browse → select → play
- [ ] Test Drama Asia section
- [ ] Test Anime section
- [ ] Test episode list
- [ ] Test search & filter

**Step 5.3: Performance Testing**
- [ ] Test instant play speed
- [ ] Test pre-resolved cache
- [ ] Test concurrent users

**Step 5.4: Deploy**
- [ ] `npm run build` (frontend)
- [ ] `pm2 restart iclix-api` (backend)
- [ ] Verify tunnel URL works
- [ ] Test on mobile browser

---

## 📁 FILES TO CREATE/MODIFY

### New Files (Backend)
```
backend/services/
├── vidsrc-resolver.js          # VidSrc chain scraper
├── multi-source-resolver.js    # Multi-source with failover
├── subtitle-generator.js       # Auto subtitle generator
├── content-fetcher.js          # TMDB content fetcher
└── pre-resolver.js             # Pre-resolve popular content

backend/data/
└── content-db.json             # Content database

backend/cache/
└── resolved-urls.json          # Resolved URL cache
```

### Modified Files (Backend)
```
backend/
├── server.js                   # Add new endpoints
└── services/
    └── streaming-sources/      # Update existing scrapers
```

### Modified Files (Frontend)
```
frontend/src/
├── components/
│   ├── HeroBanner.jsx          # Full HD + trailer + metadata
│   ├── MovieCard.jsx           # Rating + badges
│   ├── MediaCard.jsx           # Rating + badges
│   ├── VideoPlayer.jsx         # New resolver + subtitle
│   └── MovieRow.jsx            # Section headers
├── pages/
│   ├── Home.jsx                # Drama Asia + Anime sections
│   ├── TVDetail.jsx            # Episode grid + season selector
│   ├── AnimeDetail.jsx         # Episode grid + season selector
│   ├── MovieDetail.jsx         # Production logos + social buttons
│   └── SearchResults.jsx       # Filters + sort
└── App.css                     # Typography + spacing + colors
```

---

## ⏱️ ESTIMATED TIME

| Phase | Task | Time |
|-------|------|------|
| 1 | Video Resolver Engine | 3-4 jam |
| 2 | Content Database | 2-3 jam |
| 3 | Frontend Upgrade | 4-5 jam |
| 4 | Backend API | 1-2 jam |
| 5 | Testing & Deploy | 1-2 jam |
| **Total** | | **11-16 jam** |

---

## 🎯 SUCCESS CRITERIA

1. ✅ Video instant play (no loading delay)
2. ✅ Drama Asia section: 500+ titles
3. ✅ Anime section: 500+ titles
4. ✅ Episode list: 2-column grid with thumbnails
5. ✅ Banner: Full HD, no crop, no bugs
6. ✅ Trailer: Manual play in hero
7. ✅ Subtitle: Auto-generated Indonesian
8. ✅ Design: Premium, clean, IDLIX-style
9. ✅ Search: Filters working
10. ✅ Mobile: Responsive, fast

---

## 🚀 READY TO EXECUTE

User: "habis ini kita kerjakan semua plan kita tadi"
Mona: Siap Mas! Gas dari Phase 1 sampai Phase 5.

---

## Related Files
- `/home/ubuntu/obsidian-vault/03-RESEARCH/iclix-idlix-design-reference.md`
- `/home/ubuntu/obsidian-vault/03-RESEARCH/iclix-ui-ux-audit-2026-06-18.md`
- `/home/ubuntu/obsidian-vault/03-RESEARCH/iclix-video-resolver-research.md`
- `/home/ubuntu/iclix/` — ICLIX project directory
