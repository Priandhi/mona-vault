# DexScreener Project Links Extraction

The DexScreener API response includes an `info` object with project links. Always extract these for alerts instead of hardcoding DEX swap URLs.

## API Response Structure

```json
{
  "baseToken": {"name": "...", "symbol": "..."},
  "priceUsd": "...",
  "marketCap": 123456,
  "liquidity": {"usd": 50000},
  "info": {
    "websites": [{"url": "https://project.com"}],
    "socials": [
      {"type": "twitter", "url": "https://twitter.com/project"},
      {"type": "telegram", "url": "https://t.me/project"},
      {"type": "discord", "url": "https://discord.gg/project"}
    ]
  }
}
```

## Extraction Code

```python
result = {
    "name": base.get("name", "Unknown"),
    "symbol": base.get("symbol", "???"),
    # ... standard fields ...
    "website": None,
    "twitter": None,
    "telegram": None,
    "discord": None,
}

info = d.get("info", {})
websites = info.get("websites", [])
if websites:
    result["website"] = websites[0].get("url") if isinstance(websites[0], dict) else websites[0]

socials = info.get("socials", [])
for s in socials:
    if isinstance(s, dict):
        s_type = s.get("type", "").lower()
        s_url = s.get("url", "")
        if s_type == "twitter" and not result["twitter"]:
            result["twitter"] = s_url
        elif s_type == "telegram" and not result["telegram"]:
            result["telegram"] = s_url
        elif s_type == "discord" and not result["discord"]:
            result["discord"] = s_url
```

## Alert Link Format

```python
links = []
if t.get("dex_url"): links.append(f'<a href="{t["dex_url"]}">📊 Chart</a>')
if t.get("website"): links.append(f'<a href="{t["website"]}">🌐 Website</a>')
if t.get("twitter"): links.append(f'<a href="{t["twitter"]}">🐦 Twitter</a>')
if t.get("telegram"): links.append(f'<a href="{t["telegram"]}">📱 Telegram</a>')
if t.get("discord"): links.append(f'<a href="{t["discord"]}">💬 Discord</a>')
links.append(f'<a href="https://debank.com/profile/{w_info["address"]}">👤 DeBank</a>')
```

**NEVER** hardcode DEX swap URLs like `aerodrome.finance/swap?...` — they break for tokens on other DEXes.
