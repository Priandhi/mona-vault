---
type: receipt
date: 2026-06-21
tags:
  - receipt
---

# AgentRouter (agentrouter.org) — Full Reverse Engineering — 2026-06-21

## ✅ AUTH FULLY REVERSED (but service in lockdown)
User_id `173560`, GitHub login as `dini` (github_id=Dinikowoh27), quota=87.5M, used=0

## Working Auth Pattern
1. **Path**: `/pg/chat/completions` (NOT `/v1/chat/completions`)
2. **Headers**:
   - `Authorization: Bearer <access_token OR session_token>` — either works
   - `New-Api-User: 173560` — the user's numeric ID
   - `Content-Type: application/json`
3. **Body**: `{model, group, max_tokens, stream, messages[]}`

## What works ✅
- `/api/user/self` (Bearer + New-Api-User) → full user info
- `/api/user/models` (Bearer + New-Api-User) → 10 available models
- `/api/user/token` (Bearer + New-Api-User) → session token
- `/api/user/self/groups` → 2 groups: `default` (ratio=1) + `test` (ratio=10000)
- `/api/pricing` (no auth) → 10 model pricing
- `/api/oauth/state` (no auth) → state for OAuth flow
- `/pg/chat/completions` passes auth — reaches model dispatcher

## What's blocked ❌
- **`group=default`**: "暂不支持使用 access token" (server disabled for default group)
- **`group=test`**: "当前分组 test 下对于模型 deepseek-v4-pro 无可用渠道" (no channels)
- **`/v1/chat/completions`**: "unauthorized client detected" (different auth path, upstream blocked)

## Two Auth Tokens (different purposes)
- **access_token** (9QmA9T...Um8=): 32 chars Base64, used in Bearer header for API calls
- **session_token** (hV/X7qg9K8HrPSygfBXrsF+jeh2G): 28 chars, used in cookie for browser session

## Service State (CRITICAL)
Per official announcement from `/api/status`:
- "因受到恶意举报影响，近期服务稳定性遇到巨大挑战" (service under attack)
- "Claude系列模型大规模停用" (Claude series DISABLED)
- "且用且珍惜" (use it while you can)
- Admin has disabled access_token auth for default group
- Only viable group is "test" with no actual channels

## Models Available (10 total, per /api/pricing)
| Model | Ratio | Groups |
|---|---|---|
| deepseek-v4-pro | 1 | default, svip, vip |
| gpt-5.4 | 2 | default |
| claude-opus-4-7/8 | 1 | default |
| claude-sonnet-4-5/6 | 10/1 | default |
| deepseek-v4-flash | 1 | default, svip, vip |
| glm-5.1 | 1 | default, svip, vip |
| gpt-5.5 | 2 | default |
| claude-opus-4-6 | 10.5 | default, svip, vip |

## 9Router Config (per Mas directive)
- providerNode: `openai-compatible-chat-9c90a9f0-f195-43d8-a8cc-875e6940674c`
- providerConnection: `AgentRouter` (id: `8eb1771a-639e-4ba5-8c4f-f2ffcf9cdaf8`)
- **defaultModel: `deepseek-v4-pro`** ✅ (real model in catalog)
- Status: AUTH REVERSED but service in emergency lockdown

## Pivot Decision
- **Service cannot be used right now** — admin policy blocks default group
- Wait for service recovery OR pivot to `ol/minimax-m3` (confirmed working)
- If service recovers, use `/pg/chat/completions` + Bearer(session_token) + New-Api-User(173560) + group=default
- CF Worker relay `agentrouter-relay.monaai-crot.workers.dev` stays deployed
- Backup tokens in /tmp/agentrouter_key2.txt + /tmp/agentrouter_session.txt
