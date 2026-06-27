#!/usr/bin/env python3
"""
YUNA — Soft-Stop Monitor (Hexa 2026-06-16)
Runs every 5 minutes via cron. If any position has uPnL < -5% of margin,
close it via market reduceOnly.

This is a backup safety net since testnet max stop order limit = 1 per symbol.
Mainnet has higher limits, so SL algo orders will work there.

Usage: python3 yuna_soft_stop.py [--dry-run]
"""
import hmac, hashlib, time, json, sys, os
from urllib.parse import urlencode
import urllib.request
import argparse
from pathlib import Path


def load_keys(p):
    return dict(line.strip().split('=', 1) for line in open(p) if '=' in line and not line.startswith('#'))


def signed_get(b, p, q, k, s):
    """Signed GET to Binance API. Retries on transient HTTP errors (408/429/5xx)."""
    last_err = None
    for attempt in range(3):
        try:
            q['timestamp'] = int(time.time()*1000); q['recvWindow'] = 5000
            qs = urlencode(q); sig = hmac.new(s.encode(), qs.encode(), hashlib.sha256).hexdigest()
            r = urllib.request.Request(f'{b}{p}?{qs}&signature={sig}', headers={'X-MBX-APIKEY': k})
            return json.loads(urllib.request.urlopen(r, timeout=10).read())
        except urllib.error.HTTPError as e:
            last_err = e
            # Retry only on transient errors
            if e.code in (408, 429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** attempt)  # 1s, 2s backoff
                continue
            raise  # Non-retryable — bubble up
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise
    raise last_err  # All retries exhausted


def market_close(base, symbol, side, qty, key, secret):
    params = {
        'symbol': symbol, 'side': side, 'type': 'MARKET',
        'quantity': str(qty), 'reduceOnly': 'true',
        'timestamp': int(time.time()*1000), 'recvWindow': 5000,
    }
    qs = urlencode(params)
    sig = hmac.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = f"{base}/fapi/v1/order?{qs}&signature={sig}"
    req = urllib.request.Request(url, data=b'', method='POST', headers={'X-MBX-APIKEY': key})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {'_error': e.code, 'msg': e.read().decode()[:200]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help="Don't actually close, just report")
    parser.add_argument('--threshold', type=float, default=-0.05, help="Loss threshold (default -5%% of margin)")
    args = parser.parse_args()

    BASE = 'https://testnet.binancefuture.com'
    tk = load_keys('/home/ubuntu/dozero/config/.testnet_keys')

    pos = signed_get(BASE, '/fapi/v2/positionRisk', {}, tk['API_KEY'], tk['API_SECRET'])
    active = [p for p in pos if abs(float(p['positionAmt'])) > 0]

    if not active:
        # Silent = healthy
        return

    triggered = []
    for p in active:
        sym = p['symbol']
        amt = abs(float(p['positionAmt']))
        entry = float(p['entryPrice'])
        lev = int(p['leverage'])
        upnl = float(p['unRealizedProfit'])
        margin = (amt * entry) / lev
        loss_pct = upnl / margin if margin > 0 else 0

        if loss_pct <= args.threshold:
            triggered.append((p, upnl, margin, loss_pct, side_check := ('SELL' if float(p['positionAmt']) > 0 else 'BUY')))

    if not triggered:
        return  # Silent = no action

    # Build alert
    msg_lines = [f'🚨 YUNA SOFT-STOP TRIGGERED ({len(triggered)})']
    for p, upnl, margin, loss_pct, side in triggered:
        msg_lines.append(f'   {p["symbol"]:<13} uPnL ${upnl:+.2f}  loss {loss_pct*100:+.2f}%  margin ${margin:.2f}')

    if args.dry_run:
        msg_lines.append('')
        msg_lines.append('[DRY-RUN] No actual close performed')
        print('\n'.join(msg_lines))
        return

    # Execute closes
    for p, upnl, margin, loss_pct, side in triggered:
        amt = abs(float(p['positionAmt']))
        sym = p['symbol']
        result = market_close(BASE, sym, side, amt, tk['API_KEY'], tk['API_SECRET'])
        if result.get('_error'):
            msg_lines.append(f'   ❌ {sym}: close FAILED: {result["msg"][:80]}')
        else:
            avg = result.get('avgPrice', '?')
            msg_lines.append(f'   ✅ {sym} CLOSED @ {avg}  (saved from ${upnl:+.2f})')
        time.sleep(0.2)

    # Send via Telegram (Hermes home channel) — but stay silent if no telegram
    print('\n'.join(msg_lines))


if __name__ == '__main__':
    main()
