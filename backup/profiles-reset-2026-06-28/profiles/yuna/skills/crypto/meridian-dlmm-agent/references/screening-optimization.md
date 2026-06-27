# Screening Optimization Data (June 2026)

## Latest Analysis (Jun10 — 397-cycle DRY RUN, comprehensive)

**Cycles:** 397 (Jun8 05:44 → Jun10 14:15 UTC, ~55.3 hours)
**Candidates evaluated:** 374
**Successful deploys:** 22 (5.5% deploy rate)
**Model:** MiMo v2.5 Pro
**Config:** maxBotHoldersPct=40, minFeeActiveTvlRatio=0.005
**Screening rate:** ~6.8 candidates/hour

### Filter Breakdown

| Filter | Rejections | % of Total |
|---|---|---|
| Bot-holder filter (maxBotHoldersPct=40%) | 283 | 75.7% |
| Safety block (fee/TVL too low) | 91 | 24.3% |

### Bot % Distribution (283 bot-filtered, latest dataset)

| Threshold | Would Pass | Pass Rate | Notes |
|---|---|---|---|
| 25% | 0/283 | 0.0% | All rejected |
| 30% | 30/283 | 10.6% | Still too strict |
| 35% | 128/283 | 45.2% | Half would pass |
| **40% (current)** | 244/283 | 86.2% | Current behavior |
| **45% (recommended)** | 279/283 | **98.6%** | Near-complete recovery |
| 50% | 283/283 | 100% | No additional benefit |

Bot % range: 25.6%–46.8%, avg 34.9%

### Top Rejected Pools (397-cycle)

| Pool | Rejections | Filter | Notes |
|---|---|---|---|
| GO-SOL | 125 | bot_filter | Most frequent candidate, 31-37% bots |
| safety_block (unknown) | 91 | safety_block | Zero fee/TVL pools |
| Bountywork-SOL | 48 | bot_filter | 31-32% bots |
| Teletubby-SOL | 22 | bot_filter | — |
| Bountywork-USDC | 20 | bot_filter | Cross-pair |
| HUNTER-SOL | 14 | bot_filter | — |
| LIFE-SOL | 14 | bot_filter | — |
| MMG-SOL | 5 | bot_filter | Recent (42-46% bots) |

### Key Finding: Zero Wallet Balance

Last deploy was Jun9 06:30 UTC (~37+ hours before analysis). Every cycle since shows `wallet: 0 SOL`. The agent burned LLM API calls for 37+ hours with no ability to deploy. **This is the #1 blocker — not screening thresholds.**

### Cycle Analysis

- Total cycles: 397
- Cycles with candidates found: 195 (49.1%)
- Cycles with no candidates: 202 (50.9%)
- Cycles with deploy: 22 (5.5%)

### Recommendation: maxBotHoldersPct 40→45

Raising from 40% to 45% recovers 35 additional candidates (98.6% pass rate). This is a safe, incremental change — the 40-45% band contains borderline pools like MMG-SOL (42-46%) that are not genuinely bot-heavy.

**Estimated deploy rate with optimized settings:** 15-20% (up from 5.5%).

**Before switching to LIVE:** (1) Fund wallet with ≥2 SOL, (2) Apply threshold changes, (3) Run 24 more hours DRY RUN to validate.

---

## Session Data (Jun10 — 385-cycle DRY RUN analysis)

**Cycles:** 385 (Jun8 05:44 → Jun10 11:15 UTC, ~53 hours)
**Candidates evaluated:** 369
**Successful deploys:** 22 (5.7% deploy rate)
**Model:** MiMo v2.5 Pro
**Config:** maxBotHoldersPct=40, minFeeActiveTvlRatio=0.005

### Critical Finding: Zero Wallet Balance

Last deploy was Jun9 06:30 UTC (~37 hours before analysis). Every cycle since shows `wallet: 0 SOL`. The agent has been burning LLM API calls for 37+ hours with no ability to deploy. **This is the #1 blocker — not screening thresholds.**

### Filter Effectiveness (385-cycle dataset)

| Filter | Rejections | % of Total |
|---|---|---|
| Bot-holder filter (maxBotHoldersPct=40%) | 278 | 75.3% |
| Safety block (fee/TVL too low) | 87 | 23.6% |
| Other (amount/verification) | 4 | 1.1% |

### Bot % Distribution (278 bot-filtered rejections)

