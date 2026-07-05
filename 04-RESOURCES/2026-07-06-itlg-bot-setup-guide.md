# Interlink Labs ITLG Auto-Claim Bot — Setup Guide
Belum lengkap? Baca dulu sampai bawah sebelum mulai.

---

## Apa yang Bot Ini Lakukan

- Auto-claim ITLG airdrop tiap 4 jam (sesuai rate Interlink)
- Auto-watch ads buat mining bonus
- Auto-recovery burned tokens (tiket system off-chain)
- Notif Telegram ke forum topic tiap claim/recovery sukses
- Stat counter: Mines, Ads, Recovers, Errors, Uptime
- Human-like jitter (10-120s) biar gak kena ban

---

## Prasyarat

### 1. Akun Interlink Labs
- Download app Interlink di HP
- Register pakai email Gmail (aktif)
- Verify loginId (contoh: `0008811`) + passcode 6 digit (contoh: `030302`)
- Wallet address (EVM) tersambung ke akun (ambil dari app settings)

### 2. VPS / Server
- Linux (Ubuntu 22.04 ke atas recommended)
- Python 3.10+
- Akses root/sudo untuk systemd
- IP publik (bebas, gak perlu WARP/residential)

### 3. Gmail App Password
Karena OTP Interlink sering masuk folder **Spam**, bot harus baca INBOX + Spam. Wajib App Password (16 chars no-space).

### 4. Telegram Bot
- Bikin bot via @BotFather → ambil token
- Buat group/forum, add bot jadi admin dengan izin topik
- Catat chat_id group (contoh: `-1003899936547`)
- Catat topic_id (forum thread, contoh: `10832`)

---

## Langkah 1: Download Bot Code

```bash
git clone https://github.com/feb-frmn/itlg-claim.git ~/itlg-claim
cd ~/itlg-claim
```

> Repo asli: feb-frmn/itlg-claim. Tapi ada 3 bug yang harus di-patch (lihat Langkah 4).

---

## Langkah 2: Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install requests
deactivate
```

---

## Langkah 3: Config.json

Bikin `~/itlg-claim/config.json`:

```json
{
  "loginId": "0008811",
  "passcode": "030302",
  "email": "email.kamu@gmail.com",
  "imapPassword": "abcd efgh ijkl mnop",
  "deviceId": "3272b692bfa909d9",
  "tgBotToken": "BOT_TOKEN_DARI_BOTFATHER",
  "tgChatId": "-1003899936547",
  "tgThreadId": 10832
}
```

### Catatan:
- `deviceId`: string hex random bebas (panjang 16+). Generate: `openssl rand -hex 8`
- `imapPassword`: Gmail App Password (16 chars, **spasi diabaikan** atau tulis utuh)
- `tgThreadId`: **wajib** kalau group pakai forum topics. Tanpa ini, notif ke group default bukan topik
- Test bot token: `curl https://api.telegram.org/bot<TOKEN>/getMe`

---

## Langkah 4: Patch 3 Bug Bot

Repo original punya 3 bug yang wajib di-patch:

### Bug 1: OTP folder Spam tidak dibaca

Interlink OTP sering masuk Gmail Spam. Bot original cuma poll INBOX → stuck 120s.

**Fix:** Edit `bot.py`, di function `grab_otp(...)`, ganti `mail.select("inbox")` dengan loop keduanya:

```python
# Sebelum:
mail.select("inbox")
status, data = mail.search(...)

# Sesudah:
for folder in ["inbox", "[Gmail]/Spam"]:
    try:
        mail.select(folder)
        status, data = mail.search(...)
        if status == "OK" and data[0]:
            # break setelah dapat OTP di folder manapun
            break
    except Exception:
        continue
```

### Bug 2: tgThreadId tidak dikirim

Bot original kirim notifikasi hanya ke `chat_id`. Untuk grup forum, perlu `message_thread_id` di payload.

**Fix:** Edit `send_telegram_notif(...)` di `bot.py`:

```python
payload = {"chat_id": chat_id, "text": text}
if thread_id:
    payload["message_thread_id"] = int(thread_id)
```

Patch sama juga di `send_recovery_notif(...)`. Pastikan `tgThreadId` ada di `config.json`.

### Bug 3: Recovery tiket tidak di-claim

Bot original tidak ada endpoint recovery (`/recovery/claim`) untuk recover burned tokens. Ini perlu ditambahkan.

**Fix:** Tambah function baru di `bot.py`:

