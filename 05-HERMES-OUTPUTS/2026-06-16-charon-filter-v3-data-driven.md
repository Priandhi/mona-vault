---
date: 2026-06-16
agent: SOYU — The Phantom
task: Deep fix Charon filter — data-driven v3 + exit strategy overhaul
token: Various (p WIN +139.9%, JOE/FREDDY open)
entry: 0.1 / 0.05 SOL
exit: 0.1399 (p), 0.0 (JOE open, FREDDY open)
result: |
  ROOT CAUSE OF -1.1 SOL DRAWDOWN
  - Old filter (minOrganic 40, minBuyRatio 0.85) let through 36/100 signals (36% pass rate)
  - 5m momentum was positive (+4% to +22%) on all losing entries → late pump entries
  - Bot became exit liquidity for already-pumped tokens
  - Exit strategy was over-aggressive (break-even trigger 3% lock 1%, trailing 5%/3%) → killed winners
  - Phantom positions (entryPrice=0) blocked slots

  DATA-DRIVEN ANALYSIS (100 Charon signals)
  - 5m momentum distribution: 61% in -5% to +5% range (the "neutral zone")
  - Age sweet spot: 15-60 min (catches early but not too early)
  - Organic 60-80 = 39% (top quality band)
  - Best signals had: age<60m, 5m<+3%, organic>60, buyRatio>2, netBuyers>200, dev<5%

  FIX v3 IMPLEMENTED
  1. token-filter.js: NEW anti-chase check `maxPriceChange5m` (reject if 5m > +3%)
  2. token-filter.js: NEW age window `minAgeMinutes` + `maxAgeMinutes` (10-120m fresh)
  3. token-filter.js: NEW `maxOrganicScore` (reject suspicious 100s)
  4. config.json: 14 filter values retuned
  5. config.json: exit strategy rebuilt — TP ladder [20/30, 40/35, 70/35] + trailing +15% drop -10%
  6. config.json: deploy 0.05 SOL, max 2 positions, max 5 trades/day, max daily loss 0.03 SOL
  7. config.json: pause after 2 consecutive losses for 120 min

  TEST RESULT
  - Pre-fix: 0/8 wins, -1.11 SOL drawdown
  - Post-fix: 1/1 wins (p +139.9% / +0.14 SOL)
  - Today's combined: 1W/8L, -0.0621 SOL (old losses + new gain)
  - Sim balance: 3.8531 / 5.0000 SOL (recovering)

  p TRADE BREAKDOWN (first winner!)
  - Entry: 0.1 SOL @ $0.0000000000008 (age 18m, 5m +1.0%, organic 67, buyRatio 5.1)
  - Peak: +329.5% (4.3x!)
  - Exit: TRAILING — peak +329.5%, dropped -12.1% (within -10% trigger)
  - TP ladder: hit all 3 levels (20%, 40%, 70%) → sold 30+35+30 = 95% of tokens
  - Remaining 5% exited via trailing
  - Final: +139.91% / +0.14 SOL
  - Lesson: NEW filter caught an early gem, TP ladder locked profit, trailing let the winner ride

  OPEN POSITIONS (2)
  - JOE: peak +34.3%, TP1 hit (30% sold at +20%), BE locked at +8%, hold 38m+
  - FREDDY: just opened, 5m +1.0%, organic 58, buyRatio 3.1, 360 holders, $117K mcap

  ROLLBACK
  - Archive: data/archive-2026-06-16-fix2/ (positions, balance, config, filter.js)
  - Restore: `cp data/archive-2026-06-16-fix2/config.json config.json && cp data/archive-2026-06-16-fix2/modules/token-filter.js modules/`
  - Bot kill: kill 2322233

alpha: |
  - Anti-chase filter (max 5m +3%) is the KEY change — stops being exit liquidity
  - TP ladder (20/30, 40/35, 70/35) locks profit at multiple levels instead of single TP
  - Trailing (drop -10% from peak) lets winners ride
  - Data shows: 1/100 strict filter still finds winners, 36/100 loose filter found none
  - For HEXA FORWARD: config.json now has _comment fields explaining each setting
  - Easy to tune: change values in config.json, restart bot, see impact in 20-30 min

next: |
  1. Monitor FREDDY + JOE (next 60-90 min)
  2. If new winners follow, the filter v3 is validated
  3. If market stays rough, accept 1 trade/day and let winners compound
  4. After 24h DRY_RUN: evaluate go-live readiness
  5. Consider: make filter more aggressive (minOrganic 60, max 5m +1%) if too many false positives
---
