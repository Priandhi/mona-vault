Hexa rules: "gas"=execute now no pause/ask. New facts=accept. Same mistake 3x=fix now. "[gass]" without action=lying. Write SOUL.md only with patch(). "jangan muter-muter"=stop repeating failing approach, pivot immediately to alternatives.
§
VPS Hexa (13.211.42.29, AWS): id_ed25519. Bot @Hexa1_Bot. Kimchi API direct. SSH port 22 OPEN + banner timeout = sshd hung (VPS alive) → AWS Console browser SSH or Stop+Start.
§
9Router: :20128 pw:Mona187. Bearer key works. DB: ~/.9router/db/data.sqlite. Keys expire HOURS. **Bare model name (e.g. `mimo-v2.5-pro` no prefix) → 404 default openai provider. Use matching prefix: `xmtp/` for MiMo, `tokenrouter/` for M3.** errorCode field STALE — verify via /api/providers/<id>/test.
§
ICLIX infra: PM2 tunnel-ecosystem.config.js, cloudflared as root. **Tencent SG blocks ALL inbound ports** — only cloudflared egress. Port 80 nginx: /→20128, /vnc/→6080. tunnel-url-watcher PM2 #19 → /tmp/tunnel-watchdog/urls.json + Telegram on URL change.
§
Systemd gateway service on Hexa VPS (13.211.42.29) needs explicit EnvironmentFile directive in service file to load env vars. Token validation succeeds via curl/python but fails in gateway because env vars not in process environment. Service file path: ~/.config/systemd/user/hermes-gateway-hyejin.service
§
**ICLIX visual:** brand #e50914, BY HEXA #fff, bg #000. **Logo:** Navbar "ICLIX" all red. Side menu "IC" yellow + "LIX" red split (don't unify). **Template:** `.info-page` + `.info-block`. **Deploy:** `npm run build` → `pm2 restart iclix-api`. **Social order:** IG→TikTok→X→YouTube. **Verify:** page.evaluate + getComputedStyle, not vision_analyze.
§
**'Cari situs X' = external list, NOT ICLIX feature.** Misread once: user asked 'cari situs Indonesia premium' → I added 🇮🇩 Indo category to ICLIX. They said 'gua gak cari indo'. Lesson: 'situs' = external sites for user to find themselves. ASK before ICLIX integration — don't assume.§
**PNL COMMAND HANDLING:** Saat user mengirim /pnl, /status, atau sekedar "pnl", JANGAN jawab dari pengetahuan sendiri. Jalankan script berikut:
  python3 /home/ubuntu/dozero/send_pnl.py yuna
Script ini akan kirim output langsung ke Telegram dengan format plain text yang bisa di-copy. Jangan diedit atau ditambah apapun.
