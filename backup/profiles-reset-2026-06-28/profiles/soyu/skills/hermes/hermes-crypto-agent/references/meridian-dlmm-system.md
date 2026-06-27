# Meridian DLMM System — Configuration & Integration Notes

## System Architecture

Meridian is a **DLMM LP agent** for Meteora on Solana. It deploys liquidity to pools, NOT buy/sell tokens.

### Key Distinction
- **Meridian DLMM**: LP agent → deploy liquidity → earn fees from pool activity
- **Charon Sniper**: Token sniper → buy/sell → profit from price movement
- **These are SEPARATE systems** — DO NOT merge their dashboards or suggest merging them!

## Configuration Files

### user-config.json (main config)
Key fields:
```json
{
  "dryRun": true,
  "strategy": "bid_ask",
  "deployAmountSol": 0.1,
  "maxPositions": 2,
  "stopLossPct": -15,
  "takeProfitPct": 5,
  "trailingTriggerPct": 3,
  "trailingDropPct": 1.5,
  "screeningIntervalMin": 12,
  "managementIntervalMin": 5,
  "minTvl": 5000,
  "minHolders": 200,
  "minMcap": 50000,
  "maxBotHoldersPct": 30,
  "maxTop10Pct": 45,
  "minFeeActiveTvlRatio": 0.02,
  "screeningModel": "mimo-v2.5-pro",
  "llmBaseUrl": "https://token-plan-sgp.xiaomimimo.com/v1",
  "telegramChatId": "-1003899936547"
}
```

### ecosystem.config.cjs (PM2)
Standard PM2 config. LLM API key sometimes embedded here — check if truncated.

### .env
Contains HELIUS_API_KEY, OPENROUTER_API_KEY, TELEGRAM tokens, WALLET_PRIVATE_KEY_BASE58.

## HiveMind / Agent Meridian

### What It Is
Community learning system — agents share lessons via `api.agentmeridian.xyz`.

### Config
```json
{
  "agentId": "agt_70eec351baa90156fa761b84",
  "publicApiKey": "bWVyaWRpYW4taXMtdGhlLWJlc3QtYWdlbnRz",
  "agentMeridianApiUrl": "https://api.agentmeridian.xyz/api",
  "hiveMindUrl": "https://api.agentmeridian.xyz",
  "hiveMindPullMode": "auto"
}
```

### Files
- `hivemind.js` — bootstrap, register, sync
- `hivemind-cache.json` — cached shared lessons
- `agent-meridian.js` — API calls with x-api-key header

## Charon Integration into Meridian

Added `tools/charon-signals.js` to fetch Charon signals as pre-screening data:
- Fetches signals in parallel with Meteora pool discovery
- Cross-references Charon data with Meteora candidates
- Adds Charon metrics to LLM prompt for better decisions
- Shows Charon-only "early signals" as additional context

## MiMo Model Quirks

MiMo (mimo-v2.5-pro) via direct API:
- Frequent "Empty response, retrying..." — wastes API calls
- Fix: `maxSteps: 10` (not 15), `temperature: 0.3` (not 0.2)
- Rate limits on OpenRouter free tier — use MiMo direct API instead

## Common Issues

### API Key Truncation
`.env` and `ecosystem.config.cjs` sometimes have truncated API keys (13 chars instead of 35). Always verify key length.

### PM2 Restarts
High restart count (19+) is normal for Meridian — caused by SIGINT signals from config reloads, not crashes. Check error logs for actual issues.

### Bot Holder Filter
Common rejected pools:
- GO-SOL: bots ~34-37% (threshold 30%)
- Bountywork-SOL: bots ~31% (threshold 30%)
