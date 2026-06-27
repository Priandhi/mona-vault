# Kimchi.dev Response Format Reference (Verified Jun11)

## Working Models (content in `message.content`)

| Model | Content Location | Format | Speed |
|-------|-----------------|--------|-------|
| `minimax-m2.7` | `message.content` | Wrapped in `<think>...</think>` tags | ~1s |
| `minimax-m2.5` | `message.content` | Wrapped in `<think>...</think>` tags | ~2s |
| `nemotron-3-super-fp4` | `message.content` | Plain text + `reasoning_content` | ~1.1s |

## Thinking Models (behavior depends on max_tokens)

| Model | Content Location | Notes |
|-------|-----------------|-------|
| `kimi-k2.5` | `content` (when max_tokens≥50) or `reasoning_content` (when max_tokens<50) | See below |
| `kimi-k2.6` | Same as kimi-k2.5 | Consistently times out, unusable |

**kimi-k2.5 max_tokens behavior:**
- `max_tokens: 10` → reasoning consumes all tokens → `content: null`, text in `reasoning_content`
- `max_tokens: 50+` → returns proper `content: " Hello! How can I help you today?"` + `reasoning_content`
- Verified Jun11: NOT a thinking-model issue — just a token budget issue. Works fine with adequate max_tokens.

## Parsing Pattern

```python
# Safe content extraction for any Kimchi model
msg = response['choices'][0]['message']
content = msg.get('content') or msg.get('reasoning_content', '')
# Strip thinking tags if present
import re
content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
```

## User-Agent Requirement

Kimchi.dev Cloudflare blocks Python's default `urllib.request` User-Agent.
- ❌ Default Python UA → 403 Forbidden
- ✅ `User-Agent: curl/8.5.0` → works
- ✅ 9Router Node.js client → works (uses undici UA)

Fix for direct Python testing:
```python
headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
    'User-Agent': 'curl/8.5.0'  # Required!
}
```

## SSE vs JSON Format

- Kimchi models via 9Router: return plain JSON
- Kiro models via 9Router: return SSE streaming by default
- Always add `"stream": false` when testing via Python scripts
