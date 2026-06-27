# Video Embed Sources — Test Results

Tested: 2026-06-12 from VPS (43.163.85.51)

## Source Test Results (Fight Club, TMDB ID 550)

| Source | URL | HTTP Status | Works in iframe | Mobile Safari |
|--------|-----|-------------|-----------------|---------------|
| VidLink.pro | `https://vidlink.pro/movie/550` | 200 ✅ | ✅ Yes | ✅ Yes |
| AutoEmbed | `https://autoembed.co/movie/tmdb/550` | 200 ✅ | ✅ Yes | ⚠️ Chain iframes |
| VidSrc.to | `https://vidsrc.to/embed/movie/550` | 200 ✅ | ✅ Yes | ⚠️ Sometimes blocked |
| 2embed.org | `https://www.2embed.org/embed/tmdb/movie/550` | 000 ❌ | ❌ Timeout | ❌ |
| VidSrc.me | `https://vidsrc.me/embed/movie?tmdb=550` | 000 ❌ | ❌ Timeout | ❌ |
| Embed.su | `https://embed.su/embed/movie/550` | 000 ❌ | ❌ Timeout | ❌ |
| MultiEmbed | `https://multiembed.mov/?video_id=550&tmdb=1` | 403 ❌ | ❌ Blocked | ❌ |

## Recommended Source Order

1. **VidLink.pro** — Most reliable, single iframe, works on mobile
2. **AutoEmbed** — Good fallback, but chains through player.autoembed.co → nextgencloudfabric.com
3. **VidSrc.to** — Last resort, chains through vsembed.ru

## AutoEmbed Iframe Chain

```
autoembed.co/movie/tmdb/550
  └── player.autoembed.co/embed/movie/550
        └── nextgencloudfabric.com/embed/movie/550 (actual player)
```

This chain can cause issues with:
- Mobile Safari cross-origin iframe restrictions
- Referrer policy conflicts
- Slow loading due to multiple redirects

## VidLink.pro Structure

- Direct Next.js app rendering player
- Uses `https://image.tmdb.org` for poster/backdrop
- Clean single-level embed
- Supports both movie and TV with episode routing:
  - Movie: `/movie/{tmdb_id}`
  - TV: `/tv/{tmdb_id}/{season}/{episode}`

## Implementation Pattern

```jsx
const EMBED_SOURCES = [
  { name: 'VidLink', url: (id) => `https://vidlink.pro/movie/${id}` },
  { name: 'AutoEmbed', url: (id) => `https://autoembed.co/movie/tmdb/${id}` },
  { name: 'VidSrc', url: (id) => `https://vidsrc.to/embed/movie/${id}` },
];

// Always include "Open in New Tab" link
<a href={sources[srcIdx].url(id)} target="_blank" rel="noopener">
  ↗ Open in New Tab
</a>
```
