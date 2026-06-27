# Twitter/X Access Patterns (Updated Jun 2026)

## What Works

### Syndication API (No Auth)
```
curl -s "https://cdn.syndication.twimg.com/tweet-result?id=TWEET_ID&token=0" \
  -H "User-Agent: Mozilla/5.0"
```
- Returns: tweet text, user info, article preview, media
- No auth required
- **Best for:** Reading tweet content without login

## What Doesn't Work
- Direct login from VPS → "temporarily limited"
- Guest API → deprecated/empty
- oEmbed → deprecated/empty
- Free proxies → can GET (read tweets) but can't POST/login

## Recommended for Airdrop Twitter Tasks
1. Read tweets: Syndication API (no auth needed)
2. Login/interact: Residential proxy (~$2-5/month) or manual from phone only