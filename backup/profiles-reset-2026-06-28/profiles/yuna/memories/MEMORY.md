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
ICLIX: brand #e50914, BY HEXA #fff, bg #000. Logo: navbar ICLIX all red; side menu "IC" yellow + "LIX" red split. Deploy: `npm run build` → `pm2 restart iclix-api`. Social order: IG→TikTok→X→YouTube.
§
PROJECT VIOLET v2 — Smart Money + Order Flow engine. Path: /home/ubuntu/project-violet/. 20x lev, 4% SL, 1:2/1:3 RR. MTF: Daily→H4→H1→M15. **Execution: LIMIT entry + algo SL/TP via /fapi/v1/algoOrder (algoType=CONDITIONAL, type=STOP_MARKET/TAKE_PROFIT_MARKET, reduceOnly=true) — pre-placed w/o position. Dedup: skip if existing position/pending algos. Precision: floor qty to stepSize. /fapi/v1/order STOP_MARKET reduceOnly FAILS w/o position (-4120). cancel_algo returns code=STRING "200".**
§
YUNA $HOME=/home/ubuntu/.hermes/profiles/yuna/home/ — `~` in cp/mv expands nested. Cron `script:` = bare filename under `~/.hermes/profiles/yuna/scripts/.