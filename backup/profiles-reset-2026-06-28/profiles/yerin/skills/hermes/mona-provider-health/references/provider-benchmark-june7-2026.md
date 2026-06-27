# Provider Benchmark — June 7, 2026 (Live Test)

## Test Environment
- Server: Tencent VPS (43.163.85.51)
- Time: 22:00 UTC+8
- Test: Simple prompt ("Apa ibukota Indonesia? 1 kata."), max_tokens=3-10

## Results

| Provider | Model | Latency | tok/s | HTTP Status | Notes |
|----------|-------|---------|-------|-------------|-------|
| MiMo | mimo-v2.5-pro | 2.9s | 25.7 | 200 | Primary, local via Xiaomi API |
| GeneralCompute | minimax-m2.7 | 0.5s | N/A | 200 | FASTEST! Previously thought dead |
| Gemma-4 | gemma-4-31b-it:free | 1.6s | 44.7 | 200 | Fastest OR free model |
| Nemotron-Super | nemotron-3-super-120b:free | 0.8s | N/A | 200 | Reliable |
| Nemotron-Ultra | nemotron-3-ultra-550b:free | 5.7s | ~1.0 | 200 | Works but slow |
| 9Router | deepseek-chat-v3-0324 | 4.4s | N/A | 200 (broken JSON) | Extra data in response |
| Qwen3-Coder | qwen3-coder:free | — | — | 429 | Rate limited |
| Hermes-405B | hermes-3-405b:free | — | — | 429 | Rate limited |

## Coding Task Test (fibonacci with memoization)

| Provider | Time | Tokens Out | tok/s | Output Quality |
|----------|------|-----------|-------|----------------|
| MiMo | 2.9s | 74 | 25.7 | ✅ Correct, complete |
| Gemma-4 | 1.7s | 78 | 44.7 | ✅ Correct, complete |
| Nemotron-Super | 10.0s | 300 | 29.9 | ✅ Correct (hit max_tokens) |

## Key Findings
1. **GeneralCompute resurrection**: Previously 403 (dead), now 200 with 0.5s latency. May have been temporary outage or key issue.
2. **400B+ models always rate limited**: Qwen3-Coder (480B) and Hermes-405B consistently return 429 on free tier.
3. **Gemma-4 is the hidden gem**: 31B model but 44.7 tok/s, fastest free model by throughput.
4. **Nemotron-Ultra works but impractical**: 5.7s for simple prompt, ~1.0 tok/s. Too slow for interactive use.
5. **yaml.dump key truncation**: Confirmed bug — yaml.dump can replace 73-char API keys with 13-char masks. Always verify post-write.

## Recommended Provider Stack
1. **Primary daily**: MiMo v2.5-pro (local, 2.9s, always available)
2. **Fast backup**: GeneralCompute minimax-m2.7 (0.5s, free)
3. **Multimodal/fast OR**: Gemma-4 (1.6s, 44.7 tok/s, free)
4. **Reliable OR**: Nemotron-Super (0.8s, free)
5. **Heavy reasoning**: Nemotron-Ultra (5.7s, only if needed)
