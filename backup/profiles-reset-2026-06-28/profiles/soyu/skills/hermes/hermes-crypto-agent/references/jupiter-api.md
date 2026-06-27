# Jupiter Aggregator API — Solana Token Swaps

> Last verified: 2026-06-09

## API Base URL
```
https://api.jup.ag/swap/v1
```

**⚠️ BREAKING CHANGE (2026):** Jupiter moved from `https://api.jup.ag` (v6) to `https://api.jup.ag/swap/v1`. The old `/quote` and `/swap` endpoints return 404. The old `/price/v2` endpoint is GONE.

## Endpoints

### GET /quote
```
/quote?inputMint={mint}&outputMint={mint}&amount={lamports}&slippageBps={bps}
```
Returns: `{ inputMint, inAmount, outputMint, outAmount, otherAmountThreshold, swapMode, priceImpactPct, ... }`

### POST /swap
```
POST /swap
Content-Type: application/json

{
  "quoteResponse": <quote object>,
  "userPublicKey": "<base58 pubkey>",
  "wrapAndUnwrapSol": true,
  "dynamicComputeUnitLimit": true,
  "prioritizationFeeLamports": 100000
}
```
Returns: `{ swapTransaction: "<base64 encoded VersionedTransaction>" }`

**⚠️ Does NOT return `txid`!** The response contains a serialized transaction that must be:
1. Deserialized (`VersionedTransaction.deserialize(Buffer.from(base64, "base64"))`)
2. Signed (`tx.sign([keypair])`)
3. Sent (`connection.sendRawTransaction(tx.serialize())`)
4. Confirmed (`connection.confirmTransaction(txHash, "confirmed")`)

### Price API — GONE
The `/price/v2` and `/price/v1` endpoints return 404. Use quote-based estimation instead:
```js
// Get price via quote: 0.001 SOL → tokens → price = 0.001 / tokens
const lamports = 1000000; // 0.001 SOL
const quote = await getQuote(SOL_MINT, tokenMint, lamports, 500);
const tokens = Number(quote.outAmount);
const pricePerTokenSOL = lamports / tokens / 1e9;
```

## Full Swap Implementation (Node.js)

```js
import { Connection, Keypair, VersionedTransaction } from "@solana/web3.js";
import bs58 from "bs58";

const JUPITER_API = "https://api.jup.ag/swap/v1";
const SOL_MINT = "So11111111111111111111111111111111111111112";

async function executeSwap(quote, keypair, connection, priorityFee = 100000) {
  // 1. Get swap transaction from Jupiter
  const resp = await fetch(`${JUPITER_API}/swap`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      quoteResponse: quote,
      userPublicKey: keypair.publicKey.toBase58(),
      wrapAndUnwrapSol: true,
      dynamicComputeUnitLimit: true,
      prioritizationFeeLamports: priorityFee,
    }),
  });
  const { swapTransaction } = await resp.json();

  // 2. Deserialize
  const tx = VersionedTransaction.deserialize(
    Buffer.from(swapTransaction, "base64")
  );

  // 3. Sign
  tx.sign([keypair]);

  // 4. Send with retries
  const rawTx = Buffer.from(tx.serialize());
  const txHash = await connection.sendRawTransaction(rawTx, {
    skipPreflight: true,
    maxRetries: 2,
  });

  // 5. Confirm
  await connection.confirmTransaction(txHash, "confirmed");
  return txHash;
}
```

## Pitfalls
- **404 on /quote**: You're using the old URL. Must be `https://api.jup.ag/swap/v1/quote`
- **`swapData.txid` is undefined**: Jupiter returns `swapTransaction`, not `txid`
- **Price API 404**: `/price/v2` is gone. Use quote-based estimation.
- **Empty curl response**: Jupiter may block curl without proper headers. Use Node.js `fetch()` instead.
- **Micro-cap tokens**: Quote may return 0 or fail for very low liquidity tokens. Always check `outAmount > 0`.
- **Slippage**: 500 bps (5%) is safe for most tokens. Use 300-500 for large caps, 500-1000 for micro-caps.
- **Priority fee**: 100K lamports is moderate. Use 50K-200K depending on congestion.
