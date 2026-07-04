# 2026-07-04 Squad Dispatch — Wallet on Telegram

**Task:** Dispatch 4 WOT (Wallet on Telegram) bug bounty tasks to 4-bot squad (liora, zqya, riva, nova) via Hermes Kanban.
**Result:** 4/4 tasks running stable (verified 90s+ stable after multiple fix iterations).
**Started:** 2026-07-04 07:52 SGT
**Status:** Running (as of 08:31 SGT)

## Root Causes of Multiple Crashes

1. **Kimchi provider expired** — api_key `castai_v1_...` mengembalikan 401 dari `llm.kimchi.dev`. Squad profiles (liora/zqya/riva/nova) semua pakai `custom:kimchi` → semua LLM call gagal → dispatcher crash → reaped zombie workers.

2. **fallback_providers YAML format bug** — gua pass JSON-string ke config.yaml, YAML parser malah parse jadi list of chars (`['[', '"', '9', 'r', 'o', ...]`). Saat fallback triggered, pencarian provider gagal → "no registered providers found for the requested model".

3. **Profile-scoped skills missing** — kanban `--skill X` butuh skill ada di `~/.hermes/profiles/<name>/skills/` dir (profile-scoped), bukan global `~/.hermes/skills/`. Profile skills dir hanya berisi builtin skill (creative/data-science/dll). Custom skill bug-bounty-squad, security-recon, dll harus DI-COPY ke profile skills dirs.

## Fixes Applied

1. **Patch 4 squad config.yaml:**
   - `model.default`: `glm-5.2` (dari `kimchi/kimi-k2.7` / `kimchi/deepseek-v4-flash`)
   - `model.provider`: `custom:iamhc`
   - `model.base_url`: `https://api.iamhc.cn/v1` 
   - Tambah iamhc ke `custom_providers` (api_key `sk-Ppt...` copied dari default profile)
   - Hapus kimchi dari custom_providers

2. **Fix `fallback_providers`** jadi list of strings native Python:
   ```python
   cfg['fallback_providers'] = ['TokenRouter', 'nvidia', 'TensorMesh', 'Coundit', 'iamhc']
   ```

3. **Copy 4+ skill ke profile-scoped skills:**
   - `bug-bounty-squad` → 4 profile
   - `security-recon` → 4 profile
   - `web-security-api-exploitation` → zqya
   - `testing-api-for-broken-object-level-authorization` → nova
   - `testing-api-authentication-weaknesses` → riva
   Pattern: `shutil.copytree(global_skill_path, profile_skills_path)`

4. **Restart 4 gateway** (`systemctl --user restart hermes-gateway-{name}.service`) untuk apply config + re-seed skill registry.

## Final Status (verified 2026-07-04 08:31 SGT)

```
● t_e0996b23  running   liora  WOT-P1-RECON  → data/ output started
● t_ec4b165a  running   zqya   WOT-P2-EXPLOIT → LLM processing
● t_19ac4bfc  running   riva   WOT-P3-AUTHZ  → raw/ output (pay_main.txt 1.4MB!)
● t_3a61ade0  running   nova   WOT-P4-AUTO   → LLM processing
```

Worker count: 3 active hermes subprocess workers.

## Monitoring

Cron job `bb-squad-monitor` (job_id `3dc23bcd8a68`):
- Schedule: every 10 minutes
- Script: `/home/ubuntu/.hermes/scripts/bb_squad_monitor.py`
- Deliver: origin (topic 8460 — Mona)
- State file: `/home/ubuntu/.hermes/cron/output/bb_squad_state.json`
- Triggers alert kalau:
  - Status changes (running→done/blocked)
  - New output files detected

## LLM Provider Status (sanity check)

- iamhc glm-5.2: 200 OK, 1.2s latency ✅ (kini dipakai squad profiles)
- Kimchi kimi-k2.7: 401 dead ❌
- Kimchi deepseek-v4-flash: 401 dead ❌

## Next Steps

- Tunggu squad kerja tiap phase (~15-30 menit per phase pertama recon)
- Monitor output via cron job alert
- Squad output akan tertulis ke `/home/ubuntu/bugbounty/wallet-on-telegram/squad-output/<bot>/`
- Squad punya 10-15 menit timeout default (per-kanban-task)
- Jika ada stuck task → lihat `hermes kanban show <task_id>` + `hermes kanban log <task_id>`
- Jika ada blocked task baru → cek skill missing via `hermes --profile <bot> skills list | grep <skill_name>`

## Decisions

- Gak hapus Kimchi dari config default profile (Mas mungkin punya API key baru nanti). Hanya hapus dari squad profiles yang butuh working LLM sekarang.
- Pakai iamhc sebagai provider squad karena hanya itu yang verified live (selain dari beberapa komputasi-expensive provider).
- Cron deliver=origin biar Mas dapat alert di topic 8460.
- Backup config tiap profile: `config.yaml.bak_dispatch_wot` (jangan dihapus buat rollback).

## Issues

- Kimchi api_key mati tiba-tiba. Memory sebelumnya bilang "Kimchi DIHAPUS 2026-07-03" padahal api_key-nya cuma expired. Update memory dengan fakta ini.
- Profile-specific skills копи pattern wajib diingat. Nantinya kalau ada skill custom baru, perlu copy ke `~/.hermes/profiles/<name>/skills/` bila ingin dipakai oleh profile itu.
