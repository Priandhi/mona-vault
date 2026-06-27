# 9Router Status — Historical & Current

## ⚠️ STATUS: 9Router IS ACTIVE (Re-enabled June 11, 2026)

**9Router was briefly removed June 10, 2026 but re-enabled June 11, 2026.** It is the current central LLM hub.

The migration steps below are HISTORICAL — they were completed but then reversed.

## Current State (as of June 12, 2026)
- **9Router**: ✅ RUNNING on port 20128 (systemd `9router.service`)
- **Role**: Central LLM hub — all agents (Mona, Meridian, Charon) route through it
- **Providers connected**:
  - Kimchi.dev: minimax-m2.7 (prefix `kimchi/`)
  - TokenRouter: MiniMax-M3 (prefix `tokenrouter/`)
  - Xiaomi MiMo: mimo-v2.5-pro (via MonaAi connection)
  - 459 built-in free models
- **Hermes config**: Single custom_provider "9router" → `http://localhost:20128/v1`
- **Auth**: CLI secret at `~/.9router/auth/cli-secret`
- **DB**: `~/.9router/db/data.sqlite`

## Why 9Router Was Re-Enabled
- Key rotation: Multiple Kimchi API keys need rotation — 9Router handles this automatically
- Round-robin: Multiple provider accounts for rate limit avoidance
- Central hub: Single point for all agents instead of per-agent config

## HISTORICAL — Migration to Hermes Fallback (June 10, 2026, later reversed)

### What Was Done
1. Set Hermes `fallback_providers` chain
2. Added direct custom_providers for MiMo, Groq, Nemotron-Super
3. Stopped and disabled 9Router systemd service

### Why It Was Reversed
- Needed key rotation for multiple Kimchi accounts
- 9Router's round-robin was useful for rate limits
- Single agent config simpler than per-agent provider setup

### Tradeoffs (still valid)
| Feature | 9Router | Hermes Fallback |
|---------|---------|-----------------|
| Provider failover | ✅ | ✅ |
| Load balancing | ✅ (round-robin) | ❌ (sequential) |
| Key rotation | ✅ | ❌ |
| Resource usage | ~80MB RAM | 0 (built-in) |
| Complexity | Extra service | Config only |

## If 9Router Needs Removal Again
```bash
sudo systemctl stop 9router
sudo systemctl disable 9router
# Then configure Hermes fallback_providers + direct custom_providers
# See SKILL.md "Quick Health Check" section for provider setup
```
