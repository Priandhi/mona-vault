---
name: "hermes-web-search"
description: "Configure and troubleshoot Hermes's web search backend. Covers first-time setup, backend switching (Brave / DuckDuckGo / Tavily / custom), and fixing a broken backend (402 errors, rate limits, CAPTCHAs)."
tags:
  - hermes
  - web-search
  - brave
  - duckduckgo
  - tavily
  - config
  - troubleshoot
---
# Hermes Web Search Configuration

> Configure and troubleshoot Hermes's web search backend. Two skills: one for setting up a backend (config), one for fixing a broken one (fix).

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "web search setup", "configure brave", "switch backend", "duckduckgo" | `references/web-search-config/` |
| "web search broken", "402 brave", "exhausted", "fix search" | `references/web-search-fix/` |

## Architecture

Hermes's `web_search` tool is a thin wrapper over a configured backend. The default backend has been Brave; Brave's free tier has been exhausted for many users, requiring a switch.

```
web_search() tool
        ↓
   <configured backend>
        ↓
   Brave / DuckDuckGo / Tavily / custom
```

## When to Load Each

- `web-search-config` — first-time setup, switching backends, configuring API keys, multi-backend chains with fallback
- `web-search-fix` — when `web_search` is failing (402, rate limit, CAPTCHA, backend down), and you need the diagnose-and-fix recipe

## PITFALLS

1. **Brave free tier is 2000 queries/month** and resets on the 1st of each month. Once exhausted, all calls return 402.
2. **DuckDuckGo has no API key** but rate-limits aggressively. Use sparingly.
3. **Tavily** is paid but has a generous free trial. Best for production.
4. **Don't** try to use multiple backends in parallel — pick one and configure fallback.

## Topic Pages

- `references/web-search-config/SKILL.md` — Backend setup, Brave / DuckDuckGo / Tavily / custom configuration
- `references/web-search-fix/SKILL.md` — Diagnose and fix a broken web_search backend

## Related

- `delegate-coding-agents` — for falling back to `web_extract` + agent reasoning when web_search is exhausted
