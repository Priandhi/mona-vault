#!/usr/bin/env bash
# discover-and-validate-iptv.sh — Find live m3u8 streams in iptv-org catalog
# Usage: ./discover-and-validate-iptv.sh [keyword1 keyword2 ...]
# No args = scan all sports/football/world cup related keywords

set -e

M3U_URL="https://iptv-org.github.io/iptv/index.m3u"
M3U_FILE="/tmp/iptv.m3u"
OUT="/tmp/iptv_results.tsv"

if [ $# -eq 0 ]; then
  KEYWORDS=("beIN" "SPOTV" "FIFA" "Fox Sport" "TVRI Sport" "ESPN" "World Cup" "Piala Dunia")
else
  KEYWORDS=("$@")
fi

echo "=== Downloading iptv-org catalog ==="
curl -sS -o "$M3U_FILE" --max-time 60 "$M3U_URL" 2>&1 | tail -1 || true
ls -lh "$M3U_FILE"
echo

echo "=== Filter + 3-Layer Validate (HTTP 200 + #EXTM3U body + variant count) ==="
echo

# Single Python script does the whole pipeline
python3 - "$M3U_FILE" "$OUT" "${KEYWORDS[@]}" <<'PYEOF'
import sys, re, urllib.request, urllib.error

m3u_path, out_path = sys.argv[1], sys.argv[2]
keywords = [k.lower() for k in sys.argv[3:]]

m3u = open(m3u_path).read()
lines = m3u.split('\n')

# Parse (name, url) pairs from EXTINF + URL
channels = []
for i, line in enumerate(lines):
    if line.startswith('#EXTINF'):
        m = re.search(r',(.+)$', line)
        name = m.group(1).strip() if m else line[:60]
        for j in range(i+1, min(i+3, len(lines))):
            if lines[j].startswith('http'):
                channels.append((name, lines[j].strip()))
                break

# Filter by keywords
seen = set()
candidates = []
for n, u in channels:
    if u in seen: continue
    seen.add(u)
    if any(k in n.lower() for k in keywords):
        candidates.append((n, u))

print(f"Found {len(candidates)} candidate channels. Validating each...")
print()

results = []
for name, url in candidates:
    # Layer 1: HTTP
    try:
        req = urllib.request.Request(url, method='HEAD', headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36'
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            status = r.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception:
        status = 0

    if status != 200:
        print(f"❌ HTTP {status} | {name}")
        continue

    # Layer 2 + 3: fetch body, check m3u8 + count variants
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36'
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read(2000).decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"❌ HTTP 200 but body fetch failed: {str(e)[:60]} | {name}")
        continue

    if '#EXTM3U' not in body and '#EXT-X' not in body:
        preview = body[:60].replace('\n', ' ')
        print(f"❌ HTTP 200 but NOT m3u8 | {name} | preview: {preview}")
        continue

    variants = body.count('#EXT-X-STREAM-INF')
    inf = body.count('#EXTINF')
    print(f"✅ HTTP 200 | variants={variants} | inf={inf} | {name}")
    results.append((name, url, variants))

# Save for downstream piping
with open(out_path, 'w') as f:
    for name, url, v in results:
        f.write(f"{name}\t{url}\t{v}\n")

print()
print(f"=== {len(results)} working streams saved to {out_path} ===")
print()
print("To use in LiveTV.jsx, copy ✅ lines and add to TV_CHANNELS array:")
print(f"  cat {out_path} | column -t -s $'\\t'")
PYEOF

chmod +x scripts/discover-and-validate-iptv.sh
echo
echo "=== To run: bash scripts/discover-and-validate-iptv.sh ==="
echo "=== With custom keywords: bash scripts/discover-and-validate-iptv.sh 'beIN' 'CNN' 'Al Jazeera' ==="
