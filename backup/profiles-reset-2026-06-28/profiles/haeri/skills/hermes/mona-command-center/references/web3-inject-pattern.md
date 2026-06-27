# Web3 Provider Injection for Browser Automation

Inject a fake MetaMask-like `window.ethereum` provider into headless browser pages so dApps detect and connect to the wallet programmatically.

## When to Use

For dApps that use `window.ethereum` directly (Uniswap, 1inch, most DeFi protocols). NOT for Galxe/Layer3/Zealy (they use WalletConnect v2 exclusively).

## How It Works

1. Create a JavaScript class that mimics MetaMask's provider API
2. Override `window.ethereum` with the fake provider
3. Handle `eth_requestAccounts`, `personal_sign`, `eth_signTypedData_v4`, `eth_sendTransaction`
4. Sign requests are intercepted and handled server-side (private key never leaves the server)

## Critical: Inject BEFORE Page Load

```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context()
    
    # MUST use add_init_script() — injects BEFORE page scripts run
    # If you inject after page load, dApp's wagmi/ethers already cached "no provider"
    await context.add_init_script(INJECT_JS)
    
    page = await context.new_page()
    await page.goto(dapp_url, wait_until="networkidle")
```

## Provider Properties (must match MetaMask)

```javascript
{
    isMetaMask: true,
    chainId: '0x1',
    selectedAddress: '0x...',
    // Must have request(), on(), removeListener(), emit()
}
```

## Sign Flow (Server-Side Signing)

The injected provider stores sign requests in `window.__SIGN_REQUEST` and sets `window.__SIGN_DONE = false`. The Python server polls for pending requests, signs with eth_account, and injects the signature back.

```python
async def handle_sign_request(page, private_key, address):
    has_request = await page.evaluate("() => !!window.__SIGN_REQUEST")
    if not has_request:
        return False
    
    request = await page.evaluate("() => window.__SIGN_REQUEST")
    # Sign server-side
    signed = Account.sign_message(encode_defunct(text=request['msg']), private_key)
    
    # Inject signature back
    await page.evaluate(f"() => {{ window.__SIGN_RESULT = '0x{signed.signature.hex()}'; window.__SIGN_DONE = true; }}")
    return True
```

## EIP-6963 Support

Modern dApps (wagmi v2+) use EIP-6963 for wallet detection instead of `window.ethereum`. The inject script dispatches `eip6963:announceProvider` events. However, some dApps (like Galxe) use WalletConnect SDK that bypasses both mechanisms.

## Known Limitations

- Galxe/Layer3/Zealy: WalletConnect v2 only, inject doesn't work
- Some dApps check for MetaMask-specific internal methods that are hard to fake
- EIP-712 typed data signing needs domain/types/message parsing
- `eth_sendTransaction` needs full nonce/gas management server-side

## File Location

`~/.hermes/scripts/mona_web3_inject.py` — contains WEB3_INJECT_JS template and handle_sign_request/handle_tx_request functions.
