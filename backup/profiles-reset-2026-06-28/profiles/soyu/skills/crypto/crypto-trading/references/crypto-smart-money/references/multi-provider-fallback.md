# Multi-Provider Fallback Architecture

## Problem
Single-provider whale tracking systems fail silently when the API goes down. Zerion has persistent 429 rate limits. Alchemy free tier can be exhausted.

## Solution: Fallback Chain with Circuit Breaker

### Provider Priority
1. **Alchemy** (primary) — 300M CU/month free, block-aware polling
2. **Zerion** (secondary) — 3 req/sec, wallet tracking, trade classification
3. **Helius** (tertiary) — Solana + EVM, enhanced API

### Circuit Breaker Logic
- Track failures per provider
- After 5 consecutive failures → mark provider as "down"
- Cooldown: 5 minutes before retry
- Auto-reset on success
- Fall through to next provider in chain

### API Key Locations
| Provider | Vault File | Format |
|----------|-----------|--------|
| Alchemy | `vault/.alchemy_key` | Plain key string |
| Zerion | `vault/.zerion_api_key` | Plain key string |
| Helius | `vault/.meridian_env` | `HELIUS_API_KEY=*** ...` |

**PITFALL:** Helius key is embedded in `.meridian_env` as a key-value pair, not a standalone file. Must parse: `line.split('=', 1)[1].strip()`

### Implementation
See `~/.hermes/scripts/mona_enhanced_monitor.py` for the `ProviderChain` class.

### Whale Scoring
- **Tier 1 (Elite):** decay_win_rate >= 70%, avg_trade >= $10K
- **Tier 2 (Good):** decay_win_rate >= 55%, avg_trade >= $5K
- **Tier 3 (Normal):** everything else
- **Auto-blacklist:** win_rate < 30% after 5+ trades → 7 days

### Convergence Detection
3+ non-blacklisted whales buying same token within 1 hour → SUPER ALERT
Intensity: 3=🔥🔥🔥, 4=🔥🔥🔥🔥, 5=🔥🔥🔥🔥🔥
