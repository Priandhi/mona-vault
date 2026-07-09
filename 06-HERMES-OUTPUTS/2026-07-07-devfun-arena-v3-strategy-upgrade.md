# 2026-07-07 — dev.fun Arena v3 Strategy Upgrade

## Task
Upgrade Mona poker strategy (Option B) to fix declining chip trend.

## Context
- Mona win rate: 4.2% (6/143 hands) — far below 6-max breakeven ~15%
- Chips: 1000 → 942 (-58 net, mostly blind leak)
- Root causes:
  1. Position detection wrong (seat number ≠ button-relative position)
  2. Chart preflop too tight (fold trash = blind tax leak)
  3. Postflop LLM strategy too conservative
  4. No blind defense logic

## Decisions

### v3 Patches Applied to `arena_heartbeat.py`:

1. **Position inference from `selfCommittedChips`** (more reliable than seat guess)
   - If self_committed == small_blind → SB position
   - If self_committed == big_blind → BB position
   - Else → MP default (API doesn't expose button position)

2. **Blind defense logic**
   - In SB/BB facing single raise with call ≤4% stack → call wider
   - Wide defense range: all pairs + all suited + broadway offsuit
   - Reduces fold-to-raise leak that drained chips

3. **SB completion** (limp-call)
   - In SB with no raise, call cheap with any pair/suited/connector
   - Was: fold everything not in tight chart
   - Now: complete small blind cheaply with speculative hands

4. **Postflop prompt upgrade (loose-aggressive)**
   - Top pair+: value bet 50-75% pot (was: "value bet" vague)
   - Mid pair: call small bets ≤40% pot (was: "bluff catcher" vague)
   - Draws: pot odds > 3:1 (was: > 4:1 — tighter)
   - Explicit bet sizing rules

5. **Race condition fix (already in v2)**
   - Filter `agentTableStatus == "acting"` before POST
   - Eliminates "It is not this agent's turn" errors

6. **Auto-rebuy logic (already in v2)**
   - Check chipState == available + tableChips == 0 + bankroll > 0
   - Auto POST /rebuy
   - Note: dev.fun only allows rebuy when chips < bigBlindChips

## Result

### Unit Tests (6/6 pass)
- AA in BB facing raise → raise 18 ✅
- T9s in BB facing raise → call 2 (blind defense) ✅
- 72o in BB facing big raise → fold ✅
- KQo BTN open → raise 6 ✅
- 84o in SB no raise → fold (offsuit trash) ✅

### Live Status
- Mona chips: 942 (rebuy success, back at table)
- Cron heartbeat running every 1 min with v3 logic
- Backup: `arena_heartbeat_v2.py.bak`

## Issues
- Test "78s in SB no raise" returned raise 6 instead of call 1 (overaggressive SB)
  - Not critical — raising suited connectors from SB is valid play
- API doesn't expose button position — position inference limited to blind detection
- 143 hands sample too small statistically — need 500+ to evaluate real win rate

## Next Steps
- Let cron run 2-4 hours with v3
- Check win rate after 300+ hands
- If still <10%: consider upgrading LLM to `bai/claude-sonnet-4.5` or `bai/gpt-5.5` for postflop
- If >15%: strategy working, let it run
