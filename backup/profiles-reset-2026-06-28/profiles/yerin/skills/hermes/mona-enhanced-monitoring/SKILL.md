---
name: mona-enhanced-monitoring
description: "Multi-provider whale tracking with fallback chain (Alchemy → Zerion → Helius), whale scoring (tier 1/2/3), convergence detection, auto-blacklist, win rate decay. Block-aware 1s polling for real-time detection."
triggers:
  - whale tracking
  - smart money
  - convergence detection
  - multi-provider
  - enhanced monitor
---

# Mona Enhanced Monitoring v2.0

Multi-provider whale tracking system with automatic failover and intelligent scoring.

## Architecture

```
mona_enhanced_monitor.py
├── ProviderChain (Alchemy → Zerion → Helius)
│   ├── Circuit breaker (5 failures = 5min cooldown)
│   ├── Auto-failover on error
│   └── Success rate tracking
├── WhaleDatabase
│   ├── Tier system (1=elite, 2=good, 3=normal)
│   ├── Win rate with decay (0.95^age_days)
│   ├── Auto-blacklist (win rate < 30%)
│   └── Blacklist duration: 7 days
├── ConvergenceDetector
│   ├── Multi-whale same-token detection
│   ├── Threshold: 3+ whales within 1 hour
│   └── Intensity levels (3=🔥🔥🔥, 4=🔥🔥🔥🔥, 5=🔥🔥🔥🔥🔥)
└── EnhancedMonitor
    ├── Block-aware polling (1s interval)
    ├── WETH/stablecoin filtering
    └── Market cap filter ($5K-$1M)
```

## Provider Fallback Chain

1. **Alchemy** (primary) — 300M CU/month free, block-aware polling
2. **Zerion** (secondary) — 3 req/sec, wallet tracking
3. **Helius** (tertiary) — Solana + EVM, enhanced API

Circuit breaker: 5 failures → 5min cooldown → auto-reset

## Whale Scoring

```python
# Decay-weighted win rate
weight = 0.95 ** age_days
decay_win_rate = sum(weighted_wins) / sum(weights)

# Tier classification
Tier 1 (Elite): decay_win_rate >= 70% AND avg_trade >= $10K
Tier 2 (Good):  decay_win_rate >= 55% AND avg_trade >= $5K
Tier 3 (Normal): everything else

# Auto-blacklist
if total_trades >= 5 and win_rate < 30%:
    blacklist(7 days)
```

## Convergence Detection

When 3+ non-blacklisted whales buy the same token within 1 hour:
- Creates CONVERGENCE alert
- Includes whale tiers, win rates, total USD
- Intensity based on whale count

## Data Files

- `~/.hermes/data/whale_db.json` — Whale database
- `~/.hermes/data/convergence_alerts.json` — Alert history
- `~/.hermes/data/whale_blacklist.json` — Blacklisted whales
- `~/.hermes/data/monitor_seen.json` — Dedup (48h prune)

## Usage

```python
from mona_enhanced_monitor import EnhancedMonitor

monitor = EnhancedMonitor(whale_addresses=['0x...'])
alerts = monitor.scan_once()  # Single scan
monitor.run_continuous(interval=5)  # Continuous loop
```

## API Key Locations

| Provider | Vault File | Format |
|----------|-----------|--------|
| Alchemy | `vault/.alchemy_key` | Plain key string |
| Zerion | `vault/.zerion_api_key` | Plain key string |
| Helius | `vault/.meridian_env` | `HELIUS_API_KEY=*** ...` |

**PITFALL:** Helius key is embedded in `.meridian_env` as a key-value pair, not a standalone file. Must parse:
```python
for line in (vault / '.meridian_env').read_text().splitlines():
    if line.startswith('HELIUS_API_KEY=***        helius_key = line.split('=', 1)[1].strip()
```

## Pitfalls

1. **Zerion persistent 429** — Free tier has per-minute/hour limits, not per-second
2. **Alchemy free tier** — 300M CU/month, ~15s polling = ~170K CU/day
3. **WETH false positives** — Always filter WETH and stablecoins
4. **Convergence false positives** — Check whale tier before alerting (tier 3 = unreliable)
