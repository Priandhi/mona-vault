# HLS Proxy Implementation for Live TV

## Problem Summary

M3U8 streams from Indonesian CDNs have CORS restrictions. A naive backend proxy breaks because HLS manifests contain relative URLs that HLS.js resolves against the wrong base URL (the proxy URL instead of the original stream URL).

## Solution: Manifest URL Rewriting Proxy

The proxy intercepts manifest responses and rewrites all URLs to absolute proxied URLs. This works across all 3 HLS levels:

```
Master Manifest (level 1)
  ├── variant playlist A → /api/proxy?url=<absolute_url>
  └── variant playlist B → /api/proxy?url=<absolute_url>

Variant/Chunklist (level 2)
  ├── segment_001.ts → /api/proxy?url=<absolute_url>
  ├── segment_002.ts → /api/proxy?url=<absolute_url>
  └── segment_003.ts → /api/proxy?url=<absolute_url>

Segments (level 3)
  └── Raw video data (MPEG-TS) → piped through directly
```

## Complete Backend Proxy (server.js)

```javascript
import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import path from 'path';
import http from 'http';
import https from 'https';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(cors());
app.use(express.json());

// Serve frontend
app.use(express.static(path.join(__dirname, '../frontend/dist')));

// === LIVE TV PROXY (with manifest rewriting) ===
app.get('/api/proxy', async (req, res) => {
  const url = req.query.url;
  if (!url) return res.status(400).json({ error: 'Missing url param' });
  
  try {
    const protocol = url.startsWith('https') ? https : http;
    const parsedUrl = new URL(url);
    const domain = parsedUrl.hostname;
    const baseUrl = url.substring(0, url.lastIndexOf('/') + 1);
    
    const options = {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        'Referer': `https://${domain}/`,
        'Origin': `https://${domain}`
      },
      timeout: 10000,
    };
    
    const request = protocol.get(url, options, (stream) => {
      const contentType = stream.headers['content-type'] || '';
      const isManifest = contentType.includes('mpegurl') || 
                         contentType.includes('m3u8') || 
                         url.endsWith('.m3u8');
      
      if (isManifest) {
        let body = '';
        stream.on('data', chunk => body += chunk.toString());
        stream.on('end', () => {
          const rewritten = body.split('\n').map(line => {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith('#')) return line;
            
            let absoluteUrl;
            if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
              absoluteUrl = trimmed;
            } else {
              absoluteUrl = baseUrl + trimmed;
            }
            return `/api/proxy?url=${encodeURIComponent(absoluteUrl)}`;
          }).join('\n');
          
          res.setHeader('Content-Type', 'application/vnd.apple.mpegurl');
          res.setHeader('Access-Control-Allow-Origin', '*');
          res.setHeader('Cache-Control', 'no-cache');
          res.send(rewritten);
        });
        stream.on('error', (e) => res.status(500).json({ error: e.message }));
      } else {
        res.setHeader('Content-Type', contentType || 'video/mp2t');
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Cache-Control', 'public, max-age=5');
        stream.pipe(res);
      }
    });
    
    request.on('error', (e) => res.status(500).json({ error: e.message }));
    request.on('timeout', () => {
      request.destroy();
      res.status(504).json({ error: 'Timeout' });
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Catch-all for SPA
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/dist/index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => console.log(`Server running on port ${PORT}`));
```

## Frontend HLS.js Component

```jsx
import React, { useState, useRef, useEffect } from 'react'
import Hls from 'hls.js'

export default function LiveTV() {
  const [playing, setPlaying] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const videoRef = useRef(null)
  const hlsRef = useRef(null)

  useEffect(() => {
    if (!playing || !videoRef.current) return
    const video = videoRef.current
    const streamUrl = playing.stream // e.g., '/api/proxy?url=https://...'

    if (hlsRef.current) hlsRef.current.destroy()

    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 90,
        maxBufferLength: 30,
      })
      
      hls.loadSource(streamUrl)
      hls.attachMedia(video)
      
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setLoading(false)
        video.play().catch(e => console.log('Play error:', e))
      })
      
      hls.on(Hls.Events.FRAG_LOADED, () => {
        setLoading(false)
        setError(null)
      })
      
      hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              setTimeout(() => hls.startLoad(), 2000) // Retry
              break
            case Hls.ErrorTypes.MEDIA_ERROR:
              hls.recoverMediaError()
              break
            default:
              setError('Stream tidak bisa diputar. Coba channel lain.')
              setLoading(false)
              hls.destroy()
              break
          }
        }
      })
      
      hlsRef.current = hls
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = streamUrl
      video.addEventListener('loadedmetadata', () => {
        setLoading(false)
        video.play().catch(e => console.log('Play error:', e))
      })
    }

    return () => {
      if (hlsRef.current) { hlsRef.current.destroy(); hlsRef.current = null }
    }
  }, [playing])
}
```

## Tested Working Channels (2026-06-13)

All validated with: HTTP 200 + body contains `#EXTM3U` or `#EXT-X`.

