# DeBank Social Profile Extraction

## API Endpoint
```
GET https://api.debank.com/user/address/{address}
```
No auth required. Returns user profile with social accounts.

## Response Structure
```json
{
  "data": {
    "name": "Username",
    "ens": "vitalik.eth",
    "social_accounts": {
      "twitter": {
        "screen_name": "elonmusk",
        "name": "Elon Musk",
        "profile_image_url": "https://...",
        "followers_count": 150000000
      },
      "telegram": {
        "username": "elonmusk_tg",
        "name": "Elon Official"
      },
      "discord": {
        "username": "elon#1234",
        "name": "Elon Discord"
      },
      "github": {
        "username": "elonmusk",
        "name": "Elon GitHub"
      }
    }
  }
}
```

## Extraction Pattern — SEPARATE EACH PLATFORM
```python
accounts = user.get('social_accounts', {})

# Twitter
twitter = accounts.get('twitter', {})
profile['twitter'] = twitter.get('screen_name', '')
profile['twitter_name'] = twitter.get('name', '')
profile['twitter_followers'] = twitter.get('followers_count', 0)

# Telegram
telegram = accounts.get('telegram', {})
profile['telegram'] = telegram.get('username', '') or telegram.get('screen_name', '')
profile['telegram_name'] = telegram.get('name', '')

# Discord
discord = accounts.get('discord', {})
profile['discord'] = discord.get('username', '') or discord.get('screen_name', '')

# GitHub
github = accounts.get('github', {})
profile['github'] = github.get('username', '') or github.get('screen_name', '')
```

## Alert Format — Label Each Platform
```python
# Twitter — link to twitter.com
if person.get('twitter'):
    url = f"https://twitter.com/{person['twitter']}"
    lines.append(f'   🐦 Twitter: <a href="{url}">@{person["twitter"]}</a>')

# Telegram — link to t.me
if person.get('telegram'):
    url = f"https://t.me/{person['telegram']}"
    lines.append(f'   📱 Telegram: <a href="{url}">@{person["telegram"]}</a>')

# Discord — no link (Discord doesn't have public profile URLs)
if person.get('discord'):
    lines.append(f'   💬 Discord: {person["discord"]}')

# GitHub — link to github.com
if person.get('github'):
    url = f"https://github.com/{person['github']}"
    lines.append(f'   🐙 GitHub: <a href="{url}">@{person["github"]}</a>')
```

## Pitfalls
1. **NEVER mix platforms** — Twitter handle goes to twitter.com, Telegram username goes to t.me. Don't put a Twitter handle in a Telegram link or vice versa.
2. **Field names differ** — Twitter uses `screen_name`, Telegram uses `username`. Both may also have `name` (display name).
3. **Followers only for Twitter** — Telegram/Discord/GitHub don't have follower counts in DeBank response.
4. **Graceful fallback** — If `username` is empty, try `screen_name`. Some accounts have one but not the other.
5. **Cache aggressively** — Social profiles rarely change. Cache for 1 hour minimum.
6. **Rate limits** — DeBank has undocumented rate limits. Add delays between lookups.
