# TokenRouter vs 9Router — Key Differences

## Overview

| Aspect | TokenRouter | 9Router |
|--------|-------------|---------|
| Type | Commercial SaaS (tokenrouter.com) | Self-hosted proxy (local VPS) |
| Access | Web dashboard + API key | Local port 20128 + cloudflared tunnel |
| Cost | Pay per usage, free tiers available | Free (self-hosted), own API keys |
| Providers | Many commercial providers | Your own API keys + OAuth connections |
| MiniMax M3 | Free tier on tokenrouter.com | NOT available unless you have key |

## TokenRouter Free Models (Jun 2026)

- **MiniMax-M3**: FREE (both input and output $0)
- **MiniMax-Hailuo-2.3**: 50% off (video model)

These are ONLY free on TokenRouter's own infrastructure.

## How to Use TokenRouter in 9Router

If you want TokenRouter's free models in 9Router:

1. Register at https://tokenrouter.com
2. Get API key from Dashboard → API Keys
3. In 9Router: Add as **Custom OpenAI Compatible** provider
4. Use TokenRouter endpoint: `https://api.tokenrouter.com/v1`
5. Add your TokenRouter API key

**Limitation**: This adds TokenRouter as another provider to route through 9Router, but you're still paying TokenRouter's rates. The "free" only applies if using TokenRouter directly.

## When to Use Which

- **TokenRouter direct**: When you want their specific free models (MiniMax M3) without setting up your own keys
- **9Router**: When you want to aggregate ALL your providers (Kimchi, Kiro, MiMo, custom) under one endpoint with fallback routing

## Confusion Point

User saw "MiniMax M3 free" on tokenrouter.com and asked if it could be used in 9Router. The answer is: indirectly, by adding TokenRouter as a custom provider — but the free tier is TokenRouter's own, not 9Router's.

If the goal is just accessing MiniMax M3 free, using TokenRouter directly (not through 9Router) is simpler.