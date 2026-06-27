---
name: operator-workspace-bootstrap
description: Bootstrap or extend an operator's working directory on a VPS/host — scaffold a class-organized folder tree, harden secret stores (chmod 700 vault), drop sensible .gitignore + README, and AVOID re-scaffolding when an existing workspace is already in place. Triggers — "bikin folder di vps", "atur workspace", "setup project structure", "buatkan struktur folder", "organize my server", "scaffold workspace", or any user asking you to "atur sebaik mungkin" a directory layout for ongoing operator work.
---

# Operator Workspace Bootstrap

For setting up or extending a long-lived working directory on a server / VPS / dev box for an individual operator. Covers crypto-ops, automation, builds, data, and a hardened secrets vault under one root.

This skill is about the **filesystem and conventions**, not about the projects that live inside it. Once the workspace exists, the actual work happens in skills like `hermes-crypto-agent`, the github-* family, etc.

## ⚠️ Pitfall #1 — DISCOVER BEFORE SCAFFOLD

The single biggest mistake on these requests: user says "bikin folder" / "atur sebaik mungkin" / "set up workspace", and you immediately scaffold a fresh tree under a name you invented. Then the user reveals there was already a workspace at a different path from a prior session — now there are two roots and the operator has to pick.

**Always probe first, in this order:**

1. **Check persistent memory** for any line mentioning the operator's workspace root (search for "workspace", "ops", "~/" entries). The memory tool injects these every turn — re-read them before scaffolding.
2. **Probe the filesystem** for likely existing roots:
   ```bash
   ls -la ~/ | grep -iE "(workspace|ops|projects|mona|work)"
   find ~ -maxdepth 2 -type d -name "*workspace*" -o -name "*-ops" 2>/dev/null | head -20
   ```
3. **If an existing root is found**, ASK the operator which to use before creating anything new:
   > "Gue notice udah ada `~/<existing>/` dari sesi sebelumnya. Mau lanjutin yang itu, ganti, atau merge?"
4. **Only scaffold fresh if nothing exists OR the operator explicitly confirms a new root.**

## Standard Layout (when scaffolding fresh)

Use this as the default class-level tree. Adapt categories to the operator's actual surface area — don't carry empty folders the operator will never use.

```
<workspace-root>/
├── crypto-ops/      # On-chain work: wallets, airdrops, snipers, arb, mev, multichain
├── automation/      # Scrapers, bots, schedulers, webhooks
├── builds/          # Production projects: web, api, cli, mobile
├── scripts/         # One-off utility scripts
├── data/            # raw / processed / exports / backups
├── logs/            # Runtime logs
├── docs/            # Notes, runbooks
├── sandbox/         # Experimental / throwaway
└── vault/  🔒       # Secrets — chmod 700, keys / configs / secrets
```

Always include at the root:
- `README.md` — map of the structure + quick commands (du, tar backup, tree)
- `.gitignore` — block `vault/`, `.env*`, `*.key`, `mnemonic*`, `seed*`, `private*`, `node_modules/`, `__pycache__/`, `*.log`

## Vault Hardening (mandatory)

The vault is the only directory where operator secrets live. Treat it like a HSM, not like a folder.

```bash
chmod 700 ~/<workspace>/vault
chmod 700 ~/<workspace>/vault/*
# write a vault-local .gitignore that excludes everything
echo -e "*\n!.gitignore" > ~/<workspace>/vault/.gitignore
```

Rules embedded in the vault README (and reinforced by the agent every session):
- Never `cat` / `echo` / `print` vault contents into chat or logs.
- Mnemonics live offline (paper / hardware). Only derived addresses or keystores go in the vault.
- API keys live in `.env` files inside individual project folders, gitignored — not in `vault/configs/` unless the operator explicitly stages them for cross-project reuse.

## Backup Convention

Document in the root README:
```bash
tar --exclude='vault' --exclude='node_modules' --exclude='__pycache__' \
    -czf ~/backups/workspace-$(date +%Y%m%d).tar.gz ~/<workspace>
```
Exclude the vault deliberately — backups go to remote storage and the vault must NOT travel through that path.

If the operator wants automated backups, schedule via `cronjob` — do not silently install a system cron.

