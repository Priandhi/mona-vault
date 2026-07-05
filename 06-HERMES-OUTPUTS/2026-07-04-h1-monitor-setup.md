# Receipt: H1 Report Monitor Cron Setup

**Task:** Setup automated monitoring for Wallet on Telegram HackerOne reports  
**Date:** 2026-07-04  
**Time:** ~10 minutes  
**Status:** ✅ COMPLETE

---

## Result

### Deliverables
1. ✅ Monitor script: `/home/ubuntu/.hermes/scripts/h1_report_monitor.py` (6.9KB)
2. ✅ Cron job: `h1-report-monitor` (job_id: 6f0551b0071c)
3. ✅ State file: `/home/ubuntu/bugbounty/wallet-on-telegram/h1_monitor_state.json`
4. ✅ Test run: Successful (3 reports checked, 0 changes on first baseline run)

### Cron Configuration

| Setting | Value |
|---------|-------|
| **Name** | h1-report-monitor |
| **Job ID** | 6f0551b0071c |
| **Schedule** | Every 6 hours (360m) |
| **Repeat** | Forever |
| **Deliver** | local (output saved, Telegram notifications handled internally) |
| **Next Run** | 2026-07-05 05:52 SGT |

### Monitored Reports

| Report # | Title | Severity |
|----------|-------|----------|
| 3842471 | CORS Misconfiguration with Credentials | HIGH |
| 3842475 | Missing Rate Limiting Headers | MEDIUM |
| 3842478 | Internal IP Disclosure | INFO |

### Notification Triggers

Script sends Telegram notification to TWILIGHT COVENANT (topic 8460) when:
- ✅ Status change (unknown → triaged → resolved, etc.)
- ✅ Triaged timestamp set
- ✅ Bounty awarded ($ amount)
- ✅ Severity categorized (low/medium/high/critical)
- ✅ Weakness category assigned
- ✅ Team members view report
- ✅ Team adds internal notes

### How It Works

1. **Baseline run:** Saves current state to `h1_monitor_state.json`
2. **Every 6 hours:** Compares current state vs saved state
3. **If changes detected:** Sends formatted Telegram message with:
   - Report number + title
   - List of changes
   - Link to HackerOne report
4. **State updated:** New state saved for next comparison

---

## Decisions

1. **6-hour interval** — Frequent enough to catch triage quickly, not so frequent to spam
2. **Deliver=local** — No need to log every "no changes" run to chat; only notify on actual changes
3. **Telegram internal** — Script handles notifications directly (not via cron delivery) for real-time alerts
4. **State file per target** — Each bug bounty program gets its own state file

---

## Issues

None — script tested successfully, cron registered, first baseline run complete.

---

## Next Steps

### Automated (Cron)
- [ ] First check: 2026-07-05 05:52 SGT
- [ ] Subsequent: Every 6 hours
- [ ] Notifications: Only on status changes

### Manual (Optional)
- [ ] Check status anytime: `python3 /home/ubuntu/.hermes/scripts/h1_report_monitor.py`
- [ ] View state: `cat /home/ubuntu/bugbounty/wallet-on-telegram/h1_monitor_state.json`
- [ ] Reset baseline: Delete state file, run script manually

### Mas
- [ ] Wait for Telegram notification when team triages reports
- [ ] Expected triage time: 1-7 days (usually 48 hours for active programs)
- [ ] When notified: Review + respond to any team questions ASAP

---

## Files Generated

```
/home/ubuntu/.hermes/scripts/h1_report_monitor.py — Monitor script (6.9KB)
/home/ubuntu/bugbounty/wallet-on-telegram/h1_monitor_state.json — Baseline state
```

---

**Status:** ✅ Monitoring active  
**Next Check:** 2026-07-05 05:52 SGT (~6 hours)  
**Notification Channel:** TWILIGHT COVENANT Telegram (topic 8460)