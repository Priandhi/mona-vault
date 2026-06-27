# Autonomous Engine v3.0 — TradingAgents-Inspired Architecture

## Overview

Engine v3.0 = v2.0 (DOZERO.X SMC) + 4 new modules inspired by TradingAgents + Fincept Terminal.

**New modules (June 2026):**
1. `mona_debate.py` — Adversarial Debate System
2. `mona_coinglass.py` — CoinGlass Data Integration
3. `mona_memory_learning.py` — Memory-Driven Learning
4. Fear & Greed Index (inline function)

## Module 1: Adversarial Debate System (`mona_debate.py`)

Inspired by TradingAgents' dual debate architecture. Runs BEFORE every entry.

**Flow:**
1. `BullResearcher.analyze()` — builds case FOR the trade (signal strength, SMC confluence, regime alignment, volume, MTF alignment, OI divergence, CVD)
2. `BearResearcher.analyze()` — builds case AGAINST (regime mismatch, funding rate contrarian, extreme fear/greed, low volume, weak signals, SMC conflict, wide spread)
3. `RiskManager.evaluate()` — weighs both sides, applies risk adjustments (consecutive losses, drawdown, position count, low balance)

**Verdicts:**
- `STRONG_ENTER` — net score >= 40, bull >= 60
- `ENTER` — net score >= 20, bull >= 50
- `SIZE_DOWN` — net score >= 0, bull >= 40
- `PASS` — everything else (skip trade entirely)

**Argument strength:** Each argument has `strength` (0-1) and `data_source`. Top 3 arguments per side are highlighted.

**History:** Saved to `~/.hermes/data/evolution/debate_history.json` (last 200 debates).

## Module 2: CoinGlass Data Integration (`mona_coinglass.py`)

Fetches market intelligence from Binance public API + Alternative.me.

**Data sources:**
- **Funding Rate** — `/fapi/v1/premiumIndex` — positive = longs pay shorts (crowded long)
- **Open Interest** — `/fapi/v1/openInterest` + `/futures/data/openInterestHist` — 24h trend (rising/falling/neutral)
- **Long/Short Ratio** — `/futures/data/topLongShortPositionRatio` — top trader positioning
- **Liquidations** — `/futures/data/forceOrders` — recent forced closes, dominant side detection
- **Fear & Greed** — `api.alternative.me/fng/` — crypto sentiment index (0-100)

**Sentiment score (`compute_sentiment_score`):**
Returns -100 to +100. Positive = supports trade direction, negative = against.
- Funding: contrarian (high positive funding for LONGs = -50 points per 0.01)
- OI trend: rising + LONG = +10, falling + LONG = -10
- L/S ratio: >65% crowded = -20, <40% contrarian = +15
- Liquidations: cascade against your side = -15
- Fear/Greed: extreme greed + LONG = -15, extreme fear + LONG = +10

**Cache:** 120s default, 5 min on 418 ban, 1 hour for Fear & Greed.

## Module 3: Memory-Driven Learning (`mona_memory_learning.py`)

Stores decisions + outcomes, extracts lessons, injects into prompts.

**Decision storage:** On trade open, stores: symbol, side, entry_price, score, regime, debate_verdict, debate_confidence, signals snapshot, coinglass intel.

**Outcome recording:** On trade close, records: exit_price, pnl_pct, exit_type. Auto-extracts lessons:
- LOSS in RANGING market → "avoid RANGING entries"
- LOW score (<70) LOSS → "stick to 75+"
- SIZE_DOWN verdict ignored + LOSS → "trust the debate"
- HIGH score (80+) WIN → "high conviction works"
- STRONG_ENTER debate WIN → "debate system reliable"

**Lesson injection:** `get_lessons_for_prompt(max_lessons=5)` returns formatted string for engine prompt.

**Stats:** `get_stats()` returns total trades, wins, losses, win_rate, avg_win_pnl, avg_loss_pnl, lessons_count.

**Storage:** `~/.hermes/data/evolution/lessons_learned.json` (500 max), `~/.hermes/data/evolution/decision_history.json` (500 max).

## Module 4: Fear & Greed Index

Inline function `get_fear_greed_cached()` in `mona_autonomous.py`.
- Source: Alternative.me API
- Cache: 1 hour
- Display: In startup log
- Use: Contrarian signal in debate arguments, extreme values warn of reversals

## Integration Points

**Before entry (`_scan_and_trade`):**
```
best_opportunity = scan...
debate_result = self.debate_system.debate(...)
if debate_result.verdict == 'PASS':
    log.info("DEBATE PASS: skip")
else:
    await self._execute_trade(best_opportunity)
```

