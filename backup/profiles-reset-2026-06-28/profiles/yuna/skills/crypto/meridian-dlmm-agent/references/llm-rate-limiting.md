# LLM Rate Limiting for MiMo in agent.js

## Problem

When using MiMo with aggressive screening intervals (10 min), the LLM API can return 429 if multiple tool-call steps happen in quick succession. Each screening cycle makes 3-10 LLM calls (one per ReAct step). Without rate limiting, MiMo returns 429 → SDK retries with 500ms delay → still 429 → empty response → "Empty response, retrying..." loop.

## Solution: Rate Limiter + Custom 429 Handling

### 1. Add rate limiter constant (top of agent.js)

```javascript
let _lastLLMCall = 0;
const MIN_LLM_INTERVAL_MS = 3000; // 3 seconds between calls (MiMo rate limit)
```

### 2. Add delay before each LLM call

Before `client.chat.completions.create(reqParams)`:

```javascript
// Rate limit: ensure minimum interval between LLM calls
const now = Date.now();
const elapsed = now - _lastLLMCall;
if (elapsed < MIN_LLM_INTERVAL_MS) {
  const waitMs = MIN_LLM_INTERVAL_MS - elapsed;
  await new Promise(r => setTimeout(r, waitMs));
}
_lastLLMCall = Date.now();
response = await client.chat.completions.create(reqParams);
```

### 3. Disable SDK retries (we handle ourselves)

```javascript
const client = new OpenAI({
  baseURL: process.env.LLM_BASE_URL || "https://openrouter.ai/api/v1",
  apiKey: process.env.LLM_API_KEY || process.env.OPENROUTER_API_KEY,
  timeout: 5 * 60 * 1000,
  maxRetries: 0,  // Disable SDK retries — we handle retries ourselves with proper delays
});
```

### 4. Add 429 to error handling with longer backoff

```javascript
const errCode = response.error?.code;
if (errCode === 429 || errCode === 502 || errCode === 503 || errCode === 529) {
  const wait = errCode === 429 ? (attempt + 1) * 15000 : (attempt + 1) * 5000;
  // ... retry logic
}
```

## Important Notes

- **`maxRetries: 0` does NOT prevent ALL retries in openai v4.104.0** — some 429 retries may still appear from the SDK's internal fetch pipeline. If 429 messages persist, the source is likely `@solana/web3.js` (Helius RPC), NOT the OpenAI SDK.
- **3-second interval** is conservative for MiMo. Can try 2s if screening feels too slow.
- **15-second 429 backoff** is aggressive but necessary — MiMo rate limits can lasting 10-30 seconds.

## Results

**Before:** 4-6 empty responses per screening cycle, 2-3 minute delays
**After:** 0-1 empty responses, screening completes in ~90 seconds

**Reality check (Jun8):** Even with all these changes, 429 errors may persist because the source is often Helius RPC (`@solana/web3.js`), NOT MiMo. The LLM rate limiter helps with MiMo-specific 429s but won't touch the RPC 429s. See `references/rpc-rate-limiting.md` for the full picture. The two rate limiters (LLM + RPC) work independently and both are needed.
