# ITLG Stat Counter Upgrade — Opsi 1 Complete

**Date:** 2026-07-06
**Goal:** Match bot temen v5.4 display: `⛏️ Mines | 📺 Ads | ♻️ Recovers | ❌ Errors | Uptime`

---

## What Changed

### New helper functions (50 lines added)

- `bump_counter(name, by=1)` — increments counter, persists to claim_state.json, idempotent on missing state
- `get_counters()` — returns dict `{mines, ads, recovers, errors, started_at}` with all 5 keys safe-defaulted
- `format_uptime()` — returns `"Xh Ym"` (or `"0h 0m"` if started_at=0)
- `load_claim_state()` — added `counters` key to default state schema

### Hook points (5 source-line edits)

| Hook | File position | What |
|------|---------------|------|
| `bump_counter("ads")` | `trigger_ads()` line 416 | Ad watch returned valid retry data (NOT already-claimed) |
| `bump_counter("mines")` | `attempt_claim()` line 664 | Claim success (statusCode 200) |
| `bump_counter("mines")` | `attempt_claim()` retry path line 697 | Retry claim success |
| `bump_counter("recovers")` | `check_and_recover()` line 504 | Recovery ticket claimed (200/201) |
| `bump_counter("errors")` | `attempt_claim()` line 717 | Claim failed (non-early status) |

### Display changes

**`--status` console output:**
```
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📊 Stats:  ⛏️ Mines: 1  📺 Ads: 0  ♻️ Recovers: 0  ❌ Errors: 0
  ⏱️ Uptime: 0h 30m
```

**Telegram notif (claim success):**
```
⛏️ Mines: 1  |  📺 Ads: 0
♻️ Recovers: 0  |  ❌ Errors: 0
⏱️ Uptime: 0h 30m
```

---

## Edge Cases Handled

1. **State file wiped** — `load_claim_state` returns default with counters. `bump_counter` writes fresh counters dict on first call.
2. **State created before counters feature** — `bump_counter` calls `setdefault("counters", ...)` + per-key `setdefault(k, ...)`. Existing state files without counters key still work.
3. **`trigger_ads` "Already claimed in this frame"** — `data.data = false` → counter NOT incremented. Only counts new ad watches.
4. **Recovery ticket failure** (non-200/201) — recovers NOT incremented.

---

## Verification

**Ad-hoc (not test-suite green): 19/19 PASS**

| # | Check | Result |
|---|-------|--------|
| 1-3 | 3 new functions defined | ✅ |
| 4 | Syntax check (py_compile) | ✅ clean |
| 5-6 | In-memory counter persistence (5+3+2+3 bumps) | ✅ exact match |
| 7 | Edge case: state wipe → auto-init | ✅ |
| 8 | `format_uptime` regex `^\d+h \d+m$` | ✅ |
| 9-11 | `--status` displays Stats + Uptime + separator | ✅ |
| 12-15 | 5 hook points exist (grep counts) | ✅ all exact |
| 16-17 | TG notif + recovery notif include stats_line | ✅ |
| 18-19 | systemd service active + new PID post-restart | ✅ |

### Live API Edge Case Verified

Telegram notif sukses terkirim ke topic 10832 dengan counter line. `trigger_ads` LIVE return `{"data":{"data":false,...}}` karena sudah claim di frame ini → `ads` counter NOT inflated (correct behavior).

---

## Files Modified

- `/home/ubuntu/itlg-claim/bot.py` (3 patches: helpers, hooks, display — 50+ lines added)
- `/home/ubuntu/obsidian-vault/05-HERMES-OUTPUTS/2026-07-06-itlg-stat-counter-upgrade.md` (this)

## State Snapshot

- Bot PID: 1900859 (post-restart)
- Balance: 74 ITLG
- Counters at deploy: `{mines: 0, ads: 0, recovers: 0, errors: 0, started_at: <now>}`
- Service: itlg-claim.service active

## What's Next

Opsi 2 (multi-account) + Opsi 3 (group mining) requires Mas to register 2 more Interlink accounts (KYC perlu email + face verification). Bot temen likely menggunakan ini untuk dapat mining offset → ~1h 20m per claim (instead of 4h).

Opsi 1 closes the display/counter gap. Bot kita functionality sekarang match screenshot temen. Tinggal rate gap (4h vs 60s) yaitu hard constraint dari sisi API — no client-side fix kecuali multi-account.
