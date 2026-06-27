> Migrated from `openrouter-free-models` (consolidated June 2026).

# OpenRouter Free Models for Hermes Agent

## Overview

OpenRouter provides access to 20+ free models from NVIDIA, Google, Qwen, Meta, and others. All $0.00 cost. This skill covers discovery, testing, and Hermes config integration.

## Step 1: Discover Free Models

```python
import urllib.request, json

url = 'https://openrouter.ai/api/v1/models'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=20)
data = json.loads(resp.read())
models = data.get('data', [])

# Filter free models (prompt=0 AND completion=0)
free = [m for m in models if m.get('pricing', {}).get('prompt', '-1') == '0' and m.get('pricing', {}).get('completion', '-1') == '0']

# Sort by context length
free.sort(key=lambda x: x.get('context_length', 0), reverse=True)

for m in free[:20]:
    print(f"{m['id']} | ctx:{m.get('context_length',0)}")
```

## Step 2: Test Models

Test with a simple prompt before committing. Use the OpenRouter API key from `.env` (`OPENROUTER_API_KEY`).

```python
data = json.dumps({
    'model': '<model_id>',
    'messages': [{'role': 'user', 'content': 'Hello, who are you? 20 words max'}],
    'max_tokens': 50
}).encode()
req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=data, headers={
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
})
resp = urllib.request.urlopen(req, timeout=30)
r = json.loads(resp.read())
print(f"Model: {r['model']}, Cost: {r['usage']}")
```

**PITFALL: Rate limiting.** Free tier has aggressive rate limits (429 on rapid-fire). Space tests 5-10 seconds apart. Don't test more than 3 models in quick succession.

**PITFALL: yaml.dump truncates API keys.** When writing config.yaml back with Python's `yaml.dump()`, keys can get truncated to masked versions (e.g., `sk-or-...f4f6` instead of full 73-char key). This causes 401 "User not found" on ALL OpenRouter calls. **Fix:** Always read real key from `.env` (`OPENROUTER_API_KEY`) and write explicitly to each provider. Verify key length = 73 chars, starts with `sk-or-v1-`.

## Step 3: Add as Custom Providers in Hermes Config

Edit `~/.hermes/config.yaml` under `custom_providers:`. Each provider needs:

```yaml
custom_providers:
  - api_key: <openrouter_api_key>
    api_mode: chat_completions
    base_url: https://openrouter.ai/api/v1
    model: <model_id>
    name: <provider_name>
```