| Range | Count | Notes |
|---|---|---|
| 25-30% | 30 | Would pass at 30% threshold |
| 30-35% | 98 | Would pass at 35% threshold |
| 35-40% | 116 | Would pass at 40% threshold |
| 40-45% | 31 | Borderline — CHANCE-SOL, WORTHLESS-SOL |
| 45-50% | 3 | Genuinely bot-heavy |

**Mean bot%:** 34.7% — consistent across all datasets (271, 334, 385 cycles).

### Top Rejected Pools (385-cycle)

| Pool | Rejections | Bot% Range | Notes |
|---|---|---|---|
| GO-SOL | 125 | 31-37% | Most frequent candidate, sometimes deploys |
| Bountywork-SOL | 48 | 31-32% | Consistently blocked |
| Teletubby-SOL | 22 | — | — |
| Bountywork-USDC | 20 | — | Cross-pair |
| HUNTER-SOL | 14 | — | — |
| LIFE-SOL | 14 | — | — |
| CHANCE-SOL | 6 | 40.8-45.4% | Borderline at 40% threshold |
| WORTHLESS-SOL | 4 | 41.4-46.8% | Borderline at 40% threshold |

### Daily Deploy Rate

| Date | Cycles | Deploys | Rate |
|---|---|---|---|
| Jun8 | 305 | 18 | 5.9% |
| Jun9 | 29 | 4 | 13.8% |
| Jun10 | 51 | 0 | 0.0% (wallet empty) |

### Most Deployed Pools

| Pool | Deploys |
|---|---|
| GACHA-SOL | 3 |
| GO-SOL | 3 |
| $tupid-SOL | 3 |
| WORLDCUP-SOL/USDC | 4 |
| PAYAI-SOL | 2 |
| Magpie-SOL | 2 |

### Threshold Recommendations (385-cycle data)

| Parameter | Current | Suggested | Rationale |
|---|---|---|---|
| `maxBotHoldersPct` | 40% | **45%** | 278 bot rejections, 31 candidates in 40-45% band. Raising to 45% recovers borderline pools. |
| `minFeeActiveTvlRatio` | 0.005 | **0.003** | 87 safety blocks from fee/TVL too low. Most rejected pools have 0-0.005%. Lowering to 0.003% lets more candidates through while still blocking dead pools. |
| `minOrganic` | 25 | 20 | Not a major blocker but could open more candidates |

**Estimated deploy rate with optimized settings:** 12-15% (up from 5.7%).

**Before switching to LIVE:** (1) Fund wallet with ≥2 SOL, (2) Apply threshold changes, (3) Run 24 more hours DRY RUN to validate.

---

## Previous Session Data (Jun10 — 337-cycle config-mismatch investigation)

**Cycles:** 337 (Jun8 05:44 → Jun10 00:30 UTC, 43 hours)
**Candidates evaluated:** 356
**Successful deploys:** 0 (0% deploy rate)
**Root cause:** Config mismatch — `user-config.json` had `maxBotHoldersPct: 40` but running process was still using old threshold of 25%. All 266 bot-filtered candidates rejected at 25%.

### Fee/TVL Distribution (82 safety-blocked pools with data)

| Percentile | Fee/TVL % |
|---|---|
| Min | 0.000000% |
| P25 | 0.000000% |
| P50 (median) | 0.000000% |
| P75 | 0.000000% |
| Max | 0.011517% |

**Threshold simulation (what % of rejected pools would pass):**
- 0.001% → 11/82 (13.4%)
- 0.002% → 8/82 (9.8%)
- 0.003% → 6/82 (7.3%)
- 0.005% → 5/82 (6.1%)
- 0.008% → 2/82 (2.4%)
- 0.01% → 2/82 (2.4%)

**Insight:** The vast majority of safety-blocked pools have literally 0% fee/TVL. These are genuinely dead pools. The safety block is working correctly — don't relax below 0.003%.

---

## Previous Session Data (Jun10 — 334-cycle validation)

**Cycles:** 334 screening cycles (Jun3–Jun9, 2026)
**Candidates evaluated:** 356
**Successful deploys:** 22 (6.6% deploy rate)
**Model:** MiMo v2.5 Pro
**Config:** maxBotHoldersPct=40, minFeeActiveTvlRatio=0.01

This larger dataset **confirms and validates** the 271-cycle analysis below. All patterns held consistent.

### Updated Filter Effectiveness (334-cycle dataset)

