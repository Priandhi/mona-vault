# Galxe GraphQL API Schema — Introspected June 2026

**Endpoint:** `https://graphigo.prd.galaxy.eco/query`

## Auth Flow (Verified Working)

```graphql
# 1. Get nonce
mutation { nonce }  # returns String

# 2. Signin → JWT
mutation Signin($input: Auth!) { signin(input: $input) }
# Auth input: {address, addressType: \"EVM\", message: siwe_message, signature: \"0x...\"}
# Returns: JWT string (use as Authorization header, NOT Bearer)
```

**SIWE message format (MUST include Expiration Time):**
```
app.galxe.com wants you to sign in with your Ethereum account:
{address}

I authorize the Galxe credential to verify my identity.

URI: https://app.galxe.com
Version: 1
Chain ID: 1
Nonce: {nonce}
Issued At: {ISO_timestamp}
Expiration Time: {ISO_timestamp + 24h}
```

**PITFALL:** Without `Expiration Time` → error `expirationTime must not be empty`.
**PITFALL:** Mutation names are **lowercase**: `nonce`, `signin` (NOT `signIn`).

## Campaign Queries

```graphql
query($input: ListCampaignInput!) {
  campaigns(input: $input) {
    list { id name status description rewardName rewardType chain startTime endTime cap numNFTMinted space { name } }
    pageInfo { hasNextPage endCursor }
  }
}
# Variables: {input: {listType: \"Trending\", statuses: [\"Active\"], first: 20, after: \"\"}}
# Works WITHOUT auth ✅
```

**PITFALL:** `numParticipants` NOT valid. Use `cap` and `numNFTMinted`.
**PITFALL:** `claimAmount` and `isClaimable` NOT valid Credential fields. Only: id, name, type, description.
**ListType:** Newest, Earliest, Trending, Tutorial, MostGG
**CampaignStatus:** Draft, Active, NotStarted, Expired, CapReached, Deleted

## Captcha — WASM-based (NOT GeeTest, NOT reCAPTCHA!)

**BREAKTHROUGH (June 2026):** Galxe captcha is a **custom WASM module**, NOT GeeTest or reCAPTCHA. Error says \"Invalid recaptcha token\" but that's misleading.

**How it works:**
1. Frontend loads `wasm_lib_bg.*.wasm` from `b.galxestatic.com/new-web-prd/_next/static/media/`
2. JS module 28021 exports `H` function which calls WASM `generate_data()`
3. Token: `{lotNumber: sha256(apiName), captchaOutput: <WASM-encrypted>, passToken: sha256(timestamp), genTime: <timestamp>}`
4. WASM has `detect_cdp()` (anti-Playwright) and `generate_sentry()` (anti-bot)

**Bypass — webpack module extraction in browser:**
```javascript
// On app.galxe.com, extract webpack require:
const chunks = window.webpackChunk_N_E;
chunks.push([['captcha_extract'], {}, function(req) { window.__wr = req; }]);

// Generate token:
const mod = window.__wr(28021);
const token = await mod.H({apiName: 'PrepareParticipate'});
// → {lotNumber, captchaOutput, passToken, genTime, encryptedData}
```

**Full browser claim flow:**
```javascript
// 1. Load ethers.js CDN
// 2. Create wallet from PK → sign SIWE → JWT
// 3. Generate captcha via __wr(28021).H({apiName: 'PrepareParticipate'})
// 4. Sign: wallet.signMessage('I want to participate in campaign ' + campaignId)
// 5. Call prepareParticipate with captcha + signature + mintCount: 1
// 6. If allow → on-chain TX to SpaceStation contract
```

**YesCaptcha does NOT work** — Galxe doesn't use standard captcha.

## prepareParticipate — Required Fields

```graphql
mutation($input: PrepareParticipateInput!) {
  prepareParticipate(input: $input) {
    allow disallowReason signature nonce
    spaceStationInfo { address chain version }
    mintFuncInfo { funcName nftCoreAddress claimFeeAmount verifyIDs powahs cap }
  }
}
```

**Required:** campaignID, address, addressType, signature (wallet sig), mintCount (1), captcha ({lotNumber, captchaOutput, passToken, genTime})

**CaptchaInput:** `{lotNumber, captchaOutput, passToken, genTime, encryptedData}`

**Common disallowReason:**
- \"Exceed limit, available claim count is 0\" — already claimed
- \"Invalid main reward gas config\" — campaign bug, skip
- \"Invalid mint count: 0\" — missing mintCount
- \"Invalid recaptcha token\" — missing/invalid captcha

## On-Chain Claim

When `prepareParticipate` returns `allow: true`:
- `signature` — Galxe's server sig for contract
- `spaceStationInfo.address` — contract address
- `mintFuncInfo` — params (nftCoreAddress, verifyIDs, powahs, cap, claimFeeAmount)

**SpaceStation contract:**
- `claim(cid, starNFT, dummyId, powah, claimFeeAmount, signature)` — payable
- `claimCapped(...)` — with cap
- `claimBatch(...)` — batch

**PITFALL:** Wallet needs gas tokens on campaign's chain.

## Task Operations

```graphql
mutation($r: VerifyUserTaskRequest!) { verifyUserTask(request: $r) { success } }
mutation($r: ClaimedUserTaskRequest!) { claimedUserTask(request: $r) { success taskRewardCount } }
```

## Enums

**AddressType:** EVM, SOLANA, SUI, APTOS, TWITTER, DISCORD, TELEGRAM, EMAIL, BITCOIN, TON + 15 more
**Chain:** ETHEREUM, BSC, MATIC, ARBITRUM, BASE, SOLANA, SUI, TON, GRAVITY_ALPHA + 80 more

## Multi-Wallet Strategy

10 wallets from `vault/.wallets_evm`. Each claims each campaign once:
1. SIWE login → JWT per wallet
2. Discover campaigns (Newest less likely claimed)
3. Captcha → prepareParticipate → on-chain claim
4. Rate limit: 500ms/campaign, 2-4s jitter/wallet

**Existing account:** priandhi.eth (0xe489...2Ff, Veliciiaa) — many campaigns already claimed.

## Scripts

- `~/.hermes/scripts/galxe_claimer.py` v2.0 — SIWE auth, discovery, prepareParticipate. Venv: `~/mona-workspace/venv-galxe/`
- Browser-based flow with ethers.js + webpack extraction is the ONLY working captcha approach.
