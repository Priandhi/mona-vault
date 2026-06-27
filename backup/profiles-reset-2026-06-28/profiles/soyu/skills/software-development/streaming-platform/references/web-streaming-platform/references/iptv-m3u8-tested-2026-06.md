# IPTV M3U8 Stream Testing Results (2026-06-12, expanded 2026-06-13)

Content-validated M3U8 streams for Indonesian and international TV channels.
Sources: `https://iptv-org.github.io/iptv/countries/id.m3u` (country-specific) and `https://iptv-org.github.io/iptv/index.m3u` (full catalog, 2.4MB / 24k lines / 50k+ channels)

## Validation (MANDATORY)

```bash
test_stream() {
  name=$1; url=$2
  response=$(curl -s -L --max-time 8 "$url" 2>/dev/null | head -5)
  if echo "$response" | grep -q "#EXTM3U\|#EXT-X"; then echo "✅ $name - VALID HLS"
  else echo "❌ $name - NOT HLS"; fi
}
```

**Three-layer validation** (HTTP status alone is NOT enough — see pitfalls #19, #20):
1. **HTTP reachable** — `curl -sIL` returns 200 (not 000, not 404)
2. **Valid m3u8 content** — body starts with `#EXTM3U` or has `#EXT-X-STREAM-INF` (NOT HTML, NOT binary)
3. **Multi-variant (for adaptive bitrate)** — count of `#EXT-X-STREAM-INF` lines ≥ 2

```bash
# Comprehensive 3-layer check
url="https://example.com/stream.m3u8"
status=$(curl -sIL --max-time 8 -A "Mozilla/5.0" "$url" | grep -oE 'HTTP/1\.[01] [0-9]+|HTTP/2 [0-9]+' | tail -1)
body=$(curl -sL --max-time 8 -A "Mozilla/5.0" "$url" 2>/dev/null | head -c 1500)
if [[ "$body" == *"#EXTM3U"* || "$body" == *"#EXT-X"* ]]; then
  variants=$(echo "$body" | grep -c "#EXT-X-STREAM-INF")
  echo "✅ $status | variants=$variants | $url"
else
  echo "❌ $status | NOT m3u8 | $url | preview: $(echo $body | head -c 80)"
fi
```

## Discovery Workflow (Filter Full M3U by Keyword)

The full iptv-org index.m3u is 2.4MB / 24k lines. To find specific channels (e.g. World Cup broadcasters):

```bash
curl -sS -o /tmp/iptv.m3u https://iptv-org.github.io/iptv/index.m3u

# Build URL pairs (EXTINF + URL)
python3 << 'EOF'
import re
m3u = open('/tmp/iptv.m3u').read()
lines = m3u.split('\n')
channels = []
for i, line in enumerate(lines):
    if line.startswith('#EXTINF'):
        m = re.search(r',(.+)$', line)
        name = m.group(1).strip() if m else line[:60]
        for j in range(i+1, min(i+3, len(lines))):
            if lines[j].startswith('http'):
                channels.append((name, lines[j].strip()))
                break
# Filter for keywords
keywords = ['beIN', 'SPOTV', 'FIFA', 'Fox Sport', 'TVRI Sport']
matches = [c for c in channels if any(k in c[0] for k in keywords)]
# Dedup
seen = set(); out = []
for n, u in matches:
    if u not in seen: seen.add(u); out.append((n, u))
for n, u in out: print(f"{n}\t{u}")
EOF
```

Then pipe the URLs through the 3-layer validator above.

## Working Streams — World Cup 2026 (Jun 2026, validated 1080p+)

Piala Dunia 2026 sedang berlangsung (11 Jun – 19 Jul 2026). Stream terbaik yang verified live + valid m3u8:

| Channel | Resolusi | URL | CDN | Catatan |
|---|---|---|---|---|
| **beIN SPORTS XTRA** (EN) | 1080p, 7 variants | `https://bein-xtra-bein.amagi.tv/playlist.m3u8` | Amagi (Cloudflare) | ⭐ **Penyiar resmi FIFA** untuk US, free worldwide |
| **beIN Sports XTRA en Español** | 1080p, 4 variants | `https://dc1644a9jazgj.cloudfront.net/beIN_Sports_Xtra_Espanol.m3u8` | Cloudfront | Spanish commentary |
| **TVRI Sport HD** (ID) | 720p, 5 variants | `https://ott-balancer.tvri.go.id/live/eds/SportHD/hls/SportHD.m3u8` | TVRI Balancer | Free-to-air Indonesia |
| **TVRI Nasional** (ID) | 1080i, 5 variants | `https://ott-balancer.tvri.go.id/live/eds/Nasional/hls/Nasional.m3u8` | TVRI Balancer | Backup jika TVRI Sport down |
| **SPOTV** (ID) | 720p | `http://primestreams.tv:826/live/mookie22/49aV7nBsK4/119515.m3u8` | primestreams (3rd party) | Indonesia rights holder, **bisa mati sewaktu-waktu** |
| **SPOTV 2** (ID) | 1080p | `http://primestreams.tv:826/live/mookie22/49aV7nBsK4/119516.m3u8` | primestreams (3rd party) | Same as SPOTV, 1080p version |
| **Fox Sports 1** (US) | 1280p | `http://cdn12.henico.net:8080/live/gsctv/index.m3u8` | henico (3rd party) | Kemungkinan geo-blocked di luar US |

**Pilih strategi:**
- **Paling stabil:** beIN SPORTS XTRA (CDN profesional, official FIFA broadcaster)
- **Paling jernih:** SPOTV 2 1080p (kalau server hidup) atau beIN XTRA
- **Paling lengkap (ID context):** TVRI Sport HD + beIN XTRA (dual screen)

## Working Streams — Indonesia TV (10 verified, content-validated)

Indonesian (10): tvOne, BeritaSatu, BTV, Bandung TV, Banten TV, BRTV, Caruban TV, Biznet Adventure, Biznet Kids, Biznet Lifestyle

**Major Indonesian networks (RCTI, SCTV, Indosiar, Trans7) are NOT freely available** — behind auth/DRM atau geo-blocked dari IP VPS.

## Working Streams — International (3 verified, content-validated)

International (3): DW News, TRT World, Red Bull TV

## Sports Group Channels — Mostly Dead

The iptv-org "Sports" group has 100+ channels. Reality (validated 2026-06-13):
- Most "Sports" channels return 404 or stale URLs
- FIFA+ main URL (`d2w9q46ikgrcwx.cloudfront.net/...`) is 404 — catalog claims it, server gone
- The few that work: beIN XTRA, Fox Sports 1 (via 3rd party), SPOTV (id, 3rd party)
- **Don't trust the catalog** — always validate. Use the 3-layer check above.

## PITFALL: 3rd-Party Hosted Streams Die Often

Streams hosted on `primestreams.tv`, `henico.net`, `indihuy.streamized.net` are user-contributed and can vanish without notice. Real uptime is 50-70% in best case. Strategy:
- Always provide 2+ alternatives (free official + 3rd party)
- The "Featured/Pinned" card should go to the most stable stream (beIN XTRA, not SPOTV)
- Add a "Report broken stream" button that pings Telegram

See `streaming-platform-builder` skill's main SKILL.md for the React integration pattern + featured card CSS.
