# Bahasa Indonesia Conversion — Session Log & Reference

## Origin

User explicit request: **"bahasa indonesia aja bos"** (Indonesian only, boss).

Context: User had just sent `/positions@DinoCantik_Bot` to Meridian and got an English response (`## 📊 Positions & Portfolio`, `### Open Positions`, `**None** — 0 active DLMM positions`, `### 💰 Wallet Balance`, `### 📈 Lifetime Stats`). User wanted the entire bot output in Bahasa Indonesia.

## Scope of the Conversion

61 user-facing strings converted across 4 files:

| File | Strings | Coverage |
|---|---|---|
| `index.js` | 43 | Command handlers, format functions, TUI shell, error throws |
| `telegram.js` | 13 | notify functions + BOT_COMMANDS descriptions |
| `briefing.js` | 4 | Morning briefing format |
| `prompt.js` | 1 | `languageRule` constant injected into 3 prompt branches |
| **Total** | **61** | |

## File:line Locations of Indonesian Strings

### `prompt.js` (1 string, but 3 injection points)

- `languageRule` constant defined at line 16
- Injected at:
  - Line 22: MANAGER branch `return \`${languageRule}You are an autonomous DLMM LP agent on Meteora, Solana. Role: MANAGER...`
  - Line 38: base/GENERAL branch `let basePrompt = \`${languageRule}You are an autonomous DLMM LP...`
  - Line 109: SCREENER branch `return \`${languageRule}You are an autonomous DLMM LP agent on Meteora, Solana. Role: SCREENER...`

The `languageRule` text (full string):
> "🌐 LANGUAGE RULE — ABSOLUTELY MANDATORY: All text you output to the user MUST be in BAHASA INDONESIA (Indonesian)... Translate technical terms to Indonesian equivalents (deploy→deploy, position→posisi, open→buka, close→tutup, candidate→kandidat, etc.)..."

### `index.js` (43 strings)

**Format functions** (lines ~1000-1080):
- `formatWalletStatus()` — "Wallet / Harga SOL / Posisi terbuka / Jumlah deploy berikutnya / Dry run: ya/tidak / HiveMind: aktif/mati"
- `formatConfigSnapshot()` — "Snapshot Config / Strategi / Trailing: aktif/mati / OOR: Xm / Repeat deploy cooldown: aktif/mati / Yield floor / min usia / Screening / Interval: manage/screen / HiveMind: aktif/mati"

**`/help` text** (`formatHelpText()`, lines ~1288-1312):
- Header: "Perintah Telegram"
- 19 command descriptions, all in Indonesian

**Command handlers** (lines ~1450-1545):
- `/positions` empty: "Tidak ada posisi terbuka."
- `/positions` header: "📊 Posisi Terbuka (N):"
- `/positions` row: "X. PAIR | $VALUE | PnL: +/-X | fee: $X | Nm"
- `/positions` footer: "/close <n> untuk tutup | /set <n> <note> untuk set instruksi"
- `/pool` error: "Nomor tidak valid. Jalankan /positions dulu."
- `/pool` row labels: "Pool / Posisi / Range / aktif / PnL / fee / Nilai / Usia / DALAM RANGE / OOR / Catatan"
- `/close` start: "Menutup PAIR..."
- `/close` success: "✅ PAIR ditutup / PnL: / tx tutup: / Tx claim:"
- `/close` fail: "❌ Gagal tutup"
- `/closeall` start: "Menutup N posisi..."
- `/closeall` done: "Close-all selesai. / ditutup / gagal / tidak diketahui"

**Candidate display** (lines ~515, 992, 1002, 1325, 1331):
- `runDeterministicScreen()`: "Kandidat teratas (N)" / "Tidak ada kandidat tersedia." / "Contoh yang di-filter:" / "Tidak ada kandidat tersedia saat ini."
- `describeLatestCandidates()`: "Belum ada kandidat di cache. Jalankan /screen dulu." / "Kandidat cache terakhir (N) — diupdate"
- `formatCandidates()`: "Tidak ada pool eligible saat ini."

**Error throws** (line ~1338):
- `deployLatestCandidate()`: "Index kandidat tidak valid. Jalankan /screen dulu."

**Screening fallback** (line ~520):
- "Tidak ada kandidat tersedia." / "Contoh yang di-filter:" / "Tidak ada kandidat tersedia (semua di-filter oleh aturan launchpad / holder-quality)."

**TUI interactive shell** (lines ~1769, 1822-1834, 1848, 1960):
- Startup banner: "Perintah:" / "Deploy X SOL ke pool itu" / "Biar agent pilih dan deploy otomatis" / "Refresh wallet + posisi" / "Refresh daftar pool teratas" / "Tampilkan briefing pagi" / "Pelajari top LPers" / "Tampilkan threshold screening" / "Trigger evolusi threshold manual" / "Matikan agent"
- Busy state: "Agent sedang sibuk, tunggu sebentar..."
- Deploy action: "Deploy X SOL ke POOL_NAME..."
- Study command: "Tidak ada pool eligible untuk dipelajari."

### `telegram.js` (13 strings)

**`notifyDeploy()`** (lines ~440-460):
- "✅ **Berhasil Deploy** PAIR" / "Jumlah: X SOL" / "Range harga:" / "Cakupan range:" / "Bin step:" / "Base fee:" / "Posisi:" / "Tx:"

