# Receipt: Setup Zqya & Liora TWILIGHT COVENANT Gateway

**Task:** Setup Hermes gateway untuk 2 bot baru TWILIGHT COVENANT — Zqya (SWE) & Liora (Research) — pasang SOUL.md, config.yaml, skill assignment, dan aktifkan gateway.

**Date:** 2026-06-30

---

## Result

| Bot | Profile | Topic ID | Model | Gateway Status |
|-----|---------|----------|-------|----------------|
| @Zqya_Ai_Bot | zqya | 8852 | kimchi/deepseek-v4-flash | ✅ active (PID 2045369) |
| @Lioraa_Ai_Bot | liora | 8853 | kimchi/kimi-k2.7 | ✅ active (PID 2045453) |

- SOUL.md Zqya & Liora dipasang ke masing-masing profile dir.
- Telegram config diperbaiki: `allow_from`, `group_allowed_chats`, `allowed_chats`, `allowed_topics`.
- Gateway restart berhasil dan stabil.
- Test kirim pesan ke topic 8852 & 8853 berhasil (message_id 8926 & 8927).

---

## Decisions

1. **SOUL.md mapping fix**: cache documents `doc_1d7a9392b6fb_SOUL.md` isinya LIORA, `doc_9a47a485f3f8_SOUL.md` isinya ZQYA. Saya copy sesuai identitas ke profile masing-masing.
2. **User filter**: default profile pakai `allowed_user_ids`, tapi Hermes adapter membaca `allow_from` dari config. Diubah ke `allow_from: ['1492210461']` agar Mas diizinkan.
3. **Group chat filter**: tambah `group_allowed_chats: '-1003899936547'` agar gateway menerima pesan dari forum group.
4. **Restart pattern**: `hermes --profile <name> gateway restart` setelah config fix, bukan start ulang manual.

---

## Issues

1. **Gateway crash loop awal**: konfigurasi user/topic filter tidak cukup, sehingga gateway tidak memproses pesan. Setelah config fix dan restart, stabil.
2. **getUpdates kosong setelah test pertama**: butuh restart gateway supaya polling pickup kembali.
3. **Syntax error di execute_code saat baca .env**: heredoc/string literal dengan `'***`  redaction pecah; workaround pakai terminal script file.

---

## Next Steps

1. Verifikasi bot merespons dengan persona yang benar saat Mas kirim pesan ke topic 8852/8853 atau DM.
2. Kalau respon tidak sesuai, cek `agent.log` masing-masing untuk model call dan persona load.
3. Assign skills enabled jika belum — skill list per profile sudah diatur di config.yaml (`skills.enabled`).
4. Update kanban kalau Mas ingin task ini di-track.

---

## Verification Commands

```bash
hermes gateway list
systemctl --user status hermes-gateway-zqya.service hermes-gateway-liora.service
```
