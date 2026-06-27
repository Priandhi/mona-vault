# Kiro Connection Setup in 9Router

## Dashboard Flow (Recommended)

1. Navigate to `http://localhost:20128/dashboard/providers/kiro`
2. Click **"Add Connection"**
3. Modal appears with 3 options:
   - **AWS Builder ID** — Recommended, free AWS account required (DeviceCode OAuth flow)
   - **AWS IAM Identity Center** — Enterprise users
   - **Import Token** — Paste refresh token from Kiro IDE
4. For Import Token: paste the refresh token → click "Import Token"
5. 9Router validates by attempting a token refresh against Kiro's auth endpoint

## Token Storage

- **File**: `~/.aws/sso/cache/kiro-auth-token.json`
- **Auto-import endpoint**: `GET /api/oauth/kiro/auto-import` — reads from this file
- **Import endpoint**: `POST /api/oauth/kiro/import` — accepts `{ "refreshToken": "..." }`

### Token File Format
```json
{
  "refreshToken": "aorAAAAA...",
  "accessToken": "aoaAAAAA...",
  "region": "us-east-1",
  "expiresAt": "2026-06-18T12:51:00Z",
  "clientId": "y8ajXt6tRpqfvTiVhGdq-XVzLWVhc3QtMQ",
  "clientSecret": "eyJraW...",
  "oauthFlow": "DeviceCode",
  "scopes": ["codewhisperer:completions", "codewhisperer:analysis", "codewhisperer:conversations"]
}
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/oauth/kiro/auto-import` | GET | Auto-detect token from `~/.aws/sso/cache/kiro-auth-token.json` |
| `/api/oauth/kiro/import` | POST | Import refresh token (`{ "refreshToken": "..." }`) |
| `/api/oauth/kiro/social-authorize` | GET | Start Google/GitHub OAuth flow (`?provider=google`) |
| `/api/oauth/kiro/social-exchange` | POST | Exchange OAuth code for tokens |

## Available Models (prefix: `kr/`)

- `kr/claude-sonnet-4.5` — Best coding
- `kr/claude-haiku-4.5` — Fast
- `kr/deepseek-3.2` — Free reasoning
- `kr/qwen3-coder-next` — Code specialist
- `kr/glm-5` — GLM
- `kr/MiniMax-M2.5` — MiniMax
- Thinking variants: `kr/claude-sonnet-4.5-thinking`, `kr/claude-haiku-4.5-thinking`
- Agentic variants: `kr/claude-sonnet-4.5-agentic`, `kr/claude-haiku-4.5-agentic`
- Combined: `kr/claude-sonnet-4.5-thinking-agentic`, `kr/claude-haiku-4.5-thinking-agentic`

## ⚠️ CRITICAL: Browser Cookie Tokens ≠ Kiro IDE Tokens

**Tokens from Mises Browser / Cookie Editor will NOT work with 9Router's Kiro import.**

The import endpoint validates tokens by attempting a refresh against Kiro's AWS Cognito auth endpoint. Browser session cookies (`AccessToken` / `RefreshToken` from `kiro.dev` cookies) use a different auth flow (session-based) than the AWS Builder ID DeviceCode flow that 9Router expects.

**Symptoms:**
- Import returns: `"Token validation failed: Token refresh failed: {"message":"Bad credentials"}"`
- Token format looks similar (starts with `aoaAAAAA...` / `aorAAAAA...`) but validation fails

**Why:**
- Browser cookies use Kiro's web session auth (tied to browser session state)
- 9Router uses AWS Builder ID DeviceCode flow (tied to `clientId` + `clientSecret`)
- The refresh tokens are not interchangeable between flows

**Fix:**
1. Use **AWS Builder ID** option in dashboard (opens Google OAuth in browser)
2. Or get refresh token from **Kiro IDE** (desktop app) → Settings → Accounts
3. Or use the existing `~/.aws/sso/cache/kiro-auth-token.json` from a previous Kiro CLI login

## ⚠️ Kiro Pro vs Free Tier — Different Auth Systems

**AWS Builder ID always creates a NEW free-tier account (50 credits).** It does NOT link to an existing Kiro Pro subscription.

- **Kiro Pro** = subscription on `app.kiro.dev` via Google OAuth (web session auth)
- **AWS Builder ID** = separate identity system (DeviceCode flow via AWS Cognito)
- **Kiro CLI** (`kiro-cli login --license pro`) = also creates free tier, even with `--license pro` flag
- **9Router's Kiro provider** = uses AWS Builder ID flow → always free tier

**The Pro subscription and AWS Builder ID are completely separate auth systems.** There is no known way to use a Kiro Pro subscription through 9Router.

**Recommendation:** Skip Kiro Pro for 9Router. Use Kimchi + MiMo instead:
- `kimchi/minimax-m2.7` for main tasks ($240+ remaining credit)
- `xmtp/mimo-v2.5-pro` for fallback

## Phone Access via Cloudflare Tunnel

When direct VPS IP port is blocked, user needs to access 9Router dashboard from phone (Mises browser) to complete OAuth:

```bash
cloudflared tunnel --url http://localhost:20128
# Get URL from logs → share with user
```

**Critical:** The OAuth flow (AWS Builder ID → Google login) must happen in the **user's browser** (Mises on phone), NOT in the VPS browser automation. The VPS browser can't complete OAuth on behalf of the user because the redirect goes to AWS/Google login pages that require user interaction.

**Workflow:**
1. Start cloudflared tunnel on VPS
2. Share URL with user (format: `https://xxx.trycloudflare.com`)
3. User opens URL in Mises → logs into 9Router dashboard
4. User navigates to Kiro AI → Add Connection → AWS Builder ID
5. User completes Google OAuth in Mises
6. Token auto-saved to 9Router DB
