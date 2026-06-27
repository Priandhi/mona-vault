# Provider Cleanup — Removing Unused Providers & API Keys

## When to Clean Up
- Provider fails repeatedly (auth errors, rate limits)
- `hermes status` shows `✗ (not set)` for providers you don't use
- Commented-out API keys in `.env` for providers you'll never use
- User says "remove model yang gak bisa di pake"

## Cleanup Steps

### 1. Backup First
```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.backup.$(date +%Y%m%d_%H%M%S)
cp ~/.hermes/.env ~/.hermes/.env.backup.$(date +%Y%m%d_%H%M%S)
```

### 2. Identify What's Used
```bash
hermes status 2>/dev/null | grep -A 30 "API Keys"
hermes doctor 2>/dev/null | grep -E "✗|⚠"
```

### 3. Edit config.yaml

**Remove failed providers from `providers` section:**
```yaml
# Remove entries like:
providers:
- api_key: sk-xxx
  model: deepseek-v4-flash
  name: bai
```

**Remove unused STT/TTS sections:**
```yaml
stt:
  # REMOVE these if not configured:
  elevenlabs: ...
  mistral: ...
  openai: ...

tts:
  # REMOVE these if not configured:
  edge: ...
  elevenlabs: ...
  mistral: ...
  neutts: ...
  openai: ...
  piper: ...
  xai: ...
```

**Change image_gen if gemini unavailable:**
```yaml
auxiliary:
  image_gen:
    model: mimo-v2-omni  # Use working provider
    provider: mimo
```

### 4. Clean .env File
Remove commented-out API keys for unused providers:
```bash
# Remove lines like:
# GEMINI_BASE_URL=...
# KIMI_API_KEY=***
# MINIMAX_API_KEY=***
# FIRECRAWL_API_KEY=***
# FAL_KEY=
# BROWSERBASE_API_KEY=***
# GITHUB_TOKEN=***
```

### 5. Verify
```bash
hermes doctor 2>/dev/null
hermes status 2>/dev/null
```

## Common Provider Status

### Keep (Working)
- `mimo` — Xiaomi MiMo (primary)
- `generalcompute` — MiniMax/Gemini
- `nemotron-ultra` — OpenRouter free (550B)
- `nemotron-super` — OpenRouter free (120B)
- `gemma4` — OpenRouter free (31B)

### Remove (Unused/Failed)
- `bai` — DeepSeek v4 Flash (often fails)
- Any provider with `✗ (not set)` in status
- Commented-out API keys in .env

## Key Lesson
When user says "API key error" on Telegram → they mean the HERMES model provider,
NOT a side project's API key. The agent literally cannot respond if its own model
provider is down. Always check self-diagnosis first before diagnosing projects.
