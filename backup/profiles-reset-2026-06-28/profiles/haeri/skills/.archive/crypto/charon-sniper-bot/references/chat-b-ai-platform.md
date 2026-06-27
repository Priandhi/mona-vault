# chat.b.ai / chat.ainft.com — Platform Notes

## Discovery (Jun9)

**chat.b.ai** is a frontend for **chat.ainft.com** (AINFT — AI + NFT platform).

### Key Facts
- **Actual domain:** `chat.ainft.com` (chat.b.ai redirects/rewrites to it)
- **Tech stack:** Next.js SPA + Auth.js v5 (NextAuth)
- **Login methods:** Wallet (MetaMask, TronLink, Trust, Phantom, Binance, OKX, KuCoin, Bitget, TokenPocket, Bybit) + Google OAuth
- **NO email/password registration** — wallet or Google only
- **New user gift:** 500,000 free credits
- **API key format:** `sk-xxx...xxxx`

### Auth Flow (Wallet)
1. User clicks Login → selects chain tab (TRON / EVM / Solana) → clicks wallet provider
2. Frontend requests wallet connection via `window.ethereum`
3. Server provides nonce/challenge, user signs with wallet
4. Signature verified server-side → account created + session

### Auth Flow (Google)
Standard OAuth redirect flow → account created on callback.

### API Key Usage
- Generated from **Settings → API** inside logged-in dashboard
- Format: `sk-` prefix, ~60+ chars
- Use as `Authorization: Bearer ***` header
- Web session cookie ≠ API key

### Browser Automation Challenges
- Next.js SPA doesn't render in headless browser without residential proxy
- Mock `window.ethereum` injection works but React event handlers may not detect it
- Best approach: use API directly if key available, or register manually from phone

### Registration Automation (Future)
1. Generate wallet (1000 ready at `~/.hermes/farm/wallets_1000.json`)
2. Inject `window.ethereum` mock before page load
3. Intercept signing request, sign with Python `eth_account`
4. Submit signature → extract API key

**Status:** Not yet automated. User needs manual registration first.
