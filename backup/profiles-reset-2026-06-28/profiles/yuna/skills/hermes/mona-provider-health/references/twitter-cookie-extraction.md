# Twitter/X Cookie Extraction Guide

## Problem
Twitter/X login from VPS is blocked by IP-based bot detection. Error: "We've temporarily limited your login."

## Solution: Extract Cookies from Local Browser

### Method 1: Chrome DevTools
1. Open x.com in Chrome (logged in)
2. Press F12 → Application tab → Cookies → `https://x.com`
3. Find and copy these two values:
   - `auth_token` — long hex string
   - `ct0` — long hex string
4. Save to VPS:
   ```bash
   echo 'AUTH_TOKEN_VALUE' > ~/.hermes/vault/.x_auth_token
   echo 'CT0_VALUE' > ~/.hermes/vault/.x_ct0
   chmod 600 ~/.hermes/vault/.x_auth_token ~/.hermes/vault/.x_ct0
   ```

### Method 2: "Get cookies.txt LOCALLY" Extension
1. Install Chrome extension: "Get cookies.txt LOCALLY"
2. Go to x.com (logged in)
3. Click extension icon → Export
4. Copy the `auth_token` and `ct0` values from the exported file
5. Save to vault as above

### Method 3: Mobile Browser
1. Open x.com in mobile browser (logged in)
2. This is harder — mobile browsers don't have DevTools
3. Use a cookie manager app or switch to desktop

## Verification
```bash
# Check files exist and are non-empty
wc -c ~/.hermes/vault/.x_auth_token ~/.hermes/vault/.x_ct0
# auth_token should be ~40+ chars, ct0 should be ~40+ chars
```

## Known Issues
- Files were found EMPTY in June 2026 — credentials were lost/never properly saved
- Cookies expire — if Twitter actions fail, user may need to re-extract
- Multiple accounts: use separate files per account (`.x_auth_token_2`, etc.)
