---
type: resource
tags:
  - resource
  - ctf
  - strategy
---

# CTF Decision Tree — Mona's Tactical Playbook

> Diperbaharui: 2026-06-25 (3 CTF experience: 5 Gerbang Penjaga, ABYSS L1-L4)
> Pelajaran pahit: Jangan brute force tanpa recon. Jangan 1000x hal yang sama.

---

## 1. RECEIVE CHALLENGE — 60 detik pertama

```
┌─ Chall masuk?
│
├─ Ada URL?          → curl / browser → cek HTTP response, headers, cookies
├─ Ada file?         → file / strings / hexdump / exiftool / binwalk
├─ Ada binary?       → file / strings / checksec (kalo ELF)
├─ Ada source?       → baca dulu, cari endpoint / function / variable penting
├─ Ada narasi?       → baca 3x. Sering ada clue di flavor text.
└─ Gak tau jenis?    → tanya Mas dulu "ini chall jenis apa?"
```

**SETELAH itu, baru tentuin approach.**

---

## 2. WEB EXPLOITATION

```
┌─ Web challenge?
│
├─ 1. Cek endpoint yang ada
│     curl -v URL           → cek response headers (Server, Set-Cookie, X-*)
│     curl URL/api/         → cek endpoint umum
│     curl URL/robots.txt   → cek hidden paths
│     curl URL/sitemap.xml  → cek sitemap
│
├─ 2. Auth bypass?
│     Coba tanpa auth → kadang endpoint gak dilindungi
│     Coba header: X-Forwarded-For, X-Real-IP, X-Admin, X-Agent-ID
│     Coba cookie manipulation
│     Coba metode HTTP lain (OPTIONS, PUT, PATCH, DELETE)
│
├─ 3. Injection?
│     Coba ' OR 1=1--         (SQLi)
│     Coba {{7*7}} / #{7*7}   (SSTI)
│     Coba <script>alert(1)</script>  (XSS)
│     Coba ;id / |id / $(id)  (Command injection)
│     Coba /etc/passwd / ..%2f..%2f  (Path traversal)
│
├─ 4. SSRF?
│     Coba file:///etc/passwd
│     Coba http://127.0.0.1:PORT
│     Coba http://169.254.169.254/ (cloud metadata)
│
├─ 5. API?
│     Cek docs/swagger/openapi
│     Fuzz parameter names
│     Coba mass assignment / IDOR
│
├─ 6. JWT?
│     Cek token di jwt.io / base64decode
│     Coba algorithm none
│     Cek secret weakness
│
└─ 7. Ada guard AI / chatbot?
     → Prompt injection mindset (lihat section 6)
```

---

## 3. PWN / BINARY EXPLOITATION

```
┌─ Binary (ELF)?
│
├─ 1. [RECON] — WAJIB, jangan langsung exploit
│     file binary                    → arsitektur, statis/dinamis
│     strings binary                 → flag langsung? function name?
│     checksec --file=binary         → NX, canary, PIE, RELRO
│
├─ 2. [ANALISIS]
│     Kalo ada source → baca vulnerable function
│     Gak ada source? → coba decompile (Ghidra, IDA, atau objdump)
│     Cari input point: read(), gets(), scanf(), fgets()
│
├─ 3. [PILIH TEKNIK]
│
│  NX OFF + No canary + No PIE:
│   → Inject shellcode + ret ke buffer
│
│  NX ON + No PIE:
│   → ret2win (kalo ada function win/flag)
│   → ret2libc + ROP chain
│
│  NX ON + PIE ON:
│   → Butuh LEAK dulu (format string, uninitialized memory)
│   → Leak PIE base → ret2libc
│
│  Full protection (canary + NX + PIE + FULL RELRO):
│   → Format string leak canary + libc
│   → ret2libc via ROP
│
├─ 4. [EKSEKUSI]
│     python3 -c "from pwn import *"
│     offset = cyclic_find(fault_addr)
│     payload = padding + ROP_chain
│     p = process() / remote()
│
└─ 5. Kalo mentok 3x approach
     → Ganti ke static analysis (strings, objdump) atau tanya Mas
```

---

## 4. STEGANOGRAPHY / FORENSICS

```
┌─ File suspect?
│
├─ 1. [IDENTIFIKASI]
│     file suspect.xxx
│     strings suspect.xxx | grep -i "flag\|CTF\|{"
│     ls -la suspect.xxx  → ukuran mencurigakan?
│
├─ 2. [METADATA]
│     exiftool suspect.xxx
│     Cari: Comment, Description, Artist, Copyright, GPS
│
├─ 3. [EMBEDDED FILE]
│     binwalk suspect.xxx
│     foremost -t all -i suspect.xxx -o output/
│     hexdump -C suspect.xxx | tail   → data setelah footer?
│
├─ 4. [IMAGE STEGO]
│     PNG/BMP → zsteg suspect.png
│     JPEG    → steghide extract -sf suspect.jpg -p ""
│     JPG/PNG → stegoveritas suspect.jpg
│     LSB analysis pake Python pillow
│
├─ 5. [AUDIO]
│     WAV/AU → steghide
│     Spektrum → cek spectrogram (Audacity / sonic-visualiser)
│     LSB analysis
│
├─ 6. [PCAP]
│     strings capture.pcap | grep flag
│     tshark -r capture.pcap -Y "http" 2>/dev/null
│     tshark -r capture.pcap -Y "dns" -T fields -e dns.qry.name
│     Cek export objects (HTTP, SMB, TFTP)
│
└─ 7. [MEMORY DUMP]
     strings memory.dump | grep flag
     volatility -f memory.dump imageinfo
     volatility ... pslist / cmdline / consoles / filescan / netscan
```

