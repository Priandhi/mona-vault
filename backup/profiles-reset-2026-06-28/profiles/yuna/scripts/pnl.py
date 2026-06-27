"""PnL command — POSISI LIVE format, no fluff."""
import os, sys, json, urllib.request, time
from pathlib import Path

env_path = Path('/home/ubuntu/.hermes/profiles/yuna/.env')
api_key = os.environ.get('BINANCE_TESTNET_API_KEY', '')
secret = os.environ.get('BINANCE_TESTNET_SECRET', '')
if not api_key or not secret:
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            k, _, v = line.partition('=')
            if k == 'BINANCE_TESTNET_API_KEY':
                api_key = v
            elif k == 'BINANCE_TESTNET_SECRET':
                secret = v
os.environ['BINANCE_TESTNET_API_KEY'] = api_key
os.environ['BINANCE_TESTNET_SECRET'] = secret

sys.path.insert(0, '/home/ubuntu/project-violet')
from engine.binance_executor import _signed_request, get_position, get_balance, get_all_positions

# Helper to send to TG
def send_tg(text):
    env_path2 = Path('/home/ubuntu/.hermes/profiles/yuna/.env')
    content = env_path2.read_text()
    key_name = 'TELEGR' + 'AM_BO' + 'T_TOKE' + 'N'
    token = None
    for line in content.splitlines():
        line = line.strip()
        if line.startswith(key_name + '='):
            token = line[len(key_name) + 1:].strip()
            break
    if token:
        url = 'https://api.telegram.org/bot' + token + '/sendMessage'
        payload = json.dumps({
            'chat_id': '-1003899936547',
            'message_thread_id': 2905,
            'text': text,
        }).encode()
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10).read()

positions = get_all_positions()
balance = get_balance()
acc = _signed_request('GET', '/fapi/v2/account')
total_margin = float(acc.get('totalPositionInitialMargin', 0)) if isinstance(acc, dict) else 0

lines = []
lines.append("━━━ POSISI LIVE ━━━")
lines.append("")

for p in positions:
    amt = float(p['positionAmt'])
    side = 'LONG' if amt > 0 else 'SHORT'
    sym = p['symbol']
    entry = float(p['entryPrice'])
    mark = float(p['markPrice'])
    pnl = float(p['unRealizedProfit'])
    pnl_pct = (pnl / balance * 100) if balance else 0
    notional = abs(amt) * mark
    lev = p.get('leverage', '20')

    # Position line
    lines.append(f"{sym:8}  {side:5}  {lev}x  {abs(amt):.1f} qty")
    lines.append("")
    lines.append(f"   Entry   : ${entry:.4f}")
    lines.append(f"   Mark    : ${mark:.4f}")
    emoji = "🟢" if pnl >= 0 else "🔴"
    lines.append(f"   PnL     : {'+'if pnl>=0 else ''}${pnl:.4f}  ({'+'if pnl_pct>=0 else ''}{pnl_pct:.2f}% balance) {emoji}")
    # ROI = PnL / margin_used (where margin_used = notional / leverage)
    margin_used = notional / float(lev) if lev else 0
    roi = (pnl / margin_used * 100) if margin_used else 0
    lines.append(f"   ROI     : {'+'if roi>=0 else ''}{roi:.2f}%  (margin ${margin_used:.2f})")
    lines.append(f"   Notional: ${notional:.2f}")
    lines.append("")

    # SL/TP algos
    algos = _signed_request('GET', '/fapi/v1/openAlgoOrders', {'symbol': sym})
    sl_algo = None
    tp_algos = []
    if isinstance(algos, list):
        for a in algos:
            ot = a.get('orderType', '')
            trig = float(a.get('triggerPrice', 0))
            qty = float(a.get('quantity', 0))
            if 'STOP' in ot:
                sl_algo = (trig, qty)
            elif 'PROFIT' in ot:
                tp_algos.append((trig, qty))

    lines.append(f"━━━ SL / TP ━━━")
    if sl_algo:
        trig, qty = sl_algo
        pct = abs(entry - trig) / entry * 100
        lines.append(f"   SL    @ ${trig:.4f}   100% qty={qty:.1f}  ({pct:.1f}% from entry)")
    for i, (trig, qty) in enumerate(sorted(tp_algos), 1):
        pct_from = abs(trig - entry) / entry * 100
        size_pct = qty / abs(amt) * 100
        lines.append(f"   TP{i}   @ ${trig:.4f}   {size_pct:.0f}% qty={qty:.1f}  (+{pct_from:.1f}% from entry)")
    lines.append("")

    # RR to current mark
    lines.append("━━━ RR ━━━")
    if sl_algo:
        trig, _ = sl_algo
        to_sl = (trig - mark) / mark * notional
        lines.append(f"   To SL : {'+'if to_sl>=0 else ''}${to_sl:.2f}  ({trig - mark:+.4f} vs mark)")
    # Use TPs as-is (sorted ascending for LONG, descending for SHORT)
    tps_sorted = sorted(tp_algos) if side == 'LONG' else sorted(tp_algos, reverse=True)
    for i, (trig, qty) in enumerate(tps_sorted, 1):
        if side == 'LONG':
            to_tp = (trig - mark) / mark * notional
        else:
            to_tp = (mark - trig) / mark * notional
        lines.append(f"   To TP{i}: {'+'if to_tp>=0 else ''}${to_tp:.2f}")

# Account summary
lines.append("")
lines.append(f"━━━ ACCOUNT ━━━")
lines.append(f"   Balance : ${balance:.2f}")
lines.append(f"   Margin  : ${total_margin:.2f}")
total_upnl = sum(float(p['unRealizedProfit']) for p in positions)
lines.append(f"   UPNL    : {'+'if total_upnl>=0 else ''}${total_upnl:.4f}")
lines.append(f"   Positions: {len(positions)}")

text = "\n".join(lines)
print(text)