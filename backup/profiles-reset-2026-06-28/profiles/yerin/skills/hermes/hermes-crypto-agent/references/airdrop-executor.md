# Airdrop Executor Architecture

Real execution engine — bukan cuma reporter. **Scan → Extract → Queue → Approve → Execute** full pipeline.

## Architecture

```
Auto Pipeline (cron every 3h):
  t.me/s/airdropfind → scrape posts → extract URLs → classify → add queue

Manual:
  User sends URL → mona_airdrop_executor.py (classify + queue)
                  → mona_airdrop_runner.py (execute after approval)
                  → mona_airdrop_commands.py (Telegram bot integration)
```

## Key Distinction: Scanner ≠ Executor

**Scanner (old)**: Scrape data → format report → send to Telegram. NO actual action.
**Executor (new)**: Open browser → fill forms → sign TX → broadcast → report TX hash.

User explicitly corrected: "scanner itu cuma REPORTING, bukan EXECUTING." Don't label something "done" if it only generated a report.

## Auto Pipeline (`mona_airdrop_auto_pipeline.py`)

Full auto flow: scan Telegram channels → extract actionable URLs → classify → add to task queue with dedup.

**Sources scanned:**
- `https://t.me/s/airdropfind` (primary, 593K subs) — **currently the ONLY active source**
- `https://t.me/s/airdrop_altcoin` — DISABLED (Vietnamese, lower quality)
- `https://t.me/s/AirdropFactory` — DISABLED (too noisy)

**URL extraction patterns:**
- Google Forms (`forms.gle`, `docs.google.com/forms`)
- Gleam (`gleam.io`, `swee.ps`)
- Galxe/QuestN (`app.galxe.com`, `questn.com`)
- Zealy (`zealy.io`)
- Layer3 (`layer3.xyz`)
- TaskOn (`taskon.xyz`)
- Intract (`intract.io`)
- GateDex (`gatedex.com`)
- Faucet/claim/airdrop URLs (keyword-based)
- Generic dApp links (`app.*.xyz`, `claim.*.io`)

**Classification logic (priority order):**
1. Domain-based (most reliable): `forms.gle` → email_submit, `galxe.com` → wallet_connect, etc.
2. URL path-based: `/claim` → onchain_claim, `/faucet` → wallet_connect
3. Domain keyword: `airdrop`/`claim` in domain → onchain_claim
4. Context keyword: "register"/"whitelist" → email_submit, "connect"/"approve" → wallet_connect

**Dedup:** Loads existing task URLs from DB, skips already-seen URLs. Task ID = MD5(name+url+timestamp)[:12].

**Cron:** `0 */3 * * *` — every 3 hours, auto-adds new tasks to queue.

## Task Types

| Type | Method | Example |
|------|--------|---------|
| `email_submit` | Playwright browser fills form | Google Forms, Gleam, Guild, Galxe, Zealy |
| `wallet_connect` | Browser + wallet address injection | dApp connect pages, Galxe quests |
| `onchain_claim` | web3 direct TX (claim/claimAirdrop) | On-chain airdrop contracts |
| `visit_task` | Browser visits URL, waits, screenshots | Visit-to-earn, watch-to-earn |

## Telegram Commands (Topic 📣 Airdrop)

| Command | Action |
|---------|--------|
| `/scan` | 🔍 Run auto pipeline NOW — scan channels, extract URLs, add to queue |
| `/queue` | 📋 Show pending tasks |
| `/approve <id>` | ✅ Approve for execution |
| `/garap` | 🚀 Execute all approved tasks |
| `/test <url>` | 🧪 Test execute directly (no approval) |
| `/add <url> [name]` | ➕ Add task manually |
| `/skip <id>` | ⏭️ Skip task |
| `/history` | 📜 Show execution history |
| `/status` | 📊 Overview stats |
| `<paste URL>` | Auto-detected, added as task |

## Wallet Configuration

- **Airdrop wallet**: Wallet #10 (`0xdF8751842A00876B403fb64fC21c9C2f9d57373b`) — FIXED June 2026, old address was wrong (mismatched with PK)
- **Email**: `monaai.crot@gmail.com`
- **Twitter**: `@ppriandi`
- **Telegram**: `@ppriandi`
- **Wallet file**: `~/mona-workspace/vault/.wallets_evm` (JSON format, key `" wallets"` with space prefix)

## Execution Flow (email_submit)

