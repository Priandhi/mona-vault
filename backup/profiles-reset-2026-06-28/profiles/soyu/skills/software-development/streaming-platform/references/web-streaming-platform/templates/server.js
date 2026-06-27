import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const API_KEY = process.env.TMDB_API_KEY || 'YOUR_KEY_HERE';
const BASE = 'https://api.themoviedb.org/3';
const LANG = 'id-ID';

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../frontend/dist')));

async function tmdb(path, params = {}) {
  const url = new URL(`${BASE}${path}`);
  url.searchParams.set('api_key', API_KEY);
  url.searchParams.set('language', LANG);
  for (const [k, v] of Object.entries(params)) {
    if (v != null) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`TMDB ${res.status}`);
  return res.json();
}

// Trending
app.get('/api/trending', async (req, res) => {
  try { res.json(await tmdb('/trending/all/day', { page: req.query.page || 1 })); }
  catch (e) { res.status(500).json({ error: e.message }); }
});

app.get('/api/trending/:type/:time', async (req, res) => {
  try { res.json(await tmdb(`/trending/${req.params.type}/${req.params.time}`, { page: req.query.page || 1 })); }
  catch (e) { res.status(500).json({ error: e.message }); }
});

// Movie detail (with videos, credits, similar)
app.get('/api/movie/:id', async (req, res) => {
  try { res.json(await tmdb(`/movie/${req.params.id}`, { append_to_response: 'videos,credits,similar,recommendations' })); }
  catch (e) { res.status(500).json({ error: e.message }); }
});

// Movie lists (popular, top_rated, upcoming, now_playing)
app.get('/api/movie/:list(popular|top_rated|upcoming|now_playing)', async (req, res) => {
  try { res.json(await tmdb(`/movie/${req.params.list}`, { page: req.query.page || 1 })); }
  catch (e) { res.status(500).json({ error: e.message }); }
});

// TV detail
app.get('/api/tv/:id', async (req, res) => {
  try { res.json(await tmdb(`/tv/${req.params.id}`, { append_to_response: 'videos,credits,similar,recommendations' })); }
  catch (e) { res.status(500).json({ error: e.message }); }
});

// TV episode detail
app.get('/api/tv/:id/season/:s/episode/:e', async (req, res) => {
  try { res.json(await tmdb(`/tv/${req.params.id}/season/${req.params.s}/episode/${req.params.e}`)); }
  catch (e) { res.status(500).json({ error: e.message }); }
});

// TV lists
app.get('/api/tv/:list(popular|top_rated|on_the_air|airing_today)', async (req, res) => {
  try { res.json(await tmdb(`/tv/${req.params.list}`, { page: req.query.page || 1 })); }
  catch (e) { res.status(500).json({ error: e.message }); }
});

// Discover with filters
app.get('/api/discover/:type(movie|tv)', async (req, res) => {
  try {
    const params = { page: req.query.page || 1, sort_by: req.query.sort_by || 'popularity.desc' };
    if (req.query.with_genres) params.with_genres = req.query.with_genres;
    if (req.query.with_origin_country) params.with_origin_country = req.query.with_origin_country;
    if (req.query.year) params.year = req.query.year;
    res.json(await tmdb(`/discover/${req.params.type}`, params));
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// Search
app.get('/api/search', async (req, res) => {
  try { res.json(await tmdb('/search/multi', { query: req.query.q, page: req.query.page || 1 })); }
  catch (e) { res.status(500).json({ error: e.message }); }
});

// Genres
app.get('/api/genre/:type(movie|tv)/list', async (req, res) => {
  try { res.json(await tmdb(`/genre/${req.params.type}/list`)); }
  catch (e) { res.status(500).json({ error: e.message }); }
});

// SPA fallback
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/dist/index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => console.log(`Server running on :${PORT}`));
