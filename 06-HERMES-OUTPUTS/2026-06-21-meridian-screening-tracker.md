---
type: receipt
date: 2026-06-21
tags:
  - receipt
---

# 2026-06-21 — Meridian Screening Tracker Run

| Field | Value |
|---|---|
| **Date** | 2026-06-21 |
| **Agent** | MONA — The Architect |
| **Task** | Run Meridian screening tracker pipeline (parse → analyze → report) and apply optimal threshold recommendations for 0.364 SOL wallet |
| **Result** | Pipeline ran cleanly. No new screening cycles since June 17 (PM2 was offline June 18-20). Today PM2 is online again but every cycle fails with OpenAI provider credentials error → no candidate data captured. **No threshold changes recommended** — live config is already more permissive than both optimizer and screening tracker suggestions. |
| **Decisions** | (1) Skip `--parse` new data collection (all 636 historical cycles already tracked). (2) Cross-referenced live config vs optimizer vs screening tracker — live is MORE permissive on both `maxBotHoldersPct` (55>30) and `minFeeActiveTvlRatio` (0.002<0.025). (3) Skip optimizer's `--collect` (today's log absent; data already tracked). (4) No restart attempted — wallet=0 SOL, .env DRY_RUN=true, agent erroring out — triple-blocker persists. |
| **Issues** | **NEW since June 21 03:47 baseline:** (1) PM2 now manages meridian (id=3, online, 83m uptime, restarted ~09:45) but `.env DRY_RUN=true` still blocks LIVE. (2) **Every screening cycle fails**: `[ERROR] Agent loop error at step 0: 404 No active credentials for provider: openai` — despite `LLM_MODEL=tokenrouter/MiniMax-M3` in .env and `config.llm.screeningModel="tokenrouter/MiniMax-M3"` resolved fresh. Log shows `[CRON] Starting screening cycle [model: openai/gpt-4o-mini]` though Node check confirms actual config value is `tokenrouter/MiniMax-M3` — possible OpenRouter model routing issue OR stale PM2 process using different model. (3) PM2 runtime applying `maxBotHoldersPct=30` despite live user-config.json having 55 — likely stale config snapshot from PM2 start (before June 21 config edits). (4) PM2 log shows `Computed deploy amount: 0.98 SOL (wallet: 3 SOL)` — but Node check returns `computeDeployAmount(3) = 0.04` — likely stale config when PM2 started (deployAmountSol/positionSizePct different). (5) Wallet still 0 SOL (was 0.364 historically). (6) Telegram bot 401 Unauthorized (token expired). |
| **Next** | (1) User should fund wallet `9XJU…LZ3X` to ≥0.16 SOL (recommended 0.5+). (2) Flip `DRY_RUN=true → false` in `~/mona-workspace/meridian/.env`. (3) Investigate OpenAI provider credentials — possible fix: ensure `OPENROUTER_API_KEY` is set and that `tokenrouter/MiniMax-M3` routes correctly (or change to a model name that resolves to a working provider). (4) After wallet funded + .env fixed + LLM credentials fixed, do `pm2 restart meridian` to pick up new config snapshot (currently PM2 is using stale maxBotHoldersPct=30 and stale deployAmount logic). (5) Optional: clear stale simulated position `sim_B3puMRwG_1781669422257` (HermesWorld-SOL from June 17) before restart so first cycle doesn't get blocked by `maxPositions: 1`. (6) Optional: fix Telegram bot token. |

## Diagnostic Summary

**Pre-flight:**
- Wallet: **0.000 SOL** (empty, unchanged since June 17)
- executor.js L808: **patched** (`const minDeploy = config.management.deployAmountSol;`)
- `.env` DRY_RUN: **`true`** (overrides `dryRun: false` in user-config.json)
- PM2: **online** (id=3, 83m uptime, ↺=0) — NEW since 03:47 baseline
- PM2 log mtime: 2026-06-21 11:00:05 (recent, but all cycles erroring)
- management block in user-config.json: NOT empty (was incorrectly identified earlier — full thresholds present)

**Screening stats:**
- Total cycles: **636** (no new since June 17)
- Total candidates: 590
- Deploy cycles: **32** (5.0% rate)
- No-deploy cycles: 604
- Rejections: **360 bot_filter + 230 safety_block**
- Avg bot % of rejected: 35.6%
- Avg fee/TVL of rejected: 0.193%
- Last 50 cycles: **0 deploys** (agent errored on every cycle today)

**Config assessment (cross-reference tiebreaker):**
| Param | Live | Optimizer | Screening Tracker | Verdict |
|---|---|---|---|---|
| `maxBotHoldersPct` | 55 | 30 | 55→55 | **live MORE permissive** ✓ |
| `minFeeActiveTvlRatio` | 0.002 | 0.025 | 0.002→0.01 (wrong dir) | **live MORE permissive** ✓ |

Live config is already optimal. **No threshold changes applied.**

**Deploy amount discrepancy (persistent issue):**
- 95/96 historical deploy_position calls exceeded `deployAmountSol: 0.04`
- Amount distribution: 0.04 (1), 0.10 (21), 0.12 (1), 0.15 (35), 0.16 (3), 0.50 (7), 0.98 (3), 1.00 (21), 2.00 (4)
- Root cause: `prompt.js` L122 COMPOUNDING instruction (June 20 baseline finding)
- Code-level clamp needed in `executor.js` before LIVE mode is safe for small wallet

**Sub-type analysis of last-50-cycle safety_block rejections** (per June 17 pattern):
- Sub-type A (real-time 0% fee/TVL, market conditions): dominant
- Sub-type B (LLM self-censor about 0.1 minimum): minor
- Both are downstream of the OpenAI provider error — screening cycles never reach candidate evaluation

**Today's failure mode is NOT a threshold issue** — it's an LLM provider connectivity problem. Threshold tuning can't fix this.
