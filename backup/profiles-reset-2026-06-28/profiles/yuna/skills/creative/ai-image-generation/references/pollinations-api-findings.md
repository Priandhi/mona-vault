# Pollinations.ai API — Test Results (June 2026)

## Verdict: UNRELIABLE — do not recommend

### GET Endpoint (`image.pollinations.ai/prompt/{encoded}`)
- Works for 1 request, then returns **402 "Queue full"** (max 1 queued per IP)
- Requires URL-encoding the prompt
- Returns 768x768 JPEG regardless of requested `width`/`height`
- "Unlimited access" requires payment via crypto (Base chain USDC)
- Rate limit: 1 request per IP, then 402

### POST Endpoint (`image.pollinations.ai/`)
- Returns **200 OK** but generates **random abstract art** that completely ignores the prompt
- Tested with both simple and detailed prompts — same garbage output every time
- The `prompt` field in JSON body is not respected
- Model param (`flux`, `turbo`) doesn't help

### POST Endpoint (`text.pollinations.ai/openai/images/generations`)
- OpenAI-compatible format
- Returns 402 rate limit similar to GET
- Not tested successfully due to rate limiting

### Summary
- POST endpoint is broken (ignores prompts)
- GET endpoint works but rate-limited to 1 request per IP
- Not suitable as a free alternative to HuggingFace FLUX
- Date tested: June 5, 2026
- VPS IP: 43.163.85.51
