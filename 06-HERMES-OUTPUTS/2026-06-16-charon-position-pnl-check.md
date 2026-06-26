---
date: 2026-06-16
agent: SOYU — The Phantom
task: Cek posisi charon + PnL report (Hexa request)
token: N/A (snapshot/reporting only)
entry: N/A
exit: N/A
result: |
  BOT STATE
  - index.js (PID 2038126) + server.js (PID 1514436) — both running
  - mode: DRY_RUN
  - deploy: 0.2 SOL/trade
  - max positions: 5
  - refresh: 600s (10 min)

  WALLET (sim)
  - Balance: 3.8889 / 5.0000 SOL
  - Total loss: -1.1111 SOL (-22.22%)
  - Closed: 25 trades | 5W / 20L (20% WR)
  - Avg win: +0.0147 SOL | Avg loss: -0.0419 SOL
  - Best: Vozinha +0.064 | Worst: FRANCE -0.200
  - Today (06-16): -0.7635 SOL (5W/20L) — 25 trades
  - Yesterday (06-15): -0.5611 SOL (0W/19L) — 19 trades, ZERO wins

  OPEN POSITIONS (3 — ALL BROKEN/PHANTOM)
  - PARQ: entryPrice=0, solInvested=0, peak +0%, age 0m  (Jupiter quote failed at entry)
  - 01:   entryPrice=0, solInvested=0, peak +0%, age 0m  (same)
  - AICAST: entryPrice=0.0001118997, solInvested=0, peak +0%, age 0m  (partial broken)

  EXIT REASON BREAKDOWN (n=25)
  - MAX HOLD (60-80min): 10  ← most positions dying from timeout, not SL
  - EMERGENCY SL -100%: 3    ← catastrophic, sells returned ~0 SOL
  - BREAK-EVEN LOCK (avg -2.5%): 7  ← break-even triggering too early, locks at +1%, sells at loss
  - STOP LOSS -23 to -30%: 2
  - TRAILING (peak +25%): 1   ← only 1 actual profitable trailing exit
  - Other: 2

  CONFIG OBSERVATIONS (vs skill benchmarks)
  - breakEven.triggerPct = 3% (TOO LOW) → skill says 15% for micro-caps
  - breakEven.lockAtPct = 1% (TOO LOW) → skill says 5%
  - trailingTriggerPct = 5% (TOO LOW) → skill says 12%
  - trailingDropPct = 3% (TOO TIGHT) → skill says 8%
  - maxHoldMinutes = 60 (TOO SHORT) → skill says 120
  - Result: tokens pump to +15-20%, break-even triggers at +3% locks at +1%, then dumps → sold at -2% to -9% instead of trailing at +10-15%

  CRITICAL ISSUES
  1. Filter is weak — 25 trades in 2 days, mostly garbage
  2. Exit strategy over-aggressive on break-even — kills winners before they peak
  3. 3 phantom positions blocking slots (PARQ, 01, AICAST) — exact "Broken position" pitfall
  4. Bot running but bleeding sim SOL — needs config retune + position cleanup

alpha: |
  - Win rate 20% is unprofitable even with good R:R (need ~35% WR at 1:2 to break even)
  - Actual R:R here: 0.0147:0.0419 = 1:2.85 (good) but WR too low → -1.11 SOL bleed
  - Break-even +3% is THE killer. Charon signals peak +15-20% on winners. Locking at +1% steals the upside.
  - Yesterday 0/19 = filter gave 0 winners — basic filter insufficient
  - Bot needs: (1) 7-layer advanced filter, (2) retuned break-even (15% trigger, 5% lock), (3) cleanup phantom positions

next: |
  1. Tunggu konfirmasi Hexa — config retune + phantom cleanup, atau diam dulu?
  2. Recommended action: HALT bot, clean 3 phantoms, retune config per skill benchmarks, restart with 7-layer filter
  3. Alternative: gas mode → eksekusi sekarang tanpa nanya
---
