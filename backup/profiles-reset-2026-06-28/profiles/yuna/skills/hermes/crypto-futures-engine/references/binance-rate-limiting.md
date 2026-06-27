# Binance Futures API Rate Limiting

## The Problem

Binance Futures API does NOT return HTTP 429 on rate limit violations. Instead, it issues a **full IP ban** lasting ~30 minutes.

### Ban Response Format
```json
{
  "code": -1003,
  "msg": "Way too many requests; IP(43.163.85.51) banned until 1780765249479. Please use the websocket for live updates to avoid bans."
}
```
- `1780765249479` = milliseconds timestamp (divide by 1000 for Unix epoch)
- Ban duration: typically 25-30 minutes

### How to Check Ban Status
```python
from datetime import datetime, timezone
ban_until_ms = 1780765249479
ban_time = datetime.fromtimestamp(ban_until_ms / 1000, tz=timezone.utc)
remaining_min = (ban_time - datetime.now(tz=timezone.utc)).total_seconds() / 60
```

## Safe API Call Settings

### Per-Cycle Budget (120s cycle)
| Call Type | Frequency | Calls/Cycle |
|-----------|-----------|-------------|
| Balance check | Every 300s | ~0.4 |
| Symbol price | Per symbol scan | 20 |
| Klines | Per symbol scan | 20 (cached 60s) |
| OI history | Per symbol scan | 20 (cached 30s) |
| Funding rate | Per symbol scan | 20 (cached 60s) |
| Agg trades | Per symbol scan | 20 (cached 10s) |
| Orderbook | Per symbol scan | 20 |
| **Total** | | **~20 fresh/cycle** |

### Implementation Pattern
```python
# In monitor_loop():
last_balance_check = 0

while self.running:
    now = time.time()
    
    # Balance: every 5 min only
    if now - last_balance_check > 300:
        await self._refresh_live_balance()
        last_balance_check = now
    
    # Symbol analysis with rate limiting
    for i, symbol in enumerate(self.config.symbols):
        if i > 0:
            await asyncio.sleep(0.5)  # 500ms between symbols
        
        analysis = await self.signals.analyze_symbol(symbol, self.config)
        # ... process analysis
    
    await asyncio.sleep(120)  # 2 min between full scans
```

### DataCollector Caching
Add TTL caching to `data.py` to avoid redundant API calls:
```python
class DataCollector:
    def __init__(self):
        self._cache = {}  # key -> (data, timestamp)
    
    async def _cached_get(self, key, url, params, ttl_sec):
        now = time.time()
        if key in self._cache:
            data, ts = self._cache[key]
            if now - ts < ttl_sec:
                return data
        data = await self._get(url, params)
        self._cache[key] = (data, now)
        return data
```

TTL values:
- Price: 5s
- Klines: 60s
- OI: 30s
- Funding: 60s
- Agg trades: 10s
- Orderbook: 5s (real-time critical)
- Fear & Greed: 300s (5 min, changes slowly)

## Recovery Procedure

If IP ban occurs:
1. Kill the running engine process
2. Wait for ban timestamp to expire (check with timestamp math)
3. Restart engine with reduced frequency
4. Set a one-shot cron job to auto-restart after ban expires

```bash
# Check if banned
python3 -c "
import hmac, hashlib, time, asyncio, aiohttp
from pathlib import Path
# ... sign request ...
# If response has code -1003, extract ban timestamp
"
```

## Comparison: Before vs After

| Setting | Before (caused ban) | After (safe) |
|---------|---------------------|--------------|
| Balance check | Every 30s | Every 300s |
| Scan interval | 30s | 120s |
| Symbol delay | None | 0.5s |
| API calls/cycle | ~100+ | ~20 |
| Caching | None | TTL-based |

## Transient Error Handling (Cron-Based Pollers)

Cron-driven scripts that hit the Binance API on a fixed schedule (e.g. soft-stop monitor every 5 min) will eventually hit transient errors. **Don't let one HTTP 408/429/5xx fail the entire cron and fire a Telegram alert every 5 minutes.**

### Common transient codes worth retrying
- `408 Request Timeout` — Binance server slow to respond
- `429 Too Many Requests` — soft rate limit, not a full IP ban
- `500/502/503/504` — server-side issues

### Retry pattern (urllib stdlib)

```python
def signed_get(b, p, q, k, s):
    """Signed GET with exponential backoff on transient errors."""
    last_err = None
    for attempt in range(3):
        try:
            q['timestamp'] = int(time.time() * 1000)
            q['recvWindow'] = 5000
            qs = urlencode(q)
            sig = hmac.new(s.encode(), qs.encode(), hashlib.sha256).hexdigest()
            r = urllib.request.Request(
                f'{b}{p}?{qs}&signature={sig}',
                headers={'X-MBX-APIKEY': k}
            )
            return json.loads(urllib.request.urlopen(r, timeout=10).read())
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (408, 429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** attempt)  # 1s, 2s backoff
                continue
            raise  # non-retryable — bubble up
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise
    raise last_err
```

**Why this matters for cron jobs:** Without retry, a single Binance blip causes a noisy Telegram "⚠️ Cron failed" alert every 5 minutes for the duration of the outage. With retry (1s + 2s), most blips resolve silently. Only genuine multi-attempt failures get reported.

**When NOT to retry:** `-1003 IP banned` — retrying just extends the ban window. Detect via the response body, not just HTTP status.
