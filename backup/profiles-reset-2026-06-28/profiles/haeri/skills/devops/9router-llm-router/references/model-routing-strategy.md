# Model Routing Strategy (9Router Hub)

## Speed Benchmarks (Verified Jun 2026)

| Provider | Model | Avg Response | Notes |
|----------|-------|-------------|-------|
| **Kimchi** | `kimchi/minimax-m2.7` | **~1.6s** | Fastest when credit available |
| MiMo | `xmtp/mimo-v2-omni` | ~1.6s | Fast, reliable fallback |
| TokenRouter | `tokenrouter/MiniMax-M3` | **~2.8s** | FREE via 9Router proxy |
| Kiro | `kr/claude-sonnet-4.5` | ~2.2s | Quality coding, needs OAuth |
| MiMo | `xmtp/mimo-v2-pro` | ~3.1s | Slower due to reasoning tokens (needs 50+ max_tokens) |

## User Priority: Kimchi First
User explicitly said: "Kimchi credit lebih banyak daripada mimo dan kiro"
Kimchi has $50-250/month credits → use as PRIMARY workhorse, not fallback.

## Recommended Routing

| Role | Model | Provider | Why |
|------|-------|----------|-----|
| Main chat | `kimchi/minimax-m2.7` | Kimchi (proxy) | Fast + smart + most credits |
| Quick tasks | `kimchi/minimax-m2.5` | Kimchi (proxy) | Fast, lower quality OK |
| Coding/debugging | `kr/claude-sonnet-4.5` | Kiro (free) | Claude quality, free |
| Code review | `kr/claude-sonnet-4.5` | Kiro (free) | Best reasoning |
| Quick code | `kr/claude-haiku-4.5` | Kiro (free) | Fast Claude |
| Vision | `xmtp/mimo-v2-omni` | MiMo (built-in) | Kimchi has no vision |
| Fallback | `xmtp/mimo-v2.5-pro` | MiMo (built-in) | Free, reliable |
| Internal tasks | `kr/deepseek-3.2` | Kiro (free) | Compression, title gen |

## 9Router as Single Endpoint
All models go through 9Router (http://localhost:20128/v1).
Hermes config: single custom_provider "9router" with model `kimchi/minimax-m2.7`.
Fallback chain: 9router (auto-selects best available model).

## Round-Robin Status (Jun 2026)
- Kiro: ON (Account 1 + Account 2, sticky=1) — ⚠️ OAuth tokens expire, reconnect via dashboard
- Kimchi: ON (Kimchi-01 through Kimchi-05, 5 keys, sticky=1) — keys expire/rotate, always test before trusting
- MiMo: ON (MonaAi only, no rotation possible)

## Kiro Model Availability
- **Free tier:** claude-sonnet-4.5, claude-haiku-4.5, deepseek-3.2, glm-5, MiniMax-M2.5
- **Pro tier (NOT available on free):** claude-opus-4.8 → returns `INVALID_MODEL_ID`
- User has Pro account but OAuth must be connected via dashboard reconnect flow

## Key Lifecycle
Kimchi keys can expire/rotate without warning. Always test keys before trusting.
Replace workflow: test new keys → DB insert with proxy → disable old → restart → verify round-robin.

## Config Template
```yaml
custom_providers:
  - api_key: <9router-cli-secret>
    api_mode: chat_completions
    base_url: http://localhost:20128/v1
    model: kimchi/minimax-m2.7
    name: 9router

fallback_providers: '["9router"]'

auxiliary:
  vision:
    provider: 9router
    model: xmtp/mimo-v2-omni
  compression:
    provider: 9router
    model: kr/deepseek-3.2
  delegation:
    provider: 9router
    model: kr/claude-sonnet-4.5
  title_generation:
    provider: 9router
    model: kr/claude-haiku-4.5
```
