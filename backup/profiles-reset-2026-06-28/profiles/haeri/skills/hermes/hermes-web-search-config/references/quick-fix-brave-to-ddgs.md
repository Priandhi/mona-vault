> Migrated from `hermes-web-search-fix` (consolidated June 2026).

# Fix Web Search Backend

When `web_search` fails with HTTP 402 (Brave quota exhausted) or no API key available.

## Symptoms
- `web_search` returns "Brave Search returned HTTP 402"
- `web_extract` returns "Brave Search (Free) is a search-only backend"
- No valid API key for firecrawl/exa/tavily/parallel

## Solution: Switch to DuckDuckGo (ddgs)

DuckDuckGo (`ddgs`) is free, unlimited, no API key needed.

### Steps

1. **Install ddgs in BOTH venvs** (agent venv AND mona venv):
```bash
~/.hermes/hermes-agent/venv/bin/python3 -m pip install ddgs
~/.hermes/venv-mona/bin/pip install ddgs
```

2. **Set config:**
```bash
hermes config set web.backend ddgs
hermes config set web.search_backend ddgs
```

3. **Remove empty/broken API keys from .env:**
```bash
# Remove empty FIRECRAWL_API_KEY if present
sed -i '/^FIRECRAWL_API_KEY=*** ~/.hermes/.env
```

4. **Test:**
```bash
# web_search should return DuckDuckGo results
```

## Pitfalls
- MUST install ddgs in `~/.hermes/hermes-agent/venv/` (the Hermes runtime venv), NOT just the mona venv
- Empty `FIRECRAWL_API_KEY=*** .env causes Firecrawl to be selected over the configured backend
- Public SearXNG instances return 403 for automated requests — don't use `searxng` backend
- `hermes gateway restart` needed after .env changes (can't restart from inside gateway)
- PM2 `--update-env` may NOT reload .env changes; use `pm2 delete <name> && pm2 start` for fresh start

## Alternative backends
- `brave-free` — limited free tier (2000 queries/month), no API key needed
- `brave` — requires API key (needs credit card)
- `searxng` — needs self-hosted instance (public ones block automated requests)
- `ddgs` — DuckDuckGo, free, unlimited ✅
