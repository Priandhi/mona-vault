# 🧠 Obsidian Vault — Mona's Permanent Memory

> **Owner:** Hye-Jin (0xjosee) | **Operator:** Mona 💜 (Hermes Agent) | **Host:** VPS Ubuntu 22.04

## 🎯 Tujuan

Vault ini adalah **single source of truth** untuk semua operasi Mona di VPS. Tiap file di sini adalah memory permanen yang:

- **Lokal & milik lo** — plain markdown, gak ada cloud lock-in
- **Versioned** — Git tracked (kecuali `04-WALLET/`)
- **Mudah disinkron** ke HP/laptop via Obsidian app + Git
- **Makin pinter seiring waktu** — receipts accumulate, sistem belajar

## 📁 Struktur Folder

### `00-INBOX/` — Tangkap cepet
Catatan kilat, ide random, link, thought dump. Belum diproses jadi project.
- Format bebas, satu file per ide atau satu file running notes
- Diproses mingguan jadi project di `02-PROJECTS/`

### `01-DAILY/` — Harian
File per hari: `YYYY-MM-DD.md`
- Summary apa yang dikerjain hari itu
- Reference ke receipt files
- Inbox items yang diproses
- Daily note adalah **first thing agent baca** di awal session

### `02-PROJECTS/` — Per project
Satu file `.md` per project aktif.
- Status project
- Decisions log
- Blockers
- Links ke receipt files terkait

Project aktif:
- `iclix.md` — streaming platform
- `owntown-bot.md` — Solana farming bot
- `mining.md` — VPS mining setup
- `21+-subproject.md` — 21+ content scraper
- `mona-vault.md` — vault ini sendiri

### `03-RESEARCH/` — Temuan & riset
Findings dari exploit attempts, security research, API discovery, new tools.
- Format: `[topic].md`
- Include: source, hypothesis, test result, conclusion

### `04-WALLET/` — ⚠️ SENSITIF
Wallet addresses, secrets reference, keypair paths.
- **JANGAN PERNAH** di-commit ke Git (sudah di-exclude)
- Tetep di-vault lokal biar agent tau wallet mana yang aktif
- Main Solana wallet: `9XJUJJ9YTq6Vrj7ZRRWAariysQrgkB8hm7QMPzMxLZ3X`

### `05-HERMES-OUTPUTS/` — Receipts
Setiap task yang agent kerjain, outputnya ditulis ke sini.
- Format: `YYYY-MM-DD-[task-name].md`
- Wajib ada: Task, Result, Decisions, Issues, Next Steps
- Ini adalah **audit trail** + **knowledge base** yang terakumulasi

## 🤖 Cara Agent Interaksi

### Awal session:
1. Baca `01-DAILY/` — cari file tanggal terbaru
2. Baca `02-PROJECTS/` — load project yang relevan
3. Baca `05-HERMES-OUTPUTS/` — cek receipts terbaru untuk konteks
4. Baca `MEMORY.md` di vault root (jika ada) — long-term persistent facts

### Selama session:
- Task selesai → tulis receipt ke `05-HERMES-OUTPUTS/`
- Project update → edit file di `02-PROJECTS/`
- Penemuan baru → tulis ke `03-RESEARCH/`
- Ide mendadak → tulis ke `00-INBOX/`

### Akhir session:
- Update daily note hari ini
- Commit semua perubahan

## 🔒 Prinsip

- **LOCAL FIRST** — gak ada cloud lock-in
- **PLAIN TEXT** — markdown, future-proof
- **EVERY RUN MAKES SYSTEM SMARTER** — receipts accumulate
- **NOTHING LOCKED IN** — bisa export, migrate, fork kapan aja

## 🔄 Sync

- VPS → Git → GitHub private repo → lo pull di HP/laptop
- Atau: VPS → local folder via Syncthing
- Lihat `INSTRUCTIONS-SYNC.md` untuk setup detail

---

*Last updated: 2026-06-14 (vault initialization day)*