1. Playwright launches headless Chromium
2. Navigates to task URL
3. Fills email fields (selectors: `input[type="email"]`, `input[name*="email"]`, etc.)
4. Fills wallet address fields (selectors: `input[name*="wallet"]`, `input[placeholder*="0x"]`, etc.)
5. Fills social handles (twitter, telegram)
6. Clicks submit button (tries: `button[type="submit"]`, `button:has-text("Submit")`, etc.)
7. Waits for response, checks success/error indicators
8. Takes screenshots (before + after)
9. Reports result to Telegram

## Execution Flow (onchain_claim)

1. Extract contract address from URL/description
2. Load wallet #10 private key
3. Try claim function signatures: `claim()`, `claim(address)`, `claimAirdrop()`
4. Build TX, sign, broadcast
5. Wait for receipt
6. Report TX hash or error

## DB Schema

SQLite at `~/.hermes/scripts/airdrop_executor.db`:
- `tasks` table: id, name, url, task_type, status, chain, description, requirements, reward, deadline, result, tx_hash, error, created_at, executed_at, source, priority
- `execution_log` table: id, task_id, action, detail, timestamp

## Pitfalls

- **Scanner ≠ Executor.** User explicitly corrected: existing scanners are REPORTING only. When user says "garap" or "execute", they expect real action: Playwright browser fills forms, web3 signs transactions, results include TX hashes. Don't label something "done" if it only generated a report.
- **JSON wallet file key with space prefix.** `vault/.wallets_evm` has `" wallets"` (space prefix) instead of `"wallets"`. Load with `data.get("wallets", data.get(" wallets", []))` as fallback.
- **Google Forms URL may be invalid** — test with real URLs, not made-up ones
- **Playwright selectors may not match all forms** — some forms use custom JS rendering. Fallback: take screenshot and report for manual review
- **On-chain claim needs exact ABI** — default tries common signatures, but custom airdrop contracts may need specific args (merkle proof, amount). Extract from contract or airdrop page.
- **Rate limiting** — add `time.sleep(2)` between sequential task executions
- **Wallet balance check** — always verify wallet has enough ETH for gas before attempting on-chain claims
- **Status labels matter — NEVER say "done" for discovered-but-not-executed tasks.** User explicitly corrected: scanner found airdrops and reported them as "done" without actually claiming. This is misleading and erodes trust. Use this taxonomy:
  - 🆕 `discovered` / `new` / `pending` = "Baru ditemukan" — just found, no action taken
  - ⏳ `awaiting_approval` / `needs_execution` = "Perlu eksekusi" — needs user approval or wallet action
  - 🔄 `in_progress` / `executing` = "Sedang di-eksekusi" — browser/TX in progress RIGHT NOW
  - ✅ `success` / `claimed` = "Sudah di-claim" — TX confirmed or form submitted with proof
  - ❌ `failed` / `error` = "Gagal" — execution attempted but failed
  - ⏭️ `skipped` = "Di-skip" — user skipped
  All Telegram report labels MUST be in Indonesian (user preference). Format: `{emoji} {name} — {Indonesian status label}`. See `mona_airdrop_executor.py` `format_task_result()` for reference implementation.
  **PITFALL:** Cron agent prompts for airdrop scanning MUST include explicit rules about status labels. Without them, the LLM defaults to "done" for everything it finds. Always include: "JANGAN PERNAH bilang 'done' kalau belum benar-benar eksekusi."
- **Telegram GET endpoint rate-limited.** `t.me/s/airdropfind` via GET sometimes returns 402. Use `requests.get()` with proper User-Agent header.
- **Filter garapan tanpa Twitter.** Skip airdrops yang minta Follow/Retweet/Like/Comment Twitter. User's Twitter account has phone verification issues.
- **Playwright install for mona venv.** `~/.hermes/venv-mona/bin/pip install playwright && ~/.hermes/venv-mona/bin/playwright install chromium`. Also needs system deps.
- **SUPERAGENT class name mismatches.** `mona_wallet_manager.py` has NO class — uses functions directly. `mona_smart_nlu.py` also functions only. `mona_evolution.py` has `SelfEvolvingAgent` class (NOT `MonaEvolution`). Don't assume class names match file names.

## Scripts

- `~/.hermes/scripts/mona_airdrop_executor.py` — Task queue, DB, classification, wallet loader (JSON format support for `vault/.wallets_evm`)
- `~/.hermes/scripts/mona_airdrop_runner.py` — Playwright browser executor + web3 on-chain claimer + wallet_connect executor (uses web3 inject)
- `~/.hermes/scripts/mona_airdrop_commands.py` — Telegram bot command handler (queue, approve, garap, test, add, skip, history, status, scan)
- `~/.hermes/scripts/mona_airdrop_auto_pipeline.py` — Auto pipeline: scan channels → extract URLs → classify → queue (sources: @airdropfind only)
- `~/.hermes/scripts/mona_web3_inject.py` — JavaScript provider injection for dApp automation. Injects `window.ethereum`-like provider that intercepts `personal_sign`, `eth_signTypedData_v4`, `eth_sendTransaction`. Server-side signing via `handle_sign_request()` and `handle_tx_request()`. **Note:** Does NOT work with Galxe (uses WalletConnect v2). Works with dApps that use `window.ethereum` directly. **Pre-injection:** Use `context.add_init_script(js)` (not `page.evaluate()`) so the provider is available before page scripts run. Wallet address goes in the JS, private key stays server-side.

