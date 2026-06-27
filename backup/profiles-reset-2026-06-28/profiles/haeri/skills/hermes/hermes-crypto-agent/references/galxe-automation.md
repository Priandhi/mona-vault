# Galxe Automation — Findings & Limitations (Updated June 2026)

## What Works (API, No Auth)

**Endpoint:** `https://graphigo.prd.galaxy.eco/query` (NOT `.org` — that domain doesn't resolve)

**Headers:**
```
Content-Type: application/json
Origin: https://app.galxe.com
User-Agent: Mozilla/5.0
```

**Verified queries (no auth needed):**

```graphql
# Check if address has Galxe account
query { addressInfo(address: "0x...") { id address username } }

# Get trending campaigns
query { campaigns(input: {first: 5, listType: Trending}) { list { id name status } totalCount } }

# Get campaigns claimable by user (uses Galxe ID, NOT address)
query { campaigns(input: {first: 20, claimableByUser: "GALXE_ID"}) { list { id name status } totalCount } }

# Get campaigns related to address (past participations)
query { campaigns(input: {first: 20, relatedByAddr: "0x..."}) { list { id name status } totalCount } }
```

**ListCampaignInput filter fields (verified via introspection):**
- `first: Int`, `after: String` — pagination
- `listType: ListType` — enum: `Newest`, `Earliest`, `Trending`, `Tutorial`, `MostGG`
- `status: CampaignStatus` — enum (Active, Expired, etc.)
- `statuses: [CampaignStatus!]` — list filter
- `claimableByUser: String` — Galxe ID (NOT wallet address)
- `relatedByAddr: String` — wallet address
- `bookmarkedBy: String` — Galxe ID
- `searchString: String` — text search
- `spaceId: ID` — filter by space
- `chains`, `types`, `permissions`, `rewardTypes`, `ecosystem` — additional filters
- `isRecurring: Boolean`, `isVerified: [Boolean]`, `ggSlot: Boolean`

**GraphQL introspection fully available** — can discover all types, fields, enums at runtime.

**Mutations (require auth — return "Invalid request" without session):**
- `sendEmailCode` — needs GeeTest CAPTCHA + auth
- `verifyEmailCode` — needs authenticated session
- All quest verification/claim mutations need auth

## Privy Authentication (APP ID FOUND)

**Privy App ID: `cm04asygd041fmry9zmcyn5o5`** ✅ CONFIRMED (June 2026)

**Discovery method:** Browser console on Galxe page:
```javascript
performance.getEntriesByType('resource').filter(r => r.name.includes('privy')).map(r => r.name)
// → ["https://auth.privy.io/api/v1/apps/cm04asygd041fmry9zmcyn5o5/cross-app/details"]
```

**Privy email OTP endpoint:**
```
POST https://auth.privy.io/api/v1/passwordless/init
Headers:
  Content-Type: application/json
  privy-app-id: cm04asygd041fmry9zmcyn5o5
Body: {"email": "user@example.com"}
```

**BLOCKED:** Returns 403 "Origin not allowed" from BOTH curl AND headless browser. Origin validation is fingerprint-based (TLS fingerprint, browser API checks), not just header-based. Cannot be bypassed with header spoofing.

## GeeTest v4 CAPTCHA Requirement

**All Galxe auth mutations require GeeTest v4 CAPTCHA.** Verified via GraphQL introspection:

```
mutation SendEmailCode($input: SendVerificationEmailInput!) {
    sendEmailCode(input: $input) { code message }
}
# $input.captcha is REQUIRED (type: CaptchaInput)
```

**CaptchaInput fields:** `lotNumber`, `captchaOutput`, `passToken`, `genTime` (all GeeTest v4)

Without captcha → 422 error: `"must be defined","path":["variable","input","captcha"]`

**Implication:** Even with correct Privy app ID and bypassed Origin check, GeeTest CAPTCHA still needs solving. Options:
- CAPTCHA solving service (2captcha, anticaptcha) — costs ~$0.001/solve
- Manual solve by user
- Browser extension that auto-solves (unreliable)

## JS Bundle Analysis (How to Find Hidden Config)

Galxe's frontend JS bundles are at `https://b.galxestatic.com/new-web-prd/_next/static/chunks/{name}.js`.

**To find bundle URLs:** In browser console:
```javascript
performance.getEntriesByType('resource').filter(r => r.name.includes('.js')).map(r => r.name)
```

**To search for config/API endpoints in bundles:**
```bash
# Get bundle URLs from page
curl -sL 'https://app.galxe.com/quest/explore/all' | grep -oP '/_next/static/chunks/[^"]+\.js' | while read chunk; do
  result=$(curl -s "https://b.galxestatic.com/new-web-prd${chunk}" | grep -oP 'TARGET_PATTERN')
  [ -n "$result" ] && echo "FOUND in ${chunk}: $result"
done
```

**Key findings from bundle analysis:**
- API endpoint: `graphigo.prd.galaxy.eco` (found in chunks 43976, app/layout, 55712)
- Privy cross-app: `auth.privy.io` (found in chunk 22379)
- GraphQL mutations: `SendEmailCode`, `SendVerifyCode`, `BindIncompleteUserAccount`, `VerifyDiscord`, `VerifyGithubAccount` (found in chunks 41461, 64590)
- CaptchaInput structure: `lotNumber`, `captchaOutput`, `passToken`, `genTime` (found in chunk 17185)

## What Doesn't Work

### Headless Browser Login (VERIFIED BROKEN — June 2026)

Galxe detects headless Chromium and triggers anti-bot page refresh. **5+ attempts in one session, ALL failed.**

**Symptoms:**
1. Login modal opens, email entered, "Send a code" clicked → OTP sent
2. Before user can provide OTP, page refreshes automatically
3. `browser_snapshot()` returns `(empty page)` or original page without modal
4. Cycle repeats — impossible to complete login flow

**stealth_warning:** `"Running WITHOUT residential proxies. Bot detection may be more aggressive"`

### Window.ethereum Injection (BROKEN)

Galxe uses WalletConnect v2 SDK — ignores injected `window.ethereum` entirely.

### iPhone Chrome Cookie Export (VERIFIED IMPOSSIBLE)

- `javascript:` URLs stripped from address bar
- No cookie viewer UI
- No bookmarklet support
- Relay server approach fails (Same-Origin Policy)

### Privy API Direct (BLOCKED — fingerprint-based Origin check)

Even with correct app ID and Origin header, Privy returns 403 "Origin not allowed".

## Recommended Approach

### Option 1: Cookie-based Session (BEST — requires user action)

**Desktop (30 seconds):**
1. User logs into Galxe on Chrome PC
2. Install "Cookie-Editor" extension → Export → JSON
3. Send JSON to Mona → save to `~/mona-workspace/vault/.galxe_cookies.json`
4. Reuse: `context.add_cookies(cookies)`

**Safari on iPhone:**
1. Login to `app.galxe.com` in Safari (NOT Chrome)
2. Type in address bar: `javascript:document.cookie`
3. Copy output → send to Mona

### Option 2: Partial Automation (NO auth needed)

For quests that don't need Galxe authentication:
- Visit URL tasks → Playwright direct visit
- On-chain claims → web3 direct TX
- Balance/hold verification → RPC check

For Galxe-specific tasks → user does manually, Mona monitors via API.

### Option 3: Wallet Signature Auth (✅ IMPLEMENTED — June 2026)

**FULLY WORKING.** Sign SIWE message with wallet PK → submit to Galxe auth → get JWT token. Bypasses browser entirely.

**Flow (verified):**
```graphql
# Step 1: Get nonce
mutation { nonce }

# Step 2: Build SIWE message (MUST include expirationTime)
# Format:
app.galxe.com wants you to sign in with your Ethereum account:
{address}

I authorize the Galxe credential to verify my identity.

URI: https://app.galxe.com
Version: 1
Chain ID: 1
Nonce: {nonce_from_step_1}
Issued At: {ISO_8601_timestamp}
Expiration Time: {ISO_8601_timestamp + 24h}

# Step 3: Sign with eth_account (EIP-191 personal_sign)
from eth_account import Account
from eth_account.messages import encode_defunct
msg = encode_defunct(text=siwe_message)
signed = Account.sign_message(msg, private_key)
signature = "0x" + signed.signature.hex()

# Step 4: Submit signin (returns JWT string)
mutation Signin($input: Auth!) { signin(input: $input) }
# Variables: {input: {address, addressType: "EVM", message: siwe_message, signature}}
```

**PITFALL:** SIWE message MUST include `Expiration Time` field. Without it → error: `expirationTime must not be empty`.

**PITFALL:** Mutation names are **lowercase**: `nonce`, `signin` (NOT `nonce`, `signIn`).

**JWT usage:** Pass as `Authorization` header (NOT `Bearer <token>`, just the raw JWT).

**Script:** `~/.hermes/scripts/galxe_claimer.py` — full implementation with login, campaign discovery, prepareParticipate.

## Quest Types Matrix

| Type | Can Automate? | Notes |
|------|--------------|-------|
| Follow on Twitter | ❌ | Needs Twitter cookies |
| Join Telegram | ❌ | Needs Telegram auth |
| Visit URL | ✅ | Playwright visit |
| On-chain TX | ✅ | web3 direct |
| Hold NFT/Token | ✅ | Check balance via RPC |
| Quiz | ⚠️ | Need to find answers first |
| Social share | ❌ | Needs Twitter/social auth |
| Daily check-in | ✅ | If authenticated |
| Claim reward | ⚠️ | Needs auth + sometimes TX |

## Known Galxe Wallets

- **priandhi.eth** / **Veliciiaa** (`0xe489306e4330Ae58De8aBfE8A3e3287d071aE2Ff`) — Email: `ppriandhi87@gmail.com`, Galxe ID: `iMQU2z7CoFDigKMiFaesm5`, X: `@Ehkamu_1`, 29 active quests, Level L1 Carbon, 1/89 XP (June 2026)

## Email-to-Wallet Mapping (Garapan Strategy)

User creating 10 Google accounts for multi-wallet Galxe farming:

| Email | Wallet | Address |
|-------|--------|---------|
| `monaai.crot@gmail.com` | Master | General Galxe registration |
| `monaai.crot1@gmail.com` | Wallet 1 | `0x29Ba...76B7` |
| `monaai.crot2@gmail.com` | Wallet 2 | `0xD723...24A5` |
| `monaai.crot3@gmail.com` | Wallet 3 | `0x5D66...1B88` |
| `monaai.crot4@gmail.com` | Wallet 4 | `0x0d36...476F` |
| `monaai.crot5@gmail.com` | Wallet 5 | `0xaE53...5556` |
| `monaai.crot6@gmail.com` | Wallet 6 | `0xFbba...7d3a` |
| `monaai.crot7@gmail.com` | Wallet 7 | `0xF80d...1b6c` |
| `monaai.crot8@gmail.com` | Wallet 8 | `0xBFc5...846b` |
| `monaai.crot9@gmail.com` | Wallet 9 | `0x743f...C436` |
| `monaai.crot10@gmail.com` | Wallet 10 | `0xdF87...373b` |
| `ppriandhi87@gmail.com` | Veliciiaa | `0xe489...E2Ff` (main Galxe) |

**Storage:** `~/mona-workspace/vault/.galxe_accounts.json` (created when user provides credentials). Accounts being created manually by user (June 2026) — Google requires phone verification per account.

## Web Platform Auth Strategy (Generalized)

Most Web3 quest platforms (Galxe, Zealy, Layer3, Intract) follow the same auth pattern: **CAPTCHA → Email OTP → Session Token**. Generalized pipeline:

```
1. Open login modal → select email auth
2. Extract CAPTCHA config from page DOM/JS bundles
3. Solve CAPTCHA via external service (YesCaptcha/CapSolver/2Captcha)
4. Inject CAPTCHA token into form fields
5. Submit email + CAPTCHA → trigger OTP send
6. User provides OTP → submit verification
7. Capture session cookies/tokens → save to vault
8. Reuse session for automated quest completion
```

**CAPTCHA solving services (verified June 2026):**
| Service | GeeTest v4 | reCAPTCHA v2 | Price | Speed |
|---------|-----------|--------------|-------|-------|
| YesCaptcha | ✅ | ✅ | ~$1.50/1000 | ~15s |
| CapSolver | ✅ | ✅ | ~$1.50/1000 | ~10s |
| 2Captcha | ✅ | ✅ | ~$2.99/1000 | ~20s |

**Pattern for extracting CAPTCHA config from JS bundles:**
```bash
# Get bundle URLs from page
curl -sL 'https://TARGET_SITE/page' | grep -oP '/_next/static/chunks/[^"]+\.js' | while read chunk; do
  curl -s "https://CDN_DOMAIN${chunk}" | grep -oiP 'captcha|geetest|recaptcha|sitekey'
done
```

## CAPTCHA Solving Service — Validated Approach (June 2026)

User's friend agent successfully bypassed CAPTCHA using **YesCaptcha** service. Confirmed working flow (reCAPTCHA v2 example):

1. Extract sitekey from page: `page.locator("data-sitekey")` → get `sitekey` + `callback`
2. Send to YesCaptcha `NoCaptchaTaskProxyless` → poll 3s interval
3. Inject token: `innerHTML + value` to all `g-recaptcha-response` textareas
4. Trigger callback: `window["callbackName"](token)` → green check + server verified

**For Galxe (GeeTest v4, NOT reCAPTCHA):**
- Galxe uses GeeTest v4 with `CaptchaInput`: `lotNumber`, `captchaOutput`, `passToken`, `genTime`
- ⚠️ **YesCaptcha does NOT support GeeTest on user's account** (tested June 2026 — ALL GeeTest variants return "任务类型不正确或不受支持"). Account has 1500 points but only supports reCAPTCHA/HCaptcha/Turnstile.
- CapSolver supports GeeTest v4 ✅ (~$1.50/1000 solves)
- 2Captcha supports GeeTest v4 ✅ (~$2.99/1000 solves)
- **Alternative:** Cookie-based session from user's browser bypasses captcha entirely.

**Status:** User interested but no budget yet (June 2026). When API key available, build full pipeline:
```python
# 1. Navigate to Galxe login modal → click email login
# 2. Extract GeeTest config from page DOM
# 3. Solve GeeTest via CAPTCHA service API
# 4. Inject captcha token into CaptchaInput fields
# 5. Submit SendEmailCode mutation with captcha
# 6. User provides OTP → submit VerifyEmailCode
# 7. Save session cookies to vault for reuse
```

## Pitfalls

- **Email binding is per-wallet, NOT per-account.** Always ask which email is bound BEFORE sending OTP. The Veliciiaa wallet uses `ppriandhi87@gmail.com`, NOT `monaai.crot@gmail.com`.
- **`graphigo.prd.galxe.org` does NOT resolve.** Use `graphigo.prd.galaxy.eco` instead.
- **`claimableByUser` takes Galxe ID, NOT wallet address.** Use `addressInfo` query first to get Galxe ID.
- **Ref IDs change between modal opens.** NEVER hardcode ref IDs — always use `browser_vision(annotate=True)`.
- **"Select Network" modal trap.** Clicking near Network button opens wrong modal. Press Escape, retry.
- **Don't build relay/proxy servers for mobile cookie extraction.** Same-Origin Policy makes it impossible. Use user-side approaches only.
- **Gmail IMAP needs App Password** — regular password returns `AUTHENTICATIONFAILED`.
