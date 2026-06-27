# Gemini Image Generation

Google's native image generation via Gemini API. Free tier but very limited quota.

## Models (June 2026)

| Model | Type | Notes |
|-------|------|-------|
| `gemini-2.5-flash-image` | Flash + image gen | Fast, limited quota |
| `gemini-3-pro-image` | Pro + image gen | Higher quality, limited quota |
| `gemini-3.1-flash-image` | Latest flash + image gen | Newest, limited quota |
| `imagen-4.0-generate-001` | Dedicated image gen | **Paid only** (400 on free tier) |
| `imagen-4.0-ultra-generate-001` | Dedicated image gen (ultra) | **Paid only** |
| `imagen-4.0-fast-generate-001` | Dedicated image gen (fast) | **Paid only** |

## API (google-genai SDK)

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=key)
response = client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents='your prompt',
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE']
    )
)

for part in response.candidates[0].content.parts:
    if part.inline_data:
        with open('output.png', 'wb') as f:
            f.write(part.inline_data.data)
    elif part.text:
        print(part.text)
```

## Quota (Free Tier)

- Image gen has **SEPARATE quota** from text generation
- ~5-15 image requests per day per model
- When exhausted: `429 RESOURCE_EXHAUSTED, limit: 0`
- Quota resets every 24h (midnight Pacific time)
- Different image models share the same project quota

## Pitfalls

- **Image gen quota ≠ text quota.** Text may work while image gen is 429.
- **Imagen models require paid plan.** Don't try `imagen-4.0-*` on free tier — returns 400.
- **SDK:** Use `google-genai` (new), NOT `google-generativeai` (deprecated, doesn't support `response_modalities`).
- **NSFW filtering:** Gemini has strict content filtering. Prompts with "lingerie", "cleavage", "sexy" may be refused or return only text (no image). Use euphemisms: "elegant portrait", "fashion photography", "glamorous".
- **Quota consumed by testing.** Each failed attempt still counts against quota. Test with minimal prompts.
