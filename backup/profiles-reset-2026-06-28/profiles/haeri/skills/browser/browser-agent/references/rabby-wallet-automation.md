# Rabby Wallet Automation — Bulk Import & Control

## Why Rabby over MetaMask

User explicitly stated: "Rabby aja metamask berat dan lemot". Rabby wins for degen multi-chain users:
- Auto multi-chain switch (no manual network add)
- Security simulation before signing
- Lightweight, faster UI
- Portfolio view across all chains

## Download & Install

```bash
# Get latest release URL
curl -sL "https://api.github.com/repos/RabbyHub/Rabby/releases/latest" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); \
  [print(a['browser_download_url']) for a in d['assets'] if 'zip' in a['name'].lower()]"

# Download and unpack
curl -L "https://github.com/RabbyHub/Rabby/releases/download/vX.X.X/Rabby_vX.X.X.zip" -o /tmp/rabby.zip
rm -rf ~/.hermes/browser-data/extensions/rabby
mkdir -p ~/.hermes/browser-data/extensions/rabby
unzip -o /tmp/rabby.zip -d ~/.hermes/browser-data/extensions/rabby/
```

Verify: `ls ~/.hermes/browser-data/extensions/rabby/manifest.json`

## Extension ID

The extension ID is determined by the unpacked path. After first Chrome launch with `--load-extension`, check:
```bash
cat ~/.hermes/browser-data/vnc-browser-rabby/Default/Preferences | python3 -c "
import sys, json
data = json.load(sys.stdin)
for ext_id, info in data.get('extensions', {}).get('settings', {}).items():
    if 'rabby' in str(info.get('path', '')).lower():
        print(f'Rabby extension ID: {ext_id}')
"
```

Or check `chrome://extensions` page via `curl -s http://localhost:9222/json`.

## Launch Chrome + Rabby on VNC

```bash
DISPLAY=:99 ~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome \
  --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --no-first-run --disable-default-apps \
  --disable-extensions-except=~/.hermes/browser-data/extensions/rabby \
  --load-extension=~/.hermes/browser-data/extensions/rabby \
  --start-maximized \
  --remote-debugging-port=9222 \
  --user-data-dir=~/.hermes/browser-data/vnc-browser-rabby \
  "chrome-extension://<EXTENSION_ID>/index.html"
```

**⚠️ CRITICAL: `DISPLAY=:99` MUST be in the command itself, not exported separately.**
Background Chrome fails with `Missing X server or $DISPLAY` if DISPLAY is exported before `terminal(background=true)`.

## Rabby Extension Routes (Hash Router)

Rabby is a React SPA with hash-based routing. Key routes:

| Route | Content |
|---|---|
| `#/welcome` | "Access All Dapps" onboarding (first page) |
| `#/password` | Set Password page |
| `#/unlock` | Unlock page (when locked) |
| `#/no-address` | "Add an Address" — options: Create New, Import Seed, Import PK, Hardware, Watch-only |
| `#/import` | Import method selection: Private Key, Seed Phrase, KeyStore |
| `#/import/input-private-key` | Private key input form (empty if accessed directly — must go through `#/import` flow) |

## Onboarding Flow (First Time)

```
#/welcome → click "Next"
→ "Self-custodial" → click "Get Started"
→ #/no-address (Add an Address)
```

After onboarding, subsequent visits go directly to `#/no-address` or `#/unlock`.

## Setting Password

Navigate to `#/password`:
```python
await page.goto("chrome-extension://<ID>/index.html#/password")
await page.wait_for_timeout(2000)

# Fill password fields
inputs = await page.query_selector_all('input[type="password"]')
await inputs[0].fill(PASSWORD)
await inputs[1].fill(PASSWORD)

# Check terms checkbox
await page.evaluate("""() => {
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        if (!cb.checked) cb.click();
    });
}""")

await page.click('button:has-text("Next")')
```

## Bulk Wallet Import via Private Key (CDP Automation)

### Architecture

Connect to running Chrome via CDP (Chrome DevTools Protocol) on port 9222.
Each wallet import opens a NEW page tab, imports, then closes the tab.

