# Session Learnings — Browser Agent

## Galxe Login Modal — Ref ID Instability (June 2026)

**Problem:** When using Hermes browser tools (`browser_click`, `browser_type`, etc.), element ref IDs (`@e1`, `@e2`, etc.) are reassigned every time a modal opens. The email textbox might be `@e6` one time and `@e12` the next.

**Solution:** ALWAYS use `browser_vision(annotate=True)` after a modal opens to get the current ref IDs. The annotated screenshot shows numbered labels `[N]` that map to ref `@eN` for the current page state.

**Workflow:**
```
1. browser_click(ref of trigger button)
2. browser_vision(annotate=True, question="What are the interactive elements?")
3. Read the annotation numbers from the screenshot
4. Use the correct ref ID from the annotation
```

**Pitfall: "Select Network" modal trap.** On Galxe (and similar multi-modal sites), clicking near the "Network" button area can accidentally open a different modal ("Select Network" instead of "Login"). If the wrong modal opens, press Escape and try again with a more precise click.

## MetaMask v13 Popup Issues (June 2026)

**Fixed:** MetaMask v13 changed SPA rendering — CloakBrowser's stealth patches (canvas/WebGL fingerprinting) conflict with MetaMask's runtime checks, leaving blank DOM.

**Fix:** `BrowserConfig(cloaking=False)` for MetaMask automation. Plain Chromium renders MetaMask perfectly.

**If site blocks headless:** Add stealth separately with `StealthConfig(geoip=True, humanize=True, fingerprint_seed=42069)` but test MetaMask flow independently.

## Onboarding Selector Changes (June 2026)

MetaMask v13 changed onboarding selectors. Updated selectors in `mm_import.py`.

## CloakBrowser `wait` Bug (June 2026)

`await page.wait()` in CloakBrowser sometimes hangs indefinitely. Use `await asyncio.sleep(N)` or `await page.wait_for_selector()` instead.

## Burner Wallet Generation (June 2026)

Generated burner wallet from seed phrase using `eth_account`:
```python
from eth_account import Account
from eth_account.hdaccount import seed_from_mnemonic
seed = seed_from_mnemonic("word1 word2 ... word12", "")
acct = Account.from_key(seed[:32])  # First 32 bytes = first private key
```

## Galxe Anti-Bot Detection (June 2026)

Galxe detects headless Chromium and triggers automatic page refresh, killing any in-progress login flow. **Tested 5+ attempts in one session, ALL failed.**

**Symptoms:**
1. Login modal opens → email entered → "Send a code" clicked
2. OTP sent to user's email
3. Before user provides OTP, page refreshes automatically
4. `browser_snapshot()` returns `(empty page)` — all state lost

**stealth_warning from Browserbase:** `"Running WITHOUT residential proxies. Bot detection may be more aggressive."`

**What doesn't help:**
- `StealthConfig(humanize=True)` — still detected
- `fingerprint_seed` — Galxe checks more than fingerprint
- Reloading and retrying — same result

**Root cause:** Galxe uses Privy auth which does fingerprint-based Origin validation (TLS fingerprint, browser API checks), not just header checks. Even curl with correct Origin header gets 403.

**Workaround options:**
1. **Residential proxy** (Browserbase paid plan) — might bypass detection
2. **CAPTCHA solving service** (YesCaptcha/CapSolver) — solve GeeTest v4, inject token via API
3. **Cookie export from real browser** — user logs in manually, exports cookies
4. **Direct API auth** — bypass browser entirely (needs CAPTCHA solver + API key)

See `hermes-crypto-agent` skill → `references/galxe-automation.md` for full analysis.

## Rabby Wallet > MetaMask for Multi-Chain Users (June 2026)

User explicitly rejected MetaMask: "Rabby aja metamask berat dan lemot". Rabby wins for degen multi-chain users:

| Feature | MetaMask | Rabby |
|---|---|---|
| Multi-chain auto-switch | ❌ Manual | ✅ Automatic |
| Security simulation | ❌ | ✅ Simulates before sign |
| Token approval view | Basic | ✅ Clear breakdown |
| Performance | Heavy, slow | Lightweight |
| Portfolio view | ❌ | ✅ Multi-chain |

