# IPTV M3U8 Stream Testing Results (2026-06-12)

Tested free M3U8 streams for Indonesian and international TV channels.
**CRITICAL: All results below are CONTENT-VALIDATED**, not just HTTP status checked.
Response body must contain `#EXTM3U` or `#EXT-X` HLS headers to be considered valid.

## Source: iptv-org/iptv GitHub Repository

**Indonesian channel list:** `https://iptv-org.github.io/iptv/countries/id.m3u`

Fetch and parse:
```bash
# Get all Indonesian channel URLs
curl -s "https://iptv-org.github.io/iptv/countries/id.m3u" | grep -E "^https?:" | head -30

# Get channel names + URLs
curl -s "https://iptv-org.github.io/iptv/countries/id.m3u" | grep -E "^#EXTINF|^https?:" | paste - -
```

## Validation Script (MANDATORY — use this before adding ANY stream)

```bash
test_stream() {
  name=$1
  url=$2
  response=$(curl -s -L --max-time 8 "$url" 2>/dev/null | head -5)
  if echo "$response" | grep -q "#EXTM3U\|#EXT-X"; then
    echo "✅ $name - VALID HLS"
  elif echo "$response" | grep -q "error\|Error\|403\|404\|forbidden"; then
    echo "❌ $name - ERROR: $(echo $response | head -1)"
  else
    echo "⚠️ $name - NOT HLS (HTTP 200 but content is: $(echo $response | head -c 80))"
  fi
}
```

**Why this matters:** HTTP 200 can return HTML pages, binary data, or non-video content.
Example: CGTN returns HTTP 200 but the body is an HTML page, not M3U8. LOFI Radio returns binary audio data.
Only streams that pass the `#EXTM3U|#EXT-X` grep check will actually play in an HTML5 `<video>` element.

## Tested & Content-VALIDATED Working Streams (2026-06-12 17:55)

### Indonesian Channels (18 working)

| Channel | URL | Category | Validated |
|---------|-----|----------|-----------|
| **Trans7** 🔥 | `https://video.detik.com/trans7/smil:trans7.smil/index.m3u8` | General | ✅ HLS |
| **Trans TV** 🔥 | `https://video.detik.com/transtv/smil:transtv.smil/index.m3u8` | General | ✅ HLS |
| MetroTV | `https://edge.medcom.id/live-edge/smil:metro.smil/playlist.m3u8` | News | ✅ HLS |
| tvOne | `http://202.80.222.20/cdn/iptv/Tvod/001/channel2000018/1024.m3u8` | News | ✅ HLS |
| BeritaSatu | `https://xtdslboppkkv-pull.bpmedialive.com/live/beritasatu/abr.m3u8` | News | ✅ HLS |
| BTV | `https://xtdslboppkkv-pull.bpmedialive.com/live/btv/abr.m3u8` | News | ✅ HLS |
| **Garuda TV** | `https://hgmtv.com:19360/garudatvlivestreaming/garudatvlivestreaming.m3u8` | General | ✅ HLS |
| **MBG TV** | `https://stream.convergen.co/mbg_stream/smil:mbStream.smil/playlist.m3u8` | Legislative | ✅ HLS |
| **Indonesiana** | `https://tvstreamcast.com/indonesiana.m3u8` | Culture | ✅ HLS |
| Bandung TV | `http://202.150.153.254:65500/bandungtvWEBSITE.m3u8` | Lokal | ✅ HLS |
| Banten TV | `https://5bf7b725107e5.streamlock.net/bantentv/bantentv/playlist.m3u8` | Lokal | ✅ HLS |
| BRTV | `https://5bf7b725107e5.streamlock.net/brtv/brtv/playlist.m3u8` | Lokal | ✅ HLS |
| Caruban TV | `https://stream.carubantv.id/hls/0/stream.m3u8` | Lokal | ✅ HLS |
| **Padang TV** | `http://122.248.43.242:1935/PADANGTV/_definst_/myStream/playlist.m3u8` | Lokal | ✅ HLS |
| **Batam TV** | `http://122.248.43.242:1935/BATAMTV/_definst_/myStream/playlist.m3u8` | Lokal | ✅ HLS |
| Biznet Adventure | `http://livestream.biznetvideo.net/biznet_adventure/smil:adventure.smil/playlist.m3u8` | Entertainment | ✅ HLS |
| Biznet Kids | `http://livestream.biznetvideo.net/biznet_kids/smil:kids.smil/index.m3u8` | Kids | ✅ HLS |
| Biznet Lifestyle | `http://livestream.biznetvideo.net/biznet_lifestyle/smil:lifestyle.smil/index.m3u8` | Lifestyle | ✅ HLS |

