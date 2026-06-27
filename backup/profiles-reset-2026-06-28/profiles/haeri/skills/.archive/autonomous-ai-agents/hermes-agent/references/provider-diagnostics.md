# Provider Diagnostics — When the User Can't Reach Mona

## Problem
User reports "API key error", "terputus" (disconnected), "gak bisa chat", or similar
connectivity issues via Telegram/gateway.

## Common Mistake
Jumping to project-specific configs (e.g. checking Meridian's Telegram bot token)
instead of checking the MAIN HERMES MODEL PROVIDER first.

## Correct Diagnostic Sequence

1. **Check main model provider health** — `grep` config.yaml for current provider + API key
2. **Test the provider endpoint** — `curl` the base_url with a simple completion request
3. **Check gateway logs** — `tail ~/.hermes/logs/gateway.log` for 401/429/502/503 errors
4. **Check .env for missing/expired keys** — custom providers in `custom_providers` section
5. ONLY THEN check project-specific configs if main provider is healthy

## This User's Provider Stack (as of June 2026)

Primary: MiMo (`custom_providers` name "mimo")
- URL: `https://token-plan-sgp.xiaomimimo.com/v1`
- Model: `MiMo-V2.5-Pro`
- API key prefix: `tp-svztbaeu...`

Fallback 1: GeneralCompute (name "generalcompute")
- URL: `https://api.generalcompute.com/v1`
- Model: `minimax-m2.7`

Fallback 2: OpenRouter (name "nemotron-ultra", "nemotron-super", "gemma4")
- URL: `https://openrouter.ai/api/v1`
- Models: `nvidia/nemotron-3-ultra-550b-a55b:free`, `nvidia/nemotron-3-super-120b-a12b:free`, `google/gemma-4-31b-it:free`

## Key Lesson
When user says "API key error" on Telegram → they mean the HERMES model provider,
NOT a side project's API key. The agent literally cannot respond if its own model
provider is down. Always check self-diagnosis first before diagnosing projects.

## Provider Cleanup
For detailed steps on removing unused providers and API keys, see:
`references/provider-cleanup.md`
