---
type: receipt
date: 2026-06-21
tags:
  - receipt
---

# AgentRouter Token `9QmA9T...Um8=` Investigation — 2026-06-21

## Discovery: This is a USER ACCESS TOKEN, not CHANNEL KEY

### Token Details
- Format: 32 chars Base64 = 24 bytes raw
- Raw hex: `f50980f534fa8ddcc9b5a237d690618d4b6133223c526f`
- Recognized by server as a valid **user access_token** (NOT channel key)

### Auth Flow (REQUIRES 2 HEADERS)
- `Authorization: Bearer <token>` — user access token
- `New-Api-User: <numeric_id>` — required for ALL API calls (admin custom feature)

### Response Behavior
| Scenario | Error |
|---|---|
| Bearer only | "未提供 New-Api-User" (need user header) |
| Bearer + New-Api-User (numeric, wrong) | "New-Api-User 与登录用户不匹配" (token valid, user_id wrong) |
| Bearer + New-Api-User (string) | "New-Api-User 格式错误" (must be numeric) |
| Bearer + correct New-Api-User | (would succeed) |
| /v1/chat/* (any auth) | "unauthorized client detected" (chat needs CHANNEL KEY, not user access token) |

### Key Insight
In OneAPI, there are TWO different tokens:
1. **User access_token** (used for /api/user/*, /api/oauth/*) — what Mas gave
2. **Channel key** (used for /v1/*, /pg/*) — what's needed for chat

Mas's `9QmA9T...` is #1, but chat needs #2. Channel key is generated from user dashboard "令牌" (token) menu.

### WAF Status
- After 50+ brute force attempts, Aliyun WAF rate-limited all requests from CF Worker
- All responses now return WAF HTML for /api/user/self
- Need to wait 5-10 minutes for WAF to clear, or use a different egress IP

### What Mas Needs to Provide
1. **User ID** (visible in dashboard URL `/console/user/<id>`)
2. OR **Channel key** (separate token from "令牌" menu, format: sk-XXX usually)
3. OR fresh tokens from a working OAuth login

### Previous (sk-8xQ...7oox) Status
- That token: 51 chars, channel key format
- Status: REJECTED at service level (likely user banned or token format changed)
- Different from `9QmA9T...` which is user access_token
