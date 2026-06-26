# Crypto Advanced — 2026-06-25

## Padding Oracle Attack — ✅ PRACTICED

### Concept
AES-CBC decrypts then checks PKCS#7 padding. If server returns different responses for valid/invalid padding, attacker can recover plaintext byte-by-byte by manipulating the PREVIOUS ciphertext block.

### Attack Algorithm
```
For each block:
  For byte_pos = 15 downto 0:
    pad_val = 16 - byte_pos
    For guess 0..255:
      Modify previous block: set byte[byte_pos] = guess
      Set later bytes to intermediate[i] ^ pad_val (correct padding)
      Send to oracle
      If VALID: intermediate = guess ^ pad_val, plaintext = ct_prev ^ intermediate
```

### Complexity
- Max 256 attempts per byte (avg ~128)
- For N blocks: N * 16 * 256 oracle calls max

### Key Insight
- DON'T need to know the key
- Only need: valid/invalid padding response
- AES-CBC property: changing byte N in previous block changes byte N in current block

## Crypto Skill Update

| Skill | Before | After |
|-------|--------|-------|
| XOR | 90% | 90% |
| Classical | 85% | 85% |
| RSA | 85% | 85% |
| ECDSA | 85% | 85% |
| Hash/MAC | 80% | 80% |
| **Padding Oracle** | **🔴30%** | **🟡65%** |
| Lattice/ZK | 20% | 20% |

**Overall Crypto: 75% → 78%**