**`notifyClose()`** (lines ~462-469):
- "🔒 **Ditutup** PAIR" / "PnL:"

**`notifySwap()`** (lines ~471-478):
- "🔄 **Swap** IN → OUT" / "Masuk: X | Keluar: Y" / "Tx:"

**`notifyOutOfRange()`** (lines ~480-486):
- "⚠️ **Di Luar Range** PAIR" / "Sudah OOR selama X menit"

**`BOT_COMMANDS` array** (lines ~391-410):
- 19 command descriptions matching the `/help` text

### `briefing.js` (4 strings, line 32-58)

- "☀️ **Briefing Pagi** (24 jam terakhir)"
- "Aktivitas:" / "Posisi Dibuka" / "Posisi Ditutup"
- "Performa:" / "Net PnL" / "Fee Didapat" / "Win Rate (24j)"
- "Pelajaran Didapat:" / "Tidak ada pelajaran baru semalam."
- "Portfolio Saat Ini:" / "Posisi Terbuka" / "PnL Seumur Hidup"

## Things That Stayed English (by design)

- **Pool names and tickers** (SPCX-SOL, ZINC-SOL, etc.) — translating would create ambiguity
- **Numbers and percentages** — universal
- **Solana wallet addresses and tx hashes** — cryptographic, never translate
- **Tool names** (deploy_position, get_pool_detail, etc.) — these are code identifiers
- **Technical abbreviations** (PnL, TVL, OOR, SOL) — universally understood in crypto community
- **JSON field names in tool calls** — must match what the LLM sends to the tool executor

## Reusable i18n Pattern (for future sessions)

When asked to change bot language (Indonesian, Spanish, Japanese, etc.) for any bot:

1. **Prompt first** — inject a LANGUAGE RULE constant at the top of `buildSystemPrompt()` and reference it in all branches. LLM does the heavy lifting for generated text.
2. **Static next** — find all hardcoded English strings in command handlers/format functions/notif builders. Grep for English words: "Closed", "Open", "Error", "Deployed", "Swapped", "Pool", "Strategy", "Config", "Deploy", "Top", "Latest", "No ".
3. **Menu/commands** — if the bot has a `BOT_COMMANDS` array, that's user-facing in the Telegram `/` menu. Must match.
4. **Verify** — run the check script, restart PM2, send a `/help` and a `/positions` to confirm.

The check script lives at `scripts/check-english-strings.sh` and greps for the most common English phrases that slip through.

## Verification After Conversion (commands run)

```bash
# Syntax check all modified files
cd ~/mona-workspace/meridian
for f in index.js prompt.js telegram.js briefing.js; do
  node --check "$f" && echo "OK: $f"
done
# -> OK: index.js / OK: prompt.js / OK: telegram.js / OK: briefing.js

# Verify LANGUAGE RULE is in prompt.js
grep -c "BAHASA INDONESIA" prompt.js
# -> 1

# Count Indonesian strings per file
for f in index.js prompt.js telegram.js briefing.js; do
  echo "$f: $(grep -c -iE "Perintah|Tidak ada|Wallet:|Posisi|Harga|Strategi|Berhasil|Ditutup|Di Luar|Menutup|Cakupan|Snapshot|Tidak valid" "$f")"
done
# -> index.js: 43 / prompt.js: 1 / telegram.js: 13 / briefing.js: 4

# Restart PM2
pm2 restart meridian

# Wait ~30s for bot to start, then send test commands
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_ALLOWED_USER_IDS}" \
  -d "text=/help@DinoCantik_Bot" > /dev/null
```

## Notes for Future Maintenance

- **If you add a new command handler** in `index.js`, write labels in Indonesian. The check script catches the most common patterns.
- **If you add a new notify function** in `telegram.js`, follow the same pattern as the existing 4 functions. Update `BOT_COMMANDS` if the notification is command-triggered.
- **If you add a new agent role** in `buildSystemPrompt()`, prepend `${languageRule}`. Without it, the LLM will respond in English for that role only.
- **The `languageRule` text itself is in English** (it has to be — the LLM understands English instructions and the rule tells the LLM what to do). Do not translate the rule text.

## Sample Indonesian Output After Conversion

```
/positions response:
📊 Posisi Terbuka (0)
Tidak ada posisi terbuka.

/wallet response:
Wallet: 0 SOL ($0)
Harga SOL: $150
Posisi terbuka: 0/3
Jumlah deploy berikutnya: 1 SOL
Dry run: ya
HiveMind: mati

Deploy notification:
✅ Berhasil Deploy SPCX-SOL
Jumlah: 1 SOL
Range harga: 0.01242 – 0.01964
Cakupan range: 36.73% downside | 0% upside | 58.05% total
Bin step: 80  |  Base fee: 1%
Posisi: 6Xm1ezt3...
Tx: 4UeLCRqAB3m1K...

Morning briefing:
☀️ Briefing Pagi (24 jam terakhir)
────────────────
Aktivitas:
📥 Posisi Dibuka: 0
📤 Posisi Ditutup: 1

Performa:
💰 Net PnL: +$0.03
💎 Fee Didapat: $0.01
📈 Win Rate (24j): 100%

Pelajaran Didapat:
• Tidak ada pelajaran baru semalam.

Portfolio Saat Ini:
📂 Posisi Terbuka: 0
📊 PnL Seumur Hidup: $0.03 (100% win)
────────────────
```
