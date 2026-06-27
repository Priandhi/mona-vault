# GitHub README Extraction Pattern

When `web_extract` and `browser_navigate` both fail (Brave Search backend can't extract, Google blocks with CAPTCHA), use the GitHub REST API directly.

## Public repo README (no auth needed)

```bash
curl -s "https://api.github.com/repos/OWNER/REPO/readme" | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
print(base64.b64decode(d['content']).decode())
"
```

Returns full README markdown. Works for any public repo. No API key needed for unauthenticated requests (60 req/hour limit).

## With auth (higher rate limit)

```bash
curl -s -H "Authorization: token YOUR_GITHUB_TOKEN" \
  "https://api.github.com/repos/OWNER/REPO/readme" | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
print(base64.b64decode(d['content']).decode())
"
```

5000 req/hour with auth.

## Repo metadata (stars, forks, language)

```bash
curl -s "https://api.github.com/repos/OWNER/REPO" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"Stars: {d['stargazers_count']}, Forks: {d['forks_count']}, Lang: {d['language']}, Updated: {d['updated_at']}\")
"
```

## Directory listing

```bash
curl -s "https://api.github.com/repos/OWNER/REPO/contents/" | python3 -c "
import sys, json
for item in json.load(sys.stdin):
    print(f\"{'📁' if item['type']=='dir' else '📄'} {item['name']}\")
"
```

## File content (any file, not just README)

```bash
curl -s "https://api.github.com/repos/OWNER/REPO/contents/PATH/TO/FILE" | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
print(base64.b64decode(d['content']).decode())
"
```

## When to use

- `web_extract` returns error (Brave Search backend can't extract)
- `browser_navigate` hits Google CAPTCHA
- Need to read multiple files from a repo quickly
- Need repo metadata (stars, forks, activity) for quality assessment

## Pitfalls

- Rate limit: 60 req/hour without auth. Use auth token if available.
- Binary files (images, compiled) return base64 but won't decode to useful text.
- Large files (>1MB) may be truncated. Use `?ref=branch` for specific branches.
- Private repos require auth with appropriate scope.
