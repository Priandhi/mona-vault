# Meridian Position Lifecycle & PnL Management

## How positions are created, monitored, and closed

### Deploy flow
1. Screener finds candidates → LLM picks best → `deploy_position` tool
2. Safety checks in `executor.js`: bin step range, position count, duplicate pool/token, SOL balance
3. Single-side SOL only (`amount_y`, `amount_x=0`)
4. `trackPosition()` in state.js → Telegram notifyDeploy

### Management cycle (every 5m)
Runs deterministic checks BEFORE LLM reasoning:

```
getMyPositions() → snapshot → PnL check → trailing TP → deterministic rules → LLM (if needed)
```

### Deterministic close rules (no LLM, priority order)

Defined in `getDeterministicCloseRule()` in `index.js`:

| Rule | Trigger | Reason |
|------|---------|--------|
| 1 | `pnl_pct <= stopLossPct` (-30%) | Stop loss — hard exit, no LLM |
| 2 | `pnl_pct >= takeProfitPct` (+8%) | Take profit — hard exit, no LLM |
| 3 | `active_bin > upper_bin + outOfRangeBinsToClose` (10 bins) | Pumped far above range |
| 4 | `active_bin > upper_bin` AND `minutes_out_of_range >= outOfRangeWaitMinutes` (20m) | Out of range too long |
| 5 | `fee_per_tvl_24h < minFeePerTvl24h` (5%) AND `age_minutes >= 60` | Low yield — pool dying |

**Suspect PnL guard**: If `pnl_pct < -90%` but position still has USD value > $0.01, rules 1-2 are skipped (likely data error).

### Trailing take profit mechanism

Two-phase system with confirmation delays:

1. **Peak tracking** (`queuePeakConfirmation`):
   - When PnL reaches `trailingTriggerPct` (5%), start tracking peak PnL
   - Confirmation delay: 15 seconds (rechecks to prevent false peaks)
   - Tolerance: 85% of peak value

2. **Drop detection** (`queueTrailingDropConfirmation`):
   - When PnL drops `trailingDropPct` (2%) from peak → potential exit signal
   - Confirmation delay: 15 seconds (rechecks to prevent false drops)
   - Tolerance: 1.0% absolute

3. **Exit**: On confirmed drop → `TRAILING_TP` exit reason → `close_position`

**Example flow:**
```
PnL: +3% → +5% (trailing activates!) → +7% (peak tracked) → +5% (drop 2% from peak)
→ 15s confirmation → still +5%? → CLOSE ✅
```

### Claim rules
- `unclaimed_fees_usd >= minClaimAmount` ($3) → CLAIM action
- After close: auto-swap base tokens to SOL (mandatory if token worth >= $0.10)

### Monitoring commands

**Telegram (in topic):**
- `/positions` — list with progress bar `[████████░░░░░░░░░░░░] 40%`
- `/close <n>` — close by index
- `/set <n> <note>` — add instruction (e.g. "close at 5% profit")

**CLI:**
```bash
node cli.js positions       # list open positions
node cli.js pnl <address>   # detailed PnL for one position
node cli.js balance         # wallet SOL + tokens
node cli.js lessons         # learned lessons from past trades
```

### Telegram notifications (all go to topic 947)

| Event | Format |
|-------|--------|
| Deploy | `✅ Deployed [pair] — [amount] SOL` + price range, coverage, bin step |
| Close | `🔒 Closed [pair] — PnL: +/- $X.XX (+/-X%)` |
| Swap | `🔄 Swapped [token] → SOL` + amount in/out |
| OOR | `⚠️ Out of Range [pair] — X minutes` |
| Screening | Live message (updated in-place as cycle progresses) |
| Management | Cycle report with position status |

### Pool memory & lessons
- `pool-memory.json` — per-pool deploy history, snapshots, cooldowns
- `lessons.json` — auto-derived from closed positions, injected into LLM prompt
- `signal-weights.json` — 13 signals, Darwinian evolution every 5 closes
- Auto-cooldown: 3x OOR close → 12h cooldown on that pool