```python
def get_recovery_next_cycle(token, device_id):
    """Return claimCycles (list of transactionIds ready to recover right now)."""
    r = api_get("/recovery/total-recoverable-next-cycle", token, device_id)
    d = safe_json(r)
    if d.get("statusCode") == 200:
        return d.get("data", {}).get("claimCycles", []) or []
    return []

def claim_recovery(token, device_id, transaction_id):
    """POST /recovery/claim for one burn transaction ticket."""
    r = api_post("/recovery/claim", {"transactionId": transaction_id}, token=token, device_id=device_id)
    return safe_json(r)

def send_recovery_notif(cfg, recovered, balance_after):
    """Send Telegram notification about successful burn recovery."""
    bot_token = cfg.get("tgBotToken")
    chat_id = cfg.get("tgChatId")
    thread_id = cfg.get("tgThreadId")
    if not bot_token or not chat_id:
        return
    from datetime import datetime
    now = datetime.now().strftime("%H:%M:%S")
    text = (
        f"♻️ ITLG Recovery Success\n\n"
        f"💎 Recovered: +{recovered} ITLG\n"
        f"📊 New Balance: {balance_after} ITLG\n"
        f"🕐 {now}\n\n"
        f"Next recovery window: next cycle reset."
    )
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if thread_id:
        payload["message_thread_id"] = int(thread_id)
    try:
        requests.post(url, json=payload, timeout=10, verify=False)
    except Exception:
        pass

def check_and_recover(cfg, token):
    """Check for available recovery tickets. If any, claim them."""
    device_id = cfg["deviceId"]
    total_recovered = 0
    try:
        claim_cycles = get_recovery_next_cycle(token, device_id)
    except Exception as e:
        return token, 0
    if not claim_cycles:
        return token, 0
    log("ok", f"Found {len(claim_cycles)} recovery ticket(s) ready to claim!")
    balance_before = get_balance(token, device_id)
    for tx_id in claim_cycles:
        if isinstance(tx_id, dict):
            tx_id = tx_id.get("transactionId") or tx_id.get("_id")
        if not tx_id:
            continue
        log("step", f"Recovering cycle ticket: {tx_id}")
        time.sleep(random.randint(5, 15))
        result = claim_recovery(token, device_id, tx_id)
        status = result.get("statusCode")
        msg = result.get("message", "")
        if status in [200, 201]:
            log("ok", f"✓ Recovery success for {tx_id}")
            total_recovered += 1
        else:
            log("warn", f"Recovery failed ({status}): {msg}")
    if total_recovered > 0:
        time.sleep(2)
        balance_after = get_balance(token, device_id)
        recovered_amount = (balance_after - balance_before) if (balance_before is not None and balance_after is not None) else None
        log("ok", f"🎉 Total recovered: +{recovered_amount} ITLG (new balance: {balance_after})")
        try:
            send_recovery_notif(cfg, recovered_amount, balance_after)
        except Exception:
            pass
        token = get_session(cfg, allow_login=False) or token
    return token, total_recovered
```

Lalu di `run_once()` dan `run_loop()`, panggil `check_and_recover(cfg, token)` sebelum `attempt_claim(cfg, token)`.

### (Opsional) Bug 4: Stat Counter

Supaya notif punya `⛏️ Mines | 📺 Ads | ♻️ Recovers | ❌ Errors | Uptime` kayak bot v5.4:

```python
# Tambah helpers (taruh setelah load_claim_state):
def bump_counter(name, by=1):
    try:
        state = load_claim_state()
        c = state.setdefault("counters", {
            "mines": 0, "ads": 0, "recovers": 0, "errors": 0, "started_at": int(time.time())
        })
        for k in ("mines", "ads", "recovers", "errors", "started_at"):
            c.setdefault(k, 0 if k != "started_at" else int(time.time()))
        c[name] = c.get(name, 0) + by
        state["counters"] = c
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        os.chmod(STATE_FILE, 0o600)
    except Exception:
        pass

def get_counters():
    state = load_claim_state()
    c = state.get("counters", {})
    return {
        "mines": c.get("mines", 0),
        "ads": c.get("ads", 0),
        "recovers": c.get("recovers", 0),
        "errors": c.get("errors", 0),
        "started_at": c.get("started_at", 0),
    }

def format_uptime():
    c = get_counters()
    started = c.get("started_at")
    if not started:
        return "0h 0m"
    delta = int(time.time() - started)
    return f"{delta // 3600}h {(delta % 3600) // 60}m"
```

**Hook points (5 tempat):**

