---
name: kiro-cli-device-flow
description: Install and authenticate Kiro CLI on headless VPS via device flow, extract tokens for 9Router integration
tags: [kiro, 9router, oauth, device-flow, headless]
---

# Kiro CLI Device Flow — Headless VPS

## Install
```bash
curl -fsSL https://cli.kiro.dev/install | bash
```

## Login (Device Flow)
```bash
kiro-cli login --use-device-flow
# Or with free license (Google/GitHub):
kiro-cli login --license free --use-device-flow
```

## IMPORTANT: Headless VPS Pattern
`terminal()` kills the process before user completes auth. Use `execute_code` with subprocess:

```python
import subprocess, time, os
proc = subprocess.Popen(
    ['kiro-cli', 'login', '--license', 'free', '--use-device-flow'],
    stdout=open('/tmp/kiro_login.txt', 'w'),
    stderr=subprocess.STDOUT, env={**os.environ}
)
time.sleep(12)
with open('/tmp/kiro_login.txt') as f:
    print(f.read())
```

## Token Location
- `~/.local/share/kiro-cli/data.sqlite3` — main token store
- Table: `auth_kv`, key: `kirocli:odic:token`
- Extract: `sqlite3 ~/.local/share/kiro-cli/data.sqlite3 "SELECT value FROM auth_kv WHERE key='kirocli:odic:token';"`

## ⚠️ 9Router Incompatibility
Kiro CLI token format (`aorAAAAAG...:signature`) is NOT compatible with 9Router's "Import Token" feature. 9Router uses a different `client_id` (`kiro-oauth-client` vs CLI's `y8ajXt...`).

**Solution**: Use 9Router dashboard Google OAuth flow instead:
1. Open dashboard → Providers → Kiro AI → Add Connection
2. Select "AWS Builder ID" → "Continue with Google"
3. Login with Google account

## 9Router Auto-Import
Looks for tokens in `~/.aws/sso/cache/kiro-auth-token.json` but requires "CLI token" header — effectively inaccessible via API.

## Model IDs via 9Router
- Kiro: `kr/claude-sonnet-4.5`, `kr/claude-haiku-4.5`, `kr/deepseek-3.2`
- MiMo: `xmtp/mimo-v2.5-pro`