### International Channels (3 working)

| Channel | URL | Category | Validated |
|---------|-----|----------|-----------|
| DW News | `https://dwamdstream102.akamaized.net/hls/live/2015525/dwstream102/index.m3u8` | News | ✅ HLS |
| TRT World | `https://tv-trtworld.medya.trt.com.tr/master.m3u8` | News | ✅ HLS |
| Red Bull TV | `https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8` | Sports | ✅ HLS |

### FAILED Content Validation (HTTP 200 but NOT playable)

| Channel | HTTP | Actual Content | Notes |
|---------|------|----------------|-------|
| CGTN | 200 | HTML page | Returns `<!DOCTYPE html>`, not video |
| LOFI Radio | 200 | Binary audio | Returns raw bytes, not M3U8 |
| BungoTV | 200 | Invalid HLS | Streamlock but content doesn't play |

### Failed HTTP — DRM/Geo-blocked (Major Indonesian Networks)

These channels CANNOT be embedded. They require official apps (RCTI+, Vidio.com) with Indonesian IP.

| Channel | Error | Notes |
|---------|-------|-------|
| RCTI | DRM/403 | Requires Widevine DRM + RCTI+ auth |
| SCTV | Geo-blocked | Requires dens.tv referrer + Indonesian IP |
| Indosiar | Geo-blocked | Requires dens.tv referrer + Indonesian IP |
| MNCTV | DRM/403 | Requires maxstream referrer + auth |
| GTV | DRM/403 | Requires maxstream referrer + auth |
| iNews | DRM/403 | Requires maxstream referrer + auth |
| NET TV | DRM/403 | Requires auth |
| Kompas TV | Geo-blocked | Requires dens.tv referrer + Indonesian IP |
| ANTV | 401 | Auth required |
| Al Jazeera | 000 | Timeout/DNS |
| France24 | 404 | Stream expired |
| NHK World | 000 | Timeout/DNS |
| Bloomberg | 000 | Timeout/DNS |

## Key Findings

1. **Trans7 and TransTV have working free streams!** Via `video.detik.com` CDN — these are major commercial channels that work without DRM. This is a significant find — always include these first.

2. **Major Indonesian networks (RCTI, SCTV, Indosiar, MNCTV, GTV, iNews, NET) are NOT freely available** — their streams require authentication (RCTI+, Vidio), DRM (Widevine/PlayReady), or are geo-blocked (Indonesia only). The `dens.tv` and `indihuy.streamized.net` DASH streams return 403/empty from outside Indonesia. Don't waste time testing these repeatedly.

3. **Local/regional channels are more accessible** — Padang TV, Batam TV, Bandung TV, Banten TV, BRTV, Caruban TV all have working public streams.

4. **MetroTV is reliable** — via `edge.medcom.id` CDN.

5. **Garuda TV, MBG TV, Indonesiana are bonus finds** — smaller channels with working streams.

6. **iptv-org repository is the best source** — regularly updated, community-maintained, country-specific lists.

7. **Streams go down without notice** — always implement "Report broken stream" button linking to Telegram contact.