**Use Python YAML for safe editing** (don't hand-edit the 600+ line config):
```python
import yaml
with open('/home/ubuntu/.hermes/config.yaml') as f:
    config = yaml.safe_load(f)
config['custom_providers'].append(new_provider)
with open('/home/ubuntu/.hermes/config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
```

## Step 4: Set Model Routing

After adding providers, configure which model serves which role:

- **Primary (heavy reasoning):** `model.default` + `model.provider` — nemotron-3-ultra-550b (550B, 1M ctx)
- **Fast/utility:** `auxiliary.*.model` + `provider` — nemotron-3-super-120b (120B, fast MoE)
- **Delegation:** `delegation.model` + `provider` — nemotron-3-super-120b or qwen3-coder
- **Coding:** Switch on demand — qwen3-coder (480B MoE, 1M ctx)
- **Multimodal:** Switch on demand — gemma-4-31b-it (31B, multimodal)
- **Agentic/tool-use:** Switch on demand — hermes-3-llama-3.1-405b (405B)

**PITFALL: Don't change primary model mid-session.** Changes take effect on NEXT session. Current session continues with the old provider.

## Known Free Models (as of June 7, 2026 — LIVE TESTED)

| Model | Params | Context | Speed | Status | Notes |
|-------|--------|---------|-------|--------|-------|
| nvidia/nemotron-3-ultra-550b-a55b:free | 550B | 1M | ~5.7s | ✅ Works | Heavy reasoning, but slow |
| nvidia/nemotron-3-super-120b-a12b:free | 120B | 1M | ~0.8s | ✅ Works | Reliable fast general |
| google/gemma-4-31b-it:free | 31B | 262K | ~1.6s (44.7 tok/s) | ✅ Works | Fastest free model! |
| qwen/qwen3-coder:free | 480B | 1M | — | ❌ DO NOT USE | Rate limited, caused severe slowness when set as model.default (June 2026 incident). User "lemot" and "muter-mulu". NEVER set as primary. |
| nousresearch/hermes-3-llama-3.1-405b:free | 405B | 128K | — | ✅ Works | Uncensored, great for obedient bots. Works as of Jun 10 2026. |
| cognitivecomputations/dolphin-mistral-24b-venice-edition:free | 24B | 33K | 48-78 tok/s | ⚠️ ~59% uptime | Venice Uncensored. Dolphin Mistral fine-tune. Free but unstable uptime. |
| moonshotai/kimi-k2.6:free | — | 262K | — | Not tested | Multimodal |
| qwen/qwen3-next-80b-a3b-instruct:free | 80B | 262K | — | Not tested | General |
| openai/gpt-oss-120b:free | 120B | 128K | — | Not tested | OpenAI open-source |
| meta-llama/llama-3.3-70b-instruct:free | 70B | 128K | — | Not tested | General |
| nvidia/nemotron-nano-12b-v2-vl:free | 12B | 128K | — | Not tested | Vision+language |

**PATTERN:** Models with 400B+ params may hit rate limits on free tier during peak hours. Hermes 3 405B works well for secondary/low-traffic bots. For high-traffic primary use, stick to ≤120B for reliable availability.

### Model Selection Guidance (when user shows a provider model list)

When user shows a long list of models and asks "which ones are good?", prioritize by USE CASE:

| Use Case | Look For | Why |
|----------|----------|-----|
| Coding/Dev | Qwen 3.6, DeepSeek V4, Kimi K2.6 | Strong code reasoning, long context |
| Trading/Fast | GPT-5-mini, MiniMax-M2.7, DeepSeek-V4-Flash | Fast inference, cheap |
| Analysis/Research | Qwen3.6-max, GPT-5, Gemini-2.5-pro | Deep reasoning, large context |
| All-rounder | GPT-5-mini, Kimi-K2.5 | Balanced quality/speed |
| Monitoring/Cron | DeepSeek-V4-Flash, MiniMax-M2.7 | Cheap enough for background tasks |

**Recommendation pattern:** Give TOP 3 ranked by quality, then 2-3 alternatives. User prefers concise ranked lists over verbose explanations.

**PITFALL — Third-party providers listing dead models:** Some API aggregators (Blueminds, Pioneer) list 40+ models in `/v1/models` but have NO active backends. Auth works (returns proper errors, not 401), but every model returns "No available channel" or similar. Always test actual inference before recommending. Don't assume listed = working.

**PITFALL — MiMo is the PRIMARY default:** User explicitly corrected Mona when she switched to Nemotron Ultra without permission. MiMo v2.5-pro is PRIMARY. Never switch primary without explicit user approval. Suggest alternatives but always note "MiMo tetap primary ya sayang" (user preference for Indonesian endearment).

**Non-OpenRouter free alternative (tested June 7, 2026):**
- **GeneralCompute** (`minimax-m2.7`) — 0.5s response! Fastest provider overall.
  - Base URL: `https://api.generalcompute.com/v1`
  - Key: `GC_API_KEY` in `.env` (68 chars, `pio_sk_...`)
  - Previously thought dead (403) but confirmed alive

## Pitfalls

- **Rate limits:** Free tier = 429 on rapid requests. Space API calls 5-10s apart.
- **Model availability:** Free models can be removed without notice. Always have fallbacks.
- **Nous Portal broken:** portal.nousresearch.com has persistent client-side errors. Use OpenRouter directly instead of the portal device code flow.
- **Config YAML safety:** Always use Python YAML library to edit config.yaml. Manual editing of 600+ line files is error-prone.
- **CRITICAL — yaml.dump truncates API keys:** `yaml.dump()` can REDACT or TRUNCATE API keys in custom_providers, replacing a 73-char `sk-or-v1-xxx` key with a 13-char mask like `sk-or-...f4f6`. This causes "Provider authentication failed" (401) errors. **Root cause:** tool output redaction or prior config write with masked values. **PREVENTION:** After ANY yaml.dump-based config edit, ALWAYS verify key lengths post-write:
  ```python
  for p in config.get('custom_providers', []):
      ak = p.get('api_key', '')
      if 'openrouter' in p.get('base_url','') and len(ak) < 50:
          print(f"WARNING: {p['name']} key truncated ({len(ak)} chars)")
  ```
  **FIX:** Read real key from `.env` (`OPENROUTER_API_KEY`, 73 chars) and re-inject into custom_providers. See `references/api-key-truncation-fix.md`.
- **Redacted keys in memory:** API keys get redacted in memory/tools. Store full key in .env, reference by env var name.
- **Credential auto-redaction in shell scripts:** When writing shell scripts via write_file/execute_code that contain API keys or Telegram tokens, the system auto-redacts them (e.g., `sk-or-v1-xxx` becomes `sk-or-...xxx`, bot tokens get `***` inserted). This makes embedded-credential scripts unreliable. **Workaround:** Use placeholder pattern — write script with `PLACEHOLDER` strings, then use `sed -i` to replace with actual values. Or better: have user manually `nano` the config after script runs.
- **Provider auth failure diagnosis:** When multiple OpenRouter providers fail simultaneously with 401, the issue is almost certainly a truncated key in config.yaml — NOT a dead provider. Check key length FIRST before assuming provider is down.
