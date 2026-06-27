# Embed Sources Reference

Tested 2026-06-12, expanded 2026-06-12. All use TMDB ID as identifier.

## Movie Embeds (7 Sources)

| Source | URL Pattern | HTTP | iframe | Notes |
|--------|-------------|------|--------|-------|
| **VidLink** ⭐ | `https://vidlink.pro/movie/{tmdb_id}` | 200 | 1 | **PRIMARY** — Next.js, cleanest player, minimal ads |
| AutoEmbed | `https://autoembed.co/movie/tmdb/{tmdb_id}` | 200 | 4 | Reliable, chains player.autoembed.co |
| VidSrc | `https://vidsrc.to/embed/movie/{tmdb_id}` | 200 | 3 | Good desktop, chains vsembed.ru |
| **Flicky** | `https://flicky.host/embed/movie/{tmdb_id}` | 200 | 4 | Fast load, good backup ⭐ NEW |
| VidCloud9 | `https://vidcloud9.com/embed/movie/{tmdb_id}` | 200 | 0 | Works but sometimes empty shell |
| **111Movies** | `https://111movies.com/movie/{tmdb_id}` | 200 | 1 | Solid fallback ⭐ NEW |
| **VidSrc.in** | `https://vidsrc.in/embed/movie/{tmdb_id}` | 200 | 2 | Alternative vidsrc network ⭐ NEW |

## TV Series Embeds (5 Sources)

| Source | URL Pattern | HTTP | iframe | Notes |
|--------|-------------|------|--------|-------|
| **VidLink** ⭐ | `https://vidlink.pro/tv/{id}/{s}/{e}` | 200 | 1 | Primary |
| VidSrc | `https://vidsrc.to/embed/tv/{id}/{s}/{e}` | 200 | 3 | Good fallback |
| **Flicky** | `https://flicky.host/embed/tv/{id}/{s}/{e}` | 200 | 4 | ⭐ NEW |
| VidCloud9 | `https://vidcloud9.com/embed/tv/{id}/{s}/{e}` | 200 | 0 | Sometimes empty |
| **VidSrc.in** | `https://vidsrc.in/embed/tv/{id}/{s}/{e}` | 200 | 2 | ⭐ NEW |

## Failed Sources (2026-06)

| Source | Status | Issue |
|--------|--------|-------|
| smashy.stream | 000 | DNS timeout |
| movie-web.app | 403 | Forbidden |
| vidsrc.xyz | 000 | DNS timeout |
| 2embed.cc | 403 | Forbidden |
| vidsrc.net | 000 | DNS timeout |
| embed69 | 000 | DNS timeout |
| autoembed.xyz | 000 | DNS timeout |
| cdnmovies | 000 | DNS timeout |
| gomovies.to | 000 | DNS timeout |
| soaper.tv | 000 | DNS timeout |
| cinezone.to | 000 | DNS timeout |
| primewire.to | 200 | Works but unreliable |
| watchsomuch | 404 | Not found |

## Recommended Fallback Chain

**Movies (priority order):**
1. VidLink.pro → 2. AutoEmbed → 3. VidSrc.to → 4. Flicky → 5. 111Movies → 6. VidSrc.in → 7. VidCloud9

**TV (priority order):**
1. VidLink.pro → 2. VidSrc.to → 3. Flicky → 4. VidSrc.in → 5. VidCloud9

## Testing Commands

```bash
# Test single source
curl -s -o /dev/null -w '%{http_code}' -L --max-time 10 'https://vidlink.pro/movie/550'

# Test all movie sources at once
for src in \
  "vidlink.pro/movie/550" \
  "autoembed.co/movie/tmdb/550" \
  "vidsrc.to/embed/movie/550" \
  "flicky.host/embed/movie/550" \
  "vidcloud9.com/embed/movie/550" \
  "111movies.com/movie/550" \
  "vidsrc.in/embed/movie/550"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -L --max-time 10 "https://$src" 2>/dev/null)
  iframes=$(curl -s -L --max-time 10 "https://$src" 2>/dev/null | grep -ci 'iframe\|video\|player')
  echo "$src => HTTP:$code iframe:$iframes"
done

# Test TV sources (Squid Game S1E1)
for src in \
  "vidlink.pro/tv/93405/1/1" \
  "vidsrc.to/embed/tv/93405/1/1" \
  "flicky.host/embed/tv/93405/1/1" \
  "vidcloud9.com/embed/tv/93405/1/1" \
  "vidsrc.in/embed/tv/93405/1/1"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -L --max-time 10 "https://$src" 2>/dev/null)
  echo "$code → $src"
done
```

## Key Notes

- **VidLink.pro is the best source** — clean Next.js player, fast loading, works on all devices
- **Flicky.host is the best NEW discovery** — fast, 4 iframe elements, reliable fallback
- All sources are free, no auth required
- Sources go down without notice — always implement 5+ source fallback
- VidLink.pro content is client-side rendered — `curl` shows loading skeleton only
- For series, filter out season_number 0 (specials)
- iframe must have `allow="autoplay; fullscreen; picture-in-picture; encrypted-media"`
- Mobile Safari blocks iframe video — ALWAYS provide "Open in new tab" fallback
- `autoembed.co` chains 3 levels: player.autoembed.co → nextgencloudfabric.com
- `vidsrc.to` chains 3 levels: vsembed.ru → cloudorchestranova.com
- VidLink.pro is single-level embed — fewer points of failure
- **Don't just check HTTP 200** — verify iframe content with grep. 200 can be Cloudflare challenge page.
