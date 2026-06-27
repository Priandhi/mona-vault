# TokenRouter Setup & Integration (June 11, 2026)

## Context

TokenRouter discovered as emergency fallback when Kimchi credits exhausted (402 Payment Required). User provided:
- Model: MiniMax-M3 (FREE)
- API Key: `sk-ciJYPhlW2VH6GolDa09TWqgTNHzhWj4frDKVy8D6RqQhM8Z4`
- Base URL: `https://api.tokenrouter.com/v1`

## Integration via 9Router

**Manual Setup (Browser UI):**
User added TokenRouter as custom OpenAI-compatible provider via 9Router dashboard:
1. Dashboard → Providers → "Add OpenAI Compatible"
2. Name: `TokenRouter`
3. Prefix: `tokenrouter`
4. Base URL: `https://api.tokenrouter.com/v1`
5. API Key: `sk-ciJ...M8Z4`
6. API Type: `Chat Completions`

**React Form Automation Failure:**
- Browser automation via Hermes browser tools FAILED
- React controlled inputs do NOT trigger `onChange` when values set via `browser_console`
- Modal form submitted with empty fields despite JS console showing values set
- Attempted: `document.querySelector('input')[N].value = 'X'` + `dispatchEvent(new Event('input'))`
- Attempted: Native input value setter + React synthetic event dispatch
- Result: Form always submitted empty

**9Router API Approach:**
- `POST http://localhost:20128/api/auth/login` → auth cookie ✅
- `GET http://localhost:20128/api/providers` → list existing connections ✅
- `POST http://localhost:20128/api/providers` → `{"error":"Invalid provider"}` ❌
- API format for creating custom provider not documented/discovered

**Resolution:** User added manually via browser (1 minute vs 2 hours automation struggle)

## Performance Testing Results

**Test via 9Router Proxy (June 11, 2026 16:07 UTC):**

| Test | Model | Time | Tokens | Result |
|------|-------|------|--------|--------|
| Math (25% of 80) | tokenrouter/MiniMax-M3 | 3.10s | 267 | ✅ Correct (20) |
| Factual (Capital Australia) | tokenrouter/MiniMax-M3 | 3.21s | 286 | ✅ Correct (Canberra) |
| Code (Prime function) | tokenrouter/MiniMax-M3 | 5.02s | 334 | ✅ Working |
| Concise (Ethereum 1 sentence) | tokenrouter/MiniMax-M3 | 2.08s | 231 | ✅ Working |

**Average latency:** 3.35s (competitive with Kimchi minimax-m2.7 @ ~3.17s)

**Direct API Test (FAILED):**
- First request: ✅ Success
- Subsequent requests: ❌ "Invalid token" error
- Likely: Rate limit or token quotas on direct access
- **Must use via 9Router proxy** — direct API unreliable

## Model Routing

**Format:** `tokenrouter/MiniMax-M3`

**Test command:**
```bash
curl -s -X POST "http://localhost:20128/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-or-v1-..." \
  -d '{"model":"tokenrouter/MiniMax-M3","messages":[{"role":"user","content":"test"}],"max_tokens":50}'
```

## Comparison: Kimchi vs TokenRouter

**Kimchi minimax-m2.7 (BEFORE credit exhaustion):**
- Latency: ~3.17s
- Cost: $50/mo free (EXHAUSTED June 11)
- Status: ❌ 402 Payment Required

**TokenRouter MiniMax-M3:**
- Latency: ~3.35s (5% slower)
- Cost: FREE (promotional — MiniMax M3 free for limited time)
- Status: ✅ ONLY working provider as of June 11 16:07 UTC

## Critical Incident Timeline (June 11, 2026)

**15:27 UTC** — User asks "enak mana sama kimchi minimax M2.7" (test comparison)
**15:28 UTC** — Agent attempts response via kimchi/minimax-m2.7 → provider failure
**15:42 UTC** — User reports "tes" → "⚠️ The model provider failed after retries"
**16:00 UTC** — Full provider health check reveals:
  - Kimchi M2.7/M2.5: ❌ 402 Payment Required (credit exhausted)
  - Kiro Sonnet 4.5/4: ❌ OAuth expired (tokens expired 15:03 & 16:59)
  - MiMo Omni: ⚠️ Responds but content empty (API bug)
  - TokenRouter M3: ✅ ONLY working provider

