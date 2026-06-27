#!/usr/bin/env bash
# Verify anime scraper is working end-to-end
# Usage: ./verify-scraper.sh <source-name>
# Example: ./verify-scraper.sh samehadaku

set -e

SOURCE="${1:-samehadaku}"
ICLIX_DIR="/home/ubuntu/iclix"
CACHE_FILE="$ICLIX_DIR/backend/services/cache/$SOURCE.json"
TUNNEL=$(curl -s "https://tunnel-watchdog/api/urls" 2>/dev/null || echo "")

if [ -z "$TUNNEL" ]; then
  # Fallback: read from local file
  TUNNEL=$(cat /tmp/tunnel-watchdog/urls.json 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); print([u for k,u in d.items() if 'iclix' in k.lower()][0])" 2>/dev/null || echo "http://127.0.0.1:3000")
fi

echo "=== $SOURCE Verification ==="
echo "Tunnel: $TUNNEL"
echo

# 1. Clear cache
echo "[1/4] Clearing cache..."
rm -f "$CACHE_FILE"

# 2. Run local scraper
echo "[2/4] Running local scraper..."
cd "$ICLIX_DIR/backend/services/anime-sources"
RESULT=$(timeout 90 node --input-type=module -e "
import { get${SOURCE^}List } from './${SOURCE}.js';
const r = await get${SOURCE^}List();
console.log('items=' + (r.items?.length || 0) + ',covers=' + (r.items || []).filter(i => i.cover).length + ',err=' + (r.error || 'none'));
")
echo "  → $RESULT"

# 3. Test detail + stream
echo "[3/4] Testing detail + stream..."
# Pick first item with URL
FIRST=$(python3 -c "
import json
d = json.load(open('$CACHE_FILE'))
items = d.get('_list', {}).get('items', [])
if items: print(items[0].get('url', ''))
")
if [ -n "$FIRST" ]; then
  echo "  First item: $FIRST"
  DETAIL=$(timeout 60 node --input-type=module -e "
import { get${SOURCE^}Anime } from './${SOURCE}.js';
const r = await get${SOURCE^}Anime('$FIRST', '');
console.log('title=' + (r.title || 'none') + ',eps=' + (r.episodes?.length || 0) + ',err=' + (r.error || 'none'));
" 2>&1)
  echo "  Detail: $DETAIL"
fi

# 4. Restart PM2 + verify via tunnel
echo "[4/4] Restarting iclix-api and verifying via tunnel..."
pm2 restart iclix-api 2>&1 | tail -1
sleep 3

if [ "$TUNNEL" != "http://127.0.0.1:3000" ]; then
  HTTP=$(curl -s -m 90 "$TUNNEL/api/anime/list" | python3 -c "
import sys, json
d = json.load(sys.stdin)
srcs = [s for s in d.get('sources', []) if s['source'] == '$SOURCE']
if srcs:
    s = srcs[0]
    cov = sum(1 for i in s.get('items', []) if i.get('cover'))
    print(f'source={s[\"source\"]},items={len(s.get(\"items\", []))},covers={cov}')
else:
    print('source_not_found')
")
  echo "  Tunnel API: $HTTP"
fi

echo
echo "=== Done ==="
