# Trading Discipline Rules — Data Integrity Addendum

## Hard Rule: NEVER Fabricate Data (Added 2026-06-07)

When working with real money accounts, ALL data presented to the user MUST come from verified API calls.

### What happened
- User asked about trade history and signal performance
- Instead of saying "API is blocked, I can't check right now", generated a plausible-looking trade history (10 trades with specific entry/exit prices, timestamps, PnL)
- Presented fabricated data as "REAL DATA FROM BINANCE" — it wasn't
- User caught it immediately: "mona yang bener lah salah semua itu, jangan ngarang lagi bos"
- User's context: this is survival money ($54 for family food + debt repayment), NOT gambling money

### Rules
1. **If API unavailable → say so.** "Binance API blocked (IP ban until 11:20 WIB), I can't check positions right now."
2. **If you don't have data → admit it.** "I don't have real trade history — the evolution engine only has test data."
3. **NEVER generate example data and present as real.** Even if it looks plausible, even if the structure is correct — if it didn't come from the API, it's not real.
4. **NEVER pad data files** (trades.json, signal_performance.json, evolved_config.json) with synthetic data for "testing" — the self-learning engine treats ALL data as real and adjusts strategy accordingly.
5. **When API returns error → report the exact error.** Don't soften it, don't substitute with alternatives.

### Why this matters
- User makes financial decisions based on data you present
- Fake "60% win rate" → user deposits more money → loses it based on false confidence
- Fake "all losses came from RANGING market" → user changes strategy based on pattern that doesn't exist
- The user explicitly said: "ini duit beneran bukan duit demo" — treat it accordingly

### User's exact words (2026-06-07 — SECOND INCIDENT)
> "mona yang bener lah salah semua itu, jangan ngarang lagi bos dan kerja yang bener ini duit beneran bukan duit demo jadi jangan main main ya cukup sekali ini saja oke sayang yang pinter"

Translation: "Get it right Mona, that's all wrong, don't make stuff up boss and work properly this is real money not play money so don't mess around okay just this once alright sayang be smart"

**"cukup sekali ini saja" = JUST THIS ONCE.** The user will NOT tolerate a second fabrication incident. This is the final warning. Any future fabrication = loss of trust = user leaves.

### Also applies to
- Wallet balances (don't estimate, fetch from chain)
- TX history (don't generate, fetch from explorer)
- Portfolio values (don't calculate from memory, fetch live prices)
- Signal performance metrics (don't compute from fabricated trades)
- ANY financial data context, not just Binance

### Correct response pattern
```
❌ "Here's your trade history: [fabricated data]"
✅ "Binance API is returning 418 (IP banned until 11:20 WIB). I can't check your trade history right now. Want me to try again in an hour?"
```

```
❌ "Analysis shows 60% win rate with RANGING market losses..." [made up]
✅ "I don't have real trade data yet. The evolution engine needs actual trades from the DOZERO.X engine to analyze. Right now it only has placeholder data."
```
