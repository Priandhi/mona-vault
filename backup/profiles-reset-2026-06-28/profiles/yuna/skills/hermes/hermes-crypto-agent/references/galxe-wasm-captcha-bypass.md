# Galxe WASM Captcha Bypass — Full Technical Reference

**Status:** Verified working June 2026
**Captcha type:** Custom WASM-based (NOT GeeTest, NOT reCAPTCHA, NOT Turnstile)
**WASM binary:** `wasm_lib_bg.9ba64712.wasm` at `b.galxestatic.com/new-web-prd/_next/static/media/`
**YesCaptcha compatibility:** NONE — all GeeTest/Recaptcha/Turnstile task types return `ERROR_TASK_NOT_SUPPORTED`

## How the captcha works

Galxe's frontend loads a custom WASM module (371KB) via webpack module `95088`. The captcha token is generated **client-side** by calling `generate_data(f64_array, api_name, optional_string)` in the WASM. This is NOT a standard captcha service — it's Galxe's own anti-bot system.

The JS wrapper (module `28021`, export `H`) does:
```javascript
let timestamp = Math.floor(Date.now() / 1000).toString();
let wasmResult = JSON.parse(await generateData(apiName, timestamp));
return {
    lotNumber: sha256(apiName),
    captchaOutput: wasmResult.geetest_encrypted,  // from WASM
    passToken: sha256(timestamp),
    genTime: timestamp,
    encryptedData: wasmResult.encrypted_data || ''
};
```

The WASM also has `detect_cdp()` — it detects Chrome DevTools Protocol (anti-Playwright).

## Bypass: Browser-based token extraction

Since the WASM runs in the browser, we extract the webpack require function and call the captcha module directly:

### Step 1: Navigate to any Galxe page
```
https://app.galxe.com/quest/{space}/{campaign_id}
```

### Step 2: Inject webpack require
```javascript
window.webpackChunk_N_E.push(['inject', {}, function(req) { window.__wr = req; }]);
```

### Step 3: Get captcha module
```javascript
const captchaModule = window.__wr(28021);
```

### Step 4: Generate token
```javascript
const token = await captchaModule.H({apiName: 'PrepareParticipate'});
// Returns: {lotNumber, captchaOutput, passToken, genTime, encryptedData}
```

### Step 5: Use in prepareParticipate
```graphql
mutation($i: PrepareParticipateInput!) {
    prepareParticipate(input: $i) {
        allow disallowReason signature nonce
        spaceStationInfo { address chain version }
        mintFuncInfo { funcName nftCoreAddress claimFeeAmount verifyIDs powahs cap }
    }
}
```
Variables:
```json
{
    "i": {
        "campaignID": "GC_xxx",
        "address": "0x...",
        "addressType": "EVM",
        "signature": "0x...(wallet signed message)",
        "mintCount": 1,
        "captcha": {
            "lotNumber": "<from WASM>",
            "captchaOutput": "<from WASM>",
            "passToken": "<from WASM>",
            "genTime": "<from WASM>"
        }
    }
}
```

## Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Invalid recaptcha token" | Missing or invalid captcha field | Generate fresh WASM token |
| "Invalid mint count: 0" | Missing `mintCount: 1` | Add mintCount to input |
| "Exceed limit, available claim count is 0" | Already claimed or not eligible | Try different campaign or wallet |
| "Invalid main reward gas config" | Server-side campaign config issue | Skip this campaign |
| "must be defined" on `signature` | Signature field required | Sign campaign message with wallet PK |

## SIWE Auth (no browser needed)

```python
# 1. Get nonce
nonce = gql('mutation { nonce }')['data']['nonce']

# 2. Build SIWE message (MUST include Expiration Time)
siwe = f"""app.galxe.com wants you to sign in with your Ethereum account:
{address}

I authorize the Galxe credential to verify my identity.

URI: https://app.galxe.com
Version: 1
Chain ID: 1
Nonce: {nonce}
Issued At: {now.isoformat()}
Expiration Time: {expiry.isoformat()}"""

# 3. Sign with eth_account
sig = Account.sign_message(encode_defunct(text=siwe), pk).signature.hex()

# 4. Get JWT
jwt = gql('mutation Signin($input: Auth!) { signin(input: $input) }',
          {'input': {'address': addr, 'addressType': 'EVM', 'message': siwe, 'signature': '0x'+sig}})
```

## Two-step claiming flow

1. `prepareParticipate` → Galxe returns `signature` + `nonce` + `spaceStationInfo` + `mintFuncInfo`
2. Wallet submits on-chain TX to SpaceStation contract (`claim()` / `claimCapped()`) using the signature from step 1

**Requires gas tokens** on the campaign's chain (MATIC, ETH, BSC, etc.)

## API endpoint

`https://graphigo.prd.galaxy.eco/query` (NOT `galxe.org`)

## Valid campaign list fields
`id`, `name`, `status`, `chain`, `cap`, `numNFTMinted`, `space { name }`, `rewardName`, `rewardType`, `startTime`, `endTime`, `description`, `thumbnail`, `tags`

**NOT valid on list:** `numParticipants` (causes GRAPHQL_VALIDATION_FAILED)

## Valid campaign detail fields (single query)
`id`, `name`, `status`, `description`, `chain`, `cap`, `numNFTMinted`, `credentialGroups { id name description credentials { id name type description } }`, `space { name }`

**NOT valid on detail:** `numParticipants`, `claimAmount`, `isClaimable` on credentials
