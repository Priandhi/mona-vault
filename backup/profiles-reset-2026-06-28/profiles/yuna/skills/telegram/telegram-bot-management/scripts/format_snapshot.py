#!/usr/bin/env python3
"""
YUNA — Telegram Plain-Text Formatter (full detail)
Style: rich per-symbol blocks (Pair, Side, Size, Entry, Mark, Lev, Margin, PnL, ROI).
Project: PROJECT VIOLET (was DOZERO; renamed 2026-06-16)

See SKILL.md in this directory for the full format spec.
"""
import hmac, hashlib, time, json
from urllib.parse import urlencode
import urllib.request


def load_keys(path):
    keys = {}
    with open(path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                keys[k] = v
    return keys


def signed_get(base, path, params, key, secret):
    params['timestamp'] = int(time.time() * 1000)
    params['recvWindow'] = 5000
    qs = urlencode(params)
    sig = hmac.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = f"{base}{path}?{qs}&signature={sig}"
    req = urllib.request.Request(url, headers={'X-MBX-APIKEY': key})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def fetch_testnet_snapshot():
    """Pull live testnet positions + today PnL + balance."""
    BASE = 'https://testnet.binancefuture.com'
    tk = load_keys('/home/ubuntu/dozero/config/.testnet_keys')

    pos = signed_get(BASE, '/fapi/v2/positionRisk', {}, tk['API_KEY'], tk['API_SECRET'])
    active = [p for p in pos if abs(float(p['positionAmt'])) > 0]

    today_start = int(time.mktime(time.strptime('2026-06-16', '%Y-%m-%d')) * 1000)
    inc = signed_get(BASE, '/fapi/v1/income',
                     {'startTime': today_start, 'limit': 1000},
                     tk['API_KEY'], tk['API_SECRET'])
    pnl_events = [x for x in inc if x.get('incomeType') == 'REALIZED_PNL']
    comm = sum(float(x['income']) for x in inc if x.get('incomeType') == 'COMMISSION')
    fund = sum(float(x['income']) for x in inc if x.get('incomeType') == 'FUNDING_FEE')
    gross = sum(float(x['income']) for x in pnl_events)
    net = gross + comm + fund
    wins = sum(1 for x in pnl_events if float(x['income']) > 0)
    losses = sum(1 for x in pnl_events if float(x['income']) < 0)
    wr = (wins / len(pnl_events) * 100) if pnl_events else 0

    bal = signed_get(BASE, '/fapi/v2/balance', {}, tk['API_KEY'], tk['API_SECRET'])
    usdt = next((b for b in bal if b['asset'] == 'USDT'), None)

    return {
        'active': active,
        'wins': wins,
        'losses': losses,
        'wr': wr,
        'gross': gross,
        'comm': comm,
        'fund': fund,
        'net': net,
        'balance': float(usdt['balance']) if usdt else 0,
        'available': float(usdt['availableBalance']) if usdt else 0,
    }


def icon_for_pnl(pnl):
    if pnl > 0:
        return '🟢'
    elif pnl < 0:
        return '🔴'
    return '⚪'


def format_qty(qty):
    """Format qty — integer if whole, else 2 decimals, with comma separator."""
    if qty == int(qty):
        return f'{int(qty):,}'
    return f'{qty:,.2f}'


def format_price(price):
    """Pick precision: <$1 = 5 decimals, <$100 = 4, else 2."""
    if price < 1:
        return f'${price:.5f}'
    elif price < 100:
        return f'${price:.4f}'
    else:
        return f'${price:.2f}'


def format_for_telegram(snapshot):
    """
    Format snapshot per the spec in SKILL.md.
    Per-symbol block: Pair, Side, Size, Entry, Mark, Lev, Margin, PnL, ROI.
    Sorted by uPnL descending. Always includes title + wallet line.
    """
    active = snapshot['active']
    out = []

    out.append('📊 PROJECT VIOLET — POSISI & PNL')
    out.append('')

    if not active:
        out.append('Tidak ada posisi aktif.')
        out.append('')
    else:
        rows = []
        total_u = 0.0
        total_margin = 0.0
        for p in active:
            amt = abs(float(p['positionAmt']))
            entry = float(p['entryPrice'])
            mark = float(p['markPrice'])
            lev = int(p['leverage'])
            upnl = float(p['unRealizedProfit'])
            margin = (amt * entry) / lev
            notional = amt * entry
            roe = (upnl / margin * 100) if margin > 0 else 0
            side = 'LONG' if float(p['positionAmt']) > 0 else 'SHORT'
            total_u += upnl
            total_margin += margin
            rows.append({
                'symbol': p['symbol'],
                'side': side,
                'qty': amt,
                'entry': entry,
                'mark': mark,
                'lev': lev,
                'margin': margin,
                'upnl': upnl,
                'roe': roe,
            })
        rows.sort(key=lambda r: -r['upnl'])

        for r in rows:
            icon = icon_for_pnl(r['upnl'])
            sym = r['symbol']
            # Pad header to 24 chars total
            header_left = f'━━━ {sym} '
            pad = 24 - len(header_left)
            if pad < 1:
                pad = 1
            out.append(f'{header_left}{"━" * pad}')
            out.append(f'  Pair    : {sym}')
            out.append(f'  Side    : {r["side"]} {icon}')
            out.append(f'  Size    : {format_qty(r["qty"])}')
            out.append(f'  Entry   : {format_price(r["entry"])}')
            out.append(f'  Mark    : {format_price(r["mark"])}')
            out.append(f'  Lev     : {r["lev"]}x')
            out.append(f'  Margin  : ${r["margin"]:.2f}')
            out.append(f'  PnL     : ${r["upnl"]:+,.2f} {icon}')
            out.append(f'  ROI     : {r["roe"]:+.2f}%')
            out.append('')

        total_roe = (total_u / total_margin * 100) if total_margin > 0 else 0
        sum_icon = icon_for_pnl(total_u)
        out.append(f'💰 TOTAL PnL : ${total_u:+,.2f} {sum_icon}')
        out.append(f'📊 TOTAL ROI : {total_roe:+.2f}% {sum_icon}')
        out.append('')
        out.append(f'💼 Wallet    : ${snapshot["balance"]:,.2f} USDT (avail ${snapshot["available"]:,.2f})')

    return '\n'.join(out)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == '--file':
        with open(sys.argv[2]) as f:
            snap = json.load(f)
    else:
        snap = fetch_testnet_snapshot()
    print(format_for_telegram(snap))
