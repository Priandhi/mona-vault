---
type: resource
tags:
  - resource
  - iclix
  - streaming
---

# ICLIX Anime Research — 2026-06-19

## Current State
- **Active sources:** AniList (metadata), AniNeko (episodes + video, Sub Indo)
- **Dead sources:** Samehadaku (Next.js migration), Oploverz (CF VIP), Otakudesu (523)
- **Total:** 123 anime items (mix of metadata-only + video)
- **Video embeds:** vibeplayer.site, bibiemb.xyz, playmogo.com

## IDLIX Analysis
- WordPress + DooPlay theme + jeniusplay.com (custom video resolver)
- Behind Cloudflare (403 managed challenge) — cannot scrape directly
- Their video sources likely from same upstream (Gogoanime/AniNeko-type)
- Key advantage: own CDN, complete episodes, Full HD
- WP REST API also blocked by CF

## Research Tasks (TODO)
1. Find alternative anime sources not behind CF:
   - AnimeDao successors
   - 9anime successors
   - Zoro.to / AniWatch successors
   - Free anime APIs (consumet.org, etc.)
2. Investigate consumet.org API — self-hosted anime API with multiple providers
3. Check if jeniusplay.com can be used independently
4. Reverse engineer AniNeko's video extraction for better quality
5. Check AniNeko episode completeness for popular anime (JJK, AoT, Naruto, One Piece)

## Key Files
- Anime sources: /home/ubuntu/iclix/backend/services/anime-sources/
- Anime page: /home/ubuntu/iclix/frontend/src/pages/Anime.jsx
- API endpoint: /api/anime/list (returns merged sources)
