# PM2 Reliable Restart for Meridian

## The Problem

`pm2 restart meridian --update-env` does NOT always clear cached environment variables from `ecosystem.config.cjs`. This causes:
- Old `LLM_BASE_URL` persisting after switching providers
- Old `LLM_API_KEY` persisting after key rotation
- Old `TELEGRAM_BOT_TOKEN` persisting after bot change

## The Fix

Always use delete + start instead of restart when changing env vars:

```bash
# WRONG (may not clear cached env):
pm2 restart meridian --update-env

# RIGHT (fully clears cached env):
pm2 delete meridian
pm2 start ecosystem.config.cjs --update-env
```

## Verification

After restart, verify the correct env vars are loaded:

```bash
# Check process environment
cat /proc/$(pm2 pid meridian)/environ | tr '\0' '\n' | grep -E "LLM_BASE|LLM_API|OPENROUTER|TELEGRAM"

# Check logs for correct model
pm2 logs meridian --lines 10 --nostream | grep "Model:"
```

## When to use which

| Scenario | Command |
|----------|---------|
| Code changes only | `pm2 restart meridian` |
| .env changes | `pm2 delete meridian && pm2 start ecosystem.config.cjs --update-env` |
| ecosystem.config.cjs changes | `pm2 delete meridian && pm2 start ecosystem.config.cjs --update-env` |
| user-config.json changes | `pm2 restart meridian` (loaded at runtime) |
