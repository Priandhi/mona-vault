Date     : 2026-06-16
Agent    : YUNA — The Strategist
Task     : Fix cron 'yuna-soft-stop' script-not-found error
Posisi   : 0 active (testnet clear)
PnL      : $0 (cron job, no PnL impact)
Result   : Cron job recovered. Next tick 22:57 produced `silent (empty output)` = healthy, no soft-stop triggered.
Decisions:
  - Root cause: YUNA profile's $HOME = /home/ubuntu/.hermes/profiles/yuna/home/, so `~` in cp command expanded to nested path /home/ubuntu/.hermes/profiles/yuna/home/.hermes/profiles/yuna/scripts/yuna_soft_stop.py
  - Cron expects absolute path /home/ubuntu/.hermes/profiles/yuna/scripts/yuna_soft_stop.py (script = filename, resolves under ~/.hermes/profiles/yuna/scripts/)
  - Fix: mv file to correct path + rm -rf nested .hermes + chmod +x
  - Verified by triggering cron run + waiting next auto-tick (22:57) — both healthy
Next     : Watch for next 1-2 cron ticks to ensure no recurrence. If healthy, this is a no-op monitor (silent = no problem).