| Lokasi | Tambah | Kapan |
|--------|--------|-------|
| `trigger_ads()` sebelum return retry time | `bump_counter("ads")` (only if `data.data is not False`) | API return valid ad watch |
| `attempt_claim()` setelah `save_claim_state(...)` di status 200 | `bump_counter("mines")` | Claim sukses |
| `attempt_claim()` retry path sukses | `bump_counter("mines")` | Retry sukses |
| `check_and_recover()` di status 200/201 | `bump_counter("recovers")` | Recovery ticket sukses |
| `attempt_claim()` akhir (claim failed) | `bump_counter("errors")` | Claim gagal non-early |

**Tampilan — di `--status` dan notif TG:**
```python
cnt = get_counters()
# Console (--status):
print(f"  📊 Stats:  ⛏️ Mines: {cnt['mines']}  📺 Ads: {cnt['ads']}  ♻️ Recovers: {cnt['recovers']}  ❌ Errors: {cnt['errors']}")
print(f"  ⏱️ Uptime: {format_uptime()}")

# Telegram notif (di akhir text):
stats_line = (
    f"\n──────────\n"
    f"⛏️ Mines: {cnt['mines']}  |  📺 Ads: {cnt['ads']}\n"
    f"♻️ Recovers: {cnt['recovers']}  |  ❌ Errors: {cnt['errors']}\n"
    f"⏱️ Uptime: {format_uptime()}"
)
text = f"...next claim in 4h.{stats_line}"
```

---

## Langkah 5: First Login (OTP)

```bash
cd ~/itlg-claim
./venv/bin/python bot.py --login
```

Bot akan:
1. Send OTP ke email
2. Poll INBOX + Spam selama 120 detik
3. Verify OTP ke Interlink
4. Save `token.json` (access + refresh JWT)

Kalau gagal, cek:
- IMAP credential benar (Gmail App Password, bukan password biasa)
- OTP masuk Spam (patch Bug 1 sudah ada)
- `deviceId` konsisten dengan native app (lihat di `config.json`)

---

## Langkah 6: Test Run

```bash
./venv/bin/python bot.py --status
```

Output-nya kira-kira:
```
╔════════════════════════════════════╗
║   Interlink ITLG — Status          ║
╚════════════════════════════════════╝

  🤖 Bot: ❌ NOT running
  💰 Balance: 74 ITLG
  🎯 Last claim: +0 ITLG (...)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📊 Stats:  ⛏️ Mines: 0  📺 Ads: 0  ♻️ Recovers: 0  ❌ Errors: 0
  ⏱️ Uptime: 0h 0m
```

Single run (sekali jalan):
```bash
./venv/bin/python bot.py --once
```

---

## Langkah 7: Setup systemd Service

Bikin file `/etc/systemd/system/itlg-claim.service` (sudo):

```bash
sudo tee /etc/systemd/system/itlg-claim.service << 'EOF'
[Unit]
Description=Interlink ITLG Auto-Claim Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/itlg-claim
ExecStart=/home/ubuntu/itlg-claim/venv/bin/python /home/ubuntu/itlg-claim/bot.py
Restart=always
RestartSec=60
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable itlg-claim.service
sudo systemctl start itlg-claim.service
sudo systemctl status itlg-claim.service
```

---

## Langkah 8: Cek Logs & Maintenance

### Logs:
```bash
sudo journalctl -u itlg-claim.service -f        # live tail
sudo journalctl -u itlg-claim.service -n 50    # last 50 lines
sudo journalctl -u itlg-claim.service --since "1 hour ago"
```

### Quick status (no sudo needed):
```bash
cd ~/itlg-claim
./venv/bin/python bot.py --status
```

### Filter error log:
```bash
sudo journalctl -u itlg-claim.service -p err
```

### Restart kalau ada masalah:
```bash
sudo systemctl restart itlg-claim.service
```

---

## Troubleshooting

### 1. OTP tidak masuk Gmail setelah `--login`

**Cek IMAP password benar** (App Password 16 chars, ada/hilang spasi):
```bash
./venv/bin/python -c "
import imaplib
m = imaplib.IMAP4_SSL('imap.gmail.com')
m.login('email.kamu@gmail.com', 'abcd efgh ijkl mnop')
m.select('[Gmail]/Spam')  # cek bisa akses Spam
print('IMAP OK')
"
```

Kalau gagal, regenerate App Password di https://myaccount.google.com/apppasswords

### 2. Notif Telegram gak masuk topik

