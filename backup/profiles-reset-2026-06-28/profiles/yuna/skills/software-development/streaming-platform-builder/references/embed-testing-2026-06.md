# Embed Source Testing Results (2026-06-12)

Comprehensive test of 15+ embed sources for TMDB-based streaming platforms.

## Testing Methodology

```bash
# 1. HTTP status check
curl -s -o /dev/null -w '%{http_code}' -L --max-time 10 'https://source.com/movie/550'

# 2. Iframe/video content verification
curl -s -L --max-time 10 'https://source.com/movie/550' | grep -ci 'iframe\|video\|player'
```

Test content:
- **Movie**: Fight Club (TMDB ID: 550)
- **TV Series**: Squid Game S1E1 (TMDB ID: 93405)

## Movie Embed Results

| Source | HTTP | iframe | URL Pattern |
|--------|------|--------|-------------|
| vidlink.pro | 200 | 1 | `https://vidlink.pro/movie/{tmdb_id}` |
| autoembed.co | 200 | 4 | `https://autoembed.co/movie/tmdb/{tmdb_id}` |
| vidsrc.to | 200 | 3 | `https://vidsrc.to/embed/movie/{tmdb_id}` |
| flicky.host | 200 | 4 | `https://flicky.host/embed/movie/{tmdb_id}` |
| vidcloud9.com | 200 | 0 | `https://vidcloud9.com/embed/movie/{tmdb_id}` |
| 111movies.com | 200 | 1 | `https://111movies.com/movie/{tmdb_id}` |
| vidsrc.in | 200 | 2 | `https://vidsrc.in/embed/movie/{tmdb_id}` |
| primewire.to | 200 | ? | `https://primewire.to/movie/{tmdb_id}` |
| moviesapi.to | 200 | ? | `https://moviesapi.to/movie/{tmdb_id}` |

### Failed Sources (2026-06)

| Source | Status | Reason |
|--------|--------|--------|
| flicky.host (imdb) | 200 | Works with IMDB ID but not TMDB |
| vidcloud9.com (imdb) | 200 | Works with IMDB ID but not TMDB |
| smashy.stream | 000 | Timeout/DNS failure |
| movie-web.app | 403 | Blocked/Cloudflare |
| cinezone.to | 000 | Timeout/DNS failure |
| watchsomuch.to | 404 | Not found |
| soaper.tv | 000 | Timeout/DNS failure |
| gomovies.to | 000 | Timeout/DNS failure |
| fmovie.to | 404 | Not found |
| 2embed.cc | 403 | Blocked |
| vidsrc.xyz | 000 | Timeout/DNS failure |
| vidsrc.net | 000 | Timeout/DNS failure |
| embed69.com | 000 | Timeout/DNS failure |
| autoembed.xyz | 000 | Timeout/DNS failure |
| cdnmovies.to | 000 | Timeout/DNS failure |

## TV Series Embed Results

Tested: Squid Game S1E1 (TMDB ID 93405)

| Source | HTTP | iframe | URL Pattern |
|--------|------|--------|-------------|
| vidlink.pro | 200 | 1 | `https://vidlink.pro/tv/{tmdb_id}/{season}/{episode}` |
| vidsrc.to | 200 | 3 | `https://vidsrc.to/embed/tv/{tmdb_id}/{season}/{episode}` |
| flicky.host | 200 | 4 | `https://flicky.host/embed/tv/{tmdb_id}/{season}/{episode}` |
| vidcloud9.com | 200 | 0 | `https://vidcloud9.com/embed/tv/{tmdb_id}/{season}/{episode}` |
| vidsrc.in | 200 | 2 | `https://vidsrc.in/embed/tv/{tmdb_id}/{season}/{episode}` |

**Note**: AutoEmbed for TV uses different pattern: `https://autoembed.co/tv/tmdb/{tmdb_id}/{season}-{episode}` (hyphen, not slash) — returned 404 in testing.

## Recommended Configuration

**Movies**: 7 servers
1. VidLink.pro (primary — cleanest UI, minimal ads)
2. AutoEmbed.co
3. VidSrc.to
4. Flicky.host
5. VidCloud9
6. 111Movies
7. VidSrc.in

**TV Series**: 5 servers
1. VidLink.pro (primary)
2. VidSrc.to
3. Flicky.host
4. VidCloud9
5. VidSrc.in

## User Expectation

> "gaboleh menyerah kita punya banyak cara buat bypass cari terus ya sayang"

Translation: "never give up, we have many ways to bypass, keep searching"

Multi-server fallback is NOT optional — it's a core feature. User expects resilience and multiple alternatives when one source fails.

## Ads & Quality Notes

- **VidLink.pro**: Relatively clean, 1-2 pop-ups on first play, minimal in-player ads
- **AutoEmbed**: More ads, multiple iframe chain can be slower
- **VidSrc.to**: Mid-range ads, reliable uptime
- **Flicky.host**: Similar to VidSrc.to
- **111Movies**: Basic embed, moderate ads

No tested source is 100% ad-free. For truly ad-free experience, would need:
- Premium embed API (paid subscription)
- Direct scraping from streaming platforms (resource-intensive, easily blocked)
- Self-hosted video CDN (expensive, legal issues)

Aggregator model (current approach) is industry standard for this class of platform (IDLIX, LK21, Rebahin, etc.).
