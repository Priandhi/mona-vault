---
name: "llm-routing"
description: "Configure alternative LLM providers behind an OpenAI-compatible endpoint: 9Router (self-hosted router), Kiro CLI (AWS), Xiaomi MiMo (cheap Claude). Use when setting up a router, switching providers, or wiring a new model into an existing OpenAI-SDK client."
tags:
  - llm-router
  - 9router
  - kiro
  - mimo
  - anthropic
  - openai-compatible
  - fallback
---
# LLM Provider Routing & Setup

> Configure and integrate alternative LLM providers behind a single OpenAI-compatible API. Covers 9Router (the in-house router), Kiro CLI (AWS), and Xiaomi MiMo (cheap Anthropic alternative).

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "9router", "self-hosted llm router", "fallback chain" | `references/9router-llm-router/` |
| "kiro", "AWS coding agent", "kiro cli" | `references/kiro-9router-setup/` |
| "MiMo", "Xiaomi API", "cheap claude" | `references/claude-code-mimo-setup/` |

## Architecture

All three projects aim for a single OpenAI-compatible endpoint (`/v1/chat/completions`) that fronts multiple upstream providers. This lets existing OpenAI SDK code (e.g. Hermes) point at the router and get failover, load balancing, and cost optimization for free.

```
Hermes / OpenAI SDK client
        ↓
   <router endpoint>
        ↓
   Provider 1 (Anthropic)
   Provider 2 (OpenAI)
   Provider 3 (MiMo / local / custom)
```

## PITFALLS

1. **Streaming format differs across routers.** 9Router returns SSE even with `stream: false`. Kiro returns JSON only. Always parse defensively (try JSON, fall back to SSE).
2. **Auth is per-router, not per-provider.** Each router has its own API key format (`sk-or-...` for 9Router, `ksk_...` for Kiro). Don't mix.
3. **Model availability changes.** Always check `GET /v1/models` before using a model. Don't hardcode names.

## Topic Pages

- `references/9router-llm-router/SKILL.md` — 9Router: self-hosted LLM API proxy/router
- `references/kiro-9router-setup/SKILL.md` — Kiro CLI: AWS coding agent with ksk_ key auth
- `references/claude-code-mimo-setup/SKILL.md` — Claude Code with Xiaomi MiMo API (cheaper alternative)
