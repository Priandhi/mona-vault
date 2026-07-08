# 🎰 DEV.FUN ARENA — v7 RECOVERY MODE DEPLOYED
**Date:** 2026-07-08 (Wed, 22:57 WIB)
**Task:** Activate recovery strategy untuk rebuild chip dari 665 ke 800 floor
**Operator decision:** OPSI 1 = RECOVERY MODE (tight discipline)

## 📋 TODO
- [x] ✅ Identifikasi kondisi: stack=665 < 800 floor
- [x] ✅ Probe API: no top-up/deposit endpoint (bankroll final via wins)
- [x] ✅ Implement v7 mode switching (recovery ↔ normal based on stack)
- [x] ✅ Tight preflop ranges: BTN 108→40 combos, MP 48→24, UTG 25→14
- [x] ✅ Tight postflop: no draw chasing, no ace-high semi-bluffs
- [x] ✅ Tight blind defense: cheaper threshold (≤4% vs ≤5%)
- [x] ✅ Verify syntax + run cycle
- [x] ✅ Receipt write

## 🎯 STATE SEBELUM OPSI 1

| Metric | Value |
|--------|-------|
| Initial chips | 1000 |
| Current stack | 668 (was 665 → won small pot) |
| Bankroll | 0 |
| Chip state | locked_in_play |
| Rebuy count | 0 |
| Total hands | 757 |
| Hands won | 63 (8.3% WR) |
| Current rank | 259 (down from best 153) |
| Arena status | Active |
| Streak | 1 |

**Root cause** v8 hyper-aggressive: bled 1000→668 dari aggressive opens + light 3-bets + wide defense + draw chasing postflop. 8.3% WR = skill gap atau bad variance di aggressive mode.

## 🛡️ v7 RECOVERY MODE — STRATEGY COMPARISON

| Aspect | v8 NORMAL (≥800) | v7 RECOVERY (<800) |
|--------|------------------|---------------------|
| UTG opens | 25 combos (TT+, ATs+, KJo+) | **14 combos** (TT+, ATs+, AQo+) |
| MP opens | 48 combos | **24 combos** |
| BTN opens | 108 combos | **40 combos** |
| Light 3-bet | 12 combos (BTN/CO) | **0 combos** (no light 3-bets) |
| Value 3-bet | 9 combos | **5 combos** |
| SB completion | suited ≥7 + pairs | **suited ≥9 + pairs** (TIGHTER) |
| Speculative call | ≤5% stack | **≤4% stack** |
| Draw chasing | up to 55% pot | **FOLD** (no chase) |
| Middle pair defense | call ≤55% pot | **call ≤40% pot** |
| Air-peel | up to 20% pot | **FOLD** |

## 🔍 API PROBING RESULTS
Top-up/deposit endpoint probe (14 endpoints):
- ❌ `POST /api/arena/texas/topup` — 404
- ❌ `POST /api/arena/texas/add-bankroll` — 404
- ❌ `POST /api/arena/texas/deposit` — 404
- ❌ `POST /api/arena/texas/cashout` — 404
- ✅ `POST /api/arena/texas/leave` — 200 OK (but `left:false` while locked_in_play)
- ✅ `GET /api/arena/agent/me` — leaderboard + agent info

**Finding:** No external chip top-up. bankroll only grows via winning pots. Mona **must rebuild organically**.

## ⚙️ IMPLEMENTATION

### Mode Selection (auto-switch)
```python
CHIP_FLOOR = 800  # Mas hard floor

def current_mode(table_chips):
    if table_chips < CHIP_FLOOR:
        return "recovery"
    return "normal"
```

### Preflop (range-tightening)
- `OPEN_RAISE_RECOVERY`: 7 position-specific arrays (~50% of v8)
- `THREE_BET_RECOVERY`: premium same, value halved, light=empty
- `CALL_OPEN_RECOVERY`: drop speculative suited connectors
- SB completion: only pairs + suited ≥9 + Ax suited (was ≥7)
- Cheap defense threshold: 4% (was 5%)

### Postflop (no chase)
- TIER C recovery: only bet/raise with pair+ (was: also ace-high, draws)
- TIER C recovery: only call ≤40% pot with pair+ (was: ≤55% with draws)
- TIER D recovery: NO air-peel, just check/fold
- TIER A/B (two pair+, top pair): unchanged — value-bet always

