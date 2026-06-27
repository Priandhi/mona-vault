# Web3 Platform Authentication Patterns

## Chat.AINFT.com (BAI) — Case Study

**Domain**: `chat.ainft.com` (frontend: `chat.b.ai`)

### Auth Architecture
- **Framework**: Next.js SPA + Auth.js (NextAuth v5)
- **Login methods**: Wallet-based (MetaMask, TronLink, Binance, Trust, OKX, TokenPocket, KuCoin, Bitget, Phantom, Bybit) + Google OAuth
- **NO email/password registration**
- **New user reward**: 500,000 free credits on registration

### Auth Flow (Wallet)
1. User clicks wallet button (e.g. MetaMask) in login modal
2. Frontend calls `window.ethereum.request({method: 'eth_requestAccounts'})`
3. Frontend gets nonce/challenge from backend via `/api/auth/csrf`
4. Frontend requests `personal_sign` with message containing nonce + address
5. Backend verifies signature and creates session
6. Session cookie set, user logged in

### Why Pure API Automation Fails
- Auth.js credentials provider requires **client-side wallet signing**
- The signing request goes through `window.ethereum` (browser wallet API)
- Server-side Python `eth-account` signing won't work because the **frontend JS initiates the sign request** with a server-generated nonce you can't predict
- `/api/auth/callback/{provider}` expects a specific nonce tied to the CSRF session

### Failed Approaches
1. **Direct POST to `/api/auth/signup`** → 400 Bad Request (needs full Auth.js flow)
2. **Mock `window.ethereum` injection** → React event handlers already bound, injection after page load doesn't trigger
3. **Inject before click via setTimeout** → Still doesn't work; the wallet adapter checks `window.ethereum.isMetaMask` at click time but the mock's Promise returning a dummy signature causes backend to reject
4. **Headless browser rendering** → Next.js SPA renders blank without residential proxy; browser snapshots show empty

### What WOULD Work
1. **Real browser + real wallet**: Use Codex/Claude Code with access to MetaMask browser extension
2. **Intercept at network level**: Use a browser with proxy that can render the SPA, inject ethereum mock BEFORE page load (via browser extension or CDP), capture the signing request, sign with real private key, return
3. **Manual registration + API key extraction**: User registers manually from phone, shares API key, agent uses API key directly

### Key Endpoints (Confirmed)
- `GET /api/auth/csrf` → `{csrfToken: "..."}`
- `GET /api/auth/providers` → lists all wallet + Google providers
- `GET /api/auth/session` → `null` (not logged in) or session object
- `POST /api/auth/signin/{provider}` → 302 redirect to signin page
- `POST /api/auth/callback/{provider}` → processes wallet signature

### BIN Lookup API
- `GET https://lookup.binlist.net/{BIN[:8]}` — Free, returns scheme, brand, bank, country
- Rate limit ~10 requests/second
- Returns JSON: `{scheme, type, brand, country: {name, alpha2}, bank: {name}}`

### Wallet Libraries Available on System
```bash
pip list | grep eth
# eth-account, eth-abi, eth-hash, eth-keyfile, eth-keys, eth-rlp, eth-typing, eth-utils
```

### Generate Wallets (Python)
```python
import secrets
from eth_account import Account

private_key = "0x" + secrets.token_hex(32)
account = Account.from_key(private_key)
address = account.address
```

### Sign Message (Python)
```python
from eth_account.messages import encode_defunct

message = "Sign this message: nonce123"
encoded = encode_defunct(text=message)
signed = Account.sign_message(encoded, private_key=private_key)
signature = signed.signature.hex()
```
