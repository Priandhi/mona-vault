# Filter v3 — Data-Driven Anti-Chase Strategy

## Origin Story (Jun 16 2026)

After a streak of 0/8 wins with the v2 filter (36% pass rate, all losing entries had positive 5m momentum), the bot was halted and a 100-signal snapshot was pulled from Charon to find the root cause.

**The data told a clear story:**
- 61% of Charon signals had 5m momentum in the -5% to +5% range (the "neutral zone")
- The v2 filter selected from the 36% pass rate, but EVERY losing entry had 5m momentum in +4% to +22% — meaning the bot was buying AT the top of an early pump
- Once a micro-cap token has pumped +20% in 5 minutes, it's typically 30-60 minutes from dumping as early buyers take profit
- The bot became exit liquidity for the early pumpers

**The fix:** add `maxPriceChange5m: 3` (reject if 5m > +3%). This single change, combined with TP ladder exit, turned a 0/8 streak into a +139.91% winner on the first qualifying token ("p", peak +329.5%).

## 100-Signal Distribution Analysis

### 5-Minute Price Change (the smoking gun)

| Bucket | Count | % |
|---|---|---|
| < -20% | 1 | 1% |
| -20% to -5% | 12 | 12% |
| -5% to 0% | 8 | 8% |
| **0% to +5%** | **61** | **61%** ← the "neutral zone" |
| +5% to +15% | 9 | 9% |
| +15% to +30% | 6 | 6% |
| > +30% | 3 | 3% |

**Insight:** the safe entry window is 0% to +3% (a sub-slice of the 61% neutral zone). Anything above +3% is "someone already pumped this, you're late."

### Age Distribution (when to look for entries)

| Bucket | Count | % |
|---|---|---|
| < 15m | 10 | 10% |
| **15m to 30m** | **16** | **16%** ← early-stage sweet spot |
| **30m to 60m** | **19** | **19%** ← best window |
| 1h to 2h | 24 | 24% |
| 2h to 6h | 25 | 25% |
| 6h to 12h | 2 | 2% |
| > 12h | 4 | 4% |

**Insight:** 35% of signals are 15-60m old — that's the early-stage window. After 2h, most are either pumped or dead. The v2 filter accepted up to 12h — way too loose.

### Organic Score (quality band)

| Bucket | Count | % |
|---|---|---|
| 0 (no data) | 25 | 25% |
| 1 to 20 | 0 | 0% |
| 20 to 40 | 3 | 3% |
| 40 to 60 | 25 | 25% |
| **60 to 80** | **39** | **39%** ← top quality band |
| 80 to 100 | 8 | 8% |

**Insight:** 25% of signals have NO organic data (organic = 0) — they should be rejected. The 60-80 band is where the highest-quality signals cluster.

### Net Buyers (24h, adoption signal)

| Bucket | Count | % |
|---|---|---|
| 0 to 50 | 53 | 53% |
| **50 to 200** | **16** | **16%** ← mild traction |
| **200 to 500** | **18** | **18%** ← real adoption |
| 500 to 1000 | 7 | 7% |
| > 1000 | 6 | 6% |

**Insight:** 53% of signals have < 50 net buyers in 24h — basically nobody cares yet. The 200+ bucket is where real adoption shows.

## The v3 Filter Rules

| Field | v2 | **v3** | Rationale |
|---|---|---|---|
| `minPriceChange5m` | (unset) | **-8** | Allow mild dip (mean reversion play), reject falling knives |
| `maxPriceChange5m` | — | **3** | **KEY: reject 5m > +3%, the single most important filter** |
| `minAgeMinutes` | — | **10** | Not too fresh (rugs) |
| `maxAgeMinutes` | 12h | **120** | 2h window, early-stage only |
| `minOrganicScore` | 30 | **55** | Top quality band |
| `maxOrganicScore` | — | **90** | Reject suspicious 100s (likely fake) |
| `minBuyRatio` | 0.8 | **1.5** | Real demand, not noise |
| `minNetBuyers` | 10 | **100** | Real adoption |
| `maxDevHoldings` | 20 | **8** | Lower rug risk |
| `maxTopHolders` | 50 | **35** | Less dump risk |
| `maxSnipers` | 100 | **40** | Less competition |
| `maxMcap` | 3M | **500K** | Micro-cap sweet spot |
| `minVolume24h` | 10K | **50K** | Active market required |
| `minVolume5m` | 500 | **1,500** | Active trading |
| `minVolAcceleration` | 0.5 | **1.0** | 5m vol must outpace 24h |

## Test Result (100 signals, v3 filter)

- **Pass rate: 1/100 = 1.0%** (target was 1-5%)
- **The 1 winner:** `petin` — age 17m, 5m -5.5%, organic 72, buyRatio 3.1, 500 holders, $83K mcap, 899 netBuyers, 0% dev holdings — ideal profile
- **Top rejection reasons:** too old (24), too fresh (13), holders<150 (13), 5m momentum out of [-8%, +3%] (18), 5m vol < $1.5K (12), mcap out of range (10), organic 0 or low (10)