### Channel Besar (Major Networks)
| Channel | Stream URL | Category |
|---------|-----------|----------|
| Trans7 | `https://video.detik.com/trans7/smil:trans7.smil/index.m3u8` | hiburan |
| Trans TV | `https://video.detik.com/transtv/smil:transtv.smil/index.m3u8` | hiburan |
| MetroTV | `https://edge.medcom.id/live-edge/smil:metro.smil/playlist.m3u8` | berita |
| tvOne | `http://202.80.222.20/cdn/iptv/Tvod/001/channel2000018/1024.m3u8` | berita |

### Berita (News)
| Channel | Stream URL |
|---------|-----------|
| BeritaSatu | `https://xtdslboppkkv-pull.bpmedialive.com/live/beritasatu/abr.m3u8` |
| BTV | `https://xtdslboppkkv-pull.bpmedialive.com/live/btv/abr.m3u8` |

### Hiburan (Entertainment)
| Channel | Stream URL |
|---------|-----------|
| Garuda TV | `https://hgmtv.com:19360/garudatvlivestreaming/garudatvlivestreaming.m3u8` |
| MBG TV | `https://stream.convergen.co/mbg_stream/smil:mbStream.smil/playlist.m3u8` |
| Indonesiana | `https://tvstreamcast.com/indonesiana.m3u8` |

### Lokal Daerah (Regional)
| Channel | Stream URL |
|---------|-----------|
| Bandung TV | `http://202.150.153.254:65500/bandungtvWEBSITE.m3u8` |
| Banten TV | `https://5bf7b725107e5.streamlock.net/bantentv/bantentv/playlist.m3u8` |
| BRTV | `https://5bf7b725107e5.streamlock.net/brtv/brtv/playlist.m3u8` |
| Caruban TV | `https://stream.carubantv.id/hls/0/stream.m3u8` |
| Padang TV | `http://122.248.43.242:1935/PADANGTV/_definst_/myStream/playlist.m3u8` |
| Batam TV | `http://122.248.43.242:1935/BATAMTV/_definst_/myStream/playlist.m3u8` |
| Balikpapan TV | `http://122.248.43.242:1935/BALIKPAPANTV/_definst_/myStream/playlist.m3u8` |
| Banjar TV | `https://banjartv.siar.us/banjartv/live/playlist.m3u8` |
| AFBTV Kupang | `https://afbtv.siar.us/live/afbtv.m3u8` |

### Agama (Religious)
| Channel | Stream URL |
|---------|-----------|
| Al-Iman TV | `https://tv.aliman.id/aliman/live.m3u8` |
| Alwafa Tarim TV | `https://ammedia.siar.us/ammedia/live/playlist.m3u8` |
| Angel TV Indonesia | `https://janya-digimix.akamaized.net/vglive-sk-234616/indonesia/ngrp:angelindonesia_all/playlist.m3u8` |
| Ashiil TV | `https://wahyu1ptv.pages.dev/AshiilTV-HD.m3u8` |
| Astha TV | `https://hgmtv.com:19360/asthatv/asthatv.m3u8` |

### Lifestyle
| Channel | Stream URL |
|---------|-----------|
| Biznet Adventure | `http://livestream.biznetvideo.net/biznet_adventure/smil:adventure.smil/playlist.m3u8` |

## Dead Streams (Confirmed NOT Working 2026-06-13)

| Channel | Reason |
|---------|--------|
| Kilisuci TV | 404 Not Found |
| Biznet Kids | Returns non-HLS content |
| Biznet Lifestyle | Connection timeout |
| RCTI, SCTV, Indosiar | DRM/geo-blocked — NOT embeddable |

## Verification Script

```bash
#!/bin/bash
# Test all streams for valid HLS content
declare -A STREAMS
STREAMS=(
  ["Trans7"]="https://video.detik.com/trans7/smil:trans7.smil/index.m3u8"
  ["TransTV"]="https://video.detik.com/transtv/smil:transtv.smil/index.m3u8"
  ["MetroTV"]="https://edge.medcom.id/live-edge/smil:metro.smil/playlist.m3u8"
  # ... add all channels
)

for name in "${!STREAMS[@]}"; do
  url="${STREAMS[$name]}"
  status=$(curl -sL -o /dev/null -w "%{http_code}" --max-time 5 "$url")
  if [ "$status" = "200" ]; then
    content=$(curl -sL --max-time 5 "$url" | head -3)
    if echo "$content" | grep -q "#EXTM3U\|#EXT-X"; then
      echo "✅ $name: HLS valid"
    else
      echo "❌ $name: HTTP 200 but NOT HLS"
    fi
  else
    echo "❌ $name: HTTP $status"
  fi
done
```

## Key Insights

1. **detik.com CDN is a goldmine** — Trans7 and TransTV stream via `video.detik.com` with no auth required. These are major commercial channels.

2. **Indonesian regional channels are accessible** — Many use Wowza Streaming Engine (`*.streamlock.net`) or `siar.us` CDN with no geo-blocking.

3. **Channel besar (RCTI, SCTV, Indosiar) are NOT embeddable** — They use DRM (Widevine/PlayReady) and geo-blocking. Don't waste time trying.

4. **Streams die without notice** — Build a "Report broken stream" button. Don't promise 100% uptime.

5. **Browser testing is mandatory** — curl validates the proxy chain, but only browser testing confirms HLS.js actually plays video. Always click a channel and verify video renders.
