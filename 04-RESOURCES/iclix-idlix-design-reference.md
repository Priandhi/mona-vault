---
type: resource
tags:
  - resource
  - iclix
  - streaming
  - design
---

# ICLIX Design Reference — IDLIX Premium Style

## Status: Reference Complete, Pending Execution
User: "simpen dulu ya mona, ada lagi gak?"

---

## 📸 SOURCE: IDLIX (z2.idlixku.com)

### Image 1: Hero/Banner + Detail Page
- Full HD One Piece key art, NO crop
- Title: "One Piece" (32px, bold, white)
- Genre tags: "Action · Animation · Adventure · Comedy" (pill-shaped)
- Metadata: "1999 · 23 Seasons · ★8.7 · Japan · JA"
- Status: Green "ONGOING" badge
- Action buttons: "Simpan 345" · "Favorit 362" · "Trailer" · "Bagikan 3"
- Production logos: Toei Animation, Shueisha, ADK (white monochrome)

### Image 2: Episode List
- 2-column grid, mobile-optimized
- Card design: Dark rounded container
- Thumbnail overlays:
  - Top-left: "S01E01" badge (dark pill, white text)
  - Top-right: "20 Oct 99" date badge
  - Bottom-left: "★7.8" rating (gold star)
  - Bottom-right: "25m" duration
- Below thumbnail:
  - Episode title (bold, white, truncated)
  - Episode description (gray, smaller, truncated)
- Controls: "Terlama" sort + "Season 1" dropdown

---

## 🎨 DESIGN SPECS

### Color Palette
| Element | Color | Hex |
|---------|-------|-----|
| Background | Pure black | #000 |
| Card background | Dark gray | #1a1a1a |
| Text primary | White | #fff |
| Text secondary | Light gray | #aaa |
| Rating star | Gold | #f5c518 |
| Status ONGOING | Green | #4CAF50 |
| Status ENDED | Gray | #666 |
| Badge bg | Semi-transparent black | rgba(0,0,0,0.7) |
| Brand accent | Red | #e50914 |

### Typography
| Element | Size | Weight | Style |
|---------|------|--------|-------|
| Hero title | 32px | Bold | Sans-serif |
| Genre tags | 14px | Regular | Uppercase, pill |
| Metadata | 13px | Regular | Dot-separated |
| Episode title | 14px | Bold | Truncated |
| Episode desc | 12px | Regular | Gray, truncated |
| Badge text | 11px | Medium | White |

### Spacing & Radius
| Element | Value |
|---------|-------|
| Card gap | 12px |
| Card padding | 12px |
| Section padding | 16px |
| Badge padding | 4px 8px |
| Card border-radius | 8px |
| Badge border-radius | 12px (pill) |
| Button border-radius | 20px (pill) |

---

## 📐 LAYOUT SPECIFICATIONS

### Hero Banner
```
┌─────────────────────────────────────┐
│                                     │
│     [Full HD Backdrop Image]        │
│     (TMDB backdrop_path original)   │
│                                     │
│     ┌─────────────────────────┐     │
│     │  Title (32px bold)      │     │
│     │  Genre · Tags · Here    │     │
│     └─────────────────────────┘     │
│                                     │
│     [Simpan] [Favorit] [Trailer]    │ ← Pill buttons
│     [Bagikan]                       │
│                                     │
│     1999 · 23S · ★8.7 · JP · JA    │ ← Metadata bar
│     [ONGOING]                       │ ← Status badge
│                                     │
│     [Studio1] [Studio2] [Studio3]   │ ← Production logos
│                                     │
└─────────────────────────────────────┘
```

### Episode Grid
```
┌─────────────────────────────────────┐
│ Episode          [Terlama] [S1 ▾]   │ ← Header + controls
├─────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐    │
│ │ [S01E01]    │ │ [S01E02]    │    │ ← 2-column grid
│ │ [20 Oct 99] │ │ [17 Nov 99] │    │
│ │ [★7.8]      │ │ [★7.9]      │    │
│ │ [25m]       │ │ [25m]       │    │
│ │             │ │             │    │
│ │ I'm Luffy!  │ │ The Great   │    │
│ │ The Man...  │ │ Swordsman.. │    │
│ │             │ │             │    │
│ │ A group of  │ │ Luffy and   │    │
│ │ pirates...  │ │ Coby...     │    │
│ └─────────────┘ └─────────────┘    │
│                                     │
│ ┌─────────────┐ ┌─────────────┐    │
│ │ [S01E03]    │ │ [S01E04]    │    │
│ │ ...         │ │ ...         │    │
│ └─────────────┘ └─────────────┘    │
└─────────────────────────────────────┘
```

