# RPC Rate Limiting for @solana/web3.js 429 Errors

## Problem

The `@solana/web3.js` Connection class has a built-in HTTP retry loop that fires 429 retries with 500ms-1000ms delays. This generates spam 429 messages that LOOK like Helius rate limits but are actually the SDK retrying its own requests.

**Verified root cause (Jun8 2026):** Testing 50 rapid requests directly to Helius returned 200 OK for ALL 50. Helius free tier handles burst traffic fine. The 429s come from `@solana/web3.js/lib/index.cjs.js:5073`.

**Misleading error format:**
```
Server responded with 429 Too Many Requests. Retrying after 500ms delay...
```
Source: `node_modules/@solana/web3.js/lib/index.cjs.js:5073` (NOT Helius)

## PRIMARY FIX: disableRetryOnRateLimit

The single most effective fix — eliminates ALL 429 spam:

```javascript
_connection = new Connection(process.env.RPC_URL, {
  commitment: "confirmed",
  disableRetryOnRateLimit: true,  // Stop @solana/web3.js from retrying 429s
});
```

Apply in BOTH `tools/dlmm.js` and `tools/wallet.js`. Verified: 24+ 429s → 0 after this change.

**Why it works:** The Connection constructor accepts an options object. `disableRetryOnRateLimit` tells the SDK to break out of the retry loop immediately on 429 instead of retrying with exponential backoff. The 429 status is passed through as an error that our own retry logic (in agent.js) can handle with proper delays.

## SECONDARY: Rate-Limited Connection Wrapper

Reduce total RPC call volume as a defense-in-depth measure (not the primary fix):

```javascript
let _rpcQueue = [];
let _rpcProcessing = false;
const RPC_MIN_INTERVAL_MS = 200; // 200ms between calls = 5/sec

async function _processRpcQueue() {
  if (_rpcProcessing) return;
  _rpcProcessing = true;
  while (_rpcQueue.length > 0) {
    const { fn, resolve, reject } = _rpcQueue.shift();
    try {
      const result = await fn();
      resolve(result);
    } catch (e) {
      reject(e);
    }
    if (_rpcQueue.length > 0) {
      await new Promise(r => setTimeout(r, RPC_MIN_INTERVAL_MS));
    }
  }
  _rpcProcessing = false;
}

function rateLimitedRpc(fn) {
  return new Promise((resolve, reject) => {
    _rpcQueue.push({ fn, resolve, reject });
    _processRpcQueue();
  });
}
```

### Full getConnection() pattern (both files)

```javascript
function getConnection() {
  if (!_connection) {
    _connection = new Connection(process.env.RPC_URL, {
      commitment: "confirmed",
      disableRetryOnRateLimit: true,  // PRIMARY fix
    });

    // SECONDARY: rate limit wrapper
    const orig = {
      getAccountInfo: _connection.getAccountInfo.bind(_connection),
      getMultipleAccountsInfo: _connection.getMultipleAccountsInfo.bind(_connection),
      getParsedAccountInfo: _connection.getParsedAccountInfo.bind(_connection),
      getProgramAccounts: _connection.getProgramAccounts.bind(_connection),
    };

    _connection.getAccountInfo = (...a) => rateLimitedRpc(() => orig.getAccountInfo(...a));
    _connection.getMultipleAccountsInfo = (...a) => rateLimitedRpc(() => orig.getMultipleAccountsInfo(...a));
    _connection.getParsedAccountInfo = (...a) => rateLimitedRpc(() => orig.getParsedAccountInfo(...a));
    _connection.getProgramAccounts = (...a) => rateLimitedRpc(() => orig.getProgramAccounts(...a));
  }
  return _connection;
}
```

For `tools/wallet.js`, also wrap:
- `getBalance`
- `getParsedTokenAccountsByOwner`

### Each file needs its OWN queue

`tools/dlmm.js` and `tools/wallet.js` each create their own Connection instance. Each file needs its own `_rpcQueue` and `_processRpcQueue`. Combined rate: 10 req/sec (5 per file).

## Background Poller Reductions (index.js)

Beyond the Connection wrapper, reduce background RPC calls in `index.js`:

### PnL Poll Interval (30s → 120s)

Line ~848 in index.js: `}, 30_000);` — change to `}, 120_000);`

This is the lightweight PnL poller that runs between management cycles. At 30s with 3 open positions, it makes 3-6 RPC calls every 30 seconds. At 120s, it's 4x less load.

### Peak/Trailing Confirmation Delays (15s → 60s)

Lines ~93-95 in index.js:
```javascript
const TRAILING_PEAK_CONFIRM_DELAY_MS = 15_000;  // change to 60_000
const TRAILING_DROP_CONFIRM_DELAY_MS = 15_000;  // change to 60_000
```

These timers trigger additional RPC calls to confirm PnL peaks. At 15s, a rapidly moving position can trigger 4+ confirmations per minute. At 60s, it's 1 max.

### Cycle Intervals (user-config.json)

For Helius free tier, use conservative intervals:
```json
{
  "managementIntervalMin": 15,
  "screeningIntervalMin": 60,
  "healthCheckIntervalMin": 120
}
```

The DRY RUN optimization table in SKILL.md uses aggressive intervals (3m/10m) — those are for data collection only and WILL cause 429 storms on free tier Helius.

## Helius Rate Limits

| Tier | Requests/sec | Requests/day |
|------|-------------|-------------|
| Free | ~10 | 100,000 |
| Developer | ~50 | 1,000,000 |
| Business | ~200 | 10,000,000 |

For a 0.364 SOL wallet running DRY RUN, free tier is sufficient if rate-limited. Going LIVE with multiple positions may need Developer tier.

## Alternative: Custom RPC Headers

Helius supports `x-helius-rate-limit` header for priority queuing, but this requires a paid plan. For free tier, the rate-limited queue is the only reliable solution.
