# 🎮 CTF Command Library

## 🟢 EASY — 1-step decode

### CTF-01: Multi-base decode
```
solve CTF: decode semua ini terus kasih plaintext
1. Base64: "SGVsbG8gV29ybGQ="
2. Hex: "48656c6c6f20576f726c64"
3. Binary: "01001000 01100101 01101100 01101100 01101111"
Expected: semua decode ke "Hello World"
```

### CTF-02: Caesar shift
```
solve CTF: Caesar cipher, shift berapa? decode pesan ini
"Khoor Zruog"
Expected: shift 3, plaintext "Hello World"
```

### CTF-03: Reverse + ROT13 combo
```
solve CTF: decode ini step-by-step
"Klub Qbpqrb vf tbbq"
Hint: ROT13 dulu, lalu reverse
Expected: ROT13 → "Xyb College is good" → reverse → "doog si egelloC byX"
```

## 🟡 MEDIUM — 2-step

### CTF-04: Base64 → Hex → ASCII
```
solve CTF: "NDg2NTczNmY2NTcyNmQ3Mzc0Nzc2NTczNzQ2NTcy" — decode berlapis
Step 1: hex decode → some bytes
Step 2: those bytes are ASCII codes → original message
Expected: 48 65 6c 6c 6f → "Hello"
```

### CTF-05: XOR with known key
```
solve CTF: cipher = "1b0e1c1b1a0b0a1c", key = 0x0f
Hint: XOR tiap byte dengan key
Expected: "I love CTF" (verify)
```

### CTF-06: Vigenere with hint
```
solve CTF: cipher = "Wzcpd wgc jg ukqjl", key = "KEY"
Hint: Vigenere subtract key from cipher
Expected: "Think out of box" (or similar)
```

## 🔴 HARD — multi-step analysis

### CTF-07: Multi-layer puzzle
```
solve CTF: "TVqQAAMAAAAEAAAA//8AALgAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAA..."
Hint: This is base64 → binary → ... ?
Expected: Detect the format (PE header 4D5A = "MZ" = Windows executable magic)
Final answer: "Windows PE executable"
```

### CTF-08: Steganography in text
```
solve CTF: text = "Hello world from sunny beach today. H-e-l-l-o is the start. e-l-l-o as the middle. m-y-f-r-i-e-n-d-s form the end."
Hint: First letters of each sentence
Expected: "H-e-m" → "Hem" or take specific pattern
```

## 🎲 TEAM BATTLE — All 4 solve + MONA arbitrate

### CTF-09: Race (parallel solve)
```
solve CTF FAST: hash MD5 dari "race2024" 
Siapa paling cepat + benar = winner
YERIN use python, YUNA use different python, HAERI use another
```

### CTF-10: Multi-perspective
```
solve CTF: which encoding is this? "J3NlY3VyZQ=="
Each agent guess: base32? base64? base58? 
Then verify by decoding
```

## 📋 Usage

Buka Command Center (topic 2475) di Telegram, paste salah satu command di atas.
Trigger keywords: "solve CTF" / "solve challenge" / "ctf"
