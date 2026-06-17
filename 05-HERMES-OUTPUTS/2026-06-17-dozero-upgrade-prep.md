# YUNA Receipt — 2026-06-17 16:30 — Dozero Upgrade Prep

**Task:** Backup current dozero engine before upgrade + stop PM2
**Result:** ✅ Backup created, PM2 stopped, ready to receive new files

## Actions
1. **Stopped PM2 dozero-auto** (id 24) — prevent auto-trade during upgrade
2. **Backed up dozero** to `/home/ubuntu/dozero.backup-20260617-163021`
   - Size: 6.8M, 89 files
   - MD5 verified: auto.py, auto_loop.py, settings.py, executor.py, reconcile.py all match original

## State at Backup
- DEFAULT_LEVERAGE = 20x
- MARGIN_PER_TRADE_USD = $90
- SL_DISTANCE_PCT = 4%
- TP_RR_MULTIPLIERS = [1.0, 2.0, 3.0]
- Liq validation MANDATORY (validate_leverage_sl)
- 1 live position: SYNUSDT LONG (33,272 qty, 20x, $90 margin, entry $0.054170)

## Rollback Command (if needed)
```bash
# Stop dozero-auto PM2
HOME=/home/ubuntu pm2 stop dozero-auto

# Restore from backup
rm -rf /home/ubuntu/dozero
cp -a /home/ubuntu/dozero.backup-20260617-163021 /home/ubuntu/dozero

# Restart
HOME=/home/ubuntu pm2 start /home/ubuntu/dozero/auto_loop.py \
  --name dozero-auto --cwd /home/ubuntu/dozero --interpreter python3

# Verify
HOME=/home/ubuntu pm2 logs dozero-auto --lines 20
```

## Awaiting
- Hexa will send new engine files (unclear if it's full replacement, settings patch, or new strategy)
- Will apply + verify MD5 + restart PM2

**Posisi:** SYNUSDT LONG still open (preserved, not touched)
**PnL:** monitored via PM2 (currently stopped, no auto-execution)
**Result:** ✅ SAFE STATE — backup verified, PM2 stopped, awaiting new files
