#!/usr/bin/env node
/**
 * send-eth-base.js — Send ETH on Base chain
 * Usage: node scripts/send-eth-base.js <from_index> <to_index> <amount_eth>
 * Example: node scripts/send-eth-base.js 1 2 0.00001
 *
 * Wallet vault: ~/mona-workspace/vault/evm_wallets_10.json
 */
const { ethers } = require('ethers');
const fs = require('fs');
const path = require('path');

const RPC = process.env.RPC_URL || 'https://mainnet.base.org';
const CHAIN_ID = parseInt(process.env.CHAIN_ID || '8453');

const VAULT_PATH = path.join(__dirname, '../../vault/evm_wallets_10.json');

function loadWallet(index) {
  const vault = JSON.parse(fs.readFileSync(VAULT_PATH, 'utf8'));
  const w = vault.wallets.find(w => w.index === parseInt(index));
  if (!w) throw new Error(`Wallet index ${index} not found in vault`);
  return w;
}

async function main() {
  const fromIdx = process.argv[2] || '1';
  const toIdx = process.argv[3] || '2';
  const amountEth = process.argv[4] || '0.00001';

  const fromWallet = loadWallet(fromIdx);
  const toWallet = loadWallet(toIdx);

  console.log(`\n🚀 Sending ${amountEth} ETH on Base`);
  console.log(`📤 From: ${fromWallet.name} (${fromWallet.address})`);
  console.log(`📥 To:   ${toWallet.name} (${toWallet.address})\n`);

  const provider = new ethers.JsonRpcProvider(RPC, CHAIN_ID);
  const wallet = new ethers.Wallet(fromWallet.privateKey, provider);

  // Pre-flight checks
  const feeData = await provider.getFeeData();
  const maxFeePerGas = feeData.maxFeePerGas || feeData.gasPrice;
  const gasLimit = 21000;
  const value = ethers.parseEther(amountEth);
  const gasCost = gasLimit * maxFeePerGas;
  const totalNeeded = value + gasCost;

  console.log(`⛽ maxFeePerGas: ${ethers.formatUnits(maxFeePerGas, 'gwei')} gwei`);
  console.log(`💰 Gas estimate: ${ethers.formatEther(gasCost)} ETH`);
  console.log(`💰 Total needed: ${ethers.formatEther(totalNeeded)} ETH`);

  const balance = await provider.getBalance(fromWallet.address);
  console.log(`💰 Source balance: ${ethers.formatEther(balance)} ETH`);

  if (balance < totalNeeded) {
    const shortfall = totalNeeded - balance;
    console.error(`\n❌ Insufficient funds! Shortfall: ${ethers.formatEther(shortfall)} ETH`);
    console.error(`   Have: ${ethers.formatEther(balance)} ETH`);
    console.error(`   Need: ${ethers.formatEther(totalNeeded)} ETH`);
    process.exit(1);
  }

  // Build & send
  const tx = { to: toWallet.address, value, gasLimit, maxFeePerGas };
  console.log(`\n📡 Broadcasting tx...`);
  const txResponse = await wallet.sendTransaction(tx);
  console.log(`🔗 Tx hash: ${txResponse.hash}`);
  console.log(`⏳ Waiting for confirmation...`);
  const receipt = await txResponse.wait();

  console.log(`\n✅ Tx confirmed! Block: ${receipt.blockNumber}`);
  console.log(`   Gas used: ${receipt.gasUsed.toString()}`);

  const balanceAfter = await provider.getBalance(fromWallet.address);
  console.log(`\n💰 Source balance after:  ${ethers.formatEther(balanceAfter)} ETH`);
}

main().catch(e => { console.error(`❌ Error: ${e.message}`); process.exit(1); });