## Extending an Existing Workspace

When discovery finds an existing root, **patch, don't replace**:

1. `tree -L 2 ~/<existing>` to map what's already there.
2. Identify gaps vs. the standard layout (often missing: `sandbox/`, `vault/`, `.gitignore`).
3. Propose the additions to the operator. List them as a diff, don't just create.
4. After confirmation, `mkdir -p` only the missing dirs. Don't touch what exists.
5. Update memory with the canonical root path so future sessions land on the right one.

## Memory Hygiene

After scaffolding or confirming a workspace, write ONE memory entry with:
- Absolute root path (both `~/` and `/home/<user>/` forms)
- One-line subfolder list
- Note: "Use as default location for new projects/scripts."

If the operator has multiple stale workspace entries in memory (from prior sessions where you scaffolded without discovering), CONSOLIDATE — `replace` the older entry, don't `add` a parallel one. Two competing workspace roots in memory will bite the next session.

## Maintaining the Workspace (Post-Bootstrap)

The workspace needs periodic hygiene. "aturin workspace", "bersihin", "hapus yang gak berguna", "beresin file" → trigger this section.

### Discovery Scan (ALWAYS run first)

Before proposing any deletion, do a full discovery scan. This is **non-negotiable** — never delete based on assumptions:

```bash
# Empty files and directories
find ~/<workspace>/ -type f -empty 2>/dev/null
find ~/<workspace>/ -type d -empty 2>/dev/null

# Hermes runtime cleanup targets (NOT memories/sessions/skills)
du -sh ~/.hermes/logs/
du -sh ~/.hermes/sessions/
ls -lt ~/.hermes/*.bak* 2>/dev/null

# API key locations in .env (masked output only)
grep -E "API_KEY|OPENAI|ANTHROPIC|TELEGRAM|OLLAMA" ~/.hermes/.env 2>/dev/null | sed 's/=.*/=***/g'
```

### What CAN Be Cleaned (Safe Targets)

These are **operator's own data** — Hermes recreates all of them on next run:

| Target | Risk | Action |
|--------|------|--------|
| Empty skeleton dirs (e.g. `scrapers/`, `bots/` with no files) | Zero — no content | Delete with confirmation |
| Old backup files (`*.bak.*`, `auth.json.bak.*`) | Zero — superseded | Delete with confirmation |
| `~/.hermes/logs/` | Zero — runtime noise | `rm -rf ~/.hermes/logs/*` |
| `~/.hermes/sessions/` | Zero — chat history only | `rm -rf ~/.hermes/sessions/*` |

### What MUST NOT Be Touched

- `~/.hermes/memories/MEMORY.md` and `USER.md` — the operator explicitly said **"jangan hilangkan memori"**. These are the session-crossing memory that keeps context across sessions. Touching them breaks the continuity the operator relies on.
- `~/.hermes/skills/` — all skill definitions
- `~/.hermes/state.db`, `kanban.db` — operational state
- `vault/` contents — secrets

### API Key Rotation

When the operator says credit is low / key is exhausted and they'll provide a new key:
1. Locate the current key in `~/.hermes/.env`
2. **Do NOT delete the old key** — comment it out with `#` prefix so it's preserved for reference
3. Add the new key in the same format
4. Confirm which provider/model the new key is for

### Initiative-Taking Style

When the operator says "kamu setting sendiri yang terbaik" / "aturin sendiri" — they want you to **make the call and present it**, not ask permission for every file. Rules:
- Run the discovery scan fully
- Present a **categorized action list** with risk level (🔴 high, 🟡 medium, ✅ safe)
- If the list is short, just execute after presenting. If it's long/complex, ask " lanjut?" first.
- Use operator-to-operator tone: direct, no fluff, no disclaimer paragraphs.

## Safe-Backup-via-Rename Pattern (Jun 13, 2026 — "asal aman dan data tidak hilang")

When user says "hapus", "buang", "bersihin", OR "hapus X tapi jangan sampai data hilang" — **default to rename, not delete.** This is the safest, instantly-reversible pattern and matches the operator's explicit safety preferences (`asal aman dan data tidak hilang`).

