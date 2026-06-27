# 9Router Auxiliary Config — Empty Fields (Jun 2026)

## Finding
The `auxiliary:` block in `~/.hermes/config.yaml` exists but ALL model fields are EMPTY:

```yaml
auxiliary:
  approval:     model: ''  # KOSONG
  curator:      model: ''  # KOSONG  
  compression:  model: ''  # KOSONG
  title_generation: model: ''  # KOSONG
  # delegation, vision fields likely missing entirely
```

## Impact
Routing is documented but NOT ACTIVE. All auxiliary tasks fall back to main model.

## Required Configuration
```yaml
auxiliary:
  vision:
    model: xmtp/mimo-v2-omni
    provider: 9router
  compression:
    model: kr/deepseek-3.2
    provider: 9router
  delegation:
    model: kr/claude-sonnet-4.5
    provider: 9router
  title_generation:
    model: kr/claude-haiku-4.5
    provider: 9router
```

## Before Enabling Kiro Routes
1. Verify Kiro OAuth still valid (expires ~1 hour)
2. Test: `curl http://localhost:20128/api/status` — check Kiro status
3. If expired: reconnect via `http://localhost:20128/dashboard/providers/kiro`

## Why This Matters
- Coding/delegation tasks currently use Kimchi → should use Kiro (free, better for code)
- Vision tasks use Kimchi → should use MiMo (only vision model)
- Compression uses Kimchi → should use Kiro deepseek (free, good compression)
- Wasting Kimchi credits on tasks other models do better/faster/free