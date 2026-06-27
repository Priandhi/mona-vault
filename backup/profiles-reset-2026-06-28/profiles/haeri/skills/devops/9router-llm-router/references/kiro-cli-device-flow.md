# Kiro CLI Device Flow — Headless VPS Pattern

## Problem
`kiro-cli login --use-device-flow` requires a long-running process that waits for user authentication. `terminal()` foreground mode kills it before user completes auth.

## Installation
```bash
curl -fsSL https://cli.kiro.dev/install | bash
```
⚠️ `https://kiro.dev/install.sh` returns 404. Use `https://cli.kiro.dev/install`.

## Solution: execute_code with subprocess

```python
import subprocess, time, os

# Run kiro-cli login in background, redirect to file
# Use --license free for Google/GitHub accounts (not Builder ID)
proc = subprocess.Popen(
    ['kiro-cli', 'login', '--license', 'free', '--use-device-flow'],
    stdout=open('/tmp/kiro_login.txt', 'w'),
    stderr=subprocess.STDOUT,
    env={**os.environ}
)

# Wait for output (device code appears in ~5-10s)
time.sleep(12)

# Read output
with open('/tmp/kiro_login.txt') as f:
    output = f.read()

print(f"PID: {proc.pid}")
print(f"Return code: {proc.poll()}")
print(f"Output:\n{output}")
```

## Output Format
```
Confirm the following code in the browser
Code: SRCR-KGPT

Open this URL: https://view.awsapps.com/start/#/device?user_code=SRCR-KGPT
```

## Auth Flow
1. User opens URL in any browser (phone/laptop)
2. User logs in with Google/GitHub (Kiro account) — must select the right auth method on the page
3. User enters the one-time code
4. Token saved to `~/.local/share/kiro-cli/data.sqlite3`

## Token Location (after successful auth)
- `~/.local/share/kiro-cli/data.sqlite3` — main token store (auth_kv table)
- `~/.aws/sso/cache/` — AWS SSO cache files

## Extract Token from sqlite3
```bash
# Check tables
sqlite3 ~/.local/share/kiro-cli/data.sqlite3 ".tables"
# → auth_kv  conversations_v2  migrations  conversations  history  state

# Extract full token JSON
sqlite3 ~/.local/share/kiro-cli/data.sqlite3 \
  "SELECT value FROM auth_kv WHERE key='kirocli:odic:token';"

# Parse with python for clean output
sqlite3 ~/.local/share/kiro-cli/data.sqlite3 \
  "SELECT value FROM auth_kv WHERE key='kirocli:odic:token';" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('ACCESS:', d['access_token']); print('REFRESH:', d['refresh_token'])"

# Extract client registration
sqlite3 ~/.local/share/kiro-cli/data.sqlite3 \
  "SELECT value FROM auth_kv WHERE key='kirocli:odic:device-registration';" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('CLIENT_ID:', d['client_id'])"
```

## Token Format (CRITICAL — for understanding 9Router incompatibility)

Kiro CLI tokens have a **colon-separated format**:
```
aorAAAAAGqg2t0yDs4sdf5LPsWbv9Ps3AzVmAwdjYyXoVd7TvmokaqAdCJu5JOp-ecf8YW8qtCKlJp0clAhjbLUxwCkc0:MGQCMEhde56NithuxmVZWA6XxyF0rDiJrmli+VFhBaxvr91/...
```

- Part before `:` = actual OAuth token
- Part after `:` = AWS signature/proof

**This format is NOT compatible with 9Router's Import Token feature**, which expects a plain OAuth refresh token without the signature suffix. Pasting the full CLI token causes "Bad credentials" error.

## ⚠️ CLI Token ≠ 9Router Import Token

The Kiro CLI uses a different `client_id` (`y8ajXt...`) than 9Router's Kiro provider. Even if you strip the signature suffix, the token won't work because:
1. Different client_id means the refresh token is bound to a different OAuth client
2. 9Router's token refresh endpoint expects tokens issued by its own client

**The only reliable way to connect Kiro to 9Router is via the dashboard Google OAuth flow** — NOT via CLI token import.

## Token Storage: `~/.aws/sso/cache/kiro-auth-token.json`

After successful CLI login, Kiro also writes a token file to `~/.aws/sso/cache/kiro-auth-token.json`:
```json
{
  "refreshToken": "aorAAAAAGqg...",
  "accessToken": "aoaAAAAAGoq...",
  "region": "us-east-1",
  "expiresAt": "2026-06-11T05:10:01Z",
  "clientId": "y8ajXt6tRpqfvTiVhGdq-XVzLWVhc3QtMQ",
  "clientSecret": "eyJraW...",
  "oauthFlow": "DeviceCode",
  "scopes": ["codewhisperer:completions", "codewhisperer:analysis", "codewhisperer:conversations"]
}
```

9Router's **auto-import** (`GET /api/oauth/kiro/auto-import`) reads this file. If the token is expired, you can update `refreshToken` + `accessToken` + `expiresAt` in this file, then trigger auto-import from the dashboard.

**⚠️ Browser cookies from kiro.dev are NOT valid for this file.** The format looks similar but tokens from Mises/Cookie Editor are for a different OAuth client and will fail with "Bad credentials".

## Pitfalls
- Device code expires in ~5 minutes — user must complete auth quickly
- `terminal()` foreground mode kills the process — use `execute_code` with subprocess
- Cloudflare tunnel URL changes each restart — always get fresh URL
- Kiro CLI v2.6.1+ required for device flow support
- `--license free` flag needed for Google/GitHub accounts (not Builder ID)
- Kiro CLI token format (`token:signature`) is incompatible with 9Router Import Token
- `~/.kiro/settings/cli.json` remains empty even after successful auth — tokens are in sqlite3 only
- Auto-import endpoint (`GET /api/oauth/kiro/auto-import`) reads from `~/.aws/sso/cache/kiro-auth-token.json`
- Browser cookies from kiro.dev (Cookie Editor export) are NOT Kiro IDE tokens — will fail with "Bad credentials"
