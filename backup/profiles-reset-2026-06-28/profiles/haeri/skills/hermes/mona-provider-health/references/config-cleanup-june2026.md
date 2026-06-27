# Config Cleanup — June 10, 2026

## What was removed

### Custom Providers (3 removed)
- `generalcompute` (minimax-m2.7) — not in fallback chain, unused
- `nemotron-ultra` (nvidia/nemotron-3-ultra-550b-a55b:free) — 550B too slow (~5.7s), unused
- `gemma4` (google/gemma-4-31b-it:free) — unused, not in fallback chain

### Legacy Fields (3 removed)
- `custom_api_key` — legacy, replaced by per-provider `api_key` in `custom_providers[]`
- `custom_base_url` — legacy, replaced by per-provider `base_url` in `custom_providers[]`
- `model.base_url` — legacy, provider routing handled by `custom_providers[]`

### Personalities (10 removed)
Removed: catgirl, pirate, shakespeare, surfer, uwu, hype, kawaii, noir, philosopher, default
Kept: helpful, concise, creative, teacher

## What was kept

### Custom Providers (3 kept)
- `mimo` — primary (mimo-v2.5-pro via token-plan-sgp.xiaomimimo.com)
- `nemotron-super` — groups default (nvidia/nemotron-3-super-120b-a12b:free via OpenRouter)
- `groq` — fallback 1 (llama-3.3-70b-versatile via api.groq.com)

### Fallback Chain
```
mimo → groq → nemotron-super
```

## Backup
- `~/.hermes/config.yaml.backup.20260610_062805`

## Why
- Simplify config — fewer providers = easier to debug
- Reduce confusion — only keep providers that are actually used
- Prevent cron job errors — unused providers with wrong model IDs cause 400/401 errors
- Cleaner fallback chain — 3 providers is enough for single-user setup

## How to restore
```bash
cp ~/.hermes/config.yaml.backup.20260610_062805 ~/.hermes/config.yaml
hermes gateway restart
```
