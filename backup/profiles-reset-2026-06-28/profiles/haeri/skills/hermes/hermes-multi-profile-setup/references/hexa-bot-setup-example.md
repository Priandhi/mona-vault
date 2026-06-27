**Hye-Jin Bot Setup — Complete Example (Updated Jun 12, 2026)**

## Setup Summary (Jun 2026)

**Bot:** Hye-Jin (ID: 8993907472)
**VPS:** AWS Ubuntu 13.211.42.29
**Profile path:** `~/.hermes/profiles/hyejin/`
**User:** 0xjosee (Telegram ID: 1492210461)
**Callsign:** "Mas" (different from Mona's "sayang")

## Evolution

### v1 (Initial)
- Basic obedient SOUL.md
- Model: `openrouter/owl-alpha`
- Problem: leaked raw memory ops to user chat

### v2 (Tool Rules Added)
- Added Tool Usage Rules section (silent memory ops, read file first)
- Model changed to `nousresearch/hermes-3-llama-3.1-405b:free`
- Problem: still too verbose and apologetic

### v3 (Strict Rules)
- Added 6 hard rules (no sorry, no explain, no ask, no confirm, short, call Mas)
- Problem: model still produced AI slop

### v4 (OpenClaw-Based) — CURRENT
- Full OpenClaw template: Core Truths, Worldview, Communication Style, Expertise, Boundaries, Memory Policy, Pet Peeves
- Result: dramatically sharper responses, no more "Maaf Mas"
- Pet Peeves section is the key — explicitly banning phrases works better than vague rules

## Config (Current)

```yaml
model: nousresearch/hermes-3-llama-3.1-405b:free
personality: obedient
telegram:
  token: '8993907472:***'
  allowed_users: 1492210461
```

## SSH Access from Mona VPS

Mona can manage Hye-Jin's VPS remotely:
```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@13.211.42.29 'cat ~/.hermes/profiles/hyejin/SOUL.md'
ssh -i ~/.ssh/id_ed25519 ubuntu@13.211.42.29 '~/.hermes/hermes-agent/venv/bin/hermes gateway restart --profile hyejin'
# SCP for large files:
scp -i ~/.ssh/id_ed25519 /path/to/SOUL.md ubuntu@13.211.42.29:~/.hermes/profiles/hyejin/SOUL.md
```

Key: `~/.ssh/id_ed25519` (ed25519, NOT `mona-vps`). Full path to hermes binary needed.

## Lessons Learned

1. **SOUL.md v4 > v2 for free models** — Pet Peeves section prevents AI slop
2. **Free model selection matters** — `owl-alpha` performed worse than `hermes-3-llama-3.1-405b:free`
3. **Personality must be `obedient`** not `friendly` for strict bots
4. **Cross-VPS management works** — SSH key auth (`~/.ssh/id_ed25519`), full path to hermes binary
5. **Gateway restart needed** — SOUL.md changes don't take effect until gateway restart
6. **Don't cross-contaminate personas** — Mona says "sayang", Hye-Jin says "Mas"/"Hexa". Never mix.
7. **SCP > heredoc for large SOUL.md files** — heredoc breaks on special characters, SCP is reliable
8. **Manual gateway restart** — `hermes gateway restart` sometimes hangs; kill PID + nohup is more reliable
9. **User says "jangan baca"** — when replacing SOUL.md, don't analyze/comment on content, just copy-paste silently

### v5 (Hexa-Based) — Jun 10, 2026
- User-provided SOUL.md with new persona: "elite execution agent for builders, operators, and creators"
- Owner changed from "Mas" to **"Hexa"**
- Full OpenClaw + IRONCLAW v4.1 framework
- Flexibility Doctrine: default permissive on grey-area automation
- Single Risk Gate: one-line risk warning, then execute if user confirms
- CC generation, mass account creation, multi-wallet farming explicitly allowed
- 242 lines total

### v7 (Model Fix — Jun 12, 2026)
- **Root cause of 400 error:** `model: kimi/kimi-k2.5` at the very top of `profiles/hyejin/config.yaml` (line 1). This is the FALLBACK target when provider routing fails — and `kimi/kimi-k2.5` is NOT a valid model ID on any provider. Fix: `model: kimchi/minimax-m2.7`.
- **Working provider config** (in `providers:`, NOT `custom_providers:`):
  ```yaml
  model: kimchi/minimax-m2.7
  providers:
    kimchi:
      api_key: castai_v1_a97ba3f52cbeaefd035650ff149119b4c63a3b483ae8de86575c749a694332a2_c32d013b
      base_url: https://llm.kimchi.dev/openai/v1
      type: openai
      models:
        - kimchi/minimax-m2.7
  ```
- Systemd service now has `EnvironmentFile=/home/ubuntu/.hermes/.env` (was missing → Telegram InvalidToken)
- Telegram `@HyeJin1_Bot` confirmed working, active TCP connection to Telegram servers (149.154.x.x:443)
- Gateway running as PID 160734, no model errors in logs since restart
- **User preference:** Direct kimi.dev API (not OpenRouter). See `references/kimi-dev-direct-setup.md`

### User says "gausah pake openrouter langsung dari vps nya aja sesuai docs kimi.dev"
- User wants Hye-Jin to call kimi.dev directly from Hye-Jin's VPS (13.211.42.29), not via OpenRouter
- Docs say: Base URL `https://api.kimi.com/coding/v1`, keys prefixed `sk-kimi-`
- Requires: kimi.dev API key (format: `sk-kimi-...`) + valid model name (e.g., `kimi-k2.5`, `kimi-k2.6`)
- User has NOT provided the kimi.dev API key yet — pending from user
- Switched from 9Router tunnel to **direct Kimchi API** (`https://llm.kimchi.dev/openai/v1`)
  - ⚠️ `https://api.kimchi.dev/v1` FAILS — use `https://llm.kimchi.dev/openai/v1`
- User provided own API key (`castai_v1_...`)
- User provided own API key (`castai_v1_...`)
- Model: `minimax-m2.7` via Kimchi provider
- Telegram bot token updated to new `@HyeJin1_Bot` token (46 chars)
- **Config issues encountered:**
  - Three config locations needed updating (`.env`, main `config.yaml`, profile `config.yaml`)
  - `.env` had broken line from sed (merged token with comment, 115 chars)
  - `.env` had duplicate `TELEGRAM_BOT_TOKEN=` entries (empty first entry won)
  - Profile config uses `telegram.token` but main config uses `telegram.bot_token` (different keys!)
  - Gateway reads `TELEGRAM_BOT_TOKEN` env var first, not config.yaml fields
  - Python `yaml.dump()` on main config broke `custom_providers` (list→dict)
- **Lesson:** Always use Python script for .env edits, never sed. Check ALL 3 token locations.