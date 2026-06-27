# Broken Position Fix — entryPrice=0 Phantom Lock

## Problem
When Jupiter quote fails AND `getTokenPrice()` returns null, the fallback in `jupiter-executor.js` calculates `price=0` and `tokenAmount=50,000,000,000`. This creates a phantom position that blocks all new buys with "Max positions reached (3/3)".

## Root Cause
```javascript
// OLD (broken) fallback:
const price = await getTokenPrice(mint);
const tokens = price ? solAmount / (price * 1e-9) : Math.round(solAmount * 1e12);
// When price=null → tokens = 0.05 * 1e12 = 50,000,000,000, price=0
```

## Fix

### 1. Update `buyToken` signature to accept signal data:
```javascript
export async function buyToken(mint, solAmount, config, sig = {}) {
```

### 2. Update call site in `index.js`:
```javascript
const buyResult = await buyToken(pick.mint, config.trade.deployAmountSol, config, pick);
```

### 3. Fix fallback chain in `jupiter-executor.js`:
```javascript
// Fallback 1: Jupiter price API
const priceUsd = await getTokenPrice(mint);
if (priceUsd && priceUsd > 0) {
  const tokens = Math.round(solAmount / priceUsd);
  return { success: true, txHash: `DRY_${Date.now()}`, amountIn: solAmount, amountOut: tokens, price: priceUsd, simulated: true };
}
// Fallback 2: Charon signal data
const tokenPrice = (sig?.priceUsd || 0);
const tokens2 = tokenPrice > 0 ? Math.round(solAmount / tokenPrice) : Math.round(solAmount * 1e9);
return { success: true, txHash: `DRY_${Date.now()}`, amountIn: solAmount, amountOut: tokens2, price: tokenPrice || (solAmount / tokens2), simulated: true };
```

### 4. Clean broken positions manually:
```bash
cd ~/mona-workspace/charon-sniper
python3 -c "
import json
with open('data/positions.json') as f:
    d = json.load(f)
d['open'] = [p for p in d['open'] if p['entryPrice'] > 0]
with open('data/positions.json', 'w') as f:
    json.dump(d, f, indent=2)
"
```

### 5. Restart bot:
```bash
pm2 restart charon-sniper
```

## Prevention
Always pass the original signal object to `buyToken()` so the fallback chain has real price data from Charon.