- Verify `tgThreadId` ada di config.json (int, bukan string)
- Verify bot admin di topik (admin rights > post messages)
- Test manual:
  ```bash
  curl "https://api.telegram.org/bot<TOKEN>/sendMessage" \
    -d chat_id="-1003899936547" \
    -d message_thread_id=10832 \
    -d text="test"
  ```

### 3. Bot stuck "Token expired"

Token JWT expire tiap 24 jam. Bot auto-refresh lewat `do_refresh()`. Kalau gagal:
```bash
cd ~/itlg-claim
./venv/bin/python bot.py --login
```

### 4. Bot jalan tapi gak claim

Cek `check_is_claimable` di log:
```
ℹ️ Not claimable. Next in 3h 23m 12s
```

Rate limit Interlink: 4 jam per cycle. Wajar. Tunggu sampai countdown habis.

### 5. Telegram notif format rusak (emoji jadi `?`)

Set locale UTF-8:
```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

Tambah di systemd service:
```
Environment=LANG=en_US.UTF-8
Environment=LC_ALL=en_US.UTF-8
```

### 6. Recovery ticket gak pernah claim

Cek manual endpoint:
```bash
TOKEN=$(jq -r .access ~/itlg-claim/token.json)
curl -H "Authorization: Bearer $TOKEN" \
     -H "deviceId: $(jq -r .deviceId ~/itlg-claim/config.json)" \
     -H "appVersion: 5.0.0" \
     "https://prod.interlinklabs.ai/api/v1/recovery/total-recoverable-next-cycle"
```

Kalau `claimCycles: []` → belum ada tiket buka. Bot akan auto-claim saat ada (dicek tiap 30 menit).

### 7. Start dari awal (reset state)

Hapus `claim_state.json` + `token.json`, login ulang:
```bash
cd ~/itlg-claim
rm claim_state.json token.json
./venv/bin/python bot.py --login
sudo systemctl restart itlg-claim.service
```

---

## Konfigurasi Multi-Akun (Opsional Multiakun)

Bot bisa di-run multi-instance dengan config berbeda:

```
~/itlg-claim-account1/
~/itlg-claim-account2/
~/itlg-claim-account3/
```

Symlink `bot.py` ke tiap dir, ubah `config.json` per akun, bikin systemd service terpisah (`itlg-claim-1.service`, `itlg-claim-2.service`, dst).

**Group Mining** butuh min 3 akun untuk claim-group-mining sukses. Bot temen v5.4 pakai strategi ini untuk naikin claim frequency (3 akun × 4h = ~1h 20m per claim).

---

## Cost & Limit

| Resource | Estimasi |
|----------|----------|
| RAM bot | ~20-30 MB |
| Disk | ~5 MB |
| Per 1 claim (4h) | +75-100 ITLG ke balance |
| Per ad watch | +35-50 ITLG (bonus, 5 frame per session) |
| Recovery per tiket | +N ITLG (varies, depends on burn cycle) |

Interlink rate limit (dari API):
- `nextFrame` cooldown: ~4h
- Ad watch: 5 frame per cycle, 10s retry interval
- Recovery ticket: cycle-based schedule (nextRecoverCycle)

---

## FAQ

**Q: Bot temen v5.4 "Mining 60s" — kenapa kita 4h?**

A: 60s itu kemungkinan label display-nya saja (poll setiap 60s). Actual claim tetap 4h. Untuk rate ~3x lebih cepat, perlu 3 akun + group mining (multiakun, offset claim).

**Q: Apakah butuh VPN/proxy?**

A: Tidak. VPS langsung udah fine. Interlink API gak block IP datacenter.

**Q: Aman untuk akun?**

A: Bot pakai jitter 10-120s sebelum claim (human-like). Gak spam API. Sejauh ini (14 hari aktif) gak ada akun kena ban.

**Q: ITLG bisa di-jual/swap?**

A: ITLG percuma di burning (penurunan saldo tiap gak active). Recovery system bikin bisa recover burn. On-chain transfer belum tersedia (testnet Taj Mahal akses terbatas).

---

##守望相助 — Final备忘

- Jangan kabur `token.json` — berisi JWT access+refresh. Kalau bocor, hijack akun
- Jangan delete `claim_state.json` — counter + history di situ
- Backup `config.json` + `token.json` ke tempat aman (private repo / encrypted storage)
- Kalau Interlink UI berubah → Swagger dan endpoint bisa update → cek `https://prod.interlinklabs.ai/api-docs-json`

Selamat mencoba — kalau ada error, cek `journalctl` dulu sebelum nanya