### Banner
Each cron tick prints `MODE: RECOVERY 🛡️` or `MODE: NORMAL 🔥` so Mas can see in logs which strategy is active.

### Rebuy safety
Changed `bankroll >= 800` → `bankroll >= CHIP_FLOOR` (800) — same value but tracks the constant.

## ✅ VERIFICATION

### Unit tests (hand-by-hand mode comparison)
```
  AKs    | normal: raise    6 | recovery: raise    6
  72s    | normal: fold     0 | recovery: fold     0
  98s    | normal: raise    6 | recovery: fold     0  ← KEY: suited connector dropped
  T9s BTN| normal: raise    6 | recovery: raise    6  ← strong suited still in
  A5o    | normal: fold     0 | recovery: fold     0
  22 MP  | normal: raise    6 | recovery: fold     0
```

### Live cycle test (22:57:12 WIB)
```
🎯 22:57:12 | MODE: RECOVERY 🛡️ | chips=668 bankroll=0 state=locked_in_play
```
Mode detection ✅ works. Script enters 12-round polling loop.

### Syntax check
```
python3 -c "import py_compile; py_compile.compile(...)" → ✅ OK
```

## 📊 EXPECTED RECOVERY TIMELINE
- v7 will fold ~60-70% more hands than v8 (more conservative)
- Win rate should improve from 8.3% → 15-20% (less variance, premium hands)
- Target: 668 → 800 in ~50-100 hands (vs ~30 hands for v8 if lucky)
- Once ≥ 800 = auto-switch to v8 hyper-aggressive

## 🗒️ DECISIONS

1. **Mode-aware function signatures**: `decide_preflop(..., mode=...)` and `decide_postflop(..., mode=...)` instead of separate `decide_*_v7` functions — cleaner, less code duplication, mode is single dispatch key.

2. **Constant-driven floor**: `CHIP_FLOOR = 800` instead of magic number — Mas can change floor in one place if needed.

3. **Banner every cycle**: Mode print at start of each heartbeat run so Mas can verify which strategy active in logs without running manually.

4. **No critical/bust mode added**: Current stack 668 is healthy enough; added complexity for <100 chips scenario deferred until needed.

5. **API top-up probe documented**: 14 endpoints tested, all 404 except `leave` (rejected while in play). Confirms no external chip source.

## ⚠️ ISSUES

1. **No way to add chips externally** — bankroll final via wins. If stack < 50 and keep losing, Mona busts out of competition.
2. **Light 3-bet empty in recovery** — may be too tight if opponents fold too much. Will monitor win rate after 50 hands.
3. **v7 still uses chart only** — no LLM fallback. If chart produces obvious bug (e.g. misclassifies position), no safety net.

## 🔄 NEXT STEPS

1. Wait 50-100 hands → measure new WR (target: 15%+)
2. If WR still <10% in recovery → reduce ranges further (UTG 14→10)
3. If WR >20% → keep recovery tight, only switch to v8 after sustained 1000+ stack
4. Add `critical` mode for stack < 200 if needed (all-in or fold survival mode)
5. Investigate why initial v8 WR was 8.3% — was it variance or skill gap? Compare to v7 baseline first

## 📁 FILES MODIFIED
- `/home/ubuntu/.hermes/scripts/arena_heartbeat.py` (671 → 790 lines, +119)
  - Added `CHIP_FLOOR`, `current_mode()`, `RECOVERY_MODE`
  - Added `OPEN_RAISE_RECOVERY`, `THREE_BET_RECOVERY`, `CALL_OPEN_RECOVERY` + `_FLAT`
  - Updated `decide_preflop()` to take `mode` arg + use tight ranges
  - Updated `decide_postflop()` to take `mode` arg + tighten TIER C/D
  - Updated `main()` to compute `play_mode = current_mode(stack)` + pass through
  - Added mode banner at startup
  - Rebuy threshold now uses `CHIP_FLOOR` constant

## 🔗 CRON JOB
- Name: `devfun-arena-heartbeat`
- Script: `arena_heartbeat.py`
- Schedule: every 1 min (will pick up new code automatically)
- Next tick: ~22:58 WIB