---

## 🔧 COMPONENTS TO MODIFY

### Frontend (React)
1. **HeroBanner.jsx** — Full HD backdrop + trailer + metadata + action buttons
2. **MovieDetail.jsx** — Social buttons + production logos + status badges
3. **TVDetail.jsx** — Season selector + ONGOING badge + episode grid
4. **AnimeDetail.jsx** — Episode grid + thumbnail overlays + metadata
5. **MovieCard.jsx** — Rating style (#f5c518 gold) + status badges
6. **MediaCard.jsx** — Rating style (#f5c518 gold) + status badges
7. **App.css** — Global typography + spacing + color variables

### Backend (Node.js)
1. **Production companies** — TMDB API `/movie/{id}` → `production_companies`
2. **Episode thumbnails** — TMDB API `/tv/{id}/season/{s}` → `still_path`
3. **Episode metadata** — Rating, duration, air date from TMDB

---

## 📋 IMPLEMENTATION CHECKLIST

### Phase 1: Hero Banner (P1)
- [ ] Full HD backdrop from TMDB `backdrop_path` (original size)
- [ ] Trailer button → play trailer in modal
- [ ] Genre tags as pill-shaped badges
- [ ] Metadata bar (year, seasons, rating, country, language)
- [ ] Status badge (ONGOING/ENDED)
- [ ] Action buttons (Simpan, Favorit, Trailer, Bagikan) with counts
- [ ] Production logos (white monochrome filter)

### Phase 2: Episode List (P1)
- [ ] 2-column grid layout
- [ ] Episode cards with thumbnail
- [ ] Thumbnail overlays (S01E01, date, rating, duration)
- [ ] Episode title + description (truncated)
- [ ] Season selector dropdown
- [ ] Sort controls (Terlama/Terbaru)

### Phase 3: Cards & Typography (P2)
- [ ] Rating in gold (#f5c518)
- [ ] Status badges on cards
- [ ] Consistent typography hierarchy
- [ ] Proper spacing and padding

### Phase 4: Polish (P2)
- [ ] Hover effects on cards
- [ ] Loading states
- [ ] Responsive design (mobile-first)
- [ ] Accessibility (contrast, focus states)

---

## 🎯 KEY DIFFERENCES: IDLIX vs ICLIX

| Element | IDLIX | ICLIX (Current) | ICLIX (Target) |
|---------|-------|-----------------|----------------|
| Banner | Full HD, no crop | Sometimes crop | Full HD, no crop |
| Trailer | In hero section | In detail page | In hero section |
| Metadata | Full (year, seasons, rating, country, lang) | Year + rating only | Full metadata |
| Status | ONGOING badge | None | ONGOING/ENDED |
| Social | 4 buttons with counts | Watch Now only | 4 buttons + counts |
| Season | Clean dropdown | Basic list | Clean dropdown |
| Logos | Production logos | None | Production logos |
| Episodes | 2-col grid with overlays | Simple list | 2-col grid with overlays |
| Typography | Consistent hierarchy | Inconsistent | Consistent hierarchy |
| Spacing | Breathable, clean | Sometimes cramped | Consistent, clean |

---

## 📁 RELATED FILES

- `/home/ubuntu/obsidian-vault/03-RESEARCH/iclix-ui-ux-audit-2026-06-18.md` — UI/UX audit
- `/home/ubuntu/obsidian-vault/03-RESEARCH/iclix-video-resolver-research.md` — Video resolver
- `/home/ubuntu/iclix/frontend/src/components/` — Frontend components
- `/home/ubuntu/iclix/frontend/src/pages/` — Page components
- `/home/ubuntu/iclix/backend/services/` — Backend services

---

## 📋 NEXT STEPS

1. Save this reference to vault ✅
2. Discuss with Mas: any additional requirements?
3. Bundle all fixes into one batch
4. Execute Phase 1 + Phase 2 together
5. Test end-to-end
6. Deploy

---

## Notes
- Mas wants "premium, clean, tidak alay/emoji berlebihan"
- Focus: Drama Asia + Anime + Film bagus
- Mobile-first responsive design
- No app needed, web only
- Domain/Firebase: later
