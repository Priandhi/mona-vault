# Telegram HTML Message Sanitization

## Problem
Telegram's HTML parser is strict. Unclosed tags, broken entities, or angle brackets in non-tag contexts cause HTTP 400 errors. Messages > 4096 chars are rejected.

## Solution: Pre-process + Retry Pattern

### 1. Sanitize HTML Before Sending
```python
import re

def _sanitize_html(text):
    # Fix unclosed tags
    for tag in ['b', 'i', 'code', 'pre', 'a']:
        opens = len(re.findall(f'<{tag}[ >]', text))
        closes = len(re.findall(f'</{tag}>', text))
        if opens > closes:
            text += f'</{tag}>' * (opens - closes)
    
    # Fix broken HTML entities
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', text)
    
    # Fix angle brackets that aren't HTML tags
    text = re.sub(r'<(?!/?(b|i|code|pre|a|em|strong|u|s|strike|del|ins)[ >])', '&lt;', text)
    
    return text
```

### 2. Truncate Long Messages
```python
if len(text) > 4000:
    text = text[:3990] + "\n\n... <i>(truncated)</i>"
```

### 3. Retry Without Parse Mode
```python
def send_message(topic_id, text, parse_mode="HTML"):
    # Sanitize first
    if parse_mode == "HTML":
        text = _sanitize_html(text)
    
    # Truncate
    if len(text) > 4000:
        text = text[:3990] + "\n\n... <i>(truncated)</i>"
    
    # Try with parse_mode
    result = try_send(topic_id, text, parse_mode)
    
    # If HTML fails, retry without parse_mode
    if not result and parse_mode == "HTML":
        result = try_send(topic_id, text, "")
    
    return result
```

### 4. Error Logging with Response Body
```python
try:
    resp = urllib.request.urlopen(req, timeout=15)
except Exception as e:
    error_body = ''
    if hasattr(e, 'read'):
        try: error_body = e.read().decode()[:200]
        except: pass
    print(f"[ERROR] send_message: {e} | body: {error_body}")
```

## Common Causes of 400 Errors

1. **Unclosed `<b>` or `<i>` tags** — Most common. Fix: count opens/closes, add missing closing tags.
2. **Angle brackets in token names** — e.g., `$KLEO<3` → `<3` parsed as HTML tag. Fix: escape to `&lt;`.
3. **Ampersands in URLs** — e.g., `?a=1&b=2` → `&b` not a valid entity. Fix: escape to `&amp;`.
4. **Message too long** — > 4096 chars. Fix: truncate to 4000 + truncation notice.
5. **Invalid characters** — Some Unicode chars break HTML parser. Fix: retry without parse_mode.

## Disable Web Page Preview
Always set `disable_web_page_preview=True` to prevent link previews from cluttering alerts:
```python
payload = {
    "chat_id": CHAT_ID,
    "message_thread_id": topic_id,
    "text": text,
    "parse_mode": "HTML",
    "disable_web_page_preview": True,
}
```
