# Kiro Auth Systems — Full Analysis

## The Problem

User has Kiro Pro subscription (1000 credits) on `app.kiro.dev` with Google login (`ppriandhi87@gmail.com`). When trying to connect Kiro to 9Router, the auth always creates a FREE tier account (50 credits) instead of using the Pro subscription.

## Root Cause: Two Separate Auth Systems

### System 1: Kiro Web App (Pro)
- **Auth method:** Google OAuth via `app.kiro.dev`
- **Token format:** `aoaAAAAA...` (access), `aorAAAAA...` (refresh)
- **Token source:** Browser cookies after Google login
- **Subscription:** Pro (1000 credits, Claude Opus 4.8)
- **OAuth client:** Web app client ID (unknown, different from CLI)
- **Token storage:** Browser cookies, optionally `~/.aws/sso/cache/kiro-auth-token.json` if Kiro IDE is installed

### System 2: AWS Builder ID (Free)
- **Auth method:** AWS Builder ID device flow
- **Token format:** `aoaAAAAA...` (access), `aorAAAAA...` (refresh) — same format!
- **Token source:** `kiro-cli login --use-device-flow` or 9Router dashboard
- **Subscription:** Free (50 credits, Sonnet/Haiku only)
- **OAuth client:** `y8ajXt6tRpqfvTiVhGdq-XVzLWVhc3QtMQ` (from kiro-cli)
- **Token storage:** `~/.local/share/kiro-cli/data.sqlite3` (CLI) or `~/.9router/db/data.sqlite` (9Router)

### Why They're Incompatible

Both systems use the same token format (`aoa`/`aor` prefixes) but different OAuth client IDs. When 9Router tries to refresh a token from System 1 using System 2's client credentials, it fails with `"Bad credentials"` because:

1. The refresh token was issued to a different `client_id`
2. AWS Cognito rejects cross-client token refresh
3. The `clientId` + `clientSecret` in `~/.aws/sso/cache/kiro-auth-token.json` must match the token's issuing client

## Attempted Solutions (All Failed)

### 1. Import Token via Dashboard
- **What:** Paste browser-extracted RefreshToken into 9Router's "Import Token" dialog
- **Result:** `"Token validation failed: Token refresh failed: {"message":"Bad credentials"}"`
- **Why:** Token from web app's OAuth client, 9Router uses CLI's client to refresh

### 2. Update kiro-auth-token.json
- **What:** Replace tokens in `~/.aws/sso/cache/kiro-auth-token.json` with browser tokens
- **Result:** Auto-import finds the token, but import still fails with "Bad credentials"
- **Why:** The `clientId`/`clientSecret` in the file are for the CLI client, not the web app client

### 3. kiro-cli login
- **What:** `kiro-cli login --use-device-flow`
- **Result:** Creates NEW free-tier account (50 credits), not linked to Pro
- **Why:** Device flow creates a new AWS Builder ID, doesn't use existing Pro subscription

### 4. AWS Builder ID → Continue with Google
- **What:** 9Router dashboard → AWS Builder ID → Continue with Google → login with Pro email
- **Result:** Creates NEW AWS Builder ID linked to Google, but still free tier
- **Why:** AWS Builder ID is a separate identity system from Kiro's web auth

### 5. Social Authorize Flow (9Router API)
- **What:** `GET /api/oauth/kiro/social-authorize?provider=google` returns an OAuth URL with PKCE
- **Response:** `{"authUrl":"https://prod.us-east-1.auth.desktop.kiro.dev/login?idp=Google&redirect_uri=kiro://kiro.kiroAgent/authenticate-success&code_challenge=...&state=...&prompt=select_account","state":"...","codeVerifier":"...","codeChallenge":"...","provider":"google"}`
- **Problem:** The `redirect_uri` is `kiro://kiro.kiroAgent/authenticate-success` — a deep link for the Kiro IDE desktop app. This CANNOT be opened in a mobile browser (Mises/Chrome). The browser will fail to redirect after Google login.
- **Code exchange:** `POST /api/oauth/kiro/social-exchange` requires `provider`, `code`, `redirectUri`, and the `codeVerifier` from the authorize step. But since the redirect_uri is a deep link, the `code` can never be captured from a browser.

### 6. Auto-detect from kiro-auth-token.json
- **What:** `GET /api/oauth/kiro/auto-import` scans `~/.aws/sso/cache/kiro-auth-token.json`
- **This file is created by:** `kiro-cli login` (device flow)
- **Format:** `{"refreshToken":"aor...","accessToken":"aoa...","region":"us-east-1","expiresAt":"...","clientId":"y8ajXt6tRpqfvTiVhGdq-XVzLWVhc3QtMQ","clientSecret":"eyJraW...","oauthFlow":"DeviceCode","scopes":["codewhisperer:completions","codewhisperer:analysis","codewhisperer:conversations"]}`
- **Can update manually:** Replace tokens with new ones from browser, keep clientId/clientSecret. But import still fails if tokens are from a different OAuth client.

## What Would Work (Theoretical)

1. **Kiro Pro CLI support** — If Kiro CLI supported `--license pro` with Google OAuth that recognizes the Pro subscription. Currently doesn't work (tested Jun 2026).

2. **Web app OAuth client extraction** — If we could extract the `clientId`/`clientSecret` from the Kiro web app and configure 9Router to use those for token refresh. Requires reverse-engineering the web app's OAuth flow.

3. **Kiro IDE token extraction** — If user has Kiro IDE installed on their computer, the IDE stores refresh tokens in `~/.aws/sso/cache/kiro-auth-token.json`. These tokens are from the CLI client and CAN be imported into 9Router. But they need to be from a Pro-linked account.

## Current Recommendation

**Skip Kiro Pro for now.** Use Kimchi + MiMo:

| Task | Model | Provider |
|------|-------|----------|
| Main | `kimchi/minimax-m2.7` | Kimchi ($50-250/mo) |
| Fallback | `xmtp/mimo-v2.5-pro` | MiMo (free, unlimited) |
| Vision | `xmtp/mimo-v2-omni` | MiMo (free) |

If Kiro is critical, user must:
1. Install Kiro IDE on their PC/laptop
2. Login with Google Pro account in the IDE
3. Extract the refresh token from IDE's token storage
4. Import that specific token into 9Router
