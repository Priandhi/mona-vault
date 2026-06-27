#!/usr/bin/env python3
"""
YUNA — Close losers (Hexa 2026-06-16, opsi C)
Market reduceOnly close for all positions with uPnL < 0.
Winners (uPnL > 0) are left running.

Use case: when SL/TP cannot be placed (testnet -4045 exhaustion) and you want
a clean slate. Accepts the realized loss but stops the bleeding.

ALWAYS show the user the list of positions you plan to close (and the keep
list) BEFORE executing, so they can adjust with --keep.
"""
import hmac, hashlib, time, json, argparse, sys
from urllib.parse import urlencode
import urllib.request


def load_keys(p):
    return dict(line.strip().split('=', 1) for line in open(p) if '=' in line and not line.startswith('#'))


def signed_get(b, p, q, k, s):
    q['timestamp'] = int(time.time()*1000); q['recvWindow'] = 5000
    qs = urlencode(q); sig = hmac.new(s.encode(), qs.encode(), hashlib.sha256).hexdigest()
    r = urllib.request.Request(f'{b}{p}?{qs}&signature={sig}', headers={'X-MBX-APIKEY': k})
    return json.loads(urllib.request.urlopen(r, timeout=10).read())


def market_close(base, symbol, side, qty, key, secret):
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quantity': str(qty),
        'reduceOnly': 'true',
        'timestamp': int(time.time()*1000),
        'recvWindow': 5000,
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
    parser = argparse.ArgumentParser(description='Close all losing positions.')
    parser.add_argument('--keep', nargs='*', help='symbols to keep running even if losers (e.g. ADAUSDT PUMPBTCUSDT)')
    parser.add_argument('--dry-run', action='store_true', help='show what would be closed, do not execute')
    args = parser.parse_args()
    keep = set(s.upper() for s in (args.keep or []))

    BASE = 'https://testnet.binancefuture.com'
    tk = load_keys('/home/ubuntu/dozero/config/.testnet_keys')

    pos = signed_get(BASE, '/fapi/v2/positionRisk', {}, tk['API_KEY'], tk['API_SECRET'])
    active = [p for p in pos if abs(float(p['positionAmt'])) > 0]

    losers = [p for p in active if float(p['unRealizedProfit']) < 0 and p['symbol'] not in keep]
    winners = [p for p in active if float(p['unRealizedProfit']) >= 0 or p['symbol'] in keep]

    print('🅲️ YUNA — CLOSE ALL LOSERS (market reduceOnly)')
    if args.dry_run:
        print('   (DRY RUN — no orders placed)')
    print('')

    if winners:
        print(f'⏭️  KEEP RUNNING ({len(winners)} positions):')
        for p in winners:
            upnl = float(p['unRealizedProfit'])
            icon = '🟢' if upnl > 0 else '⚪'
            print(f'   {icon} {p["symbol"]:<13} PnL ${upnl:+.2f}')
        print('')

    if not losers:
        print('Nothing to close — all positions are winners or in keep-list.')
        return

    print(f'🔴 CLOSING ({len(losers)} losers):')
    total_realized = 0.0
    success = 0
    failed = 0
    for p in losers:
        sym = p['symbol']
        amt = abs(float(p['positionAmt']))
        upnl = float(p['unRealizedProfit'])
        side = 'SELL' if float(p['positionAmt']) > 0 else 'BUY'

        if args.dry_run:
            print(f'   [DRY] would close {sym:<13} {side} {amt}  (PnL ${upnl:+.2f})')
            total_realized += upnl
            success += 1
            continue

        result = market_close(BASE, sym, side, amt, tk['API_KEY'], tk['API_SECRET'])
        if result.get('_error'):
            print(f'   ❌ {sym:<13} PnL ${upnl:+.2f}  CLOSE FAILED: {result["msg"][:80]}')
            failed += 1
        else:
            total_realized += upnl
            success += 1
            print(f'   ✅ {sym:<13} PnL ${upnl:+.2f}  CLOSED @ {result.get("avgPrice", "?")}')
        time.sleep(0.2)

    print('')
    print(f'SUMMARY: ✅ {success} closed  |  ❌ {failed} failed')
    print(f'Realized PnL this batch: ${total_realized:+.2f}')


if __name__ == '__main__':
    main()
