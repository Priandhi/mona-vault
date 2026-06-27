# HTML Sanitization for Telegram Messages

Telegram's HTML parser is strict — unclosed tags, broken entities, or angle brackets cause HTTP 400.

## `_sanitize_html()` Function

```python
def _sanitize_html(text):
    """Clean HTML to prevent Telegram parse errors."""
    import re
    for tag in ['b', 'i', 'code', 'pre', 'a']:
        opens = len(re.findall(f'<{tag}[ >]', text))
        closes = len(re.findall(f'</{tag}>', text))
        if opens > closes:
            text += f'</{tag}>' * (opens - closes)
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', text)
    text = re.sub(r'<(?!/?(b|i|code|pre|a|em|strong|u|s|strike|del|ins|u)[ >])', '&lt;', text)
    return text
```

**Always sanitize BEFORE sending**, not just retry on failure. Common breakers: Chinese token names (`锄头`), angle brackets in names (`$KLEO<1h>`), unclosed tags from dynamic content.

## 4-Layer Defense

1. **Sanitization** — fix HTML before sending (prevention)
2. **Truncation** — >4000 chars → truncate with `<i>(truncated)</i>` (prevention)
3. **disable_web_page_preview** — avoid link preview clutter (prevention)
4. **HTML fallback** — retry without parse_mode on failure (recovery)
