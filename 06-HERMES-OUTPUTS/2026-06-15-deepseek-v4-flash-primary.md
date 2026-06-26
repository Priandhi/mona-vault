---
type: receipt
date: 2026-06-15
tags:
  - receipt
---

# Switch primary model → orcarouter/deepseek/deepseek-v4-flash

**Task:** Switch `model.default` di `~/.hermes/config.yaml` dari `tokenrouter/MiniMax-M3` ke `orcarouter/deepseek/deepseek-v4-flash`. User prefer OrcaRouter (2 keys) bukan Zyloo (Zyloo-01 udah 402 Insufficient credit).

**Result:**
- ✅ `orcarouter/deepseek/deepseek-v4-flash` works via 9Router (~2.2s response, supports Indonesian)
- ✅ Config updated via `hermes config set model.default "orcarouter/deepseek/deepseek-v4-flash"`
- ✅ Verified via `hermes --cli -m orcarouter/deepseek/deepseek-v4-flash` → got proper Indonesian reply
- ✅ OrcaRouter-01 + OrcaRouter-02 both healthy (backoff=0, no errors)
- ⚠️ Zyloo-01 returned 402 Insufficient credit — Zyloo-02 still active for `zyloo/*` calls

**Decisions:**
- User chose to **replace primary** (override previous Jun 15 M3 default) — reason: cost, deepseek-v4-flash $0.14/1M input + 1M context
- Kept provider=9router (no need to add custom provider)
- Kept fallback_providers=['9router'] (already a list, no change)
- Did NOT touch aux models (compression/kanban/etc. tetap sama) — user cuma minta primary

**Model notes (deepseek-v4-flash):**
- Default = **thinking mode** → `content` kosong, output di `reasoning_content`
- Workaround: pass `extra_body: {"thinking": {"type": "disabled"}}` → `content` populated correctly
- 1M context, 384K max output, 2500 concurrency
- Pricing: $0.0028/1M cache hit, $0.14/1M input cache miss, $0.28/1M output
- "deepseek-chat"/"deepseek-reasoner" deprecated 2026/07/24 → v4-flash = replacement

**Issues:**
- Hermes `extra_body` field is in aux models but NOT in main `model` config — cannot globally disable thinking for primary via config.yaml. Model will run with thinking by default. May need to add it later if `content: null` becomes a problem for specific agents.
- TokenRouter M3 still listed in aux (title_generation, profile_describer). User didn't ask to change these.

**Next Steps:**
- Monitor next few sessions — kalau `content: null` bikin issue, tambahin `extra_body: {thinking: disabled}` mechanism ke Hermes primary
- Kalau ada agent yang butuh deepseek v4-pro instead of flash, bisa switch via `-m orcarouter/deepseek/deepseek-v4-pro`
- TokenRouter (M3) di aux slots bisa di-sunset juga kalau user mau — tapi gak gue ubah karena user cuma minta primary

**Files changed:**
- `~/.hermes/config.yaml` → `model.default: tokenrouter/MiniMax-M3` → `orcarouter/deepseek/deepseek-v4-flash`

**Test command for future reference:**
```bash
curl -s -X POST http://localhost:20128/v1/chat/completions \
  -H "Authorization: Bearer $(cat ~/.9router/auth/cli-secret)" \
  -H "Content-Type: application/json" \
  -d '{"model":"orcarouter/deepseek/deepseek-v4-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":100}'
```
