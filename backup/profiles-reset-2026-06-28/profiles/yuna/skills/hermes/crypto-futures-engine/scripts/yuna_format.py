"""
yuna_format.py — Telegram report formatter for PROJECT VIOLET
================================================================
APPROVED FORMAT (Hexa, 2026-06-16). Do NOT improvise the layout — the
field order, alignment, emoji placement, and section structure are
all locked in. See SKILL.md "Telegram Report Format (PROJECT VIOLET)".

Usage:
    from yuna_format import format_for_telegram
    msg = format_for_telegram(snapshots)
    send_message(msg)

Or run directly:
    python3 yuna_format.py
    (will fetch live positions via execution.BinanceFutures and print
     the formatted string to stdout for dry-run testing)
"""
from __future__ import annotations
from datetime import datetime
from typing import Any


# Field display order — DO NOT REORDER without explicit user sign-off
FIELD_ORDER = ['Pair', 'Side', 'Size', 'Entry', 'Mark', 'Lev', 'Margin', 'PnL', 'ROI']


def _fmt_value(field: str, value: Any, position_side: str = None) -> str:
    """Format a single field value with appropriate precision + emoji."""
    if value is None:
        return '—'

    if field == 'Side':
        return str(value).upper()

    if field == 'Size':
        return f"{value}"

    if field in ('Entry', 'Mark'):
        try:
            v = float(value)
            if v >= 1000:
                return f"{v:,.2f}"
            elif v >= 1:
                return f"{v:.4f}"
            elif v >= 0.01:
                return f"{v:.5f}"
            else:
                return f"{v:.7f}"
        except (ValueError, TypeError):
            return str(value)

    if field == 'Lev':
        try:
            return f"{int(float(value))}x"
        except (ValueError, TypeError):
            return str(value)

    if field == 'Margin':
        try:
            return f"${float(value):.2f}"
        except (ValueError, TypeError):
            return str(value)

    if field == 'PnL':
        try:
            v = float(value)
            emoji = '🟢' if v >= 0 else '🔴'
            sign = '+' if v >= 0 else ''
            return f"{sign}${v:.2f} {emoji}"
        except (ValueError, TypeError):
            return str(value)

    if field == 'ROI':
        try:
            v = float(value)
            emoji = '🟢' if v >= 0 else '🔴'
            sign = '+' if v >= 0 else ''
            return f"{sign}{v:.2f}% {emoji}"
        except (ValueError, TypeError):
            return str(value)

    return str(value)


def _format_symbol_block(snap: dict) -> str:
    """Format one position into the ━━━ SYMBOL ━━━ block."""
    symbol = snap.get('symbol', 'UNKNOWN')
    lines = [f"━━━ {symbol} ━━━"]

    # Determine side from positionAmt if not provided
    if 'Side' not in snap and 'positionAmt' in snap:
        amt = float(snap['positionAmt'])
        snap['Side'] = 'LONG' if amt > 0 else 'SHORT' if amt < 0 else 'FLAT'

    for field in FIELD_ORDER:
        if field in snap:
            lines.append(f"{field:<8}: {_fmt_value(field, snap[field])}")

    return '\n'.join(lines)


def format_for_telegram(snapshots: list[dict], tz_label: str = 'WIB') -> str:
    """
    Format position snapshots into the canonical Telegram message.

    Args:
        snapshots: list of dicts, each with keys matching FIELD_ORDER
                   (or raw Binance positionRisk dicts — auto-extracted)
        tz_label: timezone label, default 'WIB' (Hexa is Jakarta)

    Returns:
        Plain-text string ready to send via Telegram with parse_mode=""
    """
    # Normalize raw Binance positionRisk into our field schema
    normalized = []
    for snap in snapshots:
        if 'symbol' not in snap and 'Symbol' in snap:
            snap['symbol'] = snap['Symbol']
        if 'Pair' not in snap and 'symbol' in snap:
            snap['Pair'] = snap['symbol']

        amt = float(snap.get('positionAmt', 0))
        if amt == 0:
            continue  # skip flat positions

        # Map Binance fields
        if 'Entry' not in snap and 'entryPrice' in snap:
            snap['Entry'] = snap['entryPrice']
        if 'Mark' not in snap and 'markPrice' in snap:
            snap['Mark'] = snap['markPrice']
        if 'Lev' not in snap and 'leverage' in snap:
            snap['Lev'] = snap['leverage']
        if 'Margin' not in snap and 'initialMargin' in snap:
            snap['Margin'] = snap['initialMargin']
        if 'PnL' not in snap and 'unRealizedProfit' in snap:
            snap['PnL'] = snap['unRealizedProfit']

        # Derive ROI if missing
        if 'ROI' not in snap and 'PnL' in snap and 'Margin' in snap:
            try:
                margin = float(snap['Margin'])
                if margin > 0:
                    snap['ROI'] = (float(snap['PnL']) / margin) * 100
            except (ValueError, TypeError):
                pass

        # Derive Size
        if 'Size' not in snap and 'positionAmt' in snap:
            snap['Size'] = f"{abs(amt)}"

        normalized.append(snap)

    # Build header
    now = datetime.now()
    header = f"📊 PROJECT VIOLET — POSISI & PNL\n🕒 {now.strftime('%Y-%m-%d %H:%M')} {tz_label}"

    # Build per-symbol blocks
    blocks = [_format_symbol_block(s) for s in normalized]

    # Build summary
    total_pnl = 0.0
    total_margin = 0.0
    for s in normalized:
        try:
            total_pnl += float(s.get('PnL', 0))
            total_margin += float(s.get('Margin', 0))
        except (ValueError, TypeError):
            pass

    total_roi = (total_pnl / total_margin * 100) if total_margin > 0 else 0.0
    pnl_emoji = '🟢' if total_pnl >= 0 else '🔴'
    roi_emoji = '🟢' if total_roi >= 0 else '🔴'
    pnl_sign = '+' if total_pnl >= 0 else ''

    summary_lines = ["━━━━━━"]
    summary_lines.append(f"💰 TOTAL PnL  : {pnl_sign}${total_pnl:.2f} {pnl_emoji}")
    summary_lines.append(f"📊 TOTAL ROI  : {pnl_sign}{total_roi:.2f}% {roi_emoji}")
    summary_lines.append(f"💼 Wallet     : ${total_margin:.2f} margin used")
    summary_lines.append(f"🎯 Positions  : {len(normalized)} open")

    # Assemble
    parts = [header]
    if blocks:
        parts.append('')  # blank line after header
        parts.append('\n\n'.join(blocks))  # blank line between symbols
    parts.append('')
    parts.append('\n'.join(summary_lines))

    return '\n'.join(parts)


if __name__ == '__main__':
    # Dry-run with sample data
    sample_positions = [
        {
            'symbol': 'BTCUSDT',
            'positionAmt': 0.003,
            'entryPrice': 105250.50,
            'markPrice': 105418.20,
            'leverage': 50,
            'initialMargin': 6.32,
            'unRealizedProfit': 0.50,
        },
        {
            'symbol': 'ETHUSDT',
            'positionAmt': -0.05,
            'entryPrice': 3200.00,
            'markPrice': 3180.00,
            'leverage': 25,
            'initialMargin': 6.40,
            'unRealizedProfit': -1.00,
        },
    ]
    print(format_for_telegram(sample_positions))
