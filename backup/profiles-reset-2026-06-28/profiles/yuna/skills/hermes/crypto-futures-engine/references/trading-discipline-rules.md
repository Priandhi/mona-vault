# Trading Discipline Rules (Hardcoded — No Exceptions)

## Entry Rules

1. **Threshold is sacred** — Score ≥ 50 = enter. Below 50 = DO NOT ENTER. No exceptions. With 16 signals, 50+ captures ~5% of scan results where 5+ signals align.

2. **Wait is a valid decision** — When no setup above threshold exists, the correct action is to do nothing. "No opportunities found" is a successful scan, not a failure.

3. **Never flip-flop** — Enter → doubt → close → re-enter = guaranteed loss from spread + fees. If you're not confident enough to hold through -2% drawdown, don't enter.

4. **Volume conviction required** — H1 volume < 0.3x average = low conviction. Skip regardless of score. Price moves on volume; a BOS without volume is a fakeout.

5. **Orderbook final check** — Bid/ask ratio < 0.5 = sellers dominate. Skip even if everything else looks good.

6. **Skip high-volatility pairs** — Backtest proven: pairs with ATR% > 3% of price (ZEC, HYPE, meme coins) lose money consistently (PF < 0.8). Stick to top 10 by 24h volume. ATR% = ATR / price * 100.

## Exit Rules

6. **SL is mandatory** — Never hold a position without SL. If SL placement fails, emergency close immediately.

7. **Don't move SL backward** — Once set, SL only moves in favorable direction (trailing). Never widen SL to "give it more room."

8. **TP1 partial close** — Close 50% at TP1, move SL to breakeven. Lock in profit, let runner ride.

## Risk Rules

9. **Max 3% risk per trade** — Non-negotiable. Even if "this one is different."

10. **Max 2 positions simultaneously** — With $50-55 balance, 2 positions max. More = over-exposure.

11. **25% balance reserve** — Always keep 25% free. This is the "opportunity fund" for elite setups.

12. **Emergency stop at 5% daily drawdown** — If balance drops 5% from daily high, pause all trading for 24h.

13. **3 consecutive losses = pause** — Stop trading, review journal, identify pattern, then resume.

## Psychology Rules

14. **Revenge trading = account killer** — After a loss, the urge to "make it back" with a bigger position is the #1 account destroyer. Cool down period exists for this reason.

15. **"I should have entered" is FOMO** — Missing a trade is NOT a loss. Entering a bad trade IS a loss.

16. **Size must match target** — Before entering, calculate: `required_move = target_profit / notional`. If > 5%, position is too small to matter. Resize or skip.

17. **Compound, don't gamble** — 3% risk on $53 = $1.60/trade. 3% risk on $200 = $6/trade. Same discipline, bigger returns. The math works if you let it.

## User Communication Rules

18. **"lama banget" = frustration signal** — User gets impatient with long analysis. Optimize for speed: parallelize, cache, limit scope. Better to enter a good setup quickly than wait 5 minutes for a perfect one.

19. **"lu yang eksekusi" = DO IT NOW** — When user delegates execution, don't ask for confirmation. Analyze → decide → execute → report. User wants to see results, not options.

20. **This is family money** — User explicitly said: "buat makan kasih istriku dan bayar hutang" (feeding wife and paying debt). This is NOT gambling money. Treat every dollar as if your family depends on it.

## Autonomous Engine Discipline Rules

24. **"Fix semua" = STOP everything first** — When user says "fix semua", "benerin dulu", or "jangan entry dulu", IMMEDIATELY kill the engine, fix ALL bugs, verify with paper mode, THEN restart live. Never fix incrementally while engine is live. User explicitly said: "lu masih belum beres, benerin dulu kalau semua beres baru entry."

25. **User manually closing positions = ENGINE FAILURE** — If user has to intervene (close positions on Binance app, kill engine process), the autonomous system has FAILED. This is the worst outcome. After this happens: (a) stop engine, (b) audit ALL code paths, (c) add safety rails, (d) test paper mode, (e) only restart when user explicitly approves.

26. **All safety rails must be in place BEFORE going live** — Per-pair cooldown, flip prevention, hourly limits, minimum balance check, SL/TP verification, breakeven update, emergency close. See `references/autonomous-safety-rails.md` for the full list. Don't add them "later" — they must exist before the first live trade.

27. **SL/TP verification is NOT optional** — Every monitoring cycle must verify ALL positions have SL/TP on Binance. If missing → place it. If placement fails → emergency close. This is defense-in-depth against algo order bugs, API changes, and stale state.

28. **Breakeven must update Binance, not just local state** — When TP1 hits and SL moves to breakeven, the algo order on Binance must also be updated. Local-only breakeven means the Binance SL is still at the original price — if price reverses, you lose more than expected.

29. **Don't trade when balance < $40** — Minimum balance to open a meaningful position with proper SL/TP and margin buffer. Below $40, the position is too small to matter and fees eat profits.

## Alert Rules

21. **Alerts ONLY on trade open/close** — No periodic status updates, no scan summaries, no balance reports. User said: "jangan terus-menerus alerts, kirim kalau ada posisi dan pnl aja." Two events only: (a) trade opened, (b) trade closed. After all positions close: one line max.

22. **"No positions = no alerts" is absolute** — When no positions exist, output is SILENT. Don't send "monitoring 30 pairs" or "no setups found." Silence is the default state. User got angry: "woi di bilang kalau gak ada posisi gak usah kirim alerts masih ngeyel."

23. **Emergency alerts are the only exception** — SL placement failed, IP banned, engine crashed, liquidation risk. These MUST be sent regardless of position state.
