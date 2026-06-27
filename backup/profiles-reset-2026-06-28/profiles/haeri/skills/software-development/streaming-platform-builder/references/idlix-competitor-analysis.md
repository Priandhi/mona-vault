# IDLIX Competitor Analysis

## IDLIX Mobile UI Structure (Reference)

Source: z2.idlixku.com mobile screenshot analysis

### Header
- Logo: Bold red "IDLIX" text (no icon), top-left
- Icons: Search (🔍), Profile (👤), Close (✕) — top-right
- Background: Warm orange-brown textured gradient

### Sidebar Navigation (Full-screen overlay)
- **Auth section**: Masuk (Login) + Daftar (Register) buttons with thin borders
- **Menu items** with left icons:
  - 🏠 Beranda (Home) — ACTIVE: red text + dark gray bg
  - 🎬 Film
  - 📺 Serial TV
  - 🏷️ Genre
  - 🏆 Papan Peringkat (Rankings)
  - 🌍 Negara (Country)
  - 📅 Tahun (Year)
  - 📡 Network
- **Language section**: BAHASA label, Bahasa (✓ selected) + English options

### Main Content
- Section: "Lagi Tren Sekarang" (Trending Now)
- Filter tabs: Semua (All) | Film | Serial TV
- Content: Numbered poster cards in grid

## Key Design Takeaways

1. **Minimal logo** — Just text, no icon. Red, bold, uppercase.
2. **Icon+text menu items** — Every menu item has an emoji/icon + label
3. **Active state** — Red text + gray background highlight + checkmark
4. **Full-width buttons** — Auth buttons span full sidebar width
5. **Indonesian-first** — All UI text in Indonesian
6. **Filter tabs** — Semua/Film/Serial TV for trending content
7. **Country/Year as top-level nav** — Not buried in filters

## Improvements Over IDLIX (for ICLIX)

1. Better hero banner with auto-rotate
2. Multiple embed source fallback
3. Cast section with photos
4. YouTube trailer embeds
5. Similar content carousels
6. Genre page with movie/TV toggle
7. "Open in New Tab" for mobile Safari compatibility
