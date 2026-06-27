# Cascading 402 → Fallback → 429 Failure Mode

## The Pattern (Observed Jun10 — Meridian)

When OpenRouter paid credits run out, the failure chain is:

1. **Primary model returns 402** (payment required / credit exhaustion)
2. **Fallback logic activates**, switches to free model (e.g., `meta-llama/llama-3.3-70b-instruct:free`)
3. **Free model returns 429** (rate limited) — free models share per-account rate limits
4. **Agent loop retries**, hits 429 again on every step
5. **Max steps reached** without final answer → agent cycle fails completely

## Why This Is Different From Simple 402 or 429

- **Simple 402**: Primary model has no credits, but fallback to free model works. Agent is degraded but functional.
- **Simple 429**: Temporary rate limit, self-resolves in 10-30 minutes.
- **Cascading 402→429**: Primary permanently down (no credits), AND free model temporarily rate limited. Agent is completely non-functional until EITHER credits are added OR free model rate limit resets.

## Log Signature

```
[AGENT] Error 402 — switching to fallback model meta-llama/llama-3.3-70b-instruct:free
[ERROR] Agent loop error at step N: 429 Provider returned error
[AGENT] Rate limited, waiting 30s...
... repeats for all 10 steps ...
[AGENT] Max steps reached without final answer
```

## Decision Tree

1. **If 402 alone** (fallback works) → report as degraded, not critical
2. **If 429 alone** (paid model) → wait 10-30 min, self-resolves
3. **If 402→429 cascade** → report as critical, action needed:
   - Add OpenRouter credits (immediate fix)
   - OR wait for free model rate limit to reset (~30 min) + accept degraded operation
   - OR switch primary model to a different paid model with credits

## Auto-Heal Behavior

**Do NOT restart the process** for 402/429 errors. The process is running fine — the issue is upstream API billing/rate limits. Restarting just burns another restart counter and hits the same errors.

**Report to operator** with diagnosis: "Meridian agent loop non-functional — primary model 402 (no credits) + free fallback 429 (rate limited). Needs API credit top-up."

## Validation Command

Check if the fallback model is currently rate-limited:

```bash
curl -s -H "Authorization: Bearer YOUR_KEY" \
  "https://openrouter.ai/api/v1/chat/completions" \
  -d '{"model":"meta-llama/llama-3.3-70b-instruct:free","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',{}).get('code','OK'), d.get('error',{}).get('message',''))"
```

If this returns 429, the free model tier is still rate-limited. Wait or add paid credits.
