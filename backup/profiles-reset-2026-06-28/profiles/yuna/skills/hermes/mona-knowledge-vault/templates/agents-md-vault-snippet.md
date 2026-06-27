# VAULT MEMORY PROTOCOL — AGENTS.md Section

> Add this section to `/home/ubuntu/AGENTS.md` (and optionally to the vault's own `AGENTS.md` copy).
> Use `patch()` not `write_file` to preserve existing content.

## Snippet to Inject

```markdown
## VAULT MEMORY PROTOCOL

> The vault at `/home/ubuntu/obsidian-vault/` is Mona's permanent memory. This protocol is MANDATORY.

### Vault location
```
/home/ubuntu/obsidian-vault/
├── 00-INBOX/           # Quick ideas, random thoughts (unprocessed)
├── 01-DAILY/           # One .md per day (YYYY-MM-DD.md)
├── 02-PROJECTS/        # One .md per active project
├── 03-RESEARCH/        # Findings, exploit attempts, research results
├── 04-WALLET/          # ⚠️ SENSITIVE — Git-ignored, never push
└── 05-HERMES-OUTPUTS/  # Receipts (audit trail) — one per task
```

### Awal setiap session:
- Baca 01-DAILY/ — cari file tanggal terbaru (load context)
- Baca 02-PROJECTS/ — load project yang relevan dengan request user
- Baca 05-HERMES-OUTPUTS/ — cek receipts terbaru untuk konteks task sebelumnya

### Akhir setiap task:
- Tulis receipt ke 05-HERMES-OUTPUTS/YYYY-MM-DD-[nama-task].md
- Format receipt WAJIB berisi:
  - **Task:** apa yang dikerjain
  - **Result:** hasil/output
  - **Decisions:** keputusan yang diambil dan alasannya
  - **Issues:** masalah yang ditemukan
  - **Next Steps:** apa yang perlu dilanjut

### Aturan tambahan:
- Ide/catatan cepat → tulis ke 00-INBOX/
- Setiap project punya file sendiri di 02-PROJECTS/
- Findings/riset → tulis ke 03-RESEARCH/
- 04-WALLET/ — **JANGAN PERNAH** di-push ke Git
- End of day → update daily note (01-DAILY/YYYY-MM-DD.md)
- After daily note update → `git add -A && git commit -m "vault: YYYY-MM-DD daily"`
```

## How to Inject

```python
patch(
    mode="replace",
    path="/home/ubuntu/AGENTS.md",
    old_string="## Active Projects (refer to /home/ubuntu/obsidian-vault/02-PROJECTS/ for full details)",  # or any other section anchor
    new_string="## VAULT MEMORY PROTOCOL\n\n[snippet above]\n\n## Active Projects (refer to /home/ubuntu/obsidian-vault/02-PROJECTS/ for full details)"
)
```

Or, if injecting at end of file:
```python
# Read file, append snippet, write back via patch
patch(
    mode="replace",
    path="/home/ubuntu/AGENTS.md",
    old_string="## Reminders for Operator\n\n- Always read vault's `01-DAILY/`...",
    new_string="## Reminders for Operator\n\n- Always read vault's `01-DAILY/`...\n\n## VAULT MEMORY PROTOCOL\n\n[snippet above]"
)
```

## Why a Section in AGENTS.md

`AGENTS.md` is auto-injected into every session by Hermes Agent. By including the protocol in the user-level `AGENTS.md`, the agent starts EVERY session already knowing:
- Where the vault lives
- What the folder structure is
- The read/write protocol
- That receipts are mandatory
- That 04-WALLET/ is git-ignored

No need to re-explain each session. The protocol is in context from turn 1.
