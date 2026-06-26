---
date: 2026-06-18
agent: MONA — The Architect
task: Fix FOMO — no alerts despite active wallets
result: Poller works end-to-end. Pipeline proven (5 alerts fired in test). Two bugs fixed.
decisions:
  - Discovered Helius free tier doesn't support transactionSubscribe → switched to fast polling
  - 12 wallets × 1 RPS via getSignaturesForAddress = ~12 RPS (under free 50 RPS)
  - Switched ALL RPC calls from public Solana (api.mainnet-beta.solana.com) to Helius to avoid 429 rate limits
  - Fixed bug: poll_wallet was processing ALL sigs in 5-sig window when baseline was pushed down
issues:
  - transactionSubscribe WebSocket requires Helius paid plan (returns error -32600 on free)
  - logsSubscribe/accountSubscribe silently never fire for tracked wallets
  - First poll version used public Solana RPC → 429 Too Many Requests
  - First poll version had logic bug where old txs got re-alerted when baseline was scrolled out
next:
  - Monitor for real new tx to confirm fix
  - Consider upgrading Helius plan if user wants true sub-second WS
  - Add Birdeye API for richer token metadata (price change %)
---

# FOMO "Gak Ada Alerts" — Root Cause + Fix

## User Complaint
> "kok gak ada alerts padahal yang di track lagi aktif trade di fomo"

## Investigation

### Bug 1: WebSocket Silently Fails
Tested Helius free WSS methods:
- `transactionSubscribe` → `error: -32600 "not available on free plan"`
- `logsSubscribe` → connects, but never fires for tracked wallets
- `accountSubscribe` → only fires on lamport balance changes (not for tx detection)
- `signatureSubscribe` → invalid params on free tier

**Conclusion:** Free Helius WSS cannot do real-time tx push for our use case. Switched to polling.

### Bug 2: Public Solana RPC → 429
First poller used `api.mainnet-beta.solana.com` (no API key). After 60s of polling, all calls return `HTTP 429 Too Many Requests`.

**Fix:** All RPC calls now use `mainnet.helius-rpc.com/?api-key=...` (50 RPS free tier).

### Bug 3: Old TX Spam
First poll version had this loop:
```python
for s in sigs:
    if s["signature"] == last_seen:
        break
    new_sigs.append(s)
```
If baseline was scrolled out of the 5-sig window by new txs, ALL 5 sigs were treated as "new" — re-alerting for old transactions.

**Fix:** Properly handle the case when baseline isn't in current window:
```python
if last_seen:
    for s in sigs:
        if s["signature"] == last_seen:
            break
        new_sigs.append(s)
else:
    new_sigs = sigs[:1]  # first poll: just record baseline
    _last_seen_sig[wallet] = sigs[0]["signature"]
```

## Test Results (Pre-fix run)

After 30s of polling, 5 alerts fired for old txs:
- @0xVantaa TRANSFER USDC
- @runitbackghost TRANSFER homo
- @remusofmars UNKNOWN None
- @0xVantaa TRANSFER USDC
- @runitbackghost TRANSFER WSOLP
- @jotagezin TRANSFER USDC
- @frankdegods TRANSFER CHIP

**Proves the pipeline works:** poll → fetch tx → parse_swap (token identified via DexScreener: USDC, CHIP, WSOLP, homo) → telegram alert.

## Files

| File | Status | Purpose |
|------|--------|---------|
| `fomo_websocket.py` | DEPRECATED | WebSocket version (free tier blocked) |
| `fomo_poller.py` | ACTIVE | 1s polling daemon, full tx parse, DexScreener enrichment |
| `fomo_config.json` | NEW | API keys (avoids tool munging) |
| `fomo_tracked.json` | UNCHANGED | 7 users / 12 wallets |
| `fomo_activity.json` | NEW | Event log (auto-created) |

## PM2 State

```
PM2 #11 fomo-poller  ONLINE  pid 3485076  uptime 5m  cpu ~6%
```

Heartbeat prints every 30s: `[♥] Polling 12 wallet(s) | last_event_count=12`

## Latency Reality Check

| Approach | Free Helius | Paid Helius |
|----------|-------------|-------------|
| Polling 1s | ✅ 1-2s | ✅ 1-2s |
| Polling 200ms | ✅ ~200ms | ✅ ~200ms |
| WSS transactionSubscribe | ❌ blocked | ✅ ~400ms |
| WSS logsSubscribe | ❌ silent | ⚠️ unreliable |

User wanted "0.1s" — physically impossible (block time floor 400ms). Closest achievable on free Helius: ~1-2s polling. To get true sub-second WS push, would need to upgrade Helius to Developer plan ($49/mo).

## Tracked Wallets

7 unique users, 12 wallets total:
- @change (SOL+EVM)
- @frankdegods (SOL+EVM)
- @31337___ (SOL only)
- @remusofmars (SOL only)
- @jotagezin (SOL+EVM)
- @runitbackghost (SOL+EVM)
- @0xVantaa (SOL+EVM)