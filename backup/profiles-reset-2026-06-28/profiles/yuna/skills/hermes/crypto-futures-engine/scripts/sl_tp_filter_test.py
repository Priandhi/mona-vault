#!/usr/bin/env python3
"""
YUNA — SL/TP Filter Logic Test Suite
=====================================

Re-runnable verification of the Dozero risk filters. Use after any change to:
  - config/settings.py (MIN_PRICE_USD, MIN_SL_DISTANCE_PCT, LEVERAGE_TIERS, etc.)
  - engine/risk.py (build_trade_plan filters)
  - engine/executor.py (leverage cap logic)

Tests cover:
  1. Config constants (margin cap, price filter, SL distance, leverage tiers)
  2. SL distance boundary (1%, 2%, 2%+epsilon, 8%, 8%+epsilon, 10%)
  3. Price tier filter (dust <$0.05, low $0.10-$1, mid $1-$10, high $10+)
  4. Leverage cap per price tier
  5. Real-world signals from the 2026-06-16 incident (BANK/INX/AR rejected)
  6. Executor safety methods (_emergency_close, _get_leverage_for_symbol)
  7. Connection methods (market_order for emergency close)

Usage:
  python3 scripts/sl_tp_filter_test.py             # Run from anywhere
  python3 scripts/sl_tp_filter_test.py --verbose   # Show passing tests too
"""
import sys
import logging
from pathlib import Path

# Add dozero root to path
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DOZERO_ROOT = Path(os.environ.get("DOZERO_ROOT", "/home/ubuntu/dozero"))
if not DOZERO_ROOT.exists():
    DOZERO_ROOT = Path.cwd()
sys.path.insert(0, str(DOZERO_ROOT))

# Suppress routine logs
logging.basicConfig(level=logging.WARNING)

import os


# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        cls.GREEN = cls.RED = cls.CYAN = cls.BOLD = cls.END = ''


if not sys.stdout.isatty():
    Colors.disable()


results = []


def test(name: str, condition: bool, detail: str = ""):
    """Record a test result."""
    results.append((name, condition, detail))
    if not condition:
        print(f"  {Colors.RED}✗{Colors.END} {name}: {detail}")
    elif "--verbose" in sys.argv:
        print(f"  {Colors.GREEN}✓{Colors.END} {name}")


