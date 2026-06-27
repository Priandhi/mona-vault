# Gemini Vision-Only Configuration

Configure Google Gemini 2.0 Flash for vision (image analysis) and image generation ONLY — not for chat or other tasks.

## Setup

1. Get API key from https://aistudio.google.com/app/apikey
2. Add to `~/.hermes/.env`:
   ```
   GEMINI_API_KEY=<your_key>
   ```
3. Configure Hermes:
   ```bash
   hermes config set auxiliary.vision.provider gemini
   hermes config set auxiliary.vision.model gemini-2.0-flash
   hermes config set auxiliary.image_gen.provider gemini
   hermes config set auxiliary.image_gen.model gemini-2.0-flash
   ```

## What this enables

- `vision_analyze` tool uses Gemini for image analysis (OCR, screenshot reading, chart analysis)
- `image_gen` tool uses Gemini for generating images
- Regular chat, coding, tools — still use primary model (e.g. MiMo)

## Verification

```bash
hermes config get auxiliary.vision
# Should show: provider: gemini, model: gemini-2.0-flash
```

## PITFALL: vision_analyze file paths

`vision_analyze` may fail reading images from `~/.hermes/cache/documents/` (Telegram file cache). Workaround:
```bash
cp ~/.hermes/cache/documents/img_*.jpg ~/.hermes/screenshots/
# Then use full path: ~/.hermes/screenshots/img_*.jpg
```

## PITFALL: Don't leak Gemini key into chat

The key goes in `.env` only. Never echo it in terminal output — Hermes security redacts it but the raw value was in the command. Use `execute_code` with string variable if you need to verify the key programmatically.
