# MiMo Models Reference (Xiaomi API)

## Endpoint
- **Base URL**: `https://token-plan-sgp.xiaomimimo.com/v1`
- **Auth**: Bearer token (key in `~/.hermes/.env` as `custom_api_key`)
- **Format**: OpenAI-compatible API

## Available Models (verified June 2026)

| Model | Capabilities | Use Case |
|-------|-------------|----------|
| `mimo-v2.5-pro` | Text, code, reasoning | Primary chat/coding model |
| `mimo-v2.5` | Text, code | Lighter text model |
| `mimo-v2-pro` | Text, code | Older generation |
| `mimo-v2-omni` | **Text + Image + Audio** input → text output | **Vision** (image analysis) |
| `mimo-v2.5-tts` | Text → speech | Text-to-speech |
| `mimo-v2.5-tts-voiceclone` | Text + voice sample → cloned speech | Voice cloning (5-90s input, 8 languages) |
| `mimo-v2.5-tts-voicedesign` | Description → custom voice | Voice design (age, pitch, gender) |
| `mimo-v2.5-asr` | Speech → text | Speech recognition (Paraformer Large) |

## Vision (mimo-v2-omni)

Send images as base64 `image_url` in messages content array:

```python
import urllib.request, json, base64

url = 'https://token-plan-sgp.xiaomimimo.com/v1/chat/completions'
payload = {
    'model': 'mimo-v2-omni',
    'messages': [{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': 'What color is this image?'},
            {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}}
        ]
    }],
    'max_tokens': 100
}
req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}'
})
```

## Pitfalls

- **Vision input only**: MiMo Omni can READ images but CANNOT GENERATE images. For image gen, use Gemini or Flux.
- **Base64 only**: URL-based images return 400. Always encode to base64 first.
- **SSE format**: Responses come as Server-Sent Events even with `stream: false`. Parse accordingly.
- **9Router integration**: All MiMo models available via `http://localhost:20128/v1` with prefix `xmtp/` (e.g. `xmtp/mimo-v2.5-pro`).
- **mimo-v2-omni via 9Router**: May timeout on first call (cold start). Retry after 60s.
- **Voice models**: TTS, voiceclone, and voicedesign have different API formats — check API docs before use.
