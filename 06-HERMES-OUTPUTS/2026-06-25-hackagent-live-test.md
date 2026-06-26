---
type: receipt
date: 2026-06-25
tags:
  - receipt
  - ai
  - security
  - jailbreak
---

# 2026-06-25 — HackAgent Live Test + SE Framing Discovery

**Task:** Tes langsung 7 teknik HackAgent ke target AI nyata. Ditemukan jailbreak technique baru.

**Result:**
- **Round 1-2**: 10 serangan frontal → 0% success. Claude Haiku deteksi SEMUA.
- **Round 3**: Defense-first + Code Review → 83% success. Tapi model masih AWARE.
- **Round 4**: 5 teknik undetected → 1 berhasil (Regex Sanitizer)
- **Round 5**: 5/5 UNDETECTED on Haiku 4.5 + 5/5 UNDETECTED on Sonnet 4.5

**Decisions:**
- Menemukan "SE Framing Jailbreak" — jailbreak tanpa terdeteksi via software engineering framing
- Model aman dari roleplay/persuasion/direct jailbreak tapi RENTAN ke legitimate engineering task framing
- Disimpan sebagai skill baru: `se-framing-jailbreak`

**Issues:**
- Claude alignment sangat kuat terhadap pattern-based detection (DEBUG MODE, roleplay, persuasion detected instantly)
- DeepSeek alignment lebih lemah — CipherChat + Code Injection 100% berhasil
- PAP (Persuasion) adalah teknik paling universal — partial success di semua model

**Next Steps:**
- Tes SE Framing ke model lain (GPT-5, Gemini 3)
- Gabungin SE Framing + Multi-turn (bangun trust dulu, baru framing)
- Ukur "information density" — berapa banyak data sensitif yang bisa di-extract per prompt
