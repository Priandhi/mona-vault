# Threshold Tweaking Guide for Meridian

When user asks "tweak threshold apa?" — explain the TRADEOFF of each, not just the value.

## Key thresholds explained

### minFeeActiveTvlRatio (default: 0.05%)
- **What it does**: Filters pools by fee income relative to TVL
- **Too high (0.05%)**: Rejects good pools like AMERICA-SOL (0.0463%)
- **Too low (0.01%)**: Lets through pools with no fee activity
- **Sweet spot**: 0.03% (small wallet), 0.04% (moderate)
- **User lesson**: AMERICA-SOL was rejected by 0.04% threshold despite having decent metrics

### minTokenFeesSol (default: 30)
- **What it does**: Minimum all-time fees in SOL
- **Too high (30)**: New pools with potential can't pass
- **Too low (5)**: Dust pools with minimal trading
- **Sweet spot**: 15 (small wallet), 30 (moderate)
- **Rationale**: Pool baru tapi organic tinggi = potensi besar

### minHolders (default: 500)
- **What it does**: Minimum token holder count
- **Too high (500)**: Most Solana pools don't reach 500 holders
- **Too low (50)**: Bot-dominated pools pass
- **Sweet spot**: 200 (small wallet), 500 (moderate)

### minMcap (default: 150000)
- **What it does**: Minimum market cap in USD
- **Too high (150K)**: Early stage pools missed
- **Too low (10K)**: Dust/scam risk
- **Sweet spot**: 50K (small wallet), 150K (moderate)

### maxTop10Pct (default: 60%)
- **What it does**: Maximum percentage held by top 10 wallets
- **Too high (60%)**: Whale-dominated pools pass → dump risk
- **Too low (30%)**: Too strict, few pools qualify
- **Sweet spot**: 45% (recommended)
- **User lesson**: User wanted tighter control to avoid whale dumps

### maxBundlePct (default: 30%)
- **What it does**: Maximum percentage of holders funded by same source
- **Too high (30%)**: Manipulated pools pass
- **Too low (15%)**: Legitimate projects with common funder rejected
- **Sweet spot**: 25% (recommended)

### maxBotHoldersPct (default: 30%)
- **What it does**: Maximum percentage of bot holders (from Jupiter audit)
- **Too high (30%)**: Fake volume pools pass
- **Too low (15%)**: Normal bot activity rejected
- **Sweet spot**: 25% (recommended)
- **Verified**: HUNTER-SOL correctly filtered at 28.15% (above 25% threshold)

## Filter relationships

These are **independent gates** — a pool must pass ALL of them. Lowering any one opens more candidates but increases scam risk.

```
Pool → [minFeeActiveTvlRatio] → [minTokenFeesSol] → [minHolders] → [minMcap]
     → [maxTop10Pct] → [maxBundlePct] → [maxBotHoldersPct] → [minOrganic]
     → LLM Agent decision → Deploy or Skip
```

## User preference

User wants to understand WHY each threshold matters, not just WHAT value to set. Always explain the tradeoff when discussing thresholds. User explicitly asked: "tweak threshold apa?" — meaning they want Mona to proactively suggest improvements, not wait for user to ask.
