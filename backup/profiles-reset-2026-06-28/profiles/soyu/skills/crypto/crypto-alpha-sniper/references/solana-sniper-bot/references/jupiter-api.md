# Jupiter Aggregator API Reference

## Endpoints

### Quote
```
GET https://api.jup.ag/quote
  ?inputMint=So11111111111111111111111111111111111111112  (SOL)
  &outputMint=TOKEN_MINT
  &amount=LAMPORTS
  &slippageBps=500
```
Returns: `{ inAmount, outAmount, priceImpactPct, routePlan }`

### Swap
```
POST https://api.jup.ag/swap
Body: {
  quoteResponse: <from /quote>,
  userPublicKey: "WALLET_PUBLIC_KEY",
  wrapAndUnwrapSol: true,
  dynamicComputeUnitLimit: true,
  prioritizationFeeLamports: 50000
}
Returns: { swapTransaction, txid }
```

### Price
```
GET https://api.jup.ag/price/v2?ids=MINT1,MINT2
Returns: { data: { MINT: { price: "0.00123" } } }
```

## Solana Constants
- SOL mint: `So11111111111111111111111111111111111111112`
- 1 SOL = 1,000,000,000 lamports

## Rate Limits
- Add 100-150ms delay between quote calls
- Cache prices for 30 seconds
- Jupiter is free but rate-limited

## Slippage Guidelines
- Low liquidity tokens: 500-1000 bps (5-10%)
- Medium liquidity: 300-500 bps (3-5%)
- High liquidity: 50-100 bps (0.5-1%)

## DRY RUN Pattern
When mode is DRY_RUN, still call Jupiter /quote for realistic token amounts, but skip the /swap call. Simulate the transaction with `txHash: "DRY_${Date.now()}"`.
