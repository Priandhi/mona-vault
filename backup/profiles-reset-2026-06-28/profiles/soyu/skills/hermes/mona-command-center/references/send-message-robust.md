# Telegram Send Message — Robust Implementation

## Problem

Messages fail with HTTP 400 when: exceeding 4096 chars, HTML parse fails on special chars, unmatched tags, stray `<`/`>` in token names.

## Solution — 4-Layer Defense

### Layer 1: HTML Sanitization (PREVENT)
```python
def send_message(topic_id, text, parse_mode="HTML"):
    if parse_mode == "HTML":
        text = _sanitize_html(text)  # see html-sanitization.md
```

### Layer 2: Auto-Truncation (PREVENT)
```python
if len(text) > 4000:
    text = text[:3990] + "\n\n... <i>(truncated)</i>"
```

### Layer 3: Disable Web Preview (PREVENT)
```python
payload["disable_web_page_preview"] = True
```

### Layer 4: HTML Fallback (RECOVER)
```python
try:
    # send with HTML
except Exception as e:
    if "can't parse entities" in str(e).lower():
        payload["parse_mode"] = ""
        # retry without HTML
```

Always log the error body for debugging: `e.read().decode()[:200]`
