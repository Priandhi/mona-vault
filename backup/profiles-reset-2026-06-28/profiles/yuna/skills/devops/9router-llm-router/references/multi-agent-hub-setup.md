# Multi-Agent LLM Hub Setup via 9Router

## Architecture

All agents connect to 9Router as the single LLM endpoint with different fallback combos per role.

```
9Router (localhost:20128)
├── Provider: Xiaomi MiMo (Token Plan) — user's API key, primary
├── Provider: Kiro AI Account 1 (Claude Sonnet 4.5 via Google OAuth)
├── Provider: Kiro AI Account 2 (Claude Sonnet 4.5 via Google OAuth, round-robin)
├── Built-in: deepseek/deepseek-v4-flash (free, fast)
├── Built-in: deepseek/deepseek-v4-pro (free, strong reasoning)
├── Built-in: ag/claude-sonnet-4-6 (free, reasoning)
├── Built-in: ag/gemini-3-flash (free, multimodal)
```

## Model ID Format (CRITICAL)

When using 9Router as a provider, model IDs use the **9Router prefix**, NOT the direct API model name:

| Direct API | Through 9Router | Notes |
|-----------|----------------|-------|
| `mimo-v2.5-pro` | `xmtp/mimo-v2.5-pro` | MiMo via Token Plan |
| — | `kr/claude-sonnet-4.5` | Kiro AI (free tier) |
| — | `kr/claude-haiku-4.5` | Kiro AI (fast) |
| — | `kr/deepseek-3.2` | Kiro AI |
| — | `deepseek/deepseek-v4-flash` | Built-in free |
| — | `ag/claude-sonnet-4-6` | Built-in free |

**Common mistake:** Using `mimo-v2.5-pro` in Hermes custom_providers when base_url points to 9Router — must be `xmtp/mimo-v2.5-pro`.

## Combo Setup (via Dashboard → Combos)

### Combo: mona-primary
```
1. xmtp/mimo-v2.5-pro          → Primary (fast, user's API key)
2. kr/claude-sonnet-4.5         → Kiro AI (free, strong reasoning)
3. deepseek/deepseek-v4-pro     → Strong reasoning, free
4. deepseek/deepseek-v4-flash   → Fast + smart, free
5. ag/claude-sonnet-4-6         → Fallback, reasoning
```

### Combo: meridian-deep
```
1. xmtp/mimo-v2.5-pro          → Primary
2. kr/claude-sonnet-4.5         → DeFi pool analysis
3. deepseek/deepseek-v4-pro     → DeFi reasoning
4. kr/deepseek-3.2              → Backup
```

### Combo: charon-fast
```
1. xmtp/mimo-v2.5-pro          → Fast
2. deepseek/deepseek-v4-flash   → Fast + smart
3. ag/gemini-3-flash            → Low latency fallback
```

## Agent Config Updates

### Hermes (Mona)
Add to `~/.hermes/config.yaml` under `custom_providers`:
```yaml
- api_key: <9router-api-key>  # from ~/.9router/auth/cli-secret
  api_mode: chat_completions
  base_url: http://localhost:20128/v1
  model: xmtp/mimo-v2.5-pro    # ⚠️ MUST use xmtp/ prefix for 9Router!
  name: 9router
```

### Meridian
Add to `.env`:
```
LLM_BASE_URL=http://localhost:20128/v1
LLM_API_KEY=<9router-api-key>
LLM_MODEL=xmtp/mimo-v2.5-pro
```

⚠️ Meridian loads from `process.env.LLM_BASE_URL`, not from config files. PM2 needs `--update-env` to pick up .env changes.

### Charon
Charon (Node.js sniper) does not have LLM integration — it uses its own signal processing. No changes needed.

## Kiro Dashboard Setup (User-Executed)

The user must log into 9Router dashboard from their phone/laptop and complete Google OAuth for each Kiro account:

1. Open Cloudflare tunnel URL in browser
2. Login with dashboard password
3. Providers → Kiro AI → Add Connection
4. Select "AWS Builder ID" → "Continue with Google"
5. Login with Kiro account email
6. Repeat for second account
7. 9Router auto-enables Round Robin for multiple connections

**Why user must do this:** 9Router's Kiro Google OAuth requires browser interaction. The agent cannot automate this step — AWS bot detection blocks headless browser flows. Only the user's phone browser can complete the auth.

## Token Management

- MiMo API key: from https://token-plan-sgp.xiaomimimo.com
- Kiro: authenticated via Google OAuth through dashboard (NOT API keys)
- Each Kiro account gets separate rate limits — 2 accounts = 2x capacity
- 9Router auto-refreshes Kiro tokens when they expire

## Pitfalls

- **PM2 env caching**: After changing .env for Meridian, must `pm2 delete meridian && pm2 start ecosystem.config.cjs` — `pm2 restart` alone does not reload env vars
- **Kiro token expiry**: Access tokens expire after ~1 hour; refresh tokens last longer. 9Router auto-refreshes if refresh token is valid
- **Combo model names**: Must use full `9router-prefix/model` format (e.g., `deepseek/deepseek-v4-flash`, not just `deepseek-v4-flash`)
- **MiMo prefix through 9Router is `xmtp/`** — NOT `mimo/`. The prefix `mimo` refers to the direct Xiaomi API. Through 9Router, it's `xmtp/mimo-v2.5-pro`
