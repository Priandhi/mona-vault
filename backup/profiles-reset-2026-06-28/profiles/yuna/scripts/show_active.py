"""Show active setups: open orders + algos per symbol."""
import os, sys, urllib.request
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
from engine.binance_executor import _signed_request, get_position, get_balance
import json

# Symbols to inspect
symbols = ['VELVETUSDT', 'AGTUSDT', 'MITOUSDT']

balance = get_balance()
print(f"Balance: ${balance:.2f}\n", flush=True)

for sym in symbols:
    print(f"━━━ {sym} ━━━", flush=True)

    # Position
    pos = get_position(sym)
    if pos:
        amt = float(pos['positionAmt'])
        side = 'LONG' if amt > 0 else 'SHORT'
        pnl = float(pos['unRealizedProfit'])
        emoji = '🟢' if pnl >= 0 else '🔴'
        print(f"  POSITION: {side} {abs(amt):.4f} entry=${float(pos['entryPrice']):.4f} mark=${float(pos['markPrice']):.4f} pnl=${pnl:+.4f} {emoji}", flush=True)
    else:
        print(f"  POSITION: none", flush=True)

    # Open orders (LIMIT pending)
    orders = _signed_request('GET', '/fapi/v1/openOrders', {'symbol': sym})
    if isinstance(orders, list) and orders:
        for o in orders:
            print(f"  ORDER: {o.get('type')} {o.get('side')} qty={o.get('origQty')} @ {o.get('price')} status={o.get('status')}", flush=True)
    else:
        print(f"  ORDER: none", flush=True)

    # Open algos (SL/TP)
    algos = _signed_request('GET', '/fapi/v1/openAlgoOrders', {'symbol': sym})
    if isinstance(algos, list) and algos:
        for a in algos:
            print(f"  ALGO: {a.get('orderType'):20} {a.get('side')} qty={a.get('quantity')} @ ${a.get('triggerPrice')} status={a.get('algoStatus')}", flush=True)
    else:
        print(f"  ALGO: none", flush=True)

    # Last 3 orders (recent fills)
    history = _signed_request('GET', '/fapi/v1/allOrders', {'symbol': sym, 'limit': 3})
    if isinstance(history, list) and history:
        print(f"  RECENT:", flush=True)
        for h in history[:3]:
            print(f"    {h.get('time')} {h.get('type'):8} {h.get('side'):5} qty={h.get('origQty')} status={h.get('status')} avgPx=${h.get('avgPrice', '0')}", flush=True)
    print('', flush=True)