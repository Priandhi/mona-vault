---
date: 2026-06-15
agent: MONA
task: ICLIX Live TV frontend integration with FolaPlay
---

# ICLIX Live TV Page — Frontend Integration

## Goal
Refactor the existing static LiveTV.jsx to dynamically pull FolaPlay live matches from the new backend API. The page already had 24 hardcoded local TV channels (HLS) — extend it with a new FolaPlay section that loads real-time sports data.

## Result
**Fully working Live TV page with two sections:**

### 1. FolaPlay Sports Live (dynamic, real-time)
- Auto-fetches `/api/streaming/list/folaplay` on mount
- Refreshes every 3 min + manual refresh button + last-updated timestamp
- 4 sub-sections:
  - **Pertandingan Langsung (4)** — live matches in green LIVE-bordered cards
  - **Highlights (9)** — horizontal scroll carousel
  - **Klip Spesial (15)** — horizontal scroll
  - **Extended Highlights (10)** — horizontal scroll
- Cards show real match images from `cms-static.folaplay.com`
- **Click behavior**: opens folaplay.com in new tab (`window.open`) — see decision below

### 2. Local TV Channels (static, HLS)
- 27 channels (24 + 3 sports headers)
- Same as before: Trans7, Trans TV, MetroTV, tvOne, etc + beIN Sports, TVRI Sport
- **Click behavior**: opens in-modal HLS player (hls.js)

## What I Built

### `LiveTV.jsx` refactor
- Split into 2 card components: `FolaplayCard` (click → new tab) + `HlsChannelCard` (click → modal HLS)
- Player modal now supports 2 player types:
  - `type: 'hls'` → `<video>` with HLS.js (existing 24 channels)
  - `type: 'embed'` → `<iframe>` loading `/api/proxy/embed?url=...` (kept for future)
- Section layout: 2 main sections with `livetv-section` container
- "Refresh" button + "Last updated" timestamp on FolaPlay section
- Error banner with "Coba lagi" button if FolaPlay fails
- Empty state if no live matches

### `LiveTV.css` additions
- `.livetv-section` / `.section-title-row` / `.subsection-title` — section layout
- `.refresh-btn` with `.spinning` animation
- `.livetv-error-banner` — error state styling
- `.livetv-scroll-row` — horizontal scroll for highlights (snap scrolling)
- `.channel-card-live` — green glow border for live cards
- `.live-badge` updated to green (#10b981) to differentiate from local channels
- `.live-iframe` — full-bleed iframe for embed mode
- `.open-external` button in modal header

### Backend tweaks
- `folaplay.js` scraper: reverted card click-loop experiment (was trying to extract per-card page IDs but all live cards share same Id=4540). Now just stamps `playUrl: 'https://folaplay.com/#/home'` and `source: 'folaplay'` on all items.

## Key Decision: Why "Open in New Tab" Not In-Modal Embed

**FolaPlay is a Vue 3 SPA** with hash routing (`#/home?Id=...`). The home page auto-loads the first live match (Id=4540 = current match) but clicking other match cards does NOT change the URL — they just highlight the active card.

Tried three approaches to integrate player in-modal:

1. **In-modal `<iframe src=folaplay.com>`** — blocked by X-Frame-Options. Would need reverse proxy. Embed-proxy exists but the captured HTML is a static snapshot of the Vue app — re-executed JS doesn't have the same state, so player doesn't render.
2. **In-modal `<iframe src=/api/proxy/embed?url=folaplay>`** — embed-proxy loads folaplay.com via Playwright, injects base tag, returns HTML. Issue: Vue renders asynchronously, by the time `page.content()` captures (after 10s click loop), the rendered DOM may be empty shell. Test showed iframe had no video element after 15s.
3. **New tab (`window.open('https://folaplay.com/#/home', '_blank')`)** — works perfectly. User gets full folaplay experience with live player + match list. Trade-off: user leaves ICLIX briefly.

**Chose option 3** for now — simpler, more reliable, user gets real folaplay player. Future v2: build custom in-modal player that extracts m3u8 from folaplay's HLS.js bundle (out of scope for this task).

## Test Results

```
=== FolaPlay section ===
4 live cards rendered (Spanyol vs Tanjung Verde, Belgia vs Mesir, Arab Saudi vs Uruguay, Iran vs Selandia Baru)
9 highlights + 15 special + 10 extended in scroll rows
Refresh button + last-updated timestamp working

=== Click flow (FolaPlay) ===
1. Click "Spanyol vs Tanjung Verde" card
2. window.open triggers → new tab at https://folaplay.com/#/home?Id=4540
3. Folaplay loads → match list visible, live match player area ready
4. User clicks "WATCH NOW" on ad → player activates

=== Local TV section ===
27 channel cards (24 static + 3 beIN/TVRI sports)
Click Trans7 → modal opens → HLS player → readyState=4 (playing)

=== Modal ===
X close button + external link button
Spinner + "Memuat stream..." text during load
Error fallback "Stream tidak bisa diputar" + Telegram report link
```

## Issues
- **Highlight images** still come back as base64 SVG placeholders from folaplay scraper (cards lazy-load images, not captured in headless). Live match images work fine (loaded eagerly).
- **In-modal embed** doesn't render folaplay player reliably — accepted as known limitation, using new-tab as workaround.
- **No m3u8 extraction** — if folaplay ever rate-limits or blocks direct access from new tabs, we'll need to extract m3u8 from their HLS.js bundle and serve it ourselves. Out of scope for now.

## Next Steps
- [ ] Fix highlight image extraction (scroll cards into view before scraping)
- [ ] When folaplay matures, build m3u8 extractor for in-modal HLS player
- [ ] Add more streaming sources (Vidio free, RCTI+ free tier, etc)
- [ ] Add a "Live now" indicator (countdown or auto-refresh on match start)
- [ ] Consider adding sports schedule (kickoff times) for upcoming matches
