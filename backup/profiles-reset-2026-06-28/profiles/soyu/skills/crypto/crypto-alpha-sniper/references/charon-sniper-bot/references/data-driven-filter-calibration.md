# Data-Driven Filter Calibration — Workflow

When Charon sniper shows 3+ same-pattern losses (especially when ALL losers share a common signal feature like positive 5m momentum), stop tweaking. Re-derive thresholds from actual signal distribution.

## When to use this workflow

- WR drops below 30% for 2+ days
- Most losses share a common feature (e.g. all have 5m momentum > +5%)
- Filter pass rate is 0% (too strict) or > 30% (too loose)
- Hexa says "perbaiki" / "filter sesuka mu" / "kenapa minus"

## Step 1 — Cache 100 signals

```bash
curl -s "https://api.thecharon.xyz/api/signals" \
  -H "x-api-key: YOUR_KEY" > /tmp/charon-snapshot.json
```

## Step 2 — Distribution analysis

For each field, count buckets:

| Field | Buckets | Why it matters |
|---|---|---|
| `trending.stats5m.priceChange` | <-20, -20 to -5, -5 to 0, 0 to +5, +5 to +15, +15 to +30, >+30 | Anti-chase: 61% live in 0 to +5% bucket (default trap) |
| `ageMs` (in minutes) | <15, 15-30, 30-60, 1-2h, 2-6h, 6-12h, >12h | Fresh window: 35% live in 15-60m (sweet spot) |
| `trending.organicScore` | 0, 1-20, 20-40, 40-60, 60-80, 80-100 | Quality: 39% live in 60-80 (top tier) |
| `trending.stats24h.numNetBuyers` | <0, 0-50, 50-200, 200-500, 500-1000, >1000 | Real adoption: most have <50, target >200 |
| `graduated.devHoldingsPercent` | <2%, 2-5%, 5-10%, >10% | Rug risk: keep <5-8% |
| `graduated.sniperCount` | <10, 10-30, 30-50, >50 | Competition: <30 ideal |

Distribution count template (Python):
```python
import json
d = json.load(open("/tmp/charon-snapshot.json"))
def g(s, *keys, default=0):
    for k in keys:
        s = s.get(k) if isinstance(s, dict) else None
        if s is None: return default
    return s if s is not None else default

buckets = {"0% to +5%":0, "+5% to +15%":0, "+15% to +30%":0}
for s in d["signals"]:
    pc = g(s, "trending", "stats5m", "priceChange", default=0)
    if 0 <= pc < 5: buckets["0% to +5%"] += 1
    elif 5 <= pc < 15: buckets["+5% to +15%"] += 1
    elif 15 <= pc < 30: buckets["+15% to +30%"] += 1
print(buckets)
```

## Step 3 — Set thresholds from data

Mapping distribution insight → filter value:

| Distribution finding | Filter setting |
|---|---|
| 61% in 0-5% bucket | `maxPriceChange5m: 3` (don't chase) |
| 35% in 15-60m | `minAgeMinutes: 10, maxAgeMinutes: 120-180` |
| 39% in organic 60-80 | `minOrganicScore: 55, maxOrganicScore: 90` |
| Most have <50 netBuyers | `minNetBuyers: 100-200` (above median) |
| Most have <5% dev | `maxDevHoldings: 5-8` |
| Mean buyRatio ~3 | `minBuyRatio: 1.5-2` |

## Step 4 — Test pass rate before deploying

```bash
cd /home/ubuntu/mona-workspace/charon-sniper
node -e "
import('./modules/token-filter.js').then(({filterSignals}) => {
  const fs = require('fs');
  const config = JSON.parse(fs.readFileSync('config.json', 'utf8'));
  const d = JSON.parse(fs.readFileSync('/tmp/charon-snapshot.json', 'utf8'));
  const r = filterSignals(d.signals, config, []);
  console.log('Pass rate:', r.qualifying.length, '/', d.signals.length,
              '=', (r.qualifying.length/d.signals.length*100).toFixed(1) + '%');
  if (r.qualifying[0]) {
    const q = r.qualifying[0];
    console.log('Top:', q.symbol, 'score', q.qualityScore.toFixed(1));
  }
});
"
```

**Target pass rate: 1-5%** (10-50 trades/day given 100 signals × ~14 refreshes/hour).

- 0% → loosen: relax `maxAgeMinutes`, lower `minOrganicScore`, allow wider `minPriceChange5m`
- >10% → tighten: tighten any field that's letting too many through
- 1-5% → good. Test for 24h DRY_RUN before LIVE.

## Step 5 — Add `_comment` per setting

Every threshold needs a `_comment` field explaining the rationale so Hexa can read/tune without asking:

```json
"_maxPriceChange5m": "KEY: reject if 5m > +3% — don't chase pumps (61% of signals in 0-5% bucket are late entries)",
"maxPriceChange5m": 3,
```

## Step 6 — Deploy + restart

```bash
# 1. Backup current config + filter
cp config.json data/archive-DATE-config.json
cp modules/token-filter.js data/archive-DATE-filter.js

# 2. Write new config (with _comment fields)
# 3. Restart bot — kill old PID first (in-memory state holds old config)
kill -TERM <PID>
nohup node index.js > /tmp/charon-sniper-NEW.log 2>&1 &
```

## Step 7 — Verify within 20 min

Check the next cycle log:
- Should show `📊 [FILTER] N qualifying, M rejected` (N is non-zero if there are tokens in window)
- Top candidate should have `score > 8` and realistic fields (not 0 organic)
- Should NOT show `Cycle error: Cannot read properties of undefined` (means daily-pnl.json format bug)

If still 0 trades after 1h, the market window is just empty — that's OK. Bot will catch next fresh batch.

## Re-tuning cadence

- **Daily**: scan closed positions, look for new pattern (same exit reason 3+ times)
- **Weekly**: re-run distribution analysis on fresh snapshot, adjust thresholds
- **After market regime change** (bull → bear, meme season → utility season): full re-calibration

## Worked example (Jun 16 2026)

Pre-fix: 8/8 losers, all with 5m momentum +4% to +22% at entry. Default filter had `minPriceChange5m: -3` only (no upper bound).

Fix:
1. Distribution showed 61% of 100 signals in 0-5% bucket → `maxPriceChange5m: 3` (anti-chase)
2. Default `maxAgeHours: 12` was 8x too loose → `maxAgeMinutes: 120` (fresh window)
3. `minOrganicScore: 40` → `55` (top tier only)
4. `minBuyRatio: 0.85` → `1.5` (real demand)
5. TP ladder simplified to `[20/30, 40/35, 70/35]`

Post-fix first trade: p (5m +1.0%, organic 67, buyRatio 5.1) → peak +329.5% → +139.91% / +0.14 SOL win. New filter caught an early gem that old filter would have missed (organic 67 was too selective for old minBuyRatio 0.85 to differentiate).

## Anti-patterns to avoid

- **Setting `maxAgeHours: 12` "to be safe"** — this is the default trap. Catches post-pump dumps.
- **Loosening `minOrganicScore` to get more trades** — quality drops faster than quantity rises. Better to widen age window first.
- **Forgetting `maxOrganicScore`** — tokens with organic=100 are often fake/manipulated. Cap at 85-90.
- **Setting `minPriceChange5m` without `maxPriceChange5m`** — half the anti-chase logic is missing.
- **Using "minimum 2 sources" alone for quality** — sources count is activity, not quality. Organic + buyRatio are quality.
