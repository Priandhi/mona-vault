---
type: receipt
date: 2026-06-14
tags:
  - receipt
---

# Receipt: 2026-06-14-5-agent-system.md

## Task
Full 5-agent setup: 4 new Hermes profiles (YUNA/SOYU/YERIN/HAERI) with SOUL.md, own bot tokens, PM2 lifecycle, kanban protocol, MONA coordinator.

## Result
✅ 4 new agents created at `/home/ubuntu/.hermes/profiles/<name>/`
✅ All 4 SOUL.md files written with KANBAN PROTOCOL
✅ MONA SOUL.md updated with team dispatch
✅ All 4 agents started via PM2 ecosystem
⚠️  Bot tokens injected as PLACEHOLDER (system redaction prevented live write)

## Profile Locations

| Agent | Path | Bot | PM2 Process | Status |
|-------|------|-----|-------------|--------|
| MONA  | `/home/ubuntu/.hermes/` | @HyeJin1_Bot | (default, PID 171759) | ✅ running |
| YUNA  | `/home/ubuntu/.hermes/profiles/yuna/` | @YunaStrategistBot | yuna-gateway (id 4) | ⚠️ placeholder token |
| SOYU  | `/home/ubuntu/.hermes/profiles/soyu/` | @SoyuSnipetBot | soyu-gateway (id 5) | ⚠️ placeholder token |
| YERIN | `/home/ubuntu/.hermes/profiles/yerin/` | @YerinGrinderBot | yerin-gateway (id 6) | ⚠️ placeholder token |
| HAERI | `/home/ubuntu/.hermes/profiles/haeri/` | @HaeriCollectorBot | haeri-gateway (id 7) | ⚠️ placeholder token |

**Note:** SOYU's actual Telegram username is `@SoyuSnipetBot` (not `@SoyuPhantomBot` as the SOUL.md label said). The token is valid for `SoyuSnipetBot`. The SOUL.md label was left as written by the user.

## Decisions

1. **Cloned from default profile** — used `hermes profile create --clone` to get correct skeleton (config.yaml, .env, symlinks, etc). Then overwrote SOUL.md.
2. **Same model for all 4 agents** — `tokenrouter/MiniMax-M3` (same as MONA). Simplest, no extra config points to break. User can change per-agent later if desired.
3. **PM2 ecosystem file at `obsidian-vault/agent-ecosystem.config.js`** — declarative, version-controlled. Loaded with `pm2 start <file>`. Each agent has `interpreter: "none"` (it's a Python script with shebang).
4. **`HERMES_HOME` env var in PM2 config** — explicit override ensures each agent reads its own profile's .env, not the default.
5. **SOUL.md uses uppercase** — matches existing MONA convention at `/home/ubuntu/.hermes/SOUL.md`. The skill template uses both, uppercase is canonical.
6. **KANBAN PROTOCOL embedded in all 5 SOUL.md** — same protocol, different agents. Per-agent kanban file paths explicitly listed.

## Issues

### 🔴 CRITICAL: Bot tokens in .env are PLACEHOLDERS

The system auto-redacts credentials at the terminal/file-write layer. When I passed the tokens as command-line arguments to a Python script, the values were redacted to `***` BEFORE reaching the file. Result: each .env has `TELEGRAM_BOT_TOKEN=REPLACE_WITH_REAL_BOT_TOKEN`.

**Impact:** All 4 gateways are running, but Telegram adapter fails to create ("No adapter could be created for any of the 1 configured platform(s)"). They keep retrying every 30s. PM2 shows `↺` restarts (1-3 per agent).

**Fix:** User runs `bash /home/ubuntu/obsidian-vault/inject-tokens.sh` and pastes each real token at the prompt. The script validates via getMe, writes to .env, and restarts the PM2 process. User-side input bypasses the redaction layer (the user types in their own terminal, not through my tools).

### ⚠️ RAM tight

After starting 4 hermes gateways: 1.4Gi used of 1.9Gi total, 499Mi available, 3.3Gi swap free. We're at 74% memory usage. OOM kill risk if user starts more services. Consider:
- Reduce per-agent `max_tokens` to lower memory
- Or upgrade VPS to 4GB
- Or stop MONA's autonomous_loop (PID 173381, 22MB) if not needed

## Verification

### Profile list (hermes profile list)
```
default   tokenrouter/MiniMax-M3   running
yuna      tokenrouter/MiniMax-M3   stopped → running (via PM2)
soyu      tokenrouter/MiniMax-M3   stopped → running (via PM2)
yerin     tokenrouter/MiniMax-M3   stopped → running (via PM2)
haeri     tokenrouter/MiniMax-M3   stopped → running (via PM2)
```

### PM2 list
```
id  name           status    mem
4   yuna-gateway   online    113.5mb
5   soyu-gateway   online    113.2mb
6   yerin-gateway  online    114.0mb
7   haeri-gateway  online    113.1mb
```

### Soul.md files
- ✅ `/home/ubuntu/.hermes/SOUL.md` (MONA, with KANBAN PROTOCOL)
- ✅ `/home/ubuntu/.hermes/profiles/yuna/SOUL.md`
- ✅ `/home/ubuntu/.hermes/profiles/soyu/SOUL.md`
- ✅ `/home/ubuntu/.hermes/profiles/yerin/SOUL.md`
- ✅ `/home/ubuntu/.hermes/profiles/haeri/SOUL.md`

## Next Steps

1. **USER ACTION: Run `bash /home/ubuntu/obsidian-vault/inject-tokens.sh`** to inject real bot tokens. Paste each token at the prompt. The script auto-validates via getMe and restarts each PM2 process.
2. After inject, send `/start` to each of the 4 bots to verify they respond with their persona.
3. Test task routing: send a trading question to YUNA, sniper question to SOYU, etc.
4. If memory gets tight, consider stopping MONA's `autonomous_loop.py` (PID 173381) or upgrading VPS RAM.
5. Optional: per-agent model differentiation (e.g., give YUNA a more analytical model like `glm-5.1`).

## Git
- Commit: `2f8c167 feat: 5-agent system — PM2 ecosystem + token inject script`
- 2 files added to vault: `agent-ecosystem.config.js`, `inject-tokens.sh`
- 04-WALLET/ still git-ignored ✅
