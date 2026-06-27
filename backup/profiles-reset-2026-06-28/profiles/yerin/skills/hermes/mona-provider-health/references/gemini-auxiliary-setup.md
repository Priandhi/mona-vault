# Gemini Auxiliary Provider Setup

Configure Google Gemini for vision (image analysis) and image generation ONLY — not for regular chat.

## User Restriction

User explicitly stated: "apikey nya khusus buat scan gambar dan generate gambar aja ya bisa ? jangan di pake ke hal lain"

**NEVER** route chat, coding, fallback, or other tasks through Gemini.

## Setup Steps

### 1. Get API Key
- URL: https://aistudio.google.com/app/apikey
- Free tier available

### 2. Store Key Securely
```bash
# Save to vault
echo -n "YOUR_KEY" > ~/mona-workspace/vault/.gemini_key.txt
chmod 600 ~/mona-workspace/vault/.gemini_key.txt

# Add to Hermes .env
echo "GEMINI_API_KEY=YOUR_KEY" >> ~/.hermes/.env
```

**PITFALL**: Use `echo -n` (no newline) or the key will have trailing whitespace causing auth errors.

### 3. Configure Hermes
```bash
# Vision (image analysis)
hermes config set auxiliary.vision.provider gemini
hermes config set auxiliary.vision.model gemini-2.0-flash

# Image generation
hermes config set auxiliary.image_gen.provider gemini
hermes config set auxiliary.image_gen.model gemini-2.0-flash
```

### 4. Verify
```bash
# Check config
hermes config get auxiliary.vision
hermes config get auxiliary.image_gen

# Both should show:
# provider: gemini
# model: gemini-2.0-flash
```

## Config Location

In `~/.hermes/config.yaml`:
```yaml
auxiliary:
  vision:
    provider: gemini
    model: gemini-2.0-flash
    base_url: ''
    api_key: ''
    timeout: 120
    extra_body: {}
    download_timeout: 30
  image_gen:
    provider: gemini
    model: gemini-2.0-flash
```

## What This Enables

- **vision_analyze** tool → Uses Gemini for image analysis
- **image_gen** tool → Uses Gemini for image generation
- **OCR** → Read text from screenshots, photos, documents
- **Chart analysis** → Analyze crypto charts, graphs
- **Screenshot verification** → Verify browser automation results

## What This Does NOT Affect

- Regular chat → Still uses MiMo-V2.5-Pro
- Coding/terminal → Still uses MiMo-V2.5-Pro
- Fallback chain → Gemini is NOT in fallback (MiMo → 9Router → GeneralCompute)
- Web search → Still uses Hermes built-in

## Troubleshooting

### vision_analyze returns "no image attached"
- Copy image to `~/.hermes/screenshots/` first
- Use full path: `/home/ubuntu/.hermes/screenshots/image.jpg`

### API key not working
- Verify key in `.env`: `grep GEMINI_API_KEY ~/.hermes/.env`
- Check vault backup: `cat ~/mona-workspace/vault/.gemini_key.txt`
- Test directly: `curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=YOUR_KEY" -H "Content-Type: application/json" -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'`

### Duplicate keys in .env
- Check: `grep -c GEMINI_API_KEY ~/.hermes/.env`
- If > 1, clean up: `grep -v GEMINI_API_KEY ~/.hermes/.env > /tmp/.env.tmp && mv /tmp/.env.tmp ~/.hermes/.env`
- Re-add single key