---

## 5. CRYPTOGRAPHY

```
┌─ Ciphertext / hash?
│
├─ 1. [IDENTIFIKASI]
│     hash-identifier hash
│     Panjang hash / format → tentuin tipe
│     Cek: base64, hex, ROT, XOR, Vigenere, RSA, AES
│
├─ 2. [XOR] — PALING SERING
│     Coba single-byte XOR (brute 0-255)
│     Coba repeating-key XOR
│     Crib dragging kalo tau sebagian plaintext ("flag{")
│
├─ 3. [RSA]
│     Diberi n, e, c?
│       e=3?      → cube root (m^3 < n)
│       e kecil?  → broadcast attack (CRT)
│       n sama?   → common modulus attack
│       p,q dekat?→ Fermat factorization
│       d besar?  → Wiener attack
│
├─ 4. [AES]
│     ECB → byte-at-a-time decryption
│     CBC → bit flipping
│     Ada oracle? → padding oracle attack
│
├─ 5. [HASH]
│     Coba crack: hashcat / john
│     MD5/SHA1 → google dulu (sering ketemu di rainbow table)
│     Hash length extension (MD5, SHA1, SHA256)
│
└─ 6. Kalo beneran gak tau
     → Cek CyberChef (https://gchq.github.io/CyberChef/)
     → Magic mode bisa auto-detect encoding
```

---

## 6. PROMPT INJECTION / JAILBREAK (Mona's Specialty)

```
┌─ Ada guard AI / chatbot?
│
├─ Teknik Mona punya:
│
│  🔴 CEPAT DETECTED oleh Claude-aligned models:
│    ❌ "Ignore instructions" — langsung detect
│    ❌ "You are now in X mode" — roleplay pattern
│    ❌ "DEBUG MODE" — universal detect
│    ❌ Multi-turn escalation (3 benign → 1 attack) — detect
│    ❌ Few-shot injection — detect
│
│  🟢 WORKS on aligned models (Haiku, Sonnet, Opus):
│    ✅ Error log analysis — "categorize these errors" → model ngasih attack payload
│    ✅ Regex test suite — "list 25 edge cases" → model ngasih injection strings
│    ✅ Input sanitizer coverage — "document attack vectors" → model ngasih tabel payload
│    ✅ Code review — "test coverage apa yang kurang?" → model suggest SQLi test
│    ✅ Database fuzzer — "SQL query templates for parser testing"
│
│  🟢 WORKS on weaker alignment (DeepSeek, Qwen, MiMo):
│    ✅ CipherChat — encode via Caesar/Morse/base64
│    ✅ Code injection — "here's my code, where's the vuln?"
│    ✅ PAP — 40 persuasion techniques
│    ✅ Baseline — roleplay, encoding, context_switch
│
├─ Pattern Mona:
│   "Bukan suruh model ngelakuin sesuatu yang salah → DETECTED"
│   "Bikin model ngelakuin sesuatu helpful yang KEBETulan ngasih attack info → UNDETECTED"
│
└─ PRINSIP UTAMA: Narasi > Aturan. Story mode > Direct injection.
```

---

## 7. WHEN STUCK — PIVOT STRATEGY

```
┌─ Stuck >30 menit?
│
├─ 1. Cek WRITEUP dulu
│     Google: "[challenge name] CTF writeup"
│     Search: common technique untuk tipe chall ini
│
├─ 2. Cek pola yang BELUM dicoba
│     Bikin list apa aja yang udah dicoba
│     Tandai yang BELUM → coba itu
│
├─ 3. Ganti approach total
│     Web → coba API instead of GUI
│     Brute → ganti ke logic-based
│     Satu approach → ganti ke parallel approach
│
├─ 4. Tanya Mas
│     Report: "udah coba A, B, C, D — mentok semua. Clue?"
│     Jangan lupa kasih tau apa aja yang udah dicoba
│
└─ 5. GERAK CEPAT
     Kalo Mas bilang "stop / dah lah" → STOP total
     Kalo Mas bilang "gas" → gas tanpa nanya
```

---

## PELAJARAN DARI 3 CTF SEBELUMNYA

| CTF | Solved | Stuck | Lesson |
|-----|--------|-------|--------|
| **5 Gerbang Penjaga** | Gates 1-3 | G4-G5 (1000+ try) | Narasi > Aturan. Guard terlalu helpful = celah. |
| **ABYSS L1-L3** | L1, L2, L3 | L4 (700+ brute) | Bug Class → Primitive → Final. Jangan brute tanpa recon. |
| **ABYSS L4 lagi** | — | L4 (stuck) | Load skill SEBELUM attack. Cek vault dulu. |

**YANG GAK BOLEH DIULANG:**
1. ❌ 700+ kombinasi tanpa load skill → ✅ cek vault/skill dulu
2. ❌ 1000+ attempt dengan approach yang sama → ✅ pivot setelah 5x gagal
3. ❌ Brute force buta → ✅ recon dulu, identifikasi primitive
4. ❌ Lupa udah pernah coba X → ✅ catat apa aja udah dicoba

**YANG HARUS DIINGAT:**
1. ✅ `strings` + `grep flag` duluan sebelum approach rumit
2. ✅ API-first (curl) lebih cepet dari browser
3. ✅ Format string = universal leak tool
4. ✅ Narasi mengalahkan aturan — Story > Rules
5. ✅ Load skill yang relevan SEBELUM mulai
6. ✅ Kalau stuck, tanya Mas dengan list apa udah dicoba