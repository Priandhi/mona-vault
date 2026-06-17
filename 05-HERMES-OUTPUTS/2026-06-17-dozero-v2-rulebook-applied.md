# YUNA Receipt — 2026-06-17 16:38 — DOZERO.X v2 Rulebook Applied

**Task:** Apply DOZERO.X v2 Complete Rulebook (SMC + Order Flow integration)
**Result:** ✅ Config layer + grading + breakeven + format applied. Engine rewrite deferred (separate project).

## Applied Changes

### config/settings.py (BAB 11.1 + BAB 9.2 + BAB 10.3)
- **Risk Guards (BAB 11.1):**
  - `MAX_RISK_PCT = 0.02` (2% balance per trade = $86 cap)
  - `DAILY_LOSS_LIMIT_R = 3` (stop if -3R per day, replaces old $500 limit)
  - `MAX_DRAWDOWN_PCT = 0.15` (eval system if -15% balance)
- **v2 Grading (BAB 10.3):**
  - `CONFLUENCE_GRADING = {"ELITE": (7,9), "GOOD": (5,6), "WEAK": (3,4), "FAIL": (0,2)}`
  - `MINIMUM_CONFLUENCE_GRADE = "GOOD"` (only ELITE/GOOD execute)
- **Confluence Checklists (BAB 10.1/10.2):**
  - `CONFLUENCE_CHECKLIST_LONG` (9 items, 3 WAJIB + 3 KUAT + 2 PENDUKUNG + 1 KONFIRMASI)
  - `CONFLUENCE_CHECKLIST_SHORT` (9 items, mirror of LONG)
  - `CONFLUENCE_WAJIB_COUNT = 3`
- **Timeframes (BAB 9.2):**
  - `TIMEFRAMES = {"BIAS": "1d", "STRUCTURE": "4h", "EXECUTION": "1h", "PRECISION": "15m"}`
  - `ANALYSIS_TIMEFRAMES = ["1d", "4h", "1h", "15m"]`

### engine/scoring.py (BAB 10 — new class)
- `V2ConfluenceEngine` class with `evaluate(direction, item_results, details)` method
- `V2ConfluenceResult` dataclass (grade, tradeable, wajib_passed, reason)
- `ConfluenceItem` dataclass (name, tier, passed, detail)
- **Test results:**
  - 4/9 items = WEAK → NOT tradeable ✅
  - 9/9 items = ELITE → tradeable ✅
  - WAJIB fail = ELITE grade but NOT tradeable ✅

### engine/executor.py (BAB 13.1 + 13.2)
- `on_tp1_filled(symbol, entry_price, direction)` — move SL to entry on TP1 hit
- `trail_sl(symbol, current_sl, direction, swing_low, swing_high)` — structure-based trailing

### notifier.py (BAB 15.2)
- `send_v2_signal(signal, confluence_result)` — new format with Alasan breakdown
  - Struktur, Liquidity, OrderFlow, MTF lines
  - Score/9, Confidence (HIGH/MEDIUM), Risk %

## Pre-existing (matches v2 spec from earlier patches)
- DEFAULT_LEVERAGE = 20x ✅
- MARGIN_PER_TRADE_USD = $90 (range $75-115) ✅
- SL_DISTANCE_PCT = 4% (max 5%) ✅
- TP_RR_MULTIPLIERS = [1.0, 2.0, 3.0] ✅
- MIN_RR = 1.5 ✅
- validate_leverage_sl() in executor ✅
- Margin-based position sizing ✅
- R:R-based TP ✅

## Deferred to Separate Project
**SMC + Order Flow Engine Rewrite** (multi-day project):
- [ ] Real FVG detection (3-candle pattern)
- [ ] BOS/CHOCH detection
- [ ] IDM (Inducement) refinement
- [ ] Displacement detection
- [ ] Absorption detection (order flow)
- [ ] CVD divergence calculation
- [ ] Premium/Discount zone with Fibonacci 0-100%
- [ ] OI delta tracking
- [ ] Funding rate filter
- [ ] Spoofing/iceberg detection
- [ ] Full BAB 16 architecture: [DATA] → [COMPUTE] → [SIGNAL] → [LLM] → [EXEC]

## Live Status
- PM2 dozero-auto: online, 0 restarts, 30-min cycle
- Active position: SYNUSDT LONG (entry $0.054170, 20x, $90 margin)
- New trade: CROSSUSDT LONG limit order pending fill
- V2 confluence engine: tested 3/3 cases pass
- New format `send_v2_signal` ready for next signal

## File Locations
- Spec PDF: /home/ubuntu/dozero/docs/RULEBOOK_v2.pdf
- Spec MD: /home/ubuntu/dozero/docs/RULEBOOK_v2.md
- Backup pre-upgrade: /home/ubuntu/dozero.backup-20260617-163021
- Code changes: settings.py, scoring.py, executor.py, notifier.py

**Posisi:** SYNUSDT LONG + CROSSUSDT LONG (pending)
**PnL:** SYNUSDT ~+$0.05 unrealized
**Result:** ✅ Config layer 100% applied, engine rewrite scheduled
