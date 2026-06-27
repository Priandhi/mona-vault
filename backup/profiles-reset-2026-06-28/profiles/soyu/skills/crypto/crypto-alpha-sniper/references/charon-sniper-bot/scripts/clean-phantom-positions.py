#!/usr/bin/env python3
"""
clean-phantom-positions.py — Remove phantom positions from data/positions.json

Phantoms are positions with entryPrice=0, solInvested=None/0, or tokenAmount=0.
These block new buys ("Max positions reached") and corrupt PnL.

Usage:
    python3 clean-phantom-positions.py [path/to/positions.json]
    # Default: data/positions.json (relative to CWD)

Output:
    Prints how many phantoms were removed and how many legit positions remain.
    Backs up to positions.json.backup-<timestamp> before writing.
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

def is_phantom(pos):
    """A position is a phantom if any of these are missing/invalid."""
    ep = pos.get('entryPrice', 0)
    sol = pos.get('solInvested', pos.get('entrySol', 0))
    tok = pos.get('tokenAmount', 0)
    return ep <= 0 or sol is None or sol <= 0 or tok <= 0

def main():
    fp = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/positions.json")
    if not fp.exists():
        print(f"❌ File not found: {fp}")
        sys.exit(1)

    # Backup first
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = fp.with_suffix(f"{fp.suffix}.backup-{ts}")
    shutil.copy(fp, backup)
    print(f"📦 Backup saved: {backup}")

    # Load
    try:
        data = json.loads(fp.read_text())
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {fp}: {e}")
        sys.exit(1)

    open_pos = data.get('open', [])
    if not open_pos:
        print(f"ℹ️  No open positions in {fp}")
        return

    # Filter
    phantoms = [p for p in open_pos if is_phantom(p)]
    legit = [p for p in open_pos if not is_phantom(p)]

    if not phantoms:
        print(f"✅ No phantoms found in {len(open_pos)} open positions")
        return

    # Report
    print(f"🔍 Found {len(phantoms)} phantom position(s) in {len(open_pos)} total:")
    for p in phantoms:
        sym = p.get('symbol', '??')
        ep = p.get('entryPrice', 0)
        sol = p.get('solInvested', 'None')
        tok = p.get('tokenAmount', 0)
        print(f"  ❌ {sym:10s} | ep={ep} | sol={sol} | tok={tok}")

    # Write
    data['open'] = legit
    fp.write_text(json.dumps(data, indent=2))
    print(f"\n✅ Removed {len(phantoms)} phantom(s), kept {len(legit)} legitimate position(s)")
    print(f"📝 {fp} updated. Backup at {backup}")
    print(f"\n🔄 Restart the bot to clear the in-memory slot counter.")

if __name__ == "__main__":
    main()
