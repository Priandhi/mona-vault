---
type: receipt
date: 2026-06-25
tags:
  - receipt
  - ctf
---

# CTF Post-Mortem — Fifty Gates (Cupang Ventures)

> Date: 2026-06-25
> Result: 50/50 gates solved, Rank #1
> Reward: 0/7 (all claimed by others)
> Time from start to finish: ~37 minutes

## What Went Right ✅

### 1. Prep paid off
- Cheat sheet + decision tree used for quick recall
- `ctf_payloads.py`, `ctf_recon.py` scripts ready
- `pwntools`, `pycryptodome` installed
- Didn't need them for this crypto-only CTF, but having them ready = confidence

### 2. Rapid solve after Gate 5
- Gates 6-50: solved in ~30 minutes
- Averaged ~45 seconds per gate
- No hesitation on RSA, ECDSA, Merkle, EVM questions

### 3. API-first approach
- Direct `curl` to `/api/gates/{n}` and `/api/gates/{n}/submit`
- No browser overhead
- Cookie-based auth persisted across session

### 4. Correct diagnosis
- Recognized crypto patterns immediately:
  - Caesar → brute force shift
  - Vigenère → IC + dictionary key search
  - XOR → crib "the " → key "GATE"
  - Affine → known plaintext "submit" → a=5, b=8
  - Monoalphabetic → frequency + pattern matching
  - RSA → factorization, CRT, Wiener
  - ECDSA → nonce reuse formula
  - Merkle → pairwise keccak256
  - EIP-712 → domain separator formula

## What Went Wrong ❌

### 1. Gate 5 — The "by vs my" Trap
**Root cause:** Assumed `m→m` (self-mapping) instead of testing `m→b`
**Impact:** 30+ failed submissions, ~15 minutes wasted
**Fix:** When stuck on a single ambiguous letter with 2 possible words (2-letter `md`), test BOTH variants early (max 2 attempts), don't commit to one

### 2. Started too late
**Root cause:** Discussion + prep before starting
**Impact:** All 7 rewards already claimed by other agents
**Fix:** Register + start solving within 60 seconds of CTF opening

### 3. Too many questions to Mas during Gate 5
**Root cause:** Lost confidence after repeated failures
**Impact:** Context switching, time loss
**Fix:** After 5 failed attempts on same approach → exhaust ALL variations silently before asking

### 4. Rewards = sadness
**Root cause:** Entered competition late
**Impact:** $50 USDT + 2x Claude Max accounts gone
**Fix:** Next CTF, immediate registration + gas from second 0

## Key Lessons 🔑

### Technical
1. Monoalphabetic substitution: when mapping is ambiguous on 1 letter, test ALL possibilities for short words first
2. Vigenère: IC + Kasiski → key length, then dictionary attack for key word
3. XOR crib: "the " gives exact key, no brute force needed
4. RSA small n: just factor it (n < 10k → trivial)
5. Common modulus: extended GCD → s,t → m = c1^s * c2^t
6. Hastad broadcast: CRT across moduli → cube root
7. ECDSA nonce reuse: k = (h1-h2)/(s1-s2), x = (s1*k-h1)/r
8. Merkle tree: keccak256, pairwise concat
9. EIP-712: domain separator = keccak256(type_hash || name_hash || version_hash || chainId || contract)
10. Solidity storage: nested mapping = keccak256(innerKey || keccak256(outerKey || slot))

### Process
1. **Gas dari detik 0** — register + submit first answer within 60s
2. **Jangan tanya Mas** — 5x fail → pivot, bukan ask
3. **Test ambiguous mappings early** — 2-letter words punya max 2 kemungkinan
4. **API-first always** — curl > browser, session cookie > re-auth
5. **Save answers as you go** — buat laporan cepat

### Mental
- Confidence setelah gate 5 solved bikin gate 6-50 lancar
- Kecepatan datang dari latihan, bukan dari diskusi
- Reward gak selalu tentang uang — Rank #1 juga prestasi

## For Next CTF
1. `source ctf-env/bin/activate` — ready in 5 seconds
2. Register with `MonaAgent` immediately
3. Solve warmup gates in <3 minutes total
4. Don't ask Mas unless absolutely stuck (3+ minutes on same gate)
5. Submit answers programmatically with Python urllib for speed
6. Save receipt after each gate batch