**On trade open (`_execute_trade`):**
```
coinglass_intel = self.coinglass.get_full_intel(symbol)
self._current_decision_id = self.memory_learning.store_decision(...)
```

**On trade close (`_close_position`):**
```
self.memory_learning.record_outcome(self._current_decision_id, ...)
self._current_decision_id = None
```

## Pitfalls

- **Never fabricate data.** If Binance API returns 418 (IP banned), report "API banned" — never generate fake trade history. User极度 frustrated: "mona yang bener lah salah semua itu, jangan ngarang lagi bos dan kerja yang bener ini duit beneran bukan duit demo". This is a HARD RULE with zero exceptions.
- **Initialization order is CRITICAL.** Engine crashed twice because startup log accessed `self.memory_learning.lessons` BEFORE `__init__` set `self.memory_learning`. When patching engine `__init__`, verify that ALL new module initializations (`self.debate_system`, `self.coinglass`, `self.memory_learning`) are BEFORE any code that references them. The pattern: find the EXACT closing of the previous init block (e.g., `})` for smc_engine config dict), insert new inits AFTER that line, THEN verify startup log comes after.
- **Constructor patching pattern for mona_autonomous.py.** The smc_engine init is a multi-line dict (`DoxzeroSMCEngine({\n    'key': val,\n})`) — the closing `})` is on a separate line. When using `str.replace()`, match the EXACT opening line and search for the closing. Safer approach: read lines, find the block end, insert after it. Always `ast.parse()` the result before writing.
- **Rate limit: 50 req/min max.** Added to DataCollector._get(). Auto-waits when limit hit.
- **Top 30 symbols only.** Reduced from 528 to avoid IP ban.
- **300s scan interval.** Increased from 90s.
- **Debate PASS = skip.** Don't override debate verdict with manual entry.
- **Memory learning needs 10+ trades.** Lessons are sparse until enough data accumulates.
- **Fear & Greed cache is global.** Not per-symbol. One fetch per hour covers all symbols.
- **`<< 'PYEOF'` heredoc causes backgrounding error in terminal tool.** The terminal tool interprets `<< 'PYEOF'` as a backgrounding directive. Use `write_file` to create a `.py` file first, then execute with `python3 /tmp/script.py`. Or use `python3 -c "..."` with escaped strings.
- **Binance IP ban from excessive API calls.** 528 symbols × 8 calls = ~4,224 per loop (90s). Binance limit ~1,200/min → 418 ban for 1-2 hours. Fix: rate limiter (50/min) + top 30 symbols + 300s interval + 120s cache TTL + 5 min ban cache on 418.
- **Auto-start engine after IP ban.** Create `auto_start_engine.py` script that checks if Binance API responds, then starts engine. Set as `no_agent=True` cron job with `every 5m`. Remove the cron job once engine confirms running. Pattern: check `pgrep -f mona_autonomous` first to avoid double-start.
- **OpenClaw Superagent tools require specific directory structure.** Tools use `Path(__file__).resolve().parent.parent` to find project root. Must place tools in `openclaw/tools/*.py`, NOT flat in `openclaw_tools/`. Symbolic links for skills directories. Otherwise `'NoneType' object has no attribute '__dict__'` error during import (Python `__module__` not registered in `sys.modules`).
- **Most `NoneType` import errors are module registration issues.** When using `importlib.util.spec_from_file_location`, the module must be registered in `sys.modules` BEFORE `spec.loader.exec_module(mod)` for dataclass-based modules. Fix: `sys.modules['module_name'] = mod` before exec.
- **Engine startup must show lessons + Fear & Greed.** Added to startup banner: `log.info(f"  Lessons: {len(self.memory_learning.lessons)} learned")` and `log.info(f"  Fear & Greed: {fear['value']} ({fear['label']})")`. These prove modules loaded correctly.

## Config Changes (v2.0 → v3.0)

| Setting | v2.0 | v3.0 |
|---------|------|------|
| min_score | 50 | 75 |
| sl_atr_mult | 1.0 | 1.5 |
| max_sl_atr_mult | 2.0 | 2.5 |
| scan_interval | 90s | 300s |
| symbols | 528 | 30 |
| rate_limit | unlimited | 50/min |
| self_learning_threshold | 100 trades | 10 trades |
| alerts | silent | trade open/close only |

## Scripts

- `~/.hermes/scripts/mona_debate.py` — Adversarial Debate System
- `~/.hermes/scripts/mona_coinglass.py` — CoinGlass Data Integration
- `~/.hermes/scripts/mona_memory_learning.py` — Memory-Driven Learning
- `~/.hermes/scripts/mona_autonomous.py` — Main engine (all integrated)
- `~/.hermes/scripts/auto_start_engine.py` — IP ban auto-restart watcher
