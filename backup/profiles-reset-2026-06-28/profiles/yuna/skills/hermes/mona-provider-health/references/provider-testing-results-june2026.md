# Provider Testing Results — June 2026

## Test Date: 2026-06-05

## Summary

| Provider | Text | Vision | Status | Notes |
|----------|------|--------|--------|-------|
| Xiaomi MiMo (v2.5-pro) | ✅ | ❌ 404 | Active | Text/code only |
| Xiaomi MiMo (v2.5) | ✅ | ❌ 404 | Active | Text/code only |
| Xiaomi MiMo (v2-pro) | ✅ | ❌ 404 | Active | Text/code only |
| **Xiaomi MiMo (v2-omni)** | ✅ | ✅ | **Active** | **Multimodal — RECOMMENDED for vision** |
| Gemini 2.5 Flash | ✅ | ✅ | ⚠️ Quota | Free tier quota limited |
| Gemini 2.0 Flash | ✅ | ✅ | ❌ Exhausted | Free tier quota = 0 |
| Gemini 1.5 Flash | ❌ 404 | ❌ 404 | ❌ Deprecated | Removed from API |
| Pioneer | ❌ 403 | ❌ 403 | ❌ Forbidden | API key invalid/expired |
| GeneralCompute | ❌ DNS | ❌ DNS | ❌ Unreachable | Domain not resolving |
| Groq (via 9Router) | ❌ 401 | ❌ 401 | ❌ Token refresh | Auth token expired |

## Key Findings

### 1. MiMo Omni is the Vision Solution
- `mimo-v2-omni` supports both text AND vision
- Other MiMo models (v2.5-pro, v2.5, v2-pro) are TEXT ONLY
- Must use base64 encoding for images (URL-based images return 400)
- Free via Xiaomi MiMo API (user's credit)

### 2. Gemini Quota Pool Separation
- gemini-2.0-flash and gemini-2.5-flash have SEPARATE quota pools
- When 2.0-flash quota exhausted, switch to 2.5-flash (different pool)
- Free tier: 15 RPM, 1500 RPD per model
- gemini-1.5-flash/pro are DEPRECATED (404)

### 3. GC_API_KEY is Actually Pioneer Key
- Environment variable `GC_API_KEY` contains `pio_sk_19b53cf9...` (Pioneer format)
- NOT a GeneralCompute key despite the variable name
- Pioneer endpoint returns 403 (key invalid or expired)

### 4. GeneralCompute DNS Resolution Fails
- `api.generalcompute.com` does not resolve from VPS
- May be a temporary DNS issue or domain change
- 3 GC keys in config but endpoint unreachable

### 5. Available MiMo Models via Xiaomi API
```
mimo-v2-omni          # Multimodal (text + vision)
mimo-v2-pro           # Text/code
mimo-v2-tts           # Text-to-speech
mimo-v2.5             # Text/code
mimo-v2.5-asr         # Speech recognition
mimo-v2.5-pro         # Text/code (primary)
mimo-v2.5-tts         # Text-to-speech
mimo-v2.5-tts-voiceclone  # Voice cloning
mimo-v2.5-tts-voicedesign # Voice design
```

## Configuration Applied

### Vision Provider (Updated)
```yaml
auxiliary:
  vision:
    provider: custom
    model: mimo-v2-omni
    base_url: https://token-plan-sgp.xiaomimimo.com/v1
    api_key: tp-svztbaeuz8mffp7hymky4h2d4cyd2jz3e881eif8auqw4u9f
    timeout: 120
  image_gen:
    provider: gemini
    model: gemini-2.5-flash  # Updated from gemini-2.0-flash
```

## Testing Commands

### Test MiMo Text
```bash
curl -s http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"xmtp/mimo-v2.5-pro","messages":[{"role":"user","content":"Say OK"}],"max_tokens":50,"stream":false}'
```

### Test MiMo Vision
```python
import urllib.request, json, base64, struct, zlib, os

custom_key = os.environ.get('custom_api_key', '')
custom_url = os.environ.get('custom_base_url', '')

# Create test image (red pixel)
sig = b'\x89PNG\r\n\x1a\n'
ihdr = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
ihdr_chunk = b'IHDR' + ihdr
ihdr_crc = struct.pack('>I', zlib.crc32(ihdr_chunk) & 0xffffffff)
ihdr_full = struct.pack('>I', len(ihdr)) + ihdr_chunk + ihdr_crc
raw = b'\x00\xff\x00\x00'
compressed = zlib.compress(raw)
idat_chunk = b'IDAT' + compressed
idat_crc = struct.pack('>I', zlib.crc32(idat_chunk) & 0xffffffff)
idat_full = struct.pack('>I', len(compressed)) + idat_chunk + idat_crc
iend_chunk = b'IEND'
iend_crc = struct.pack('>I', zlib.crc32(iend_chunk) & 0xffffffff)
iend_full = struct.pack('>I', 0) + iend_chunk + iend_crc
img_b64 = base64.b64encode(sig + ihdr_full + idat_full + iend_full).decode()

url = f'{custom_url}/chat/completions'
payload = {
    'model': 'mimo-v2-omni',
    'messages': [{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': 'What color is this image? Reply in one word.'},
            {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}}
        ]
    }],
    'max_tokens': 100
}
req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {custom_key}'
})
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read())
print(data['choices'][0]['message']['content'])  # Expected: "Red"
```

### Test Gemini
```bash
# Read key from vault
GEMINI_KEY=$(cat ~/mona-workspace/vault/.gemini_key.txt)

# Test text
curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GEMINI_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Say OK"}]}]}'

# List available models
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GEMINI_KEY"
```
