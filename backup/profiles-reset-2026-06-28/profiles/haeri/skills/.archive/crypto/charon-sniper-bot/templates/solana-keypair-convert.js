// Solana keypair JSON format converter
// Solana CLI keypair = [byte, byte, ...]  (array of 64 numbers)
// Most 3rd-party bots = {private_key: "base58..."}  (object with base58 field)
const fs = require('fs');
const bs58 = require('bs58');

const SRC = process.argv[2] || process.env.SRC_KEYPAIR;
const DST = process.argv[3] || process.env.DST_KEYPAIR;

if (!SRC || !DST) {
  console.error('Usage: node solana-keypair-convert.js <src.json> <dst.json>');
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(SRC, 'utf-8'));

let bytes;
if (Array.isArray(data)) {
  bytes = new Uint8Array(data);
  console.log(`Source: Solana CLI array (${data.length} bytes)`);
} else if (data.private_key) {
  console.log(`Source already has private_key (base58). No conversion needed.`);
  fs.writeFileSync(DST, JSON.stringify(data, null, 2));
  console.log(`Copied to ${DST}`);
  process.exit(0);
} else {
  console.error('Unknown keypair format. Expected array of 64 bytes or {private_key: "..."}');
  process.exit(1);
}

if (bytes.length !== 64) {
  console.error(`Expected 64 bytes, got ${bytes.length}. Solana keypair should be 64 bytes (32 seed + 32 pubkey)`);
  process.exit(1);
}

const privkeyB58 = bs58.encode(bytes);
const out = { private_key: privkeyB58 };
fs.writeFileSync(DST, JSON.stringify(out, null, 2));
fs.chmodSync(DST, 0o600);

console.log(`Converted: ${SRC} (array) -> ${DST} (object with base58 private_key)`);
console.log(`private_key: ${privkeyB58.slice(0, 20)}...`);

try {
  const nacl = require('tweetnacl');
  const seed = bytes.slice(0, 32);
  const sk = nacl.signing.SigningKey(seed);
  const pk = bs58.encode(sk.verify_key.encode());
  console.log(`Public key: ${pk}`);
} catch (e) {
  console.log(`(install tweetnacl to auto-verify pubkey)`);
}