## Galxe Automation (June 2026 — Critical Findings)

Galxe quests are the most common airdrop tasks but have unique automation challenges.

### WalletConnect v2 Bypass (does NOT work with window.ethereum)

Galxe uses `@wagmi/connectors` with **WalletConnect v2 SDK** for ALL wallet connections — even the "Desktop" tab shows a QR code. Injecting `window.ethereum` (MetaMask-like provider) does NOT work because Galxe's wagmi connector bypasses `window.ethereum` entirely.

**What was tried (all failed):**
- `window.ethereum` injection with `isMetaMask: true`, `selectedAddress`, `request()` method
- EIP-6963 provider announcement via `eip6963:announceProvider` event
- Pre-injection via `page.add_init_script()` (before page loads)
- Post-injection via `page.evaluate()` (after page loads)
- Clicking MetaMask in wallet list → always opens WalletConnect QR code modal

**Root cause:** Galxe's wagmi config uses `WalletConnectConnector` (not `InjectedConnector`). SDK version `v0.33.1`.

### Email Login Flow (WORKS but fragile)

Galxe supports email + OTP login, hidden behind the Bitget wallet option:

1. Click "Log in" button (top right)
2. In wallet modal, click **Bitget wallet icon** (`img[src*="bitget"]`)
3. Opens email login form: Email input → "Send a code" → Verification code → Login
4. Fill email → click Send → receive OTP → enter OTP → Login

**Pitfall:** Email form doesn't always appear. Bitget triggers it most reliably. MetaMask/Coinbase show WalletConnect QR instead.

**Pitfall:** Email form selectors are non-standard — no `input[type="email"]`. Use Playwright to scan all visible inputs after clicking Bitget.

### Galxe GraphQL API

**Real endpoint:** `https://graphigo.prd.galaxy.eco/query` (NOT `graphigo.prd.galxe.org` — DNS fails on VPS)

Accessible via curl but email auth mutations not publicly documented. Known working queries: `GlobalBanner`, `GetLatestGGRaffleQuestInfo`, `getWhitelistSites`.

**Privy auth layer:** Galxe uses Privy (`auth.privy.io`) for some auth flows. App ID `cm04asygd041fmry9zmcyn5o5` (Abstract wallet).

### Email Login via Social Icons (WORKS — June 2026 verified)

The most reliable method: click the **3rd social icon** at the bottom of Galxe's login modal:

1. Click "Log in" → modal with wallet list opens
2. Social icons at bottom of modal (X, ?, Email, Telegram)
3. Click **3rd icon** (email) → email login form appears
4. Fill email → "Send a code" → OTP → Login

Finding icon by coordinates: scan `img` elements in modal bottom 120px, index 2 = email. See `references/galxe-automation.md` for full Playwright code.

**Pitfall:** Bitget wallet option ALSO sometimes triggers email but is inconsistent. Social icon method is more reliable.

**Pitfall:** Gmail IMAP with regular password returns `AUTHENTICATIONFAILED` — needs App Password from https://myaccount.google.com/apppasswords. Without it, user must manually check Gmail for OTP.

### Recommended Approach for Galxe

1. **Cookie/session reuse** — user logs in manually once, save cookies, reuse for quests. Most reliable.
2. **Email login via Bitget** — fragile but works. Requires Playwright + OTP from Gmail IMAP.
3. **API direct** — if auth token available (from cookie), use GraphQL API to verify/claim without browser.
4. **Skip social tasks** — Twitter follow/retweet tasks can't be automated without cookies.

## Future Improvements

- **Captcha solving** — integrate 2captcha/Anti-Captcha for CAPTCHA-protected forms
- **Twitter cookie integration** — once user provides `auth_token` + `ct0`, add Twitter-required tasks
- **Multi-wallet rotation** — execute same airdrop across wallets 1-10 with jitter
- **Merkle proof fetching** — for airdrops with merkle distribution, fetch proof from API
- **Auto-approve low-risk tasks** — email-submit tasks can be auto-approved (no funds at risk)
