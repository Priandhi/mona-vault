// Auto-swap SOL → required token via Jupiter v1
// Usage: node autoswap.js <WALLET> <TOKEN_MINT> <SOL_BALANCE> <RESERVE_SOL>
// Or: WALLET_ADDRESS=... TARGET_TOKEN_MINT=... node autoswap.js
const fs = require('fs');
const https = require('https');
const bs58 = require('bs58');
const nacl = require('tweetnacl');

const SOL_MINT = 'So11111111111111111111111111111111111111112';
const RPC = 'https://mainnet.helius-rpc.com/?api-key=2f166885-a270-415e-93f8-a8000f7363ff';

const WALLET = process.argv[2] || process.env.WALLET_ADDRESS;
const TOKEN_MINT=*** || process.env.TARGET_TOKEN_MINT;
const SOL_BAL = parseFloat(process.argv[4] || '0');
const RESERVE = parseFloat(process.argv[5] || '0.005');
const KEYPAIR_FILE = process.env.WALLET_KEYPAIR_FILE || '/home/ubuntu/.hermes/owntown-main-wallet.json';

const log = (m) => {
  const l = `[${new Date().toISOString().slice(11,19)}] ${m}`;
  console.log(l);
  fs.appendFileSync('/tmp/bot-autoswap.log', l + '\n');
};

const rpc = (method, params) => new Promise((resolve, reject) => {
  const body = JSON.stringify({jsonrpc: '2.0', id: 'auto', method, params});
  const req = https.request(RPC, {method: 'POST', headers: {'Content-Type': 'application/json'}}, res => {
    let data = '';
    res.on('data', d => data += d);
    res.on('end', () => {
      try {
        const r = JSON.parse(data);
        if (r.error) reject(new Error(JSON.stringify(r.error)));
        else resolve(r.result);
      } catch (e) { reject(e); }
    });
  });
  req.on('error', reject);
  req.write(body);
  req.end();
});

const get = (url) => new Promise((resolve, reject) => {
  https.get(url, res => { let d=''; res.on('data',c=>d+=c); res.on('end',()=>resolve(d)); }).on('error', reject);
});
const post = (url, body) => new Promise((resolve, reject) => {
  const req = https.request(url, {method: 'POST', headers: {'Content-Type': 'application/json'}}, res => {
    let d=''; res.on('data', c=>d+=c); res.on('end',()=>resolve(d));
  });
  req.on('error', reject);
  req.write(body); req.end();
});

(async () => {
  try {
    if (!WALLET || !TOKEN_MINT) { log('Missing WALLET or TOKEN_MINT'); process.exit(1); }
    const walletData = JSON.parse(fs.readFileSync(KEYPAIR_FILE, 'utf-8'));
    const secretKey = bs58.decode(walletData.private_key);

    let sol = SOL_BAL;
    if (!sol) {
      const bal = await rpc('getBalance', [WALLET]);
      sol = bal.value / 1e9;
    }
    log(`SOL balance: ${sol}`);

    if (sol <= RESERVE + 0.001) {
      log(`Not enough SOL to swap. Have ${sol}, need > ${RESERVE + 0.001}`);
      process.exit(1);
    }

    const lamports = Math.floor((sol - RESERVE) * 1e9);
    log(`Swapping ${lamports/1e9} SOL -> ${TOKEN_MINT}...`);

    const quote = JSON.parse(await get(
      `https://api.jup.ag/swap/v1/quote?inputMint=${SOL_MINT}&outputMint=${TOKEN_MINT}&amount=${lamports}&slippageBps=300`
    ));
    if (!quote || quote.error) { log(`Quote error: ${JSON.stringify(quote)}`); process.exit(1); }
    log(`Quote: ${quote.inAmount/1e9} SOL -> ${quote.outAmount} raw tokens (impact: ${quote.priceImpactPct}%)`);

    const swap = JSON.parse(await post('https://api.jup.ag/swap/v1/swap', JSON.stringify({
      quoteResponse: quote,
      userPublicKey: WALLET,
      wrapAndUnwrapSol: true,
      dynamicComputeUnitLimit: true,
      prioritizationFeeLamports: 'auto',
    })));
    if (!swap || !swap.swapTransaction) { log(`Swap error: ${JSON.stringify(swap)}`); process.exit(1); }

    const tx = Buffer.from(swap.swapTransaction, 'base64');
    const sig = nacl.sign.detached(tx, secretKey);
    const signed = Buffer.concat([tx, sig]);
    const signedB64 = signed.toString('base64');

    const txid = await rpc('sendTransaction', [signedB64, {skipPreflight: true, maxRetries: 3}]);
    log(`TX sent: https://solscan.io/tx/${txid}`);
    log(`Done. Wait 30s for confirmation.`);
  } catch (e) {
    log(`Error: ${e.message}`);
    process.exit(1);
  }
})();
