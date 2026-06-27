---
name: galxe-reverse-engineering
description: Galxe quest/airdrop platform — full API reverse-engineered. Includes auth, campaign discovery, captcha bypass, claim flow, and blockchain TX execution.
triggers:
  - galxe
  - quest claim
  - airdrop claim
  - OAT claim
  - galxe campaign
---

# Galxe Reverse-Engineering (Jun 2026)

## API Endpoint

```
POST https://graphigo.prd.galaxy.eco/query
Content-Type: application/json
Authorization: <JWT>  (optional for public queries)
```

## Auth Flow (SIWE → JWT)

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
Nonce: {nonce}
Issued At: {ISO timestamp}
Expiration Time: {ISO timestamp + 24h}

# Step 3: Sign with eth_account or ethers.js (EIP-191 personal_sign)

# Step 4: Submit signin
mutation Signin($input: Auth!) { signin(input: $input) }
# Returns JWT string directly (not nested object)
```

## Campaign Discovery

```graphql
query($input: ListCampaignInput!) {
  campaigns(input: $input) {
    list { id name status chain cap numNFTMinted rewardName rewardType description space { name } }
    pageInfo { hasNextPage endCursor }
  }
}
# Variables: {input: {listType: "Trending"|"MostGG"|"Newest"|"Earliest", first: 20, statuses: ["Active"]}}
```

## Campaign Detail

```graphql
query($id: ID!) {
  campaign(id: $id) {
    id name status chain description cap numNFTMinted
    credentialGroups { id name description credentials { id name type description } }
    space { name }
  }
}
```

## ⚠️ Captcha — Custom WASM (NOT GeeTest/reCAPTCHA)

Galxe uses a **custom WASM-based captcha** (`wasm_lib_bg.9ba64712.wasm`). This is NOT solvable by YesCaptcha, 2captcha, or any standard captcha service.

### How it works (from frontend JS):
1. Module 95088 loads WASM binary
2. `generate_data(f64_array, api_name, optional_string)` → returns `{"geetest_encrypted": "..."}`
3. Module 28021 wraps this as `H({apiName})` → returns:
```json
{
  "lotNumber": "sha256(apiName)",
  "captchaOutput": "<WASM-generated encrypted token>",
  "passToken": "sha256(timestamp)",
  "genTime": "<unix_timestamp_seconds>",
  "encryptedData": ""
}
```

### How to generate tokens:
**Must run in browser context** where Galxe's JS+WASM is loaded:
```javascript
// Inject webpack require
window.webpackChunk_N_E.push(['inject', {}, function(req) { window._wr = req; }]);

// Get captcha module
const captchaMod = window._wr(28021);

// Generate token
const token = await captchaMod.H({apiName: 'PrepareParticipate'});
// Returns: {lotNumber, captchaOutput, passToken, genTime, encryptedData}
```

### Why this matters:
- YesCaptcha / 2captcha / CapSolver cannot solve this
- Node.js cannot run the WASM (needs browser JS bindings)
- Playwright/Puppeteer detected via `detect_cdp()` function in WASM
- Must use browser console injection approach

## Claim Flow (2 steps + on-chain TX)

### Step 1: prepareParticipate
```graphql
mutation($input: PrepareParticipateInput!) {
  prepareParticipate(input: $input) {
    allow disallowReason signature nonce
    spaceStationInfo { address chain version }
    mintFuncInfo { funcName nftCoreAddress claimFeeAmount verifyIDs powahs cap }
  }
}
```
Input: `{campaignID, address, addressType: "EVM", signature: <wallet_sig>, mintCount: 1, captcha: <token>}`

### Step 2: participate (on-chain TX)
Uses the `signature` from prepareParticipate to call `claim()` on the SpaceStation smart contract.
**Requires gas tokens** (ETH/MATIC/BNB/etc.) on the campaign's chain.

### Step 3 (alternative): For gasless campaigns
Some campaigns allow server-side claiming without on-chain TX.

## Key Pitfalls

1. **"Invalid recaptcha token"** = captcha token missing or invalid (confusing name, it's actually WASM captcha)
2. **"Exceed limit, available claim count is 0"** = wallet already claimed this campaign
3. **"Invalid mint count: 0"** = must pass `mintCount: 1`
4. **"must be defined" on signature** = `signature` field required in PrepareParticipateInput (wallet sign)
5. **GraphQL validation errors** = field names differ from docs. Valid campaign fields: `id name status chain cap numNFTMinted rewardName rewardType space { name }`. Do NOT use `numParticipants` on list queries.
6. **Credential fields**: only `id name type description` are valid. `claimAmount` and `isClaimable` do NOT exist on the GQL schema.
7. **Browser context volatility** — webpack modules and global state lost on page navigation. Do all operations in single console evaluation.
8. **CDP detection** — WASM has `detect_cdp()` that detects Playwright/Puppeteer DevTools Protocol.

## Existing Scripts

- `~/.hermes/scripts/galxe_claimer.py` — API-based claimer (v2.0, works for discovery but can't generate captcha tokens)
- `~/.hermes/scripts/galxe_scanner.mjs` — Node.js campaign scanner (no captcha, discovery only)

## Vault Files

- `vault/.galxe_accounts.json` — priandhi.eth + 10 monaai.crot email accounts
- `vault/.galxe_wallet_pk` — priandhi.eth private key
- `vault/.galxe_cookies.json` — browser cookies
- `vault/.yescaptcha_key` — YesCaptcha API key (useless for Galxe's WASM captcha)