```python
import asyncio
from playwright.async_api import async_playwright

EXT_ID = "<extension_id>"
PASSWD = "***"

async def import_wallet(browser, wallet):
    page = await browser.contexts[0].new_page()
    try:
        # 1. Navigate to import page
        await page.goto(f"chrome-extension://{EXT_ID}/index.html#/import")
        await page.wait_for_timeout(2000)
        text = await page.inner_text("body")

        # 2. Handle locked state
        if "Unlock" in text:
            pw = await page.query_selector('input[type="password"]')
            if pw:
                await pw.fill(PASSWD)
                await page.click('button:has-text("Unlock")')
                await page.wait_for_timeout(1500)
            await page.goto(f"chrome-extension://{EXT_ID}/index.html#/import")
            await page.wait_for_timeout(2000)

        # 3. Select "Import via Private Key"
        #    This is a DIV field-option, NOT a radio button!
        await page.evaluate("""() => {
            const fields = document.querySelectorAll('.field');
            for (const field of fields) {
                const slot = field.querySelector('.field-slot');
                if (slot && slot.textContent.includes('Private Key')) {
                    field.click();
                    field.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                    return true;
                }
            }
            return false;
        }""")
        await page.wait_for_timeout(500)

        # 4. Click Next (check if enabled)
        next_btn = await page.query_selector('button:has-text("Next")')
        if next_btn:
            disabled = await next_btn.get_attribute("disabled")
            if disabled is not None:
                return False  # Option not selected
            await next_btn.click()
        await page.wait_for_timeout(1500)

        # 5. Fill private key
        target = await page.query_selector("textarea") or \
                 await page.query_selector('input[type="text"]')
        if not target:
            for inp in await page.query_selector_all("input"):
                t = await inp.get_attribute("type")
                if t in ("text", "password", None):
                    target = inp
                    break
        if not target:
            return False

        await target.fill(wallet["pk"])
        await page.wait_for_timeout(500)

        # 6. Confirm
        for label in ["Confirm", "Next", "Import"]:
            try:
                await page.click(f'button:has-text("{label}")', timeout=3000)
                break
            except:
                continue

        await page.wait_for_timeout(2000)
        text = await page.inner_text("body")
        return "Imported" in text or "Done" in text or "Address" in text

    finally:
        await page.close()  # Rabby closes page after confirm — close gracefully
```

### Key Pitfalls

1. **"Import via Private Key" is a DIV, not a radio button.** Must click the `.field` parent that contains `.field-slot` with text "Private Key". Direct `text=Import Private Key` clicks go to the wrong element.

2. **Rabby closes the extension page after successful import.** The `page.close()` in `finally` handles `TargetClosedError`. Open a fresh tab for each import.

3. **Next button is disabled until option selected.** Check `disabled` attribute before clicking.

4. **Unlock state persists across tabs.** Once unlocked in one tab, new tabs don't need unlock. But if idle timeout triggers, new tabs will show `#/unlock`.

5. **`#/import/input-private-key` route shows empty page.** Must navigate through `#/import` → select option → Next to reach the actual input form.

6. **Hash route changes on click.** Clicking "Import via Private Key" on the `#/no-address` page navigates back to `#/welcome` — this is a Rabby routing bug. Use `#/import` route directly instead.

## Wallet Data Format

```python
# From vault files
wallets = []

# EVM wallets (vault/.wallets_evm)
with open("~/mona-workspace/vault/.wallets_evm") as f:
    data = json.load(f)
for w in data[" wallets"]:  # NOTE: key has leading space
    wallets.append({"name": f"W{w['id']}", "pk": w["pk"], "address": w["address"]})

# Seed phrase → private key
from eth_account import Account
Account.enable_unaudited_hdwallet_features()
acct = Account.from_mnemonic("word1 word2 ... word12")
pk = acct.key.hex()

# Private key → address
acct = Account.from_key("0x...")
address = acct.address
```

## Remote Debugging

Always launch Chrome with `--remote-debugging-port=9222` for Playwright CDP control:
```python
browser = await p.chromium.connect_over_cdp("http://localhost:9222")
```

Get tab list: `curl -s http://localhost:9222/json`

## VNC Access for User

After setup, user accesses via:
1. localhost.run tunnel: `ssh -R 80:localhost:6080 nokey@localhost.run`
2. Password: VNC password set with `x11vnc -storepasswd`
3. User sees full Chrome + Rabby on their phone browser
