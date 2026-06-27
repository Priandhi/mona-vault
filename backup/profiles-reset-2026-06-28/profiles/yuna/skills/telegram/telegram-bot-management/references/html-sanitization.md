# HTML Sanitization for Telegram Messages

## Problem
Telegram's HTML parser is strict — unclosed tags, broken entities, or angle brackets in non-tag contexts cause HTTP 400 errors. This is especially common with crypto token names that contain:
- Chinese characters (e.g., `锄头`)
- Special characters (e.g., `<`, `>`, `&`)
- Unmatched HTML tags from dynamic content

## Solution: `_sanitize_html()` Function

```python
def _sanitize_html(text):
    """Clean HTML to prevent Telegram parse errors."""
    import re
    # Fix unclosed tags
    for tag in ['b', 'i', 'code', 'pre', 'a']:
        opens = len(re.findall(f'<{tag}[ >]', text))
        closes = len(re.findall(f'</{tag}>', text))
        if opens > closes:
            text += f'</{tag}>' * (opens - closes)
    # Remove broken entities
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', text)
    # Fix angle brackets in non-tag contexts
    text = re.sub(r'<(?!/?(b|i|code|pre|a|em|strong|u|s|strike|del|ins|u)[ >])', '&lt;', text)
    return text
```

## Usage Pattern

```python
def send_message(topic_id, text, parse_mode="HTML"):
    # 1. Sanitize FIRST
    if parse_mode == "HTML":
        text = _sanitize_html(text)
    
    # 2. Truncate
    if len(text) > 4000:
        text = text[:3990] + "\n\n... <i>(truncated)</i>"
    
    # 3. Send with retry
    try:
        # send with HTML
    except Exception as e:
        # Log error body for debugging
        error_body = ''
        if hasattr(e, 'read'):
            try: error_body = e.read().decode()[:200]
            except: pass
        print(f"[ERROR] send_message: {e} | body: {error_body}", file=sys.stderr)
        # Retry without HTML
        payload["parse_mode"] = ""
        # send again
```

## Common Failure Patterns

1. **Chinese token names**: `锄头`, `goodcoin`, `Buttcoin` — often contain special chars
2. **Unclosed tags**: Dynamic content may have `<b>` without `</b>`
3. **Ampersand in URLs**: `https://example.com?a=1&b=2` → `&amp;b=2`
4. **Angle brackets in code**: `<code>0x1234</code>` is fine, but `<0x1234>` breaks

## Testing

```python
# Test cases
test_cases = [
    "Normal text with <b>bold</b>",
    "Unclosed <b>bold text",
    "Chinese: 锄头 token",
    "URL: https://example.com?a=1&b=2",
    "Code: <code>0x1234</code>",
    "Mixed: <b>锄头</b> ($CHINESE)",
]

for text in test_cases:
    sanitized = _sanitize_html(text)
    print(f"Original: {text}")
    print(f"Sanitized: {sanitized}")
    print()
```

## Key Points

- Always sanitize BEFORE sending, not just retry on failure
- The `_sanitize_html()` function handles most common cases
- Retry without `parse_mode` as a safety net
- Log the error body (`e.read().decode()`) for debugging
- Set `disable_web_page_preview: True` to avoid link preview clutter