**Pattern:**
```bash
# 1. Generate timestamp suffix
TS=$(date +%Y-%m-%d_%H%M%S)

# 2. Rename (not delete) — instant, zero-copy, instantly reversible
mv /path/to/target /path/to/target.bak.${TS}

# 3. Verify safety
ls -la /path/to/target.bak.${TS}  # confirm still exists
# Any service that depended on the path will error → quick detection

# 4. AFTER confirming nothing broke (hours/days later):
rm -rf /path/to/target.bak.${TS}
```

**When to use rename vs delete:**
| User signal | Default action | Why |
|-------------|----------------|-----|
| "hapus" + "asal aman" | **Rename** with timestamp | User explicitly traded speed for safety |
| "hapus" alone | Ask, default rename | Cost of rename is zero, cost of delete is unrecoverable |
| "buang aja gak guna" | Ask, then rename | "Gak guna" is operator's assessment, not 100% certainty |
| "hapus permanen" / "rm aja" | Delete | Explicit instruction to remove |
| "/.junocash + keryx udah gabutuh" | Rename, then ask before final delete | User's wording suggests confidence but safety-first still wins |

**Why rename is better than delete for cleanup:**
- `mv` is **instant** (same filesystem, just updates directory entries — no data copy)
- `df -h` will NOT show space freed until `rm` later — this is a feature, not a bug. It signals "I have a backup" without committing
- If a cron job or PM2 service was depending on the path, it errors out LOUDLY within minutes — instant detection of hidden dependencies
- Rollback is one command: `mv target.bak.TS target`
- User can verify "data masih ada?" by listing the .bak. folder

**Communication pattern:**
```
"Done aman! 🛡️
- ✅ .local (1.79G) → .local.bak.2026-06-13_155102
- ✅ Semua service masih online  
- ✅ Data 100% aman (rename, bukan delete)

Rollback instant: mv .local.bak.* .local"
```

**Pitfall to avoid:** Never `rm -rf` a large directory (>500MB) without a 24-48h observation period after rename. Disk "feels" the same (because rename doesn't free space), but the operator can detect silent dependencies during this window.

### Comprehensive Inventory Request (Jun 13, 2026)

When user asks "list full" / "bahas detail" / "tunjukin semua" / "apa aja yang udah pernah lo build" — they want **a deep inventory, not a summary.** Pattern from real session:

- Initial shallow summary ("~25+ projects aktif") → user: "kok cuma itu🫠 list full mau lihat"
- Follow-up: full per-project size + sub-directory listing + file count + active run state
- User values **breadth + depth**, not just headcount

**Trigger phrases:**
- "list full", "bahas detail", "yang lengkap dong", "tunjukin semua"
- "apa aja yang udah pernah lo build" / "masih inget semua"
- "penasaran", "pengen tau", "mau liat" + emoji (🫠😁🤔)

**Required output structure:**
1. Group by domain (crypto / streaming / AI / CTF / ops)
2. Per project: name + size + purpose (1 line) + sub-structure
3. Active services separately (PM2 + health)
4. Remote infrastructure (other VPS) with status
5. Total stats at end (count + GB + active count)
6. **Offer deep-dive on individual projects**: "Mau bahas detail project tertentu?"

**Don't:** give a summary table first and hope it's enough. User will push back. **Do:** scan the filesystem first (`du`, `ls -la`, `pm2 list`), then present the comprehensive view in one shot.

### VNC Remote Desktop

For exposing a visual desktop from the VPS (browser viewing from phone/PC, visible browser automation): `references/vnc-remote-desktop-setup.md`

Covers: Xvfb virtual display, x11vnc, noVNC web client, localhost.run tunnels, Chrome on VNC display, Fluxbox window manager.

## References

- `references/discovery-recipe.md` — exact commands to probe for existing workspaces before scaffolding.
- `references/standard-tree.md` — the full layout with rationale per subdirectory, ready to paste into a README.
- `references/cleanup-recipe.md` — full discovery scan, workspace hygiene, **skills cleanup** (remove irrelevant bundled skills), **scripts deduplication**, **VPS-level cleanup** (old projects, venvs, pip cache, browser data), and logs deep clean. Includes "ask first" pattern for user-protective operators.