8. **DASH/MPD streams don't work in HTML5 video** — need HLS.js or similar library. Stick to M3U8/HLS for browser compatibility.

9. **HTTP 200 ≠ working stream** — MUST validate response body contains `#EXTM3U` or `#EXT-X` headers.

10. **dens.tv CDN is unreliable** — most `op-group1-swiftservehd-1.dens.tv` streams return 403 or timeout. Don't rely on this source.

## Testing Batch Command

```bash
test_stream() {
  name=$1; url=$2
  response=$(curl -s -L --max-time 8 "$url" 2>/dev/null | head -5)
  if echo "$response" | grep -q "#EXTM3U\|#EXT-X"; then echo "✅ $name"
  else echo "❌ $name"; fi
}

test_stream "Trans7" "https://video.detik.com/trans7/smil:trans7.smil/index.m3u8"
test_stream "TransTV" "https://video.detik.com/transtv/smil:transtv.smil/index.m3u8"
test_stream "MetroTV" "https://edge.medcom.id/live-edge/smil:metro.smil/playlist.m3u8"
test_stream "tvOne" "http://202.80.222.20/cdn/iptv/Tvod/001/channel2000018/1024.m3u8"
test_stream "BeritaSatu" "https://xtdslboppkkv-pull.bpmedialive.com/live/beritasatu/abr.m3u8"
test_stream "BTV" "https://xtdslboppkkv-pull.bpmedialive.com/live/btv/abr.m3u8"
test_stream "GarudaTV" "https://hgmtv.com:19360/garudatvlivestreaming/garudatvlivestreaming.m3u8"
test_stream "MBG TV" "https://stream.convergen.co/mbg_stream/smil:mbStream.smil/playlist.m3u8"
test_stream "Indonesiana" "https://tvstreamcast.com/indonesiana.m3u8"
test_stream "Bandung TV" "http://202.150.153.254:65500/bandungtvWEBSITE.m3u8"
test_stream "Banten TV" "https://5bf7b725107e5.streamlock.net/bantentv/bantentv/playlist.m3u8"
test_stream "BRTV" "https://5bf7b725107e5.streamlock.net/brtv/brtv/playlist.m3u8"
test_stream "CarubanTV" "https://stream.carubantv.id/hls/0/stream.m3u8"
test_stream "Padang TV" "http://122.248.43.242:1935/PADANGTV/_definst_/myStream/playlist.m3u8"
test_stream "Batam TV" "http://122.248.43.242:1935/BATAMTV/_definst_/myStream/playlist.m3u8"
test_stream "Biznet Adventure" "http://livestream.biznetvideo.net/biznet_adventure/smil:adventure.smil/playlist.m3u8"
test_stream "Biznet Kids" "http://livestream.biznetvideo.net/biznet_kids/smil:kids.smil/index.m3u8"
test_stream "Biznet Lifestyle" "http://livestream.biznetvideo.net/biznet_lifestyle/smil:lifestyle.smil/index.m3u8"
test_stream "DW News" "https://dwamdstream102.akamaized.net/hls/live/2015525/dwstream102/index.m3u8"
test_stream "TRT World" "https://tv-trtworld.medya.trt.com.tr/master.m3u8"
test_stream "Red Bull TV" "https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8"
```

## User Expectations

When user asks for major channels (RCTI, SCTV, etc.):
1. **Explain WHY** they're not available (DRM, auth, geo-blocking)
2. **Suggest alternatives**: Official apps (RCTI+, Vidio.com) with Indonesian IP
3. **Show what IS working** — don't leave them with nothing
4. **Don't give up** — user expects "gaboleh menyerah kita punya banyak cara buat bypass" (never give up, we have many ways to bypass)
5. **Keep searching** — streams change frequently, check iptv-org repo updates regularly
6. **detik.com CDN is a gold mine** — Trans7 and TransTV work via `video.detik.com`. Always check this CDN first for other detik-owned channels.
