# Receipt: Debug Zqya & Liora Gateway — Topic/DM Updates Not Received

**Task:** Debug kenapa gateway Zqya & Liora tidak menerima pesan dari Telegram (forum topic 8852/8853 maupun DM), setelah sebelumnya gateway setup berhasil.

**Date:** 2026-06-30

---

## Result

| Bot | Gateway | Config | Admin | Send to Topic | Receive via getUpdates |
|-----|---------|--------|-------|---------------|------------------------|
| Zqya | ✅ running | ✅ allowed_chats/topics | ✅ admin | ✅ yes | ❌ 0 updates |
| Liora | ✅ running | ✅ allowed_chats/topics | ✅ admin | ✅ yes | ❌ 0 updates |

CLI chat identity Zqya **terverifikasi benar** (bukan copy Mona):
> "Saya Zqya, eksekutor teknis di bawah TWILIGHT COVENANT. Operator saya adalah Sayang (Hexa / 0xjosee)"

---

## Decisions

1. **Hapus state.db lama** untuk Zqya & Liora supaya tidak ada session/system prompt stale yang bikin bot merespons sebagai Mona.
2. **Restart gateway** setelah hapus state.db.
3. **Tidak ubah config ke unrestricted** untuk test; tetap pakai allowed_chats/topics karena memang sudah benar.
4. **Verifikasi identitas via CLI chat**, bukan via Telegram polling yang sedang conflict.
5. **Restore config original** setelah test unrestricted tidak mengubah hasil.

---

## Issues

1. **Polling conflict (HTTP 409)** setiap kali curl `getUpdates` dipanggil sambil gateway sedang polling. Ini mempersulit diagnosis dari luar.
2. **getUpdates selalu 0** baik untuk forum topic maupun DM, meski bot bisa kirim pesan.
3. **Bot admin & config benar**, tapi updates tidak terdeliver.
4. **Kemungkinan root cause**:
   - Gateway PTB sedang hold polling session, sehingga curl dari luar tidak dapat updates.
   - Atau ada session polling lain (meski `ps aux` tidak menunjukkan proses lain).
   - Atau butuh cooldown setelah stop gateway sebelum polling baru bisa pickup.
5. **Kesalahan proses:** terlalu banyak tool calls untuk test berulang, sehingga kena limit iterasi Hermes.

---

## Next Steps

1. **Stop gateway zqya + liora**, tunggu 60 detik, start **hanya zqya**.
2. **Mas kirim 1 pesan** di topic 8852 tanpa curl getUpdates dari luar.
3. **Cek log zqya** `tail -f /home/ubuntu/.hermes/profiles/zqya/logs/agent.log`.
4. Kalau Zqya reply, ulangi untuk Liora.
5. Kalau masih tidak reply, periksa `BotFather → Bot Settings → Group Privacy` untuk kedua bot — harus **disabled** agar bot melihat semua pesan grup.
6. Tulis receipt lanjutan setelah verifikasi berhasil.

---

## Verification Commands

```bash
# Stop both
systemctl --user stop hermes-gateway-zqya.service hermes-gateway-liora.service
sleep 60

# Start zqya only
systemctl --user start hermes-gateway-zqya.service

# Watch log
tail -f /home/ubuntu/.hermes/profiles/zqya/logs/agent.log
```

---

## Notes

- Jangan panggil `getUpdates` via curl sambil gateway running — bikin 409 conflict.
- Jangan hapus/ubah config ke unrestricted untuk test — config sudah benar.
- CLI chat identity sudah verified, masalah bukan di SOUL.md.
