# Kiro + 9Router Integration Guide

## ⚡ Quick Start: Dashboard Google OAuth (WORKING METHOD)

The **only reliable way** to connect Kiro to 9Router's built-in provider is via the dashboard:

1. Open `http://localhost:20128/dashboard` in a real browser (phone/laptop)
2. Password: `123456`
3. Providers → Kiro AI → Add Connection → **AWS Builder ID**
4. On AWS page → **Continue with Google** → login with Kiro account email
5. Done! Token auto-saved, models available as `kr/*`

**Why other methods fail:**
- Import Token with Kiro CLI tokens → "Bad credentials" (different client_id, token:signature format)
- Import Token with browser tokens → "Bad credentials" (truncated/expired)
- Auto-import endpoint → "Local only: CLI token required" (undocumented auth)
- AWS Builder ID flow via headless browser → bot detection

## Architecture

```
Hermes/Client → 9Router (:20128) → Kiro Gateway (:8333) → Kiro API (AWS Bedrock)
                                     ↑
                              kiro-tokend (:48321, auto-refresh OAuth token)
```

## How It Works

Kiro (AWS's AI coding IDE) exposes models like Claude Opus 4.8 (1M context) via AWS Bedrock.
The API at `app.kiro.dev/api` is NOT OpenAI-compatible — it uses AWS Coral/Bedrock protocol.
To use Kiro models through 9Router, you need two extra components:

1. **Kiro Gateway** (Python, port 8333) — translates OpenAI-compatible requests → Kiro Bedrock API
2. **kiro-tokend** (port 48321) — daemon that auto-refreshes OAuth tokens

## Auth Flow

- Kiro API keys (`ksk_` prefix) are for web/CLI only — NOT usable as API auth
- The proxy stack uses **OAuth refresh tokens** from `kiro-cli login`
- kiro-tokend keeps tokens fresh automatically

## Setup

### Prerequisites
- 9Router already running (Docker on VPS)
- Node.js >= 24 (for kirowannasleep)
- Python 3 (for kiro-gateway)

### Option A: Full Ecosystem (Recommended)

Repo: `marktantongco/kiro-ai-ecosystem`

```bash
# 1. Install Kiro CLI
curl -fsSL https://cli.kiro.dev/install | bash

# 2. Login (device flow for headless VPS — CRITICAL: use --use-device-flow)
kiro-cli login --use-device-flow
# → Shows URL + one-time code
# → Open URL in any browser (phone/laptop), enter code, login with Google/GitHub
# → Token saved to ~/.local/share/kiro-cli/data.sqlite3
# NOTE: Without --use-device-flow, CLI tries to open browser and fails on headless VPS

# 3. Clone ecosystem
git clone https://github.com/marktantongco/kiro-ai-ecosystem.git
cd kiro-ai-ecosystem

# 4. Setup Kiro Gateway (Python proxy)
cd kiro-gateway
pip install -r requirements.txt
python main.py --port 8333

# 5. Setup kiro-tokend (token refresh daemon)
# Runs on port 48321, auto-refreshes OAuth tokens

# 6. Add Kiro Gateway as 9Router provider
# In 9Router dashboard → Providers → Add
# Type: OpenAI Compatible
# Base URL: http://localhost:8333/v1
# Auth: OAuth (managed by kiro-tokend)
```

### Option B: Standalone Kiro Gateway

```bash
git clone https://github.com/Jwadow/kiro-gateway.git
cd kiro-gateway
pip install -r requirements.txt
cp .env.example .env
# Edit .env with REFRESH_TOKEN or KIRO_CREDS_FILE + PROXY_API_KEY
python main.py --port 8333
```

### Option C: kirowannasleep (Multi-account)

Repo: `superti4r/kirowannasleep`

For managing multiple Kiro accounts with automatic token refresh.
Syncs OAuth credentials to 9Router's SQLite database at `~/.9router/db/data.sqlite`.

## Available Models (via Kiro)

| Model | Context | Cost Multiplier | Status |
|-------|---------|----------------|--------|
| Claude Opus 4.8 | 1M | 2.2x | Experimental |
| Claude Opus 4.7 | 1M | 2.2x | Experimental |
| Claude Opus 4.6 | 1M | 2.2x | Active |
| Claude Sonnet 4.6 | 1M | 1.3x | Active |
| Claude Sonnet 4.5 | 200K | 1.3x | Active |
| Claude Haiku 4.5 | 200K | 0.4x | Active |
| DeepSeek 3.2 | 128K | 0.25x | Experimental |
| MiniMax M2.5 | 200K | 0.25x | Experimental |
| GLM-5 | — | — | Experimental |
| Qwen3 Coder Next | — | — | Experimental |

## 9Router Model Name Format

After setup, Kiro models appear as `kr/model-name`:
- `kr/claude-opus-4-8` — Claude Opus 4.8
- `kr/claude-sonnet-4-6` — Claude Sonnet 4.6
- `kr/claude-haiku-4-5` — Claude Haiku 4.5
- `kr/deepseek-3-2` — DeepSeek 3.2

## Key Repos

| Repo | Purpose |
|------|---------|
| `marktantongco/kiro-ai-ecosystem` | Full stack: 9Router + Kiro Gateway + kiro-tokend |
| `superti4r/kirowannasleep` | Multi-account token manager for 9Router |
| `Jwadow/kiro-gateway` | Standalone Kiro → OpenAI proxy (Python, FastAPI) |
| `zesbe/9r-claude` | Claude Code CLI wrapper for 9Router/Kiro endpoints |

## Auth Methods (from kiro-gateway)

Kiro Gateway (`Jwadow/kiro-gateway`) supports 4 credential sources:

### Option 1: JSON Credentials File (Kiro IDE)
```env
KIRO_CREDS_FILE="~/.aws/sso/cache/kiro-auth-token.json"
PROXY_API_KEY="your-gateway-password"
```
JSON format:
```json
{
  "accessToken": "eyJ...",
  "refreshToken": "eyJ...",
  "expiresAt": "2025-01-12T23:00:00.000Z",
  "profileArn": "arn:aws:codewhisperer:us-east-1:...",
  "region": "us-east-1"
}
```

### Option 2: Environment Variables
```env
REFRESH_TOKEN="your_kiro_refresh_token"
PROXY_API_KEY="your-gateway-password"
```

### Option 3: AWS SSO (kiro-cli / Builder ID)
```env
KIRO_CREDS_FILE="~/.aws/sso/cache/your-sso-cache-file.json"
PROXY_API_KEY="your-gateway-password"
```
Auto-detects auth type (Kiro Desktop vs AWS SSO OIDC based on clientId/clientSecret presence).

### Option 4: kiro-cli SQLite Database
```env
KIRO_CLI_DB_FILE="~/.local/share/kiro-cli/data.sqlite3"
PROXY_API_KEY="your-gateway-password"
```
Reads from `auth_kv` table — supports both `kirocli:odic:token` and `codewhisperer:odic:token` key formats.

### Option 5: Browser Cookies
Extract refresh token from browser cookies after logging into `app.kiro.dev`.
Look for requests to `prod.us-east-1.auth.desktop.kiro.dev/refreshToken`.

### Token Refresh
- **Kiro Desktop Auth**: `https://prod.{region}.auth.desktop.kiro.dev/refreshToken`
- **AWS SSO (OIDC)**: `https://oidc.{region}.amazonaws.com/token`
- Auto-detected based on credentials file content

### Multi-Account Support
Set `ACCOUNT_SYSTEM=true` in `.env` and use `credentials.json`:
```json
[
  {"type": "json", "path": "~/.aws/sso/cache/kiro-auth-token.json"},
  {"type": "sqlite", "path": "~/.local/share/kiro-cli/data.sqlite3"},
  {"type": "refresh_token", "refresh_token": "***", "profile_arn": "arn:..."}
]
```
Failover: when one account hits 429/402, automatically tries next.

## Pitfalls

1. **`ksk_` API keys are NOT refresh tokens** — web API keys won't work for proxy auth
2. **Kiro CLI login requires browser** — use device flow on headless VPS: `kiro-cli login --use-device-flow`
3. **Token expiry** — kiro-tokend must run continuously or tokens expire
4. **AWS Bedrock protocol** — Kiro API is NOT OpenAI-compatible, gateway is mandatory
5. **Pro plan required** for Claude Opus 4.8 — Free tier only gets Sonnet 4.5 and below
6. **Regions** — Models available in us-east-1, eu-central-1
7. **9Router "Import Token" dialog fails with all token sources** — Three known failure modes:
   - Browser-extracted refresh tokens → "Bad credentials" (truncated, expired, or wrong format)
   - Kiro CLI tokens (from `kiro-cli login`) → "Bad credentials" (CLI uses different `client_id` than 9Router; tokens have `token:signature` format that 9Router rejects)
   - Auto-import endpoint → "Local only: CLI token required" (undocumented auth header)
   - **WORKAROUND:** Use the dashboard Google OAuth flow instead (see Quick Start above). This is the only method that works reliably. CLI tokens are fundamentally incompatible with 9Router's Import Token feature.
8. **Kiro CLI install URL** — Correct URL is `https://cli.kiro.dev/install` (NOT `https://kiro.dev/install.sh` which returns 404)
