# Solana Wallet Import + Key Derivation

## Quick facts
- Solana uses **base58** encoding for keys (not hex like EVM)
- Private key format: 64 bytes = 32-byte secret key + 32-byte public key (concatenated)
- Public key = last 32 bytes of the 64-byte decoded private key

## Import workflow

### 1. Get Helius RPC
Sign up at [helius.xyz](https://helius.xyz) → dashboard → RPC endpoints.
Format: `https://mainnet.helius-rpc.com/?api-key=<KEY>`

**HELIUS_API_KEY**: The standalone API key is the value after `?api-key=` in the RPC URL.
```
RPC URL:  https://mainnet.helius-rpc.com/?api-key=2f166885-a270-415e-93f8-a8000f7363ff
API Key:  2f166885-a270-415e-93f8-a8000f7363ff
```
Use this standalone key for: `HELIUS_API_KEY` env var in Meridian, enhanced APIs, webhooks.

### 2. Derive public key from base58 private key

**Node.js approach (fastest, no install needed):**
```bash
cd /tmp && npm install bs58 --save-quiet
node -e "
const bs58 = require('/tmp/node_modules/bs58').default;
const pk = '<BASE58_PRIVATE_KEY>';
const decoded = bs58.decode(pk);
if (decoded.length === 64) {
  console.log('Public key:', bs58.encode(decoded.slice(32)));
} else {
  console.log('Length:', decoded.length);
}
"
```

**Python approach (system pip often broken — PEP 668 lock):**
```python
import subprocess, base58, sys

# Install to temp dir to avoid PEP 668
subprocess.run([sys.executable, '-m', 'pip', 'install', 'base58-py',
                '--target', '/tmp/pylib', '-q'], check=True)
sys.path.insert(0, '/tmp/pylib')

pk = '<BASE58_PRIVATE_KEY>'
decoded = base58.b58decode(pk)
pubkey = decoded[32:] if len(decoded) == 64 else decoded
print(base58.b58encode(pubkey).decode())
```

### 3. Save to vault
```bash
cat > ~/mona-workspace/vault/.solana_wallet << 'EOF'
{
  "chain": "Solana",
  "rpc": "https://mainnet.helius-rpc.com/?api-key=<KEY>",
  "wallet": {
    "address": "<PUBLIC_KEY>",
    "private_key": "<BASE58_PRIVATE_KEY>"
  }
}
EOF
chmod 600 ~/mona-workspace/vault/.solana_wallet
```

### 4. Verify balance
```bash
curl -s -X POST "<RPC_URL>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"getBalance","params":["<PUBLIC_KEY>"]}' \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print(int(r['result']['value'])/1e9, 'SOL')"
```

## Vault location
All chain wallet secrets: `~/mona-workspace/vault/` (chmod 700 on dir, chmod 600 on files)