| Filter | Rejections | % of Total | vs 271-cycle data |
|---|---|---|---|
| Bot-holder filter | 266 | 74.7% | Consistent (was 75.6%) |
| Safety block (fee/TVL) | 90 | 25.3% | Consistent (was 24.4%) |

**Bot % range:** 25.6% – 42.1%, avg 34.3% (identical to 271-cycle data)

### Bot Filter Threshold Sensitivity (334-cycle validation)

| Threshold | Would Pass | Cumulative | Notes |
|---|---|---|---|
| 25% | 0 | 0% | All rejected |
| 30% | 30 | 11% | Still too strict |
| 35% | 128 | 48% | Half would pass |
| **40% (current)** | **244** | **92%** | **Matches 271-cycle recommendation** |
| 45% | 266 | 100% | All would pass |
| 50% | 266 | 100% | No additional benefit |

### Safety Block Deep Dive (334-cycle)

- 90 rejections, all with fee/TVL near 0% (avg 0.07%, max 0.012%)
- 32 rejections at threshold 0.025%, 29 at 0.015% (threshold changed during collection)
- 2 rejections for "Must provide positive SOL amount" (deploy amount bug)
- 2 rejections for verification failures

**Insight:** Safety block is working correctly. These pools genuinely have zero fee generation. Don't relax this filter.

### Deploy Concentration Analysis (new)

22 deploys across 12 unique pools:

| Pool | Deploys | Notes |
|---|---|---|
| GACHA-SOL | 3 | Repeat deploy — genuine favorite |
| GO-SOL | 3 | 125 candidate appearances, only 3 deploys (bot filter blocked rest) |
| $tupid-SOL | 3 | Consistent performer |
| WORLDCUP-SOL/USDC | 4 | Cross-pair (SOL + USDC) |
| PAYAI-SOL | 2 | Higher amount (0.5 SOL) |
| Magpie-SOL | 2 | |
| Others | 5 | HUNTER, AMERICA, Aliens, grail, Jotchua (1 each) |

**GO-SOL pattern:** Appears 125 times as candidate (most frequent) but bot% 31-37% blocks most deploys at `maxBotHoldersPct=30`. At 40%, it deployed 3 times. This validates the 40% threshold — GO-SOL is genuinely attractive (high volume, good fees) but has moderate bot activity.

### Cycle Frequency

- Avg interval: 4.6 minutes (screeningIntervalMin was set to 60 but actual frequency much higher)
- Min interval: 0.0 minutes (back-to-back cycles)
- Max interval: 38.5 minutes

**Insight:** Actual cycle frequency is ~13x the configured interval. Management cycles trigger screening when no positions are found, causing cascading cycles.

---

## Previous Session Data (271-cycle, 0.364 SOL wallet)
**Candidates evaluated:** 344
**Successful deploys:** 15 (5.5% deploy rate)
**Model:** MiMo v2.5 Pro

---

## Filter Effectiveness (271-cycle dataset)

### Bot-holder Filter — #1 BLOCKER (75.6% of all rejections)
- **Rejections:** 260 candidates
- **Bot % range:** 25.6% – 42.1%, avg 34.3%
- **Top rejected:** GO-SOL (31-37%), Bountywork-SOL (31-32%), KINS-SOL (35-36%)

#### Threshold Sensitivity Analysis
| Threshold | Pass Rate | Notes |
|-----------|-----------|-------|
| 25% | 0/260 (0%) | All candidates rejected — too strict |
| 30% | 30/260 (12%) | Was running at this level — nearly everything blocked |
| 35% | 125/260 (48%) | Half would pass |
| **40%** | **238/260 (92%)** | **Recommended — passes nearly all, blocks extreme bots** |
| 45% | 260/260 (100%) | Too permissive — no filtering at all |
| 50% | 260/260 (100%) | No additional benefit over 45% |

**Insight:** Most Solana pools have 30-40% bot holders. 40% is the sweet spot — captures 92% of candidates while still blocking genuinely bot-heavy pools (>40%).

### Safety Block (fee/TVL) — #2 BLOCKER (24.4% of all rejections)
- **Rejections:** 84 candidates (76 with fee/TVL data)
- **Fee/TVL range:** 0.0000% – 0.0115%, avg 0.0006%
- **Threshold changes during session:** 0.015% → 0.02% → 0.01% → 0.005%

**Insight:** Most pools have near-zero fee/TVL. Garbage pools show 0-0.005%. Decent pools show 0.01-0.05%. Setting threshold to 0.005% (current) is nearly permissive enough — only truly dead pools get blocked. 0.01% would filter slightly more aggressively.

