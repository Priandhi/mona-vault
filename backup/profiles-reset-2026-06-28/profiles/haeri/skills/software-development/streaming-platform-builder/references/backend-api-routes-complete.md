# Complete Backend API Routes for Streaming Platform

## Problem

The frontend calls many TMDB endpoints. If the backend doesn't proxy them, the catch-all SPA route returns HTML, and `response.json()` fails silently → empty pages with no visible errors.

## Route Order Matters!

Express matches routes in definition order. The catch-all `app.get('*', ...)` MUST be last, or it will intercept API requests and return HTML instead of JSON.

**Common bug:** `/api/movie/popular` must come BEFORE `/api/movie/:id` or Express matches "popular" as an `:id` parameter.

## Verification

```bash
# Test all routes return JSON (not HTML)
for ep in /api/trending/all/day /api/movie/popular /api/tv/popular /api/genre/movie/list "/api/discover/movie?with_origin_country=KR" "/api/search?q=avengers"; do
  content_type=$(curl -s -o /dev/null -w "%{content_type}" "http://localhost:3000$ep")
  echo "$ep → $content_type"
done
# All should return application/json; charset=utf-8
```

## Express Route Order (copy-paste ready)

```javascript
// 1. Static files
app.use(express.static(path.join(__dirname, '../frontend/dist')));

// 2. HLS Proxy
app.get('/api/proxy', ...);

// 3. Trending (parameterized BEFORE generic)
app.get('/api/trending/:type/:period', ...);
app.get('/api/trending', ...);

// 4. Movie routes (specific BEFORE parameterized)
app.get('/api/movie/popular', ...);
app.get('/api/movie/top_rated', ...);
app.get('/api/movie/upcoming', ...);
app.get('/api/movie/:id', ...);  // MUST be last among /api/movie/*

// 5. TV routes (specific BEFORE parameterized)
app.get('/api/tv/popular', ...);
app.get('/api/tv/top_rated', ...);
app.get('/api/tv/:id', ...);  // MUST be last among /api/tv/*

// 6. Genre
app.get('/api/genre/movie/list', ...);
app.get('/api/genre/tv/list', ...);

// 7. Discover (query params forwarded to TMDB)
app.get('/api/discover/movie', ...);
app.get('/api/discover/tv', ...);

// 8. Search
app.get('/api/search', ...);

// 9. SPA catch-all (ALWAYS LAST)
app.get('*', ...);
```
