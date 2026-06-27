# Telegram Send Message — Robust Implementation

## Problem
Telegram messages fail silently with HTTP 400 when:
1. Message exceeds 4096 character limit
2. HTML parse fails on special characters in token names
3. Unmatched HTML tags in dynamic content
4. Stray `<` or `>` in token names (e.g., `$KLEO<1h>`) interpreted as HTML tags

## Solution — 4-Layer Defense

### Layer 1: HTML Sanitization (PREVENT errors)
Fix HTML issues BEFORE sending, so retries are rarely needed:

```python
def _sanitize_html(text):
    """Clean HTML to prevent Telegram parse errors."""
    import re
    # Fix unclosed tags — count opens vs closes for each tag
    for tag in ['b', 'i', 'code', 'pre', 'a']:
        opens = len(re.findall(f'<{tag}[ >]', text))
        closes = len(re.findall(f'</{tag}>', text))
        if opens > closes:
            text += f'</{tag}>' * (opens - closes)
    # Fix broken HTML entities — & not followed by valid entity name
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', text)
    # Escape stray angle brackets that aren't valid HTML tags
    text = re.sub(r'<(?!/?(b|i|code|pre|a|em|strong|u|s|strike|del|ins)[ >])', '&lt;', text)
    return text
```

**Apply BEFORE sending:**
```python
def send_message(topic_id, text, parse_mode="HTML"):
    if parse_mode == "HTML":
        text = _sanitize_html(text)
    # ... rest of send logic
```

### Layer 2: Auto-Truncation (PREVENT 400)
```python
# Telegram max message length = 4096
if len(text) > 4000:
    text = text[:3990] + "\n\n... <i>(truncated)</i>"
```

### Layer 3: Disable Web Preview (PREVENT clutter)
```python
payload["disable_web_page_preview"] = True
```

### Layer 4: HTML Fallback (RECOVER from parse errors)
```python
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
        if result.get("ok"):
            return result["result"]
        else:
            # Retry without parse_mode if HTML fails
            if parse_mode == "HTML" and "can't parse entities" in str(result).lower():
                payload["parse_mode"] = ""
                # ... retry ...
except Exception as e:
    error_body = ''
    if hasattr(e, 'read'):
        try: error_body = e.read().decode()[:200]
        except: pass
    print(f"[ERROR] send_message: {e} | body: {error_body}")
    # Retry without parse_mode
    payload["parse_mode"] = ""
    # ... retry ...
```

## Why Each Layer Matters

| Layer | Problem | Solution | When |
|-------|---------|----------|------|
| Sanitization | Unclosed tags, stray `<`, broken `&` | Fix HTML before sending | Always (prevention) |
| Truncation | >4096 chars = HTTP 400 | Truncate to 4000 | Always (prevention) |
| disable_web_page_preview | Link previews clutter alerts | Set to True | Always (prevention) |
| HTML fallback | Token names with unfixable HTML chars | Retry without parse_mode | On failure (recovery) |

## Common HTML-Breaking Token Names

These patterns break Telegram's HTML parser:
- `$KLEO<1h>` — angle brackets in name
- `Token & Co` — unescaped ampersand
- `<b>Bold text` — unclosed tag
- `Price: $0.000000075` — dots in numbers are fine, but `<` in context like `$0.00001<USD>` breaks

The `_sanitize_html()` function handles all of these automatically.
