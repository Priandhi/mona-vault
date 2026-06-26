---
date: 2026-06-15
agent: MONA
task: Setup Meridian bot to use M3 via 9Router
---

# Task: Meridian → M3 via 9Router

## Goal
Switch Meridian DLMM bot LLM from `minimax/minimax-m2.7` (OpenRouter) → `tokenrouter/MiniMax-M3` (via local 9Router proxy).

## Context
- User decided to use MiniMax M3 as primary model across the stack
- 9Router already runs on :20128 with tokenrouter provider pre-configured (5 sibling connections: MONA/YERIN/YUNA/SOYU/HAERI + 1 original)
- Meridian was using OPENROUTER_API_KEY with default OpenRouter base URL
- User wanted self-hosted routing through 9Router (cost control, single ingress)

## Actions Taken

### 1. Verified 9Router routing
- `curl /v1/models` on :20128 → returns xmtp/* and aerolink/* but NOT tokenrouter (custom provider models don't always appear in /v1/models — known 9Router quirk)
- Direct `POST /v1/chat/completions` with `model: "tokenrouter/MiniMax-M3"` + Bearer from `~/.9router/auth/cli-secret` → 200 OK, response from "MiniMax AI" ✅

### 2. Updated `/home/ubuntu/meridian-agent/user-config.json`
```json
{
  "managementModel": "tokenrouter/MiniMax-M3",
  "screeningModel":  "tokenrouter/MiniMax-M3",
  "generalModel":    "tokenrouter/MiniMax-M3",
  "llmBaseUrl":      "http://localhost:20128/v1",
  "llmApiKey":       "<9router-cli-secret>",
  "llmModel":        "tokenrouter/MiniMax-M3"
}
```
- Both `.env` and `user-config.json` are git-ignored in meridian-agent → safe to write key
- Left `dryRun: true` unchanged (safety)
- Set all 3 model fields to M3 for consistency

### 3. Verified config loads
```bash
node -e "import('./config.js').then(c => console.log(c.config.llm))"
# managementModel: tokenrouter/MiniMax-M3
# screeningModel : tokenrouter/MiniMax-M3
# generalModel   : tokenrouter/MiniMax-M3
```

### 4. End-to-end LLM test
```bash
node cli.js screen --dry-run --silent
```
Result: M3 responded with proper screening report (NO DEPLOY — all candidates blocked by config gates). LLM call chain: Meridian → 9Router (localhost:20128) → tokenrouter upstream → M3. ✅

## Decisions

1. **Stored key in user-config.json (not .env)** — both are git-ignored, but user-config.json is the standard place Meridian expects llmBaseUrl/llmApiKey per its config.js schema (line 39-40).
2. **Used 9Router's cli-secret as bearer token** — this is the local ingress auth for 9Router itself, not a tokenrouter.com key. Meridian's API key now authenticates with 9Router, which then routes to tokenrouter upstream.
3. **Set all 3 roles (screener/manager/general) to same M3 model** — user asked for M3 as primary, no need to differentiate. Cost optimization.
4. **Did NOT enable Meridian in PM2** — it was disabled when I started. User didn't ask to enable. Dry-run mode is on anyway.

## Issues
- None. Migration was clean.

## Notes
- 9Router's `/v1/models` doesn't list tokenrouter models but they work via direct API call — this is a known quirk (custom provider models may not appear in /v1/models but still work).
- The 5 sibling tokenrouter connections (MONA/YERIN/YUNA/SOYU/HAERI) all share prefix `tokenrouter` and base `https://api.tokenrouter.com/v1`. 9Router will round-robin across them (assuming the strategy is configured in settings).
- The original `MiniMax-M3` connection (id `76ec5ebb...`) shows `errorCode: 403` and `lastError: null` — likely IP-blocked or expired. Left it alone; sibling connections are clean.

## Next Steps
- (Optional) Set up round-robin strategy for tokenrouter provider in 9Router settings table so all 5 sibling keys share load
- (Optional) Re-enable Meridian in PM2 (`pm2 start meridian` + `pm2 save`) when user wants it live
- Monitor first live cycle to confirm M3 quality is sufficient for screening/management decisions (previous model was m2.7 — different reasoning style)
