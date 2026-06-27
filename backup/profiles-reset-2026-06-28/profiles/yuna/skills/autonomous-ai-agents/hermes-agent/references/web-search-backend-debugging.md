# Web Search Backend Debugging Trail (Jun11 2026)

## Session Summary

Hermes web_search was broken for 2+ days. Debugging sequence:

1. **brave-free** → HTTP 402 (free tier exhausted)
2. **brave** (paid) → HTTP 402 (API key existed but quota hit)
3. **searxng** → HTTP 403 (public instances block automated requests)
4. **firecrawl** → Unauthorized (empty `FIRECRAWL_API_KEY=` in .env caused provider selection)
5. **ddgs** → ✅ Works! Free, no API key, unlimited

## Root Causes Found

### Empty API keys trigger provider selection
`FIRECRAWL_API_KEY=` (empty value) in `.env` made Hermes select Firecrawl as the search provider, even though the key was empty. The provider selection logic checks for KEY PRESENCE, not KEY VALIDITY.

**Fix:** Comment out or remove empty key lines from `.env`.

### SearXNG needs env var, not just config
Setting `hermes config set searxng_url https://instance` is not enough. The SearXNG provider reads from `process.env.SEARXNG_URL`, not from config. Must add to `.env` AND restart gateway.

### Public SearXNG instances block automated requests
Tested instances:
- `searx.be` → 403
- `search.sapti.me` → 403
- `searx.tiekoetter.com` → 403

All returned 403 for `format=json` API requests. Self-hosted SearXNG required for reliable use.

### ddgs must be installed in correct venv
Hermes uses `~/.hermes/hermes-agent/venv/`, NOT `~/.hermes/venv-mona/`. Installing in the wrong venv gives "ddgs package is not installed".

```bash
# Correct
~/.hermes/hermes-agent/venv/bin/python3 -m pip install ddgs

# Wrong (this is Mona's venv)
~/.hermes/venv-mona/bin/pip install ddgs
```

### Both `backend` and `search_backend` must be set
`search_backend` overrides `backend` for search operations. If only `backend` is changed but `search_backend` still points to the old provider, the old provider is used for search.

```bash
hermes config set web.backend ddgs
hermes config set web.search_backend ddgs  # Also set this!
```

## Decision Matrix (updated Jun11)

| Scenario | Recommended Backend | Notes |
|----------|-------------------|-------|
| Free, no API key, just works | `ddgs` | Install in hermes venv |
| Have Brave API key, low volume | `brave` | 2000 free/month, needs CC for overage |
| Self-hosted SearXNG | `searxng` | Set SEARXNG_URL in .env |
| Paid, need web_extract | `firecrawl` / `exa` / `tavily` | Requires valid API key |
