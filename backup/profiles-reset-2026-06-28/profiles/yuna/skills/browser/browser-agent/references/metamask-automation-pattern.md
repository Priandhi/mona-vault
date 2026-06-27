# MetaMask Automation Module Pattern

## Overview

Wrapping MetaMask operations in a clean async context manager class. This pattern is used when building dApp automation scripts that need wallet connectivity.

## Architecture

```
MetaMaskBrowser (async context manager)
├── launch_context_async() — CloakBrowser + MetaMask extension
├── import_wallet(seed_phrase) — MetaMask onboarding flow
├── get_address() — read current wallet address
├── switch_network(network) — ETH/BSC/Polygon/etc
├── connect_to_dapp(url) — navigate + approve connection
├── approve_transaction() — confirm pending tx in MetaMask popup
└── close() — cleanup
```

## Key Patterns

### Extension Loading for MetaMask

```python
# MetaMask v13+ uses manifest V3 — unpack CRX3 format
METAMASK_ID = "nkbihfbeogaeaoehlefnkodbefgpgknn"

# Download from Web Store
crx_path = await download_webstore_crx(METAMASK_ID, extension_dir)
# Unpack (CRX3 auto-detected)
unpacked = unpack_crx(crx_path, unpacked_dir)

# Load as extension
args = [
    f"--disable-extensions-except={unpacked}",
    f"--load-extension={unpacked}",
]
ctx = await launch_context_async(headless=False, args=args)
```

### MetaMask Onboarding Selectors (v13.x)

```python
# These selectors are version-specific — always screenshot first!
SELECTORS = {
    "get_started": "[data-testid='onboarding-get-started']",
    "import_wallet": "[data-testid='import-wallet-button']",
    "no_metrics": "[data-testid='metametrics-no-thanks']",
    "srp_word": "[data-testid='import-srp__srp-word-{idx}']",  # 0-indexed
    "new_password": "[data-testid='create-password-new']",
    "confirm_password": "[data-testid='create-password-confirm']",
    "import_button": "[data-testid='create-password-import']",
    "got_it": "[data-testid='onboarding-complete-done']",
    "next": "[data-testid='pin-extension-next']",
    "done": "[data-testid='pin-extension-done']",
}
```

### dApp Connection Flow

```python
async def connect_to_dapp(page, dapp_url):
    await page.goto(dapp_url)
    # Find and click "Connect Wallet"
    connect_btn = page.locator("text=Connect Wallet").first
    await connect_btn.click()
    # Wait for MetaMask popup
    await page.wait_for_event("popup")
    # Approve in MetaMask
    approve_btn = page.locator("[data-testid='page-container-footer-next']")
    await approve_btn.click()
```

### Network Switching

```python
NETWORKS = {
    "ethereum": {"chainId": "0x1", "name": "Ethereum Mainnet"},
    "bsc": {"chainId": "0x38", "name": "BNB Smart Chain"},
    "polygon": {"chainId": "0x89", "name": "Polygon"},
    "arbitrum": {"chainId": "0xa4b1", "name": "Arbitrum One"},
    "base": {"chainId": "0x2105", "name": "Base"},
}

async def switch_network(page, network):
    # Via MetaMask popup or window.ethereum.request
    await page.evaluate(f"""
        window.ethereum.request({{
            method: 'wallet_switchEthereumChain',
            params: [{{ chainId: '{NETWORKS[network]["chainId"]}' }}]
        }})
    """)
```

## Pitfalls

1. **MetaMask v13 SPA conflict with CloakBrowser** — `cloaking=True` causes MetaMask popup to hang. Fix: use `cloaking=False` for MetaMask automation, or use `--disable-features=RendererCodeIntegrity` flag.
2. **MetaMask popup is a separate window** — must use `page.on("popup")` or `context.pages[-1]` to access it, not `page.locator()`.
3. **Seed phrase entry uses individual input fields** — each word is a separate `<input>`, use `srp_word_{idx}` selectors.
4. **MetaMask locks after inactivity** — persistent profiles help, but re-auth may be needed.
5. **Extension ID changes on reinstall** — if you hardcode extension ID, it breaks. Use `b.find_extension("metamask")` instead.