**Conclusion:** 1% pass rate is fine. Bot only trades 5/day max, and 100 signals × 6 refreshes/hour = 600/hour. At 1% pass rate, ~6 winners/hour, way more than needed.

## The Real Winner: token "p" (Jun 17 2026)

After deploying v3 in production, the FIRST qualifying token was "p":
- Entry: 0.1 SOL @ $0.0000000000008
- Age at entry: 18 minutes (fresh)
- 5m momentum: +1.0% (NEUTRAL — not chasing, ideal)
- Organic: 67
- buyRatio: 5.1 (very high demand)
- Holders: 326
- MCap: $62K
- netBuyers: 634

The token pumped to **+329.5% peak (4.3x)**. The TP ladder captured the run:
- TP1 at +20% → sold 30% of original
- TP2 at +40% → sold 35% of original
- TP3 at +70% → sold 30% of original
- Total: ~95% via ladder
- Remaining 5% rode with trailing
- Trailing exit at +329.5% peak, dropped -12.1% (within -10% trigger)
- **Final PnL: +139.91% / +0.14 SOL** — first winner after 0/8 streak

## How to Test Filter Changes Against Real Data

When tuning the filter, use this pattern to validate against a live snapshot WITHOUT restarting the bot:

```bash
# 1. Snapshot 100 signals from Charon
curl -s "https://api.thecharon.xyz/api/signals" \
  -H "x-api-key: YOUR_KEY" > /tmp/charon-snapshot.json

# 2. Run filter against snapshot
cd /path/to/charon-sniper
node -e "
import('./modules/token-filter.js').then(async ({filterSignals}) => {
  const fs = await import('fs');
  const config = JSON.parse(fs.readFileSync('config.json', 'utf8'));
  const d = JSON.parse(fs.readFileSync('/tmp/charon-snapshot.json', 'utf8'));
  const {qualifying, rejected} = filterSignals(d.signals, config, []);
  console.log('Pass: ' + qualifying.length + '/' + d.signals.length);
  qualifying.slice(0,10).forEach(q => {
    const pc = q.trending?.stats5m?.priceChange || 0;
    console.log('  ' + q.symbol.padEnd(12) + ' score ' + q.qualityScore.toFixed(1) + ' | 5m ' + pc.toFixed(1) + '% | age ' + (q.ageMs/60000).toFixed(0) + 'm');
  });
  const reasons = {};
  rejected.forEach(r => { reasons[r.reason.split('(')[0]] = (reasons[r.reason.split('(')[0]]||0)+1; });
  console.log('\\nTop rejects:');
  Object.entries(reasons).sort((a,b)=>b[1]-a[1]).slice(0,5).forEach(([k,v]) => console.log('  ' + v + 'x ' + k));
});
"
```

This lets you iterate on filter values in 30 seconds. Target 1-5% pass rate with tokens that look like real winners (low 5m momentum, fresh age, high organic, high buyRatio).

## Token-Filter.js Code Changes for v3

The existing `modules/token-filter.js` needs three additions:

```javascript
// 1. Age window with min AND max
const minAgeMs = (f.minAgeMinutes || 0) * 60000;
const maxAgeMs = (f.maxAgeMinutes || f.maxAgeHours * 60 || 720) * 60000;
if (minAgeMs > 0 && ageMs < minAgeMs) return fail(`too fresh (${ageMin}m < ${f.minAgeMinutes}m)`);
if (ageMs > maxAgeMs) return fail(`too old (${ageMin}m > ${f.maxAgeMinutes}m)`);

// 2. Anti-chase upper bound on 5m momentum
if (f.maxPriceChange5m !== undefined && priceChange5m > f.maxPriceChange5m) {
  return fail(`5m price ${priceChange5m.toFixed(1)}% > +${f.maxPriceChange5m}% (chasing pump)`);
}

// 3. Organic score upper bound (reject suspicious 100s)
if (f.maxOrganicScore && organicScore > f.maxOrganicScore) {
  return fail(`organic ${organicScore.toFixed(0)} > ${f.maxOrganicScore} (suspicious)`);
}
```

These three checks are the v3 differentiator from v2.

## Tuning Cheat Sheet (v3 baseline → adjustments)

| Symptom | Adjustment |
|---|---|
| 0 trades/day | Lower `minOrganicScore` to 45, raise `maxAgeMinutes` to 180 |
| 1 trade/day but losing | Raise `minOrganicScore` to 65, lower `maxPriceChange5m` to 1 |
| 5+ trades/day, mostly losers | Tighten ALL filters: `minOrganicScore` 70, `minNetBuyers` 300, `minBuyRatio` 2.5 |
| Pumped token but bot didn't enter | Add `minPriceChange5m: -3` (allow -3% to +3% range only) |
| Tokens entering but stalling | Raise `minVolume5m` to 5000 (need real volume surge) |
| Late entry on big movers | Lower `maxPriceChange5m` to 1 (very strict anti-chase) |

The key insight: the v3 filter is a TUNING FRAMEWORK, not a fixed config. The values in the skill's "Optimized Config" section are the v3 starting point — adjust based on observed market conditions and your risk tolerance.