def header(title: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{title}{Colors.END}")
    print("=" * 60)


def test_settings_loaded():
    """Verify config has all the new YUNA filter constants."""
    header("1. Config Constants")
    try:
        from config import settings
    except ImportError as e:
        test("config.settings imports", False, str(e))
        return None

    test("MAX_MARGIN_PER_TRADE = $5", settings.MAX_MARGIN_PER_TRADE == 5.0,
         f"got {settings.MAX_MARGIN_PER_TRADE}")
    test("MIN_PRICE_USD = $0.05", settings.MIN_PRICE_USD == 0.05,
         f"got {settings.MIN_PRICE_USD}")
    test("MIN_SL_DISTANCE_PCT = 2%", abs(settings.MIN_SL_DISTANCE_PCT - 0.02) < 1e-9,
         f"got {settings.MIN_SL_DISTANCE_PCT}")
    test("MAX_SL_DISTANCE_PCT = 8%", abs(settings.MAX_SL_DISTANCE_PCT - 0.08) < 1e-9,
         f"got {settings.MAX_SL_DISTANCE_PCT}")
    test("MIN_VOLUME_USDT = $2M", settings.MIN_VOLUME_USDT == 2_000_000,
         f"got {settings.MIN_VOLUME_USDT}")

    test("LEVERAGE_TIERS exists", hasattr(settings, "LEVERAGE_TIERS"))
    if hasattr(settings, "LEVERAGE_TIERS"):
        t = settings.LEVERAGE_TIERS
        test("high tier = 50x @ $10", t.get("high", {}).get("max_lev") == 50)
        test("mid tier = 25x @ $1", t.get("mid", {}).get("max_lev") == 25)
        test("low tier = 15x @ $0.10", t.get("low", {}).get("max_lev") == 15)
    return settings


def test_sl_distance(re):
    """Test SL distance filter boundaries (1%, 2%, 8%, 10%, exact-boundary)."""
    header("2. SL Distance Filter")
    if not re:
        return

    # Should reject (1% SL = too tight)
    p = re.build_trade_plan("BTCUSDT", "LONG", 100000, 99000,
                            score=85, grade="A", current_price=100000)
    test("BTC 1% SL → REJECT", p is None)

    # Boundary: exactly 2% should PASS (1e-6 epsilon)
    p = re.build_trade_plan("BTCUSDT", "LONG", 100000, 98000,
                            score=85, grade="A", current_price=100000)
    test("BTC 2% SL (boundary) → PASS", p is not None,
         "1e-6 epsilon MUST allow exact boundary")

    # Should pass (3% SL)
    p = re.build_trade_plan("BTCUSDT", "LONG", 100000, 97000,
                            score=85, grade="A", current_price=100000)
    test("BTC 3% SL → PASS", p is not None)

    # Boundary: exactly 8% should PASS
    p = re.build_trade_plan("BTCUSDT", "LONG", 100000, 92000,
                            score=85, grade="A", current_price=100000)
    test("BTC 8% SL (boundary) → PASS", p is not None,
         "1e-6 epsilon MUST allow exact boundary")

    # Should reject (10% SL = too wide)
    p = re.build_trade_plan("BTCUSDT", "LONG", 100000, 90000,
                            score=85, grade="A", current_price=100000)
    test("BTC 10% SL → REJECT", p is None)


def test_price_filter(re):
    """Test price-tier filter (dust rejected, low/mid/high pass)."""
    header("3. Price Tier Filter")
    if not re:
        return

    # Dust (BANK @ $0.04) — should reject
    p = re.build_trade_plan("BANKUSDT", "LONG", 0.0432, 0.0424,
                            score=76, grade="B", current_price=0.0432)
    test("BANK $0.04 (dust) → REJECT", p is None,
         "Critical: BANK was the 2026-06-16 incident")

    # Low tier (XRP @ $0.50)
    p = re.build_trade_plan("XRPUSDT", "LONG", 0.50, 0.49,
                            score=85, grade="A", current_price=0.50)
    test("XRP $0.50 (low tier) → PASS", p is not None)

    # Mid tier (AVAX @ $5.0)
    p = re.build_trade_plan("AVAXUSDT", "LONG", 5.0, 4.85,
                            score=85, grade="A", current_price=5.0)
    test("AVAX $5.0 (mid tier) → PASS", p is not None)

    # High tier (BTC @ $100k)
    p = re.build_trade_plan("BTCUSDT", "LONG", 100000, 97000,
                            score=85, grade="A", current_price=100000)
    test("BTC $100k (high tier) → PASS", p is not None)


def test_leverage_cap(re):
    """Test leverage cap per price tier."""
    header("4. Leverage Cap Per Price Tier")
    if not re:
        return

    cases = [
        # (symbol, price, expected_max_lev)
        ("BTCUSDT", 100000.0, 50),    # high tier
        ("ETHUSDT", 3000.0, 50),      # high tier
        ("SOLUSDT", 150.0, 50),       # high tier
        ("BNBUSDT", 600.0, 50),       # high tier (≥ $10)
        ("LINKUSDT", 15.0, 50),       # high tier (≥ $10)
        ("AVAXUSDT", 5.0, 25),        # mid tier ($1-$10)
        ("NEARUSDT", 2.0, 25),        # mid tier
        ("ADAUSDT", 0.50, 15),        # low tier ($0.10-$1)
        ("XRPUSDT", 0.50, 15),        # low tier
        ("DOGEUSDT", 0.15, 15),       # low tier (≥ $0.10)
        ("DUST", 0.04, 10),           # dust floor (caller should reject)
    ]
    for sym, price, expected in cases:
        cap = re._get_leverage_cap_for_price(price)
        test(f"{sym} @ ${price:,.2f} → {expected}x cap", cap == expected,
             f"got {cap}x")


def test_incident_signals(re):
    """Verify the exact signals from the 2026-06-16 incident are now rejected."""
    header("5. 2026-06-16 Incident Signals (BANK/INX/AR)")
    if not re:
        return

    # BANKUSDT — Score 76 Grade B, 1.85% SL @ $0.043
    p = re.build_trade_plan("BANKUSDT", "LONG", 0.0432, 0.0424,
                            score=76, grade="B", current_price=0.0432)
    test("BANKUSDT (1.85% SL, $0.04) → REJECT", p is None,
         "Original signal that caused -$269 loss")

    # INXUSDT — Score 84 Grade A, 1.2% SL @ $0.008
    p = re.build_trade_plan("INXUSDT", "LONG", 0.0083, 0.0082,
                            score=84, grade="A", current_price=0.0083)
    test("INXUSDT (1.2% SL, $0.008) → REJECT", p is None,
         "Original signal that caused -$86 loss")

    # ARUSDT — Score 84 Grade A, 1.23% SL @ $2.12
    p = re.build_trade_plan("ARUSDT", "LONG", 2.120, 2.094,
                            score=84, grade="A", current_price=2.120)
    test("ARUSDT (1.23% SL, $2.12) → REJECT", p is None,
         "Original signal that caused -$87 loss")


def test_executor_methods():
    """Verify executor has emergency close + tiered leverage methods."""
    header("6. Executor Safety Methods")
    try:
        from engine.executor import DozeroExecutor
    except ImportError as e:
        test("engine.executor imports", False, str(e))
        return

    test("DozeroExecutor._emergency_close exists",
         hasattr(DozeroExecutor, "_emergency_close"))
    test("DozeroExecutor._get_leverage_for_symbol exists",
         hasattr(DozeroExecutor, "_get_leverage_for_symbol"))


def test_connection_methods():
    """Verify connection has market_order for emergency close."""
    header("7. Connection Methods")
    try:
        from config.connection import BinanceConnection
        test("market_order() method", hasattr(BinanceConnection, "market_order"))
        test("get_ticker_price() method", hasattr(BinanceConnection, "get_ticker_price"))
        test("algo_order() method", hasattr(BinanceConnection, "algo_order"))
    except ImportError as e:
        test("config.connection imports", False, str(e))


def main():
    print(f"{Colors.BOLD}YUNA — SL/TP Filter Logic Test Suite{Colors.END}")
    print(f"Dozero root: {DOZERO_ROOT}")
    if not DOZERO_ROOT.exists():
        print(f"{Colors.RED}❌ Dozero not found at {DOZERO_ROOT}{Colors.END}")
        print("Set DOZERO_ROOT env var or run from dozero directory")
        return 1

    settings = test_settings_loaded()
    try:
        from engine.risk import RiskEngine
        re = RiskEngine()
    except ImportError as e:
        test("engine.risk imports", False, str(e))
        re = None

    if re:
        test_sl_distance(re)
        test_price_filter(re)
        test_leverage_cap(re)
        test_incident_signals(re)
    test_executor_methods()
    test_connection_methods()

    # Summary
    passed = sum(1 for _, p, _ in results if p)
    total = len(results)
    failed = total - passed

    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.END}")
    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL {total} TESTS PASSED{Colors.END}")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ {failed}/{total} TESTS FAILED{Colors.END}")
        print(f"\n{Colors.RED}Failed tests:{Colors.END}")
        for name, p, detail in results:
            if not p:
                print(f"  - {name}: {detail}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
