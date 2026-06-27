# Twitter/X Syndication API — Read Tweets Without Auth

## Problem

Twitter/X aggressively blocks VPS IPs:
- Login from VPS → "temporarily limited"
- Guest API → disabled/empty responses
- All Nitter instances → dead/blocked
- web_extract on x.com → fails
- Twitter API v2 → requires auth + $100/mo

## Solution: Syndication API

Twitter's own syndication endpoint works WITHOUT auth for reading public tweets:

```
GET https://cdn.syndication.twimg.com/tweet-result?id={TWEET_ID}&token=0
```

### Python Example

```python
import urllib.request, json

tweet_id = "2063606029146034375"
url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&token=0"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read())

print(f"User: @{data['user']['screen_name']}")
print(f"Text: {data['text']}")
print(f"Likes: {data['favorite_count']}")
print(f"Date: {data['created_at']}")

# For tweets with articles/links:
if 'article' in data:
    print(f"Article: {data['article']['title']}")
    print(f"Preview: {data['article']['preview_text']}")
```

### What It Returns

- Tweet text, user info, likes, date
- Article preview (title + first ~200 chars) for link tweets
- Media info (images, video thumbnails)
- Thread/conversation info

### Limitations

- **READ ONLY** — cannot like, retweet, comment, follow
- **No login flow** — for interaction, need residential proxy + real browser
- **Article content** — only preview text, not full article (article pages may be private/404)
- **Rate limits** — unknown, but reasonable for occasional use

### Free Proxy + Syndication

Free proxies (from proxyscrape.com) can proxy the syndication API call:

```python
import urllib.request

proxy = urllib.request.ProxyHandler({'http': '147.45.170.190:3129'})
opener = urllib.request.build_opener(proxy)
resp = opener.open(f"https://cdn.syndication.twimg.com/tweet-result?id={id}&token=0")
```

This works because syndication is a simple GET — no session/cookies needed.

### Workflow for Reading Tweets

1. User shares x.com link or tweet ID
2. Extract tweet ID from URL: `x.com/user/status/{ID}`
3. Fetch via syndication API
4. If tweet contains a link (t.co), follow the link to get the destination
5. Summarize content for user

### When User Can't Share Tweet ID

If user screenshots a tweet:
1. Use `vision_analyze` to read the screenshot
2. Extract tweet URL or ID from the image
3. Fetch via syndication API for full text
