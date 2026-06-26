---
date: 2026-06-16
agent: SOYU — The Phantom
task: Fix Charon sniper — config retune + phantom position cleanup + guard
token: N/A (system fix, not a trade)
entry: N/A
exit: N/A
result: |
  PROBLEM
  - 25 closed trades, 5W/20L (20% WR), -1.1111 SOL drawdown
  - 3 phantom open positions blocking slots (PARQ, 01, AICAST/pnutbutter)
  - Config over-aggressive: break-even trigger 3% lock 1%, trailing 5%/3%, maxHold 60min
  - Bot creating phantom positions when Jupiter quote fails AND sig.priceUsd is missing

  FIXES APPLIED

  1. HALTED bot (PID 2038126 killed)
  2. CLEANED phantom positions from data/positions.json — 0 open now
     - Backup saved: data/positions.json.pre-fix-2026-06-16
  3. JUPITER-EXECUTOR GUARD (modules/jupiter-executor.js)
     - DRY_RUN fallback: if quote fails AND sig.priceUsd is missing/invalid → REJECT (return success: false)
     - Validation: outAmount <= 0 || price <= 0 || !isFinite → REJECT
     - Prevents phantom positions at source
  4. POSITION-MANAGER GUARD (modules/position-manager.js)
     - openPosition() now validates buyResult.price > 0 && amountIn > 0 && amountOut > 0
     - Returns null if invalid (belt-and-suspenders)
  5. INDEX.JS NULL CHECK (index.js)
     - if (openPosition returns null) → log + skip cycle + return
  6. CONFIG RETUNE (config.json)
     - exit.breakEven.triggerPct: 3% → 15%
     - exit.breakEven.lockAtPct: 1% → 5%
     - exit.trailingTriggerPct: 5% → 12%
     - exit.trailingDropPct: 3% → 8%
     - exit.maxHoldMinutes: 60 → 120
     - exit.takeProfitPct: 25% → 30%
     - exit.takeProfitLevels: [10/25, 15/35, 25/40] → [12/35, 20/35, 30/30]
     - trade.deployAmountSol: 0.2 → 0.1
     - trade.maxPositions: 5 → 3
     - trade.maxDailyTrades: 99 → 8
     - trade.cooldownMs: 30000 → 180000 (3m cooldown)
     - risk.maxDailyLossSol: 1.0 → 0.05
     - risk.emergencyStopLossPct: -50 → -30
     - risk.pauseDurationMinutes: 15 → 60
  7. RESTARTED bot (new PID 2048420) — config loaded correctly

  VERIFICATION
  - node --check all 4 modules: ✅ pass
  - config.json valid JSON: ✅ pass
  - Bot startup logs show new config: Deploy 0.1 SOL, BE +15%/+5%, trail +12%/-8%, maxHold 120min, maxDailyTrades 8, maxDailyLoss 0.05 SOL
  - "Daily trade limit reached" at startup (27 closed today ≥ 8) — bot will trade again tomorrow, this is correct behavior
  - Open positions: 0 (was 3+ phantoms)
  - Sim balance: 3.8889 SOL (unchanged, no new trades yet)

  ROLLBACK (asal aman)
  - Positions: cp data/positions.json.pre-fix-2026-06-16 data/positions.json
  - Config: git checkout config.json (or manual revert)
  - Bot: kill 2048420 && cd /home/ubuntu/mona-workspace/charon-sniper && git checkout modules/jupiter-executor.js modules/position-manager.js index.js && nohup node index.js > /tmp/charon-sniper.log 2>&1 &

alpha: |
  - Filter 7-layer sudah implemented (organicScore 40, buyRatio 0.85, devHoldings 15, topHolders 40, snipers 50, etc.) — tidak perlu diubah
  - Yang diubah: exit strategy (over-aggressive) + risk controls (terlalu longgar) + phantom guard
  - Trade size dikecilkan 0.2→0.1 SOL karena sim wallet tinggal 3.89, butuh konservatif
  - Expected improvement: WR 20%→35-40%, drawdown lebih terkontrol (max 0.05 SOL/hari), no more phantom blocks

next: |
  1. Monitor bot log 24 jam — catat WR + avg PnL
  2. Besok pagi (cycle fresh) verify: trade frequency turun drastis, no phantom muncul
  3. After 2-3 hari DRY_RUN stabil → pertimbangkan LIVE mode
  4. Optional: implementasi 7-layer advanced filter scoring (sdg pakai basic 7-layer — masih ada ruang)
---
