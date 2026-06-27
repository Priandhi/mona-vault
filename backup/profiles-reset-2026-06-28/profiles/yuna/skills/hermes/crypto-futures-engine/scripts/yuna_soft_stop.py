"""
yuna_soft_stop.py — Cron-based soft-stop monitor for Binance futures positions
================================================================================
Purpose: When SL/TP algo orders cannot be placed (testnet -4045 lock, exchange
issues), positions sit unprotected. Testnet does NOT auto-liquidate, so floating
loss can grow to -256% ROE. This script is the safety net.

Logic:
1. Poll /fapi/v2/positionRisk via shared BinanceFutures client
2. For each open position, compute uPnL / margin ratio
3. If ratio < THRESHOLD (default -5%), close via market reduceOnly
4. Send single Telegram alert with closed positions
5. Silent when healthy (no spam)

Install:
  python3 ~/.hermes/profiles/yuna/scripts/install_soft_stop_cron.py

Run standalone (dry-run, prints only, no closes):
  python3 yuna_soft_stop.py --dry-run
"""
from __future__ import annotations
import argparse
import asyncio
import sys
from pathlib import Path

# Add scripts dir to path for shared execution client
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

THRESHOLD_DEFAULT = -0.05  # -5% of margin


async def _fetch_positions(client) -> list[dict]:
    """Fetch all open positions from Binance."""
    return await client.get_positions()


def _filter_for_soft_stop(positions: list[dict], threshold: float) -> list[dict]:
    """Return positions whose uPnL/margin ratio is below threshold."""
    triggered = []
    for p in positions:
        amt = float(p.get('positionAmt', 0))
        if amt == 0:
            continue
        margin = float(p.get('initialMargin', 0))
        if margin == 0:
            continue
        upnl = float(p.get('unRealizedProfit', 0))
        ratio = upnl / margin
        if ratio < threshold:
            triggered.append({**p, '_ratio': ratio, '_upnl': upnl})
    return triggered


async def _close_positions(client, positions: list[dict]) -> list[dict]:
    """Close each position via market reduceOnly."""
    results = []
    for p in positions:
        amt = float(p['positionAmt'])
        side = 'SELL' if amt > 0 else 'BUY'
        qty = abs(amt)
        try:
            result = await client.market_order(
                symbol=p['symbol'],
                side=side,
                quantity=qty,
                reduce_only=True,
            )
            results.append({
                'symbol': p['symbol'],
                'side': 'LONG' if amt > 0 else 'SHORT',
                'qty': qty,
                'upnl': p['_upnl'],
                'ratio': p['_ratio'],
                'orderId': result.get('orderId'),
                'ok': 'orderId' in result or 'clientOrderId' in result,
            })
        except Exception as e:
            results.append({
                'symbol': p['symbol'],
                'side': 'LONG' if amt > 0 else 'SHORT',
                'qty': qty,
                'upnl': p['_upnl'],
                'ratio': p['_ratio'],
                'error': str(e),
                'ok': False,
            })
    return results


def _format_alert(closed: list[dict]) -> str:
    """Format the Telegram alert message for closed positions."""
    lines = ["🚨 SOFT-STOP TRIGGERED"]
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    for c in closed:
        sign = '+' if c['upnl'] >= 0 else ''
        ratio_pct = c['ratio'] * 100
        if c.get('ok'):
            status = f"closed @ orderId={c['orderId']}"
        else:
            status = f"FAILED: {c.get('error', 'unknown')}"
        lines.append(
            f"  {c['symbol']} {c['side']} qty={c['qty']}"
            f" | uPnL {sign}${c['upnl']:.2f} ({ratio_pct:.1f}%)"
            f" | {status}"
        )
    return '\n'.join(lines)


async def _send_telegram(msg: str) -> None:
    """Send message via Telegram. Best-effort — log if fails."""
    try:
        # Import here to avoid hard dep at module load
        from telegram import send_message
        send_message(msg)
    except Exception as e:
        print(f"[soft-stop] Telegram send failed: {e}", file=sys.stderr)
        print(f"[soft-stop] Message was:\n{msg}")


async def run(threshold: float = THRESHOLD_DEFAULT, dry_run: bool = False) -> int:
    """
    Main soft-stop routine.

    Returns:
        Number of positions closed (0 if healthy).
    """
    try:
        from execution import BinanceFutures
    except ImportError:
        print("[soft-stop] ERROR: execution.BinanceFutures not available", file=sys.stderr)
        return 0

    client = BinanceFutures()
    try:
        positions = await _fetch_positions(client)
    except Exception as e:
        print(f"[soft-stop] ERROR fetching positions: {e}", file=sys.stderr)
        return 0

    triggered = _filter_for_soft_stop(positions, threshold)
    if not triggered:
        return 0  # healthy — silent

    if dry_run:
        print(f"[soft-stop] DRY-RUN: would close {len(triggered)} positions:")
        for t in triggered:
            print(f"  {t['symbol']} uPnL=${t['_upnl']:.2f} ratio={t['_ratio']*100:.1f}%")
        return len(triggered)

    closed = await _close_positions(client, triggered)
    alert = _format_alert(closed)
    await _send_telegram(alert)
    return len(closed)


def main():
    parser = argparse.ArgumentParser(description='Soft-stop monitor for Binance futures')
    parser.add_argument(
        '--threshold', type=float, default=THRESHOLD_DEFAULT,
        help=f'uPnL/margin ratio threshold (default: {THRESHOLD_DEFAULT} = -5%%)'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Print what would be closed without actually closing'
    )
    args = parser.parse_args()

    closed_count = asyncio.run(run(threshold=args.threshold, dry_run=args.dry_run))
    sys.exit(0 if closed_count >= 0 else 1)


if __name__ == '__main__':
    main()
