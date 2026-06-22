# Merlin AI Proxy — 2026-06-21 Setup

## Status: PROXY RUNNING, LOGIN BLOCKED

## What Was Done
- ✅ Created skill `~/.hermes/skills/devops/merlin-ai/SKILL.md`
- ✅ Saved API contract at `references/merlin-api-contract.md`
- ✅ Created proxy at `/home/ubuntu/.hermes/scripts/merlin_proxy.py`
- ✅ Fixed MRO error (changed `ThreadingMixIn, ThreadingHTTPServer` to just `ThreadingHTTPServer` — already thread-safe in http.server)
- ✅ Proxy running on port 20133, /health returns OK
- ❌ Firebase login FAILED: "INVALID_PASSWORD" with `Yo12345@`

## What Needs to Be Done
- Need correct password for `hanya00rindu@gmail.com` from Mas
- OR refreshToken from a previous session (then can re-auth without password)
- After login works, register in 9Router as `merlin` provider (skill has full steps)
- Test 16 Pro models (claude-4.8-opus, claude-4.6-sonnet, gpt-5.5, gemini-3.1-pro, etc.)

## Password issue root cause
- Skill contract says default password is `Yo12345@` (8 chars)
- Tested directly: `INVALID_PASSWORD`
- Possibly rotated since contract was written
- Mas needs to provide current password or refreshToken

## After login, expected models (16 Pro)
- claude-4.5-haiku, claude-4.6-sonnet, claude-4.8-opus
- gpt-5.4, gpt-5.5
- gemini-2.5-flash-lite, gemini-3.0-flash, gemini-3.1-flash-lite, gemini-3.1-pro, gemini-3.5-flash
- kimi-k2.6, grok-4.3, deepseek-v4-pro, glm-5.1
- minimax-m2.5, minimax-m2.7