**Root Cause:** NO proactive credit monitoring. Kimchi credit exhaustion not detected until total failure.

**User Reaction:** "gini terus gak ada yang backup" (frustrated — no working backup chain)

## Emergency Response Pattern

When primary provider exhausted:
1. **Immediate health check ALL providers** (don't assume failures are transient)
2. **Test working provider first** (TokenRouter in this case)
3. **Switch routing immediately** (don't wait for user permission during outage)
4. **Report status honestly** ("Kimchi habis credit, switch ke TokenRouter")

**User preference:** "kamu atur sendiri" + "aku gamau gitu lagi" → wants autonomous recovery, not explanations

## Proactive Monitoring Gap

**Missing:** Credit usage alerts for Kimchi ($50/mo free tier)
**Missing:** OAuth expiration warnings for Kiro (tokens expire ~1 hour)
**Missing:** Provider health cron job (test all providers every 6h)

**Action needed:** Create monitoring cron job:
```python
cronjob(
    action='create',
    schedule='0 */6 * * *',  # every 6 hours
    prompt='Test all providers (Kimchi, Kiro, MiMo, TokenRouter) with simple prompt. Report failures to Telegram.',
    name='provider-health-monitor'
)
```

## Browser Automation Pitfall: React Controlled Inputs

**Problem:** React forms track state internally. Setting `input.value` via JS does NOT update React's internal state, so form submission sends empty/default values.

**Attempted fixes (all failed):**
```javascript
// Attempt 1: Direct value assignment
document.querySelector('input').value = 'TokenRouter';

// Attempt 2: Trigger React synthetic event
const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
  window.HTMLInputElement.prototype, 'value'
).set;
nativeInputValueSetter.call(input, 'TokenRouter');
input.dispatchEvent(new Event('input', { bubbles: true }));

// Attempt 3: Multiple event types
input.dispatchEvent(new Event('change', { bubbles: true }));
input.dispatchEvent(new Event('blur', { bubbles: true }));
```

**Root cause:** React's `onChange` handler never fires → internal state never updates → form submits stale state.

**Workaround:** Manual user input or Playwright with proper event simulation (not available in Hermes browser tools).

**Lesson:** For React-heavy admin dashboards, prefer API automation over browser automation. When API undocumented, ask user to fill form manually (1 min) vs spending hours fighting React state.

## TokenRouter Platform Info

- **Website:** https://www.tokenrouter.com
- **Docs:** https://www.tokenrouter.com/docs
- **Models page:** Shows 103+ models including MiniMax-M3 (FREE), MiniMax-Hailuo-2.3 (video, 50% off)
- **Management API:** REST API with Bearer auth (Management Key required)
- **Free models:** MiniMax-M3 (text), potentially others (promotional)

## Next Steps

1. ✅ TokenRouter added to 9Router (manual, user completed)
2. ⏳ User testing TokenRouter performance ("pased gua tes one by one")
3. ⏳ Top-up Kimchi credit OR switch primary to TokenRouter
4. ⏳ Re-auth Kiro accounts in 9Router
5. ⏳ Setup provider health monitoring cron job

## User Feedback Signals

**"gimana solusinya yang terbaik"** → wants recommendation, not options list
**"serah kamu dah"** → trusts agent to make decision
**"pased gua tes one by one"** → wants to test before committing
**"kamu tes dulu nanti kalau enak kabari kita pake aja"** → delegate testing to agent
**"kamu atur sendiri aku gamau gitu lagi"** → frustrated, wants autonomous handling

**Lesson:** When provider outage happens, user wants:
1. Quick diagnosis (not lengthy explanation)
2. Agent to fix it autonomously
3. Brief status report ("switched to X, working now")

NOT: bullet lists, troubleshooting options, "kemungkinan A/B/C", apologies.
