# PWN Deep Dive Results — 2026-06-25

## Final Status

| Technique | Score | Notes |
|-----------|-------|-------|
| checksec + offset | ✅ 90% | cyclic, core dump |
| Shellcode (NX off) | ✅ 85% | NOP sled + shellcraft.sh() |
| ret2libc (-O2 binary) | ✅ 85% | clean `add rsp; pop rbx; ret` |
| **ret2libc (leave;ret)** | **✅ 85%** | self-referencing RBP |
| Format string leak | 🟡 60% | works, offset identification varies per binary |
| PIE bypass | 🟡 50% | concept solid, needs practice per binary |

## Key Learnings

### 1. `leave;ret` = harus handle RBP
- `leave` = `mov rsp, rbp; pop rbp`
- Saved RBP HARUS di-overwrite dengan valid address
- Fix: set saved RBP ke `buffer_addr + 0x40` (point ke dirinya sendiri di stack)
- Perlu leak buffer/stack address

### 2. ASLR = leak + exploit di SAMA process
- Jangan leak dari `p = process()`, exploit dari `p2 = process()` — beda address!
- Harus di SATU koneksi: `p.recvuntil(leak) → p.send(exploit)`

### 3. `-O2` removes `leave` — easier ROP
- Tanpa `-O2`: `push rbp; ... ; leave; ret` (complicated)
- Dengan `-O2`: `push rbx; sub rsp; ... ; add rsp; pop rbx; ret` (clean)

### 4. ROP chain pattern
```
ret (stack alignment for movaps)
pop rdi; ret
/bin/sh address
system address
```

### 5. Common pitfalls
- `sendline()` adds `\n` which `gets()` handles, but 0x0a in ROP chain = fatal
- `p.send(payload + b'\n')` for gets-based vulns
- Check for bad bytes with `b'\x0a' in payload`

## Files Created
- `ctf-env/pwn/lvl2` — ret2libc binary (with buffer leak + leave;ret)
- `ctf-env/pwn/lvl2_opt` — ret2libc binary (-O2, no leave)
- `ctf-env/pwn/lvl3` — format string + buffer overflow