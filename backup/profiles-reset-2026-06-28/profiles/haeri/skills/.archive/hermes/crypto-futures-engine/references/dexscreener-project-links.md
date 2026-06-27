# DexScreener Project Links Extraction

## API Response Structure
DexScreener `/tokens/v1/base/{contract}` returns pair data with an `info` field:

```json
{
  "info": {
    "websites": [{"url": "https://example.com", "label": "Website"}],
    "socials": [
      {"type": "twitter", "url": "https://x.com/example"},
      {"type": "telegram", "url": "https://t.me/example"},
      {"type": "discord", "url": "https://discord.gg/example"}
    ]
  }
}
```

## Extraction Pattern
```python
info = d.get("info", {})
websites = info.get("websites", [])
if websites:
    result["website"] = websites[0].get("url") if isinstance(websites[0], dict) else websites[0]

socials = info.get("socials", [])
for s in socials:
    if isinstance(s, dict):
        s_type = s.get("type", "").lower()
        s_url = s.get("url", "")
        if s_type == "twitter": result["twitter"] = s_url
        elif s_type == "telegram": result["telegram"] = s_url
        elif s_type == "discord": result["discord"] = s_url
```

## Alert Link Format
```python
links = []
if t.get("dex_url"): links.append(f'<a href="{t["dex_url"]}">📊 Chart</a>')
if t.get("website"): links.append(f'<a href="{t["website"]}">🌐 Website</a>')
if t.get("twitter"): links.append(f'<a href="{t["twitter"]}">🐦 Twitter</a>')
if t.get("telegram"): links.append(f'<a href="{t["telegram"]}">📱 Telegram</a>')
if t.get("discord"): links.append(f'<a href="{t["discord"]}">💬 Discord</a>')
```

## Pitfalls
- `websites[0]` may be a string (URL) or dict (with `url` key) — check type before accessing
- `socials` may be empty for very new or unregistered tokens
- Don't hardcode DEX swap links (e.g., Aerodrome) — use project links from DexScreener instead
- Some tokens have no social links at all — handle gracefully
