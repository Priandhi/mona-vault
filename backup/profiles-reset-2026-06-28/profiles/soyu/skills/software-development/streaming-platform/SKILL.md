---
name: "streaming-platform"
description: "Build movie / series / anime streaming web platforms. Covers TMDB metadata, video embed source selection (VidLink + vidsrc), mobile-first React+Express stack, Cloudflare tunnel deployment, and ad-overlay bypass. Use when asked to build a streaming site, integrate TMDB, or set up embed players."
tags:
  - streaming
  - tmdb
  - vidlink
  - vidsrc
  - react
  - express
  - cloudflare
  - anime
---
# Streaming Platform Builder

> Build movie / series / anime streaming web platforms. Covers TMDB metadata, video embed source selection, mobile-first UI, Indonesian-targeted patterns, public-access tunneling, and Cloudflare bypass.

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "streaming platform", "movie site", "anime site", "vidlink", "TMDB", "React+Express" | `references/streaming-platform-builder/` |
| "vidlink", "vidsrc", "embed player", "cloudflare bypass" | `references/web-streaming-platform/` |

## Architecture

```
TMDB API  ──→  metadata + posters
                    ↓
              Backend (Express / FastAPI)
                    ↓
              Frontend (React / Next.js)
                    ↓
              Embed player (VidLink / vidsrc / custom)
                    ↓
              Cloudflare tunnel  ──→  public URL
```

## Topic Pages

- `references/streaming-platform-builder/SKILL.md` — Full React+Express stack with TMDB + Indonesian UI patterns
- `references/web-streaming-platform/SKILL.md` — Embed players (VidLink.pro primary + vidsrc.to), Cloudflare bypass, deployment

## Common PITFALLS

1. **TMDB API key required.** Get one at https://www.themoviedb.org/settings/api. Free tier is 50 requests/sec.
2. **VidLink is the primary embed source.** It has the best uptime and the widest content coverage.
3. **Cloudflare bypass is needed for production.** Use `cloudflared` tunnel — don't expose port 3000 directly.
4. **PITFALL: Embed sources change frequently.** Always have a fallback list (vidsrc.to, 2embed, etc.) and a health-check cron.

## Related (not part of this umbrella)

- `iclix-anti-ads-direct-play` (in `process-ops/references/iclix-anti-ads-direct-play/` after demotion) — bypass iframe ad overlays on a specific embed player
- `iclix-frontend-design`, `iclix-adult-21-plus-scrapers` — project-specific work for the ICLIX project