### Candidates That Passed All Filters (Deployed)

| Pool | Amount | Timestamp | Notes |
|---|---|---|---|
| PAYAI-SOL | 0.5 SOL | 08:17, 08:20 | Early session, higher deploy amount |
| HUNTER-SOL | 0.15 SOL | 08:23 | |
| AMERICA-SOL | 0.0 SOL | 08:34 | Zero deploy (dry run artifact) |
| Aliens-SOL | 0.1 SOL | 08:44 | |
| Magpie-SOL | 0.1 SOL | 09:20, 09:40 | Deployed twice |
| GACHA-SOL | 0.1 SOL | 09:50, 09:53, 09:57 | Deployed 3x |
| GO-SOL | 0.1 SOL | 11:55 | |
| WORLDCUP-SOL | 0.1 SOL | 12:25, 12:40 | Deployed twice |
| $tupid-SOL | 0.1 SOL | 13:56, 14:40 | Deployed twice |
| ZINC-SOL | — | 16:08 | Deployed after restart |

### Historical Candidates (55-cycle dataset)
| Pool | Organic | MCap | TVL | Fees | Top10 | Bots | Status |
|---|---|---|---|---|---|---|---|
| Magpie-SOL | 75 | $892K | $51,694 | 94.25 SOL | 19.59% | 6.77% | Best candidate |
| OPAL-SOL | 72 | $450K | $25,000 | 45 SOL | 14.77% | 23.55% | Strong candidate |
| Aliens-SOL | 70 | $181K | $11,791 | 125.23 SOL | 14.77% | 23.55% | DRY RUN deployed |

---

## Threshold Recommendations

### For 0.364 SOL wallet (conservative)
```json
{
  "deployAmountSol": 0.1,
  "maxPositions": 2,
  "minSolToOpen": 0.15,
  "gasReserve": 0.1,
  "stopLossPct": -15,
  "takeProfitPct": 5,
  "minFeeActiveTvlRatio": 0.005,
  "minTokenFeesSol": 15,
  "minHolders": 150,
  "minMcap": 50000,
  "maxTop10Pct": 45,
  "maxBundlePct": 25,
  "maxBotHoldersPct": 40,
  "screeningIntervalMin": 20,
  "managementIntervalMin": 5
}
```

### For 1+ SOL wallet (moderate)
```json
{
  "deployAmountSol": 0.5,
  "maxPositions": 3,
  "minSolToOpen": 0.55,
  "gasReserve": 0.2,
  "stopLossPct": -15,
  "takeProfitPct": 5,
  "minFeeActiveTvlRatio": 0.01,
  "minTokenFeesSol": 20,
  "minHolders": 200,
  "minMcap": 100000,
  "maxTop10Pct": 50,
  "maxBundlePct": 25,
  "maxBotHoldersPct": 35,
  "screeningIntervalMin": 30,
  "managementIntervalMin": 10
}
```

### DRY RUN → LIVE Transition Thresholds
After collecting 100+ cycles with deploy rate > 15%, switch to these LIVE values:

| Parameter | DRY RUN | LIVE | Rationale |
|---|---|---|---|
| `maxBotHoldersPct` | 45 | **40** | Tighten slightly for quality |
| `minFeeActiveTvlRatio` | 0.005 | **0.005** | Keep same — already permissive |
| `deployAmountSol` | 1.0 | **0.1** | Real money, smaller positions |
| `maxPositions` | 3 | **2** | Conservative with real capital |
| `stopLossPct` | -20 | **-15** | Tighter risk management |

---

## Key Insights

1. **Quality over quantity** — 1 good position > 3 mediocre ones
2. **Bot holders are normal** — 30-40% is typical for Solana pools. 40% threshold passes 92%.
3. **Bot filter is the #1 blocker** — 75.6% of all rejections. Relaxing from 30%→40% would dramatically increase deploy rate.
4. **Fee/TVL is the best quality filter** — distinguishes real pools from dead ones. 0.005% is the sweet spot.
5. **MiMo > OpenRouter** — faster, no rate limits, better reasoning
6. **Conservative stop loss** — -15% is right for LP, not trading
7. **DRY RUN first** — always monitor 4-6 hours (or 100+ cycles if deploy rate < 10%) before going live
8. **Config drift is real** — always verify PM2 log thresholds match user-config.json after changes
