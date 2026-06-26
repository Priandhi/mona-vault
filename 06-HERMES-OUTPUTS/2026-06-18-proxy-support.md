---
type: receipt
date: 2026-06-18
tags:
  - receipt
---

# 2026-06-18 — PROXY SUPPORT (YUNA)

## Task
Add HTTP/SOCKS proxy support to Dozero.X trading bot to avoid Binance rate limit ban (IP banned at 06:23 UTC for 5 min, lifted 06:28:50).

## Result
- ✅ Proxy support wired di `config/connection.py` (via `PROXY_URL` env var)
- ✅ Throttle 50ms between requests di `connection.py` (`_throttle()` method)
- ✅ XPL watch proxy support (`xpl_watch.py` get_xpl_state())
- ✅ PM2 ecosystem updated: `PROXY_URL=""` env slot ready
- ✅ dozero-auto restarted (PROXY_URL empty, awaiting Hexa input)
- ✅ Live test: throttle works (10 requests = 811ms dengan 50ms gap, expected ~500ms+overhead)
- ✅ Ban lifted 06:28:50 UTC, bot cycle resumed normal operation

## Decisions
- **Env var over hardcode:** `PROXY_URL` env var (HTTP/SOCKS) — flexible, no code change needed
- **Throttle as primary fix:** 50ms gap between requests = max 1200 req/min single-threaded. Binance limit = 2400 weight/min. Even with parallel workers, comfortably under limit.
- **XPL watch also got proxy support:** Previously used raw `requests.get()` bypassing connection layer, now respects `PROXY_URL`
- **Ecosystem config: empty PROXY_URL by default** — bot works without proxy, just uses throttle. If Hexa provides URL, restart picks it up.

## Issues
- Need actual proxy URL from Hexa to enable proxy mode. Options:
  - **Hexa provides private proxy** (best — fast, reliable, dedicated)
  - **Public free proxy** (risky — slow, often banned themselves, security risk)
  - **Skip proxy** (throttle alone might be enough — testnet 1-month focus, WR ratio more important than rate)

## Files Modified
- `/home/ubuntu/dozero/config/connection.py` — proxy + throttle
- `/home/ubuntu/dozero/ecosystem.config.json` — env var slot
- `/home/ubuntu/dozero/xpl_watch.py` — proxy support

## How to Enable Proxy
```bash
# Edit ecosystem config, set PROXY_URL value
nano /home/ubuntu/dozero/ecosystem.config.json
# Change "PROXY_URL": "" to "PROXY_URL": "http://user:pass@proxy:port"
# Then restart:
HOME=/home/ubuntu pm2 restart dozero-auto
```

Or inline (one-off):
```bash
HOME=/home/ubuntu PROXY_URL="http://..." python3 /home/ubuntu/dozero/auto.py
```

## Next Steps
1. Wait for Hexa to provide proxy URL (or confirm skip)
2. If proxy provided, restart and monitor first cycle
3. Testnet 1-month WR focus continues — proxy is preventive, not blocking

## Status
✅ DONE — proxy support ready, awaiting URL from Hexa
