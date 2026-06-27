#!/usr/bin/env python3
"""
YUNA — Emergency SL placement (Hexa 2026-06-16 use case)
Tries to place 1 STOP_MARKET per active position at -pct from current mark.
Used when you discover existing positions are unprotected (no SL/TP placed).

WARNING (testnet): Binance testnet does NOT support algo order query/cancel
endpoints. If -4045 (Reach max stop order limit) fires, this script cannot
recover — you must close the unprotected positions manually. See:
  - companion script: scripts/close_losers.py
  - SKILL.md section "Emergency Recovery: Unprotected Positions"
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


def signed_post(base, path, params, key, secret):
    params['timestamp'] = int(time.time() * 1000)
    params['recvWindow'] = 5000
    qs = urlencode(params)
    sig = hmac.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = f"{base}{path}?{qs}&signature={sig}"
    req = urllib.request.Request(url, data=b'', method='POST', headers={'X-MBX-APIKEY': key})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {'_error': e.code, 'code': e.code, 'msg': e.read().decode()[:300]}


def get_mark_price(base, symbol, key, secret):
    params = {'symbol': symbol, 'timestamp': int(time.time()*1000)}
    qs = urlencode(params)
    sig = hmac.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = f"{base}/fapi/v1/premiumIndex?{qs}&signature={sig}"
    req = urllib.request.Request(url, headers={'X-MBX-APIKEY': key})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    return float(data['markPrice'])


def round_price(base, symbol, price, key, secret):
    params = {'symbol': symbol, 'timestamp': int(time.time()*1000)}
    qs = urlencode(params)
    sig = hmac.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = f"{base}/fapi/v1/exchangeInfo?{qs}&signature={sig}"
    req = urllib.request.Request(url, headers={'X-MBX-APIKEY': key})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    for s in data['symbols']:
        if s['symbol'] == symbol:
            for f in s['filters']:
                if f['filterType'] == 'PRICE_FILTER':
                    tick = float(f['tickSize'])
                    return round(round(price / tick) * tick, 10)
    return round(price, 5)


def main():
    parser = argparse.ArgumentParser(description='Place emergency SL on active positions.')
    parser.add_argument('--pct', type=float, default=0.02, help='SL distance from mark (default 0.02 = 2%%)')
    parser.add_argument('--dry-run', action='store_true', help='show what would be placed, do not execute')
    parser.add_argument('--losers-only', action='store_true', help='only place SL on losing positions')
    args = parser.parse_args()

    BASE = 'https://testnet.binancefuture.com'
    tk = load_keys('/home/ubuntu/dozero/config/.testnet_keys')

    params = {'timestamp': int(time.time()*1000), 'recvWindow': 5000}
    qs = urlencode(params); sig = hmac.new(tk['API_SECRET'].encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = f"{BASE}/fapi/v2/positionRisk?{qs}&signature={sig}"
    req = urllib.request.Request(url, headers={'X-MBX-APIKEY': tk['API_KEY']})
    with urllib.request.urlopen(req, timeout=10) as r:
        positions = json.loads(r.read())
    active = [p for p in positions if abs(float(p['positionAmt'])) > 0]
    if args.losers_only:
        active = [p for p in active if float(p['unRealizedProfit']) < 0]
    active.sort(key=lambda p: float(p['unRealizedProfit']))

    print('🛡️ YUNA — EMERGENCY SL PLACEMENT (-{:.0%} from mark)'.format(args.pct))
    if args.dry_run:
        print('   (DRY RUN — no orders placed)')
    print('')
    success = 0
    failed = 0
    for p in active:
        sym = p['symbol']
        amt = float(p['positionAmt'])
        is_long = amt > 0
        close_side = 'SELL' if is_long else 'BUY'
        current_pnl = float(p['unRealizedProfit'])

        try:
            mark = get_mark_price(BASE, sym, tk['API_KEY'], tk['API_SECRET'])
        except Exception as e:
            print(f'❌ {sym}: cannot get mark price ({e})')
            failed += 1
            continue

        sl_price_raw = mark * (1 - args.pct) if is_long else mark * (1 + args.pct)
        sl_price = round_price(BASE, sym, sl_price_raw, tk['API_KEY'], tk['API_SECRET'])

        if args.dry_run:
            print(f'[DRY] {sym:<13} mark=${mark:.4f}  SL=${sl_price}  (current PnL: ${current_pnl:+.2f})')
            success += 1
            continue

        result = signed_post(BASE, '/fapi/v1/algoOrder', {
            'algoType': 'CONDITIONAL',
            'symbol': sym,
            'side': close_side,
            'type': 'STOP_MARKET',
            'triggerPrice': str(sl_price),
            'closePosition': 'true',
            'workingType': 'MARK_PRICE',
            'timeInForce': 'GTE_GTC',
        }, tk['API_KEY'], tk['API_SECRET'])

        if result.get('_error') is None or 'algoId' in result:
            algo_id = result.get('algoId', '?')
            print(f'✅ {sym:<13} mark=${mark:.4f}  SL=${sl_price}  algoId={algo_id}  (PnL: ${current_pnl:+.2f})')
            success += 1
        else:
            code = result.get('code', '?')
            msg = result.get('msg', 'unknown')
            print(f'❌ {sym:<13} mark=${mark:.4f}  SL=${sl_price}  FAILED: code={code} {msg[:80]}')
            failed += 1

        time.sleep(0.2)

    print('')
    print(f'SUMMARY: ✅ {success} placed  |  ❌ {failed} failed')
    if failed > 0 and not args.dry_run:
        print('')
        print('⚠️ Some SLs failed. Common cause: -4045 (testnet max stop order limit exhausted).')
        print('   Recovery option: run scripts/close_losers.py to close the unprotected positions.')


if __name__ == '__main__':
    main()
