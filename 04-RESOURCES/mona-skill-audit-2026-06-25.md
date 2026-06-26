# Mona Skill Audit — 2026-06-25

## PWN / Binary Exploitation — 85% ✅
| Teknik | Score | Detail |
|--------|-------|--------|
| checksec + offset | 90% | cyclic, core dump |
| Shellcode (NX off) | 85% | NOP sled + shellcraft.sh() |
| ret2libc (-O2, no leave) | 85% | Clean ROP: add rsp; pop rbx; ret |
| ret2libc (+leave;ret) | 85% | Self-referencing fake RBP |
| Format string leak | 60% | Works, offset varies per binary |
| PIE bypass | 50% | Concept solid, per-binary offset |

**Key pitfall:** `leave;ret` = `mov rsp, rbp; pop rbp` → saved RBP MUST be valid addr + leak stack

**Key pattern:** ret → pop_rdi → /bin/sh → system

---

## Reverse Engineering — 72% 🟡
| Skill | Score | Detail |
|-------|-------|--------|
| strings hunting | 90% | grep for flag, key, password, base64 |
| hexdump analysis | 85% | xxd + pattern match XOR'd data |
| UPX detect + unpack | 85% | upx -d, detect via "UPX!" string |
| disasm (objdump) | 75% | xor, cmp, call identification |
| r2 basic | 65% | afl, pdf, function finding |
| Ghidra headless | 50% | No GUI, limited analysis |
| Anti-debug bypass | 45% | ptrace detection, theory only |

**RE Pipeline:** file → strings → hexdump → objdump/r2 → decode → verify

---

## Crypto — 75% 🟡 (from CTF performance)
| Skill | Score | Detail |
|-------|-------|--------|
| XOR (single + repeating) | 90% | Brute force, crib drag |
| Classical (Caesar, Vigenère, Affine) | 85% | Freq analysis, IC, Kasiski |
| RSA basic | 85% | Factorization, common modulus, Hastad, Wiener |
| ECDSA nonce reuse | 85% | k=(h1-h2)/(s1-s2), x recovery |
| Hash/MAC | 80% | MD5 collision, PBKDF2, HMAC brute |
| Padding oracle | 30% | Theory only |
| Lattice/ZK | 20% | Theory only |

---

## CTF Speed / Process — from Fifty Gates
| Lesson | Impact |
|--------|--------|
| Gas dari detik 0 | Rewards stolen by early birds |
| Test ALL short-word variants early | Gate 5: 15min wasted on m→b vs m→m |
| Single process leak+exploit | ASLR: different process = different address |
| API-first (curl) | Faster than browser |
| Monoalphabet: frequency + pattern matching | More reliable than dictionary |

---

## Overall Combat Readiness
- **Web CTF:** 80-85% ✅
- **Crypto CTF:** 75% 🟡 (padding oracle gap)
- **PWN CTF:** 85% ✅
- **RE CTF:** 72% 🟡
- **Prompt Injection:** 85% ✅
- **Forensics/Stego:** 80% ✅