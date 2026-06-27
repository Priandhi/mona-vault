# Gemini Image Generation Reference

## Models (verified June 2026)

| Model | Type | Status | Notes |
|-------|------|--------|-------|
| `gemini-2.5-flash-image` | Gemini + image gen | ⚠️ Free tier quota-limited | Best quality/cost ratio |
| `gemini-3-pro-image` | Gemini 3 Pro + image gen | ⚠️ Free tier quota-limited | Higher quality |
| `gemini-3.1-flash-image` | Gemini 3.1 Flash + image gen | ⚠️ Free tier quota-limited | Fastest |
| `imagen-4.0-generate-001` | Dedicated image gen | ❌ Paid only | Best quality |
| `imagen-4.0-ultra-generate-001` | Dedicated image gen | ❌ Paid only | Ultra quality |
| `imagen-4.0-fast-generate-001` | Dedicated image gen | ❌ Paid only | Fast |

## SDK Usage (google-genai)

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=key)

response = client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents='Generate a portrait of a woman with dark hair',
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE']
    )
)

for part in response.candidates[0].content.parts:
    if part.inline_data:
        mime = part.inline_data.mime_type  # e.g. 'image/png'
        img_data = part.inline_data.data   # raw bytes
        with open('output.png', 'wb') as f:
            f.write(img_data)
    elif part.text:
        print(part.text)
```

## REST API (without SDK)

```python
import urllib.request, json, base64

url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={key}'
payload = {
    'contents': [{'parts': [{'text': 'Generate a portrait'}]}],
    'generationConfig': {'responseModalities': ['TEXT', 'IMAGE']}
}
req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=120)
data = json.loads(resp.read())

for part in data['candidates'][0]['content']['parts']:
    if 'inlineData' in part:
        img_data = base64.b64decode(part['inlineData']['data'])
        with open('output.png', 'wb') as f:
            f.write(img_data)
```

## Rate Limits (Free Tier)

- **Per model**: ~15 requests/day for image generation
- **Quota pools are per-model**: `gemini-2.5-flash-image` and `gemini-3-pro-image` have separate quotas
- **Reset**: Daily (midnight Pacific time, ~15:00 WIB)
- **Error**: 429 RESOURCE_EXHAUSTED with `limit: 0` = daily quota hit
- **Retry delay**: Usually 20-35 seconds for per-minute limits, but daily limits need 24h wait

## Pitfalls

- **Install SDK**: `pip install google-genai` (NOT `google-generativeai` which is deprecated)
- **gemini-2.0-flash-exp** returns 404 — not a valid model name
- **imagen-4.0** models require paid plan (400 INVALID_ARGUMENT)
- **NSFW filtering**: Gemini models have content safety filters. For unrestricted image gen, use Flux via Together AI or Stable Diffusion via Replicate
- **Old SDK**: `google.generativeai` package (deprecated) doesn't support `response_modalities` in `GenerationConfig`. Use `google.genai` package instead
- **Vision vs Image Gen**: Same Gemini API, but different models. Vision models return text analysis of images. Image gen models return image bytes. Don't confuse them.