**Download Rabby from GitHub:**
```bash
curl -sL "https://api.github.com/repos/RabbyHub/Rabby/releases/latest" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); [print(a['browser_download_url']) for a in d['assets'] if 'zip' in a['name'].lower()]"
curl -L "<URL>" -o /tmp/rabby.zip
mkdir -p ~/.hermes/browser-data/extensions/rabby
unzip -o /tmp/rabby.zip -d ~/.hermes/browser-data/extensions/rabby/
```

**Launch Chrome + Rabby on VNC:**
```bash
DISPLAY=:99 ~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome \
  --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --disable-extensions-except=~/.hermes/browser-data/extensions/rabby \
  --load-extension=~/.hermes/browser-data/extensions/rabby \
  --start-maximized \
  --user-data-dir=~/.hermes/browser-data/vnc-browser-rabby \
  "https://debank.com"
```

Rabby opens as a tab automatically — shows "Welcome to Rabby Wallet" with "I already have an address" option for import.

## VNC Remote Desktop + Tunneling (June 2026)

Full VNC setup for remote browser access from phone/PC. See `references/vnc-remote-desktop.md` for complete architecture.

**Quick:** Xvfb `:99` → x11vnc:5900 → noVNC:6080 → nginx:80 → tunnel (localhost.run)

**localhost.run > cloudflared** — cloudflared quick tunnel fails with `ERR Error unmarshaling QuickTunnel response: error code: 1101` (server 500). localhost.run works:
```bash
ssh -o StrictHostKeyChecking=no -R 80:localhost:6080 nokey@localhost.run
```
Generates URL like `https://abc123.lhr.life`. URL changes on reconnect.

**Fluxbox required for xdotool** — bare Xvfb has no window manager, `xdotool search` returns empty. Fix: `DISPLAY=:99 fluxbox &`

**Tencent Cloud blocks ALL ports** except SSH (22) at security group level. `ufw` inactive, `iptables` clean — the block is at cloud provider level. Must use tunnel or open ports in Tencent Cloud Console.

**PITFALL:** Background process `DISPLAY=:99 chrome ...` may fail with `Missing X server or $DISPLAY` if DISPLAY isn't in the command itself. Always include `DISPLAY=:99` at the start of the command, not as a separate env export.

## Rabby Bulk Wallet Import via CDP (June 2026)

**Pattern:** Connect to running Chrome via CDP (`--remote-debugging-port=9222`), open new tab per wallet, navigate to `#/import`, select "Import via Private Key" option, fill PK, confirm, close tab.

**Key discoveries:**
- "Import via Private Key" on `#/import` page is a **DIV field-option**, NOT a radio button. Must click the `.field` parent containing `.field-slot` with text "Private Key".
- Rabby **closes the extension page after successful import**. Each wallet import MUST open a fresh tab.
- Direct `text=Import Private Key` Playwright click resolves to wrong element. Use JS `evaluate()` to click `.field` parent.
- `#/import/input-private-key` route shows empty page — must go through `#/import` → select option → Next.
- The "Add an Address" page (`#/no-address`) "Import Private Key" option redirects to `#/welcome` — routing bug. Use `#/import` route directly.

**Result:** Successfully imported 12 wallets in one automated run.

**Full reference:** See `references/rabby-wallet-automation.md`

## Background Chrome DISPLAY Requirement (June 2026)

**Pitfall:** `terminal(background=True)` with `DISPLAY=:99 chrome ...` may fail with `Missing X server or $DISPLAY` because background processes don't inherit shell environment exports.

**Fix:** Always include `DISPLAY=:99` at the START of the command itself:
```bash
DISPLAY=:99 /path/to/chrome --no-sandbox ...
```
NOT: `export DISPLAY=:99 && chrome ...` (doesn't work in background mode)

## localhost.run > cloudflared for Quick Tunnels (June 2026)

**Confirmed again:** cloudflared quick tunnels (account-less) fail with `error code: 1101` / `500 Internal Server Error`. localhost.run SSH tunnel is the most reliable quick option:
```bash
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:localhost:6080 nokey@localhost.run
```

## Environment State Snapshot (June 2026)

- VPS: 43.163.85.51
- Xvfb on :99
- CloakBrowser installed (python3.12)
- MetaMask v13 (cloaking=False required)
- Rabby Wallet v0.93.92 installed (user preference over MetaMask)
- Playwright chromium in `~/.cache/ms-playwright/chromium-1223/`
- x11vnc + noVNC running (ports 5900, 6080)
- nginx reverse proxy on port 80
- fluxbox window manager + scrot installed
- localhost.run tunnel tested working
