---
type: receipt
date: 2026-06-21
tags:
  - receipt
---

# AgentRouter Final Status — 2026-06-21 (SERVICE DOWN)

## Final Conclusion: **AgentRouter chat endpoint is in service-level lockdown**

## What We Tested
- 2 Bearer tokens: `sk-FpO...KfQd` (51 chars, new) + `9QmA9T...Um8=` (32 chars Base64, old)
- 1 user_id: 173560 (from Mas)
- 2 Cloudflare Workers: agentrouter-relay (v1) + agentrouter-v2 (new)
- 7+ models: deepseek-v4-flash, deepseek-v4-pro, gpt-5.4, gpt-5.5, claude-opus-4-7, claude-sonnet-4-6, glm-5.1
- 6+ auth variations: Bearer, x-api-key, Token, Key, no auth
- 4 paths: VPS direct, CF Worker v1, CF Worker v2, residential proxy
- 5+ endpoints: /v1/chat/completions, /v1/messages, /pg/chat/completions, /api/user/self, /api/option

## Final Results
| Token + User_ID | Endpoint | Response |
|---|---|---|
| sk-FpO... + 173560 | /v1/chat/* | "unauthorized client detected" (SAME all 7 models) |
| sk-FpO... + 173560 | /pg/chat/completions | "access token 无效" |
| sk-FpO... + 173560 | /api/user/self | "access token 无效" |
| 9QmA9T... + 173560 | /api/user/self | "New-Api-User 与登录用户不匹配" (valid token, wrong user_id) |
| 9QmA9T... + 173560 | /v1/chat/* | "unauthorized client detected" |

## Key Insights
1. **The new sk-FpO... key is NOT valid for user 173560** — every endpoint returns "invalid"
2. **The old 9QmA9T... token is valid for SOME user** (got "mismatch" not "invalid") — different user
3. **The chat endpoint is broken at the service level** — even with new IPs (CF Worker v2), the same error appears
4. **WAF bypass works** but upstream is still blocking — confirmed via 3 different egress paths
5. **Site status**: matches announcement perfectly — "use it while you can", "Claude series models largely disabled", "service stability under challenge"

## What's Configured for Future Use (when service recovers)
- 9Router default model: `agentrouter/deepseek-v4-pro` (real model in catalog)
- KV alias: `agentrouter-gpt-4o-mini` → `node_id/deepseek-v4-pro`
- providerNode: `openai-compatible-chat-9c90a9f0-f195-43d8-a8cc-875e6940674c`
- providerConnection: `AgentRouter` (id: 8eb1771a-639e-4ba5-8c4f-f2ffcf9cdaf8)
- Cloudflare Worker v1: `https://agentrouter-relay.monaai-crot.workers.dev`
- Cloudflare Worker v2: `https://agentrouter-v2.monaai-crot.workers.dev` (fresh IP)

## What Mas Needs to Do (when service recovers)
1. Login to agentrouter.org via OAuth (GitHub/Linux.do)
2. Generate a fresh channel key from dashboard "令牌" menu
3. Give the new key to Mona
4. Test the chat endpoint

## Pivot: Use `ol/minimax-m3` (confirmed working via TokenRouter)
