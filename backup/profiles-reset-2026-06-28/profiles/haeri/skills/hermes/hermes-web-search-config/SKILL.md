---
name: hermes-web-search-config
description: "Configure and troubleshoot Hermes web search backends — DuckDuckGo (free), Brave, SearXNG, Firecrawl, Exa, Tavily, Parallel."
version: 1.0.0
author: Mona
tags: [hermes, web-search, config, troubleshooting, ddgs, brave, searxng]
metadata:
  hermes:
    tags: [config, web, search, troubleshooting]
---

# Hermes Web Search Backend Configuration

## Quick Decision Matrix

| Backend | API Key? | Cost | Install? | Recommended? |
|---------|----------|------|----------|--------------|
| `ddgs` (DuckDuckGo) | ❌ No | Free | `pip install ddgs` | ✅ YES — default for free users |
| `brave-free` | ❌ No | Free (rate-limited) | Built-in | ⚠️ Hits 402 fast |
| `brave` | ✅ Yes | Free 2000/mo, then paid | Built-in | ⚠️ Needs CC for overage |
| `searxng` | ❌ No | Free | Needs instance | ⚠️ Public instances often 403 |
| `firecrawl` | ✅ Yes | Paid | `pip install firecrawl-py` | ❌ Needs API key |
| `exa` | ✅ Yes | Paid | `pip install exa-py` | ❌ Needs API key |
| `tavily` | ✅ Yes | Paid | Built-in | ❌ Needs API key |
| `parallel` | ✅ Yes | Paid | Built-in | ❌ Needs API key |

**Default recommendation: `ddgs`** — no API key, no cost, works out of the box after install.

## Configuration Steps (DuckDuckGo)

### 1. Install ddgs in the CORRECT venv

Hermes uses its own venv — install there, not in mona venv:

```bash
~/.hermes/hermes-agent/venv/bin/python3 -m pip install ddgs
```

### 2. Set backend in config

```bash
hermes config set web.backend ddgs
hermes config set web.search_backend ddgs
```

### 3. Clean up conflicting API keys in `.env`

Remove or comment out empty/dummy API keys that cause provider selection issues:

```bash
# Edit ~/.hermes/.env
# Remove lines like: FIRECRAWL_API_KEY=*** (empty value causes Firecrawl to be selected)
# Keep only valid keys
```

### 4. Restart gateway

```bash
hermes gateway restart
```

### 5. Verify

```bash
hermes config show  # Check web section
```

## Troubleshooting

### "Brave Search returned HTTP 402"
- **Cause:** Free tier quota exhausted or no valid API key
- **Fix:** Switch to `ddgs` or get new Brave API key

### "Brave Search (Free) is a search-only backend and cannot extract URL content"
- **Cause:** `web.extract_backend` not set, and using brave-free for extraction
- **Fix:** Set `web.extract_backend` to empty string: `hermes config set web.extract_backend ''`
- **Note:** web_extract requires a paid backend (firecrawl/exa/tavily/parallel) with valid API key. If no key available, avoid calling web_extract — use browser tool instead.

### "Firecrawl search failed: Unauthorized: Invalid token"
- **Cause:** Empty or dummy `FIRECRAWL_API_KEY` in `.env` — Hermes selects Firecrawl as provider even with empty key
- **Fix:** Comment out or remove the line from `~/.hermes/.env`

### "SEARXNG_URL is not set"
- **Cause:** SearXNG backend needs env var, not just config setting
- **Fix:** Add `SEARXNG_URL=https://instance-url` to `~/.hermes/.env` AND restart gateway
- **Pitfall:** Most public SearXNG instances return 403 for automated requests

### "ddgs package is not installed"
- **Cause:** Installed in wrong venv
- **Fix:** Install in Hermes venv: `~/.hermes/hermes-agent/venv/bin/python3 -m pip install ddgs`

## Key Pitfalls

1. **Install in correct venv** — `~/.hermes/hermes-agent/venv/` not `~/.hermes/venv-mona/`
2. **Empty API keys cause issues** — `FIRECRAWL_API_KEY=` (empty) still makes Hermes select Firecrawl. Comment out or remove.
3. **Config vs env var** — Some backends (searxng) read from env vars, not config. Need gateway restart after `.env` changes.
4. **`search_backend` overrides `backend`** — Set BOTH when switching
5. **Cannot restart gateway from inside gateway** — Must use external terminal

## Config Keys Reference

```yaml
web:
  backend: brave-free     # Main backend (search + extract)
  extract_backend: ''      # Override for extract only (firecrawl/exa/tavily/parallel)
  search_backend: ''       # Override for search only (ddgs/brave/searxng)
  searxng_url: ''          # SearXNG instance URL (also set SEARXNG_URL in .env)
```

Priority: `search_backend` > `backend` for search, `extract_backend` > `backend` for extract.

## References

- `references/web-search-backend-debugging.md` — Jun11 session debugging trail: brave→searxng→firecrawl→ddgs progression, root causes, and fixes.
- `references/quick-fix-brave-to-ddgs.md` — Migrated from `hermes-web-search-fix`. Quick-fix playbook when Brave API is exhausted: switch to DuckDuckGo via `ddgs` package.
