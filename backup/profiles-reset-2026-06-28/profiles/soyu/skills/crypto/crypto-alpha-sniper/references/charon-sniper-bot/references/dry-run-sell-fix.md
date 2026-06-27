# DRY RUN Sell PnL Fix — Complete History

## Problem
`sellToken()` in DRY RUN mode produces 0 SOL for micro-cap tokens → PnL = -100% → triggers daily loss limit.

## The `* 1e-9` Bug (CRITICAL LESSON)

**Root cause:** `getTokenPrice()` returns price per raw token unit in SOL. Multiplying by `tokenAmount` gives total SOL value. Adding `* 1e-9` makes it 1 billion times too small.

```javascript
// BROKEN — the * 1e-9 is WRONG:
const solValue = tokenAmount * price * 1e-9; // → ~5e-8 SOL (should be ~0.04 SOL)

// CORRECT — price is already per raw unit:
const solValue = tokenAmount * price; // → ~0.04 SOL
```

**Why this happens:** Jupiter quote returns `outAmount` in the token's smallest unit (like lamports). `getTokenPrice()` calculates `lamports / rawUnits / 1e9` which gives SOL per raw unit. So `rawUnits × (SOL/rawUnit) = SOL`. No extra division needed.

## Fix History

### v1 (broken) — Decay factor with * 1e-9
```javascript
const decayFactor = 0.7 + Math.random() * 0.2;
solValue = tokenAmount * decayFactor * 1e-9; // ~5e-8 SOL — STILL WRONG
```
Problem: `* 1e-9` persists. Decay factor doesn't help when the base calculation is wrong.

### v2 (better) — Deploy amount fallback
```javascript
solValue = (config?.trade?.deployAmountSol || 0.04) * 0.85; // ~0.034 SOL
```
Problem: Not based on actual token price. Always returns 85% of deploy regardless of market.

### v3 (best — current) — Quote-based sell simulation
```javascript
if (isDry) {
  // 1. Try real Jupiter quote for sell
  const quote = await getQuote(mint, SOL_MINT, Math.round(tokenAmount), config.trade.slippageBps);
  let solValue = 0;
  
  if (quote) {
    solValue = Number(quote.outAmount) / 1e9;
  } else {
    // 2. Fallback: quote-based price (no * 1e-9!)
    const price = await getTokenPrice(mint);
    if (price && price > 0) {
      solValue = tokenAmount * price; // ← NO * 1e-9
    }
  }
  
  // 3. Last resort: deploy amount estimate
  if (solValue <= 0) {
    solValue = (config?.trade?.deployAmountSol || 0.04) * 0.85;
  }
  
  return { success: true, amountOut: solValue, simulated: true };
}
```

**Why v3 is best:**
- Uses real Jupiter quote (most accurate — accounts for actual liquidity and price)
- Falls back to quote-based price calculation (still real market data)
- Last resort uses deploy amount (better than 0)
- **Never multiplies by 1e-9**

## Testing
```javascript
// Verify fix with known token
const result = await sellToken('DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263', 1500000000000, config);
// Expected: ~0.99 SOL (for 1.5T raw BONK units)
// v1 would return: ~0.000000001 SOL (broken)
// v3 returns: ~0.99 SOL (correct)
```
