# Transfer Guide — ETH & ERC-20 on EVM Chains

## Pre-flight checklist (MANDATORY before any send)

1. **Load wallet from vault**: `~/mona-workspace/vault/evm_wallets_10.json` — index 1=mona, 2=mona2, dst.
2. **Check source balance**: `provider.getBalance(sourceAddress)` — check if > amount + gas.
3. **Fetch fee data**: `provider.getFeeData()` — use `maxFeePerGas` for EIP-1559 chains (Base, OP, Arbitrum, zkSync).
4. **Calculate total needed**: `total = sendAmount + (gasLimit * maxFeePerGas)`. For plain ETH transfer: `gasLimit = 21000`.
5. **Abort if insufficient**: If `balance < total`, tell sayang the shortfall amount + what's needed. Do NOT broadcast.

## Ethers.js setup

```bash
cd /home/ubuntu/mona-workspace
npm install ethers  # one-time install
```

## ETH transfer script template

```javascript
const { ethers } = require('ethers');

const RPC = 'https://mainnet.base.org'; // or chain-specific RPC
const CHAIN_ID = 8453;                  // Base mainnet

const provider = new ethers.JsonRpcProvider(RPC, CHAIN_ID);
const wallet = new ethers.Wallet(privateKey, provider);

async function sendEth({ to, amountEth, gasLimit = 21000 }) {
  const feeData = await provider.getFeeData();
  const maxFeePerGas = feeData.maxFeePerGas || feeData.gasPrice;

  const value = ethers.parseEther(amountEth);
  const gasCost = gasLimit * maxFeePerGas;
  const total = value + gasCost;

  const balance = await provider.getBalance(wallet.address);
  if (balance < total) {
    throw new Error(`Insufficient funds: have ${ethers.formatEther(balance)} ETH, need ${ethers.formatEther(total)} ETH (${amountEth} + gas)`);
  }

  const tx = { to, value, gasLimit, maxFeePerGas };
  const receipt = await (await wallet.sendTransaction(tx)).wait();
  return receipt;
}
```

## Base RPCs

| Network | RPC URL | Chain ID |
|---------|---------|----------|
| Base mainnet | `https://mainnet.base.org` | 8453 |
| Base mainnet (public) | `https://base.publicnode.com` | 8453 |
| Base Sepolia testnet | `https://sepolia.base.org` | 11155111 |

## Gas price check (quick one-liner)

```bash
node -e "const {ethers} = require('ethers'); new ethers.JsonRpcProvider('https://mainnet.base.org', 8453).getFeeData().then(d => console.log('gasPrice:', ethers.formatUnits(d.gasPrice, 'gwei'), 'gwei | maxFee:', ethers.formatUnits(d.maxFeePerGas, 'gwei'), 'gwei'))"
```

## Vault wallet reference

| Index | Name | Address |
|-------|------|---------|
| 1 | mona | 0x601763344b8fab56045d6e9ba14d8084c6f97abb |
| 2 | mona2 | 0x4b94248fab61fbbbecf357b12bcdb4ae58fe5396 |
| 3 | mona3 | 0xd51eb20b2ddb4a6baf95277a555e110fcfc8e301 |
| ... | ... | ... |

Full list: `~/mona-workspace/vault/evm_wallets_10.json`