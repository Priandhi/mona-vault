# 2026-06-22 — TUNING MODE + DAILY REPORT (YUNA)

## Task
Hexa request: "kan niat nya ini cari settingan yang pas agar bisa di perbaiki kalau minus, biar kalau udah live di mainnet udah bagus"
→ Convert PROJECT VIOLET into SETTING TUNING GROUND.
→ Build daily tuning report aggregator.

## Result

### Phase 1: Expand scan universe
- `engine/data.py` — added `get_all_usdt_pairs(min_volume_usd)` (filter by volume)
- `config/settings.py` — added `SCAN_MODE` (curated/volume/all), `MIN_VOLUME_USD`, `TOP_N_VOLUME`, `TOP_PAIRS` (30 curated)
- `run_cron.py` — added `get_scan_symbols(data)` function
- `SCAN_MODE = "volume"` (50 pairs by 24h volume $10M+)
- Scan interval: 15min → 5min (more data points)

### Phase 2: Log ALL signals (tuning data)
- `run_cron.py` — added `log_signal(signal, result, symbol, executed)` 
- Two log kinds: "signal" (tradeable) + "result" (non-tradeable, for tuning)
- `LOG_ALL_SIGNALS = True` in settings.py
- `SIGNALS_LOG_PATH = ~/project-violet/data/signals.jsonl`

### Phase 3: Cron updates
- `yuna-violet-scan`: schedule */15 → */5 (matches new interval)
- PM2 ecosystem: cron_restart */15 → */5
- New cron `yuna-tuning-daily`: schedule `0 23 * * *` (daily 23:00 UTC)

### Phase 4: Tuning report script
- `/home/ubuntu/project-violet/tuning_report.py` — main aggregator
- `~/.hermes/profiles/yuna/scripts/yuna_tuning_report.py` — wrapper
- Sends to Telegram via YUNA bot on `--send-telegram`
- Aggregates: total scans, grade distribution, missed requirements, close-to-tradeable pairs, balance, positions, suggestions

## Verified
- 196 scans in 1 hour (50 pairs × 4 cycles)
- All 100% FAIL (market sideways, no setups)
- Report sent to Telegram successfully
- Daily cron registered

## Decisions
- **`volume` mode (50 pairs) over `all` (497)** — most testnet-junk pairs have no real price action
- **Log FAILs with missed[]** — tuning needs to see WHY setups fail, not just count them
- **5-min interval** — 4× more data per hour, helps tune faster
- **Daily 23:00 UTC report** — Hexa gets summary at end of day

## Tuning Loop
1. Data flows into signals.jsonl (5-min cycles, 50 pairs)
2. Daily 23:00 UTC report → Telegram (auto)
3. Hexa /tuning on demand → fresh report
4. Suggestions in report point to filter adjustments
5. Iterate: tweak MIN_SCORE / MIN_RR / filter rules
6. When WR > 60% on testnet → port to mainnet

## Files Created/Modified
- `/home/ubuntu/project-violet/engine/data.py` (get_all_usdt_pairs)
- `/home/ubuntu/project-violet/config/settings.py` (SCAN_MODE, log paths)
- `/home/ubuntu/project-violet/run_cron.py` (get_scan_symbols, log_signal)
- `/home/ubuntu/project-violet/ecosystem.config.json` (cron_restart */5)
- `/home/ubuntu/project-violet/tuning_report.py` (NEW)
- `/home/ubuntu/.hermes/profiles/yuna/scripts/yuna_tuning_report.py` (NEW)
- `/home/ubuntu/.hermes/profiles/yuna/cron/jobs.json` (yuna-tuning-daily)

## Next Steps
1. Let data accumulate (24-48h for meaningful patterns)
2. Identify top missed requirements → relax filter
3. Watch for first tradeable signals
4. Build WR/PnL tracker when trades happen
5. After 30+ trades, evaluate if settings are ready for mainnet

## Status
✅ DONE — tuning mode active, daily report scheduled, on-demand via /tuning
