# Kiro API Investigation (Jun 2026)

## What is Kiro
AWS's AI coding IDE/CLI (competitor to Claude Code, Cursor). Backed by AWS Bedrock.
- **Web:** app.kiro.dev
- **Docs:** kiro.dev/docs
- **CLI install:** `curl -fsSL https://cli.kiro.dev/install | bash`

## API Key (ksk_ prefix)
- Created at app.kiro.dev → Settings → API Keys
- Keys shown only once on creation
- **Purpose:** Kiro CLI headless mode authentication ONLY
- **NOT** an OpenAI-compatible API — cannot be used as provider in Hermes/9Router

## API Endpoint Investigation
Base URL: `https://app.kiro.dev/api`

### What was tried (all returned `UnknownOperationException` with HTTP 200):
- `/v1/chat/completions` — POST with OpenAI format
- `/v1/completions` — POST with OpenAI format
- `/v1/complete`, `/chat/completions`, `/v1/generate`, `/invoke`, `/v1/invoke`
- `/v1/messages` — POST with Anthropic format + `anthropic-version` header

### Auth formats tried:
- `Authorization: Bearer <key>` → "Bearer token authentication is not supported for this operation" (401/403)
- `x-api-key: <key>` → Returns HTML frontend (200) for GET, `UnknownOperationException` for POST
- `Authorization: Api-Key <key>` → Returns HTML frontend (200) for GET

### Backend: AWS Bedrock (Amazon Coral)
Error messages confirm `com.amazon.coral.service` — this is AWS API Gateway, not a standard proxy.

## Model lineup (Kiro Pro, Jun 2026)
| Model | Context | Cost multiplier |
|-------|---------|----------------|
| Claude Opus 4.8 | 1M | 2.2x |
| Claude Opus 4.7 | 1M | 2.2x |
| Claude Opus 4.6 | 1M | 2.2x |
| Claude Sonnet 4.6 | 1M | 1.3x |
| Claude Sonnet 4.5 | 200K | 1.3x |
| Claude Haiku 4.5 | 200K | 0.4x |
| DeepSeek 3.2 | 128K | 0.25x |
| MiniMax M2.5 | 200K | 0.25x |

## Conclusion
Kiro API keys are for Kiro's own protocol only. To use Kiro models programmatically, install Kiro CLI and use headless mode. Cannot be used as a generic LLM API provider.

## Pitfall
- Don't assume all "API Key" pages expose OpenAI-compatible endpoints
- AWS Bedrock-backed services often use proprietary protocols
- `ksk_` prefix = Kiro Service Key, CLI-only
