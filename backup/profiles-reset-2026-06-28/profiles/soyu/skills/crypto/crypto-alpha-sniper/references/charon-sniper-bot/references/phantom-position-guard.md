# Phantom Position Guard — Reject, Don't Fabricate (Jun 16 2026)

## Problem

The `jupiter-executor.js` `buyToken()` DRY_RUN branch contained a fallback that **fabricated fake token amounts** when both the Jupiter quote AND the Charon `sig.priceUsd` field were unavailable. The fallback computed:

```javascript
// BROKEN (Jun 16):
const outAmount = quote ? Number(quote.outAmount) : (sig?.priceUsd > 0 ? Math.round(solAmount / sig.priceUsd) : Math.round(solAmount * 1e9));
const price = quote ? solAmount / outAmount : (sig?.priceUsd || solAmount / outAmount);
```

For a 0.2 SOL deploy with neither quote nor priceUsd: `outAmount = 0.2 * 1e9 = 200,000,000` and `price = 0.2 / 2e8 = 1e-9`. This is a **completely fabricated position** with:
- `entryPrice ≈ 1e-9` (or 0 if `sig.priceUsd` is also missing)
- `solInvested = 0.2` (the real SOL was already deducted from sim balance)
- `tokenAmount = 200,000,000` (fake)
- `peakPct = 0` (will never move)

These phantom positions:
1. **Block all subsequent buys** with "Max positions reached 3/3" / "Max positions reached 5/5"
2. **Corrupt PnL calculations** (peak never moves, max hold always triggers)
3. **Pollute the traded list** (mints are marked traded even though no real position exists)

## Symptom Variants Observed (Jun 16)

The bug surfaces in three different shapes depending on which fields are present:

| `entryPrice` | `solInvested` | `tokenAmount` | Cause |
|---|---|---|---|
| `0` | `0` | non-zero | quote failed, sig.priceUsd missing |
| `1e-12` | `null` | `65,000,000,000` | same path with random noise |
| `0.0001` | `0` | non-zero | quote returned but sig.priceUsd was used as price without conversion |

All three block the same slot. The cleanup script must check all three.

## Fix — REJECT, Never Fabricate

### 1. `modules/jupiter-executor.js` — REJECT buy when price/quote unavailable

```javascript
// modules/jupiter-executor.js (REPLACE the broken DRY_RUN block)
if (isDry) {
  const quote = await getQuote(SOL_MINT, mint, lamports, config.trade.slippageBps);
  let outAmount, price;
  if (quote) {
    outAmount = Number(quote.outAmount);
    price = solAmount / outAmount;
    log("trade", `[DRY RUN] Would buy ${outAmount} tokens @ $${price.toFixed(12)}`);
  } else if (sig?.priceUsd > 0) {
    outAmount = Math.round(solAmount / sig.priceUsd);
    price = sig.priceUsd;
    log("trade", `[DRY RUN] Quote failed, using Charon price: ${outAmount} tokens @ $${price.toFixed(12)}`);
  } else {
    // No quote AND no price — REJECT to prevent phantom position
    err("trade", `No quote AND no priceUsd for ${mint.slice(0,8)}... — REJECTING (would create phantom)`);
    return { success: false, error: "no_quote_no_price" };
  }
  // Validate to prevent phantom positions
  if (outAmount <= 0 || price <= 0 || !isFinite(outAmount) || !isFinite(price)) {
    err("trade", `Invalid buy result for ${mint.slice(0,8)}: outAmount=${outAmount}, price=${price} — REJECTING`);
    return { success: false, error: "invalid_buy_result" };
  }
  const sb = getSimBalance();
  sb.sol = Math.round((sb.sol - solAmount) * 1000000) / 1000000;
  sb.history.push({ action: "buy", sol: sb.sol, spent: solAmount, token: mint.slice(0, 8), symbol: sig?.symbol });
  saveSimBalance(sb);
  log("sim_balance", `Buy -${solAmount} SOL → balance: ${sb.sol} SOL`);
  return { success: true, txHash: `DRY_${Date.now()}`, amountIn: solAmount, amountOut: outAmount, price, simulated: true };
}
```

### 2. `modules/position-manager.js` — `openPosition()` guard (belt-and-suspenders)

```javascript
// modules/position-manager.js openPosition() — ADD at the top
export function openPosition(sig, buyResult, config) {
  // GUARD: reject phantom positions
  if (!buyResult || buyResult.price <= 0 || buyResult.amountIn <= 0 || buyResult.amountOut <= 0) {
    log("pos", `❌ REFUSED phantom position for ${sig?.symbol || '??'}: price=${buyResult?.price}, in=${buyResult?.amountIn}, out=${buyResult?.amountOut}`);
    return null;
  }
  const data = loadPositions();
  const pos = { /* ... existing position object ... */ };
  data.open.push(pos);
  savePositions(data);
  return pos;
}
```

### 3. `index.js` caller — handle `null` return

```javascript
// index.js (in the buy execution block)
if (buyResult.success) {
  const pos = openPosition(pick, buyResult, config);
  if (!pos) {
    // Phantom position rejected by openPosition guard
    log("trade", `⚠️ ${pick.symbol} phantom rejected — skipping cycle (sim balance will be reconciled next cycle)`);
    _running = false;
    return;  // NOT continue — no surrounding for loop
  }
  pos.qualityScore = pick.qualityScore;
  markTraded(pick.mint);
  _lastBuyTime = Date.now();
  await notifyBuy(pos);
  log("trade", `✅ ${pick.symbol} position opened!`);
}
```

⚠️ **Do NOT use `continue`** — there's no surrounding `for` loop in `runCycle()`. The `for` is on the signal fetch inside `fetchCharonSignals()`, not on the buy execution. Using `continue` here throws `SyntaxError: Illegal continue statement`.

### 4. Cleanup script for existing phantoms

See `scripts/clean-phantom-positions.py`. Run it once to clear existing data, then restart the bot.

```bash
cd ~/mona-workspace/charon-sniper
python3 scripts/clean-phantom-positions.py data/positions.json
# Outputs: "Removed N phantom positions, kept M legitimate"
# Backs up to data/positions.json.backup-<timestamp> automatically
```

Inline one-liner version (if you don't want to use the script):

```bash
python3 << 'EOF'
import json, shutil, sys
fp = "data/positions.json"
shutil.copy(fp, fp + ".backup-phantom-cleanup")
d = json.load(open(fp))
phantoms = [p for p in d['open'] if (p.get('entryPrice', 0) <= 0 or p.get('solInvested') is None or p.get('solInvested', 0) <= 0 or p.get('tokenAmount', 0) <= 0)]
d['open'] = [p for p in d['open'] if p not in phantoms]
print(f"Removed {len(phantoms)} phantoms, kept {len(d['open'])} legitimate")
json.dump(d, open(fp, "w"), indent=2)
EOF
```

## Verification After Fix

1. **Syntax check:** `node --check modules/jupiter-executor.js modules/position-manager.js index.js`
2. **Restart bot:** `cd ~/mona-workspace/charon-sniper && pkill -TERM -f "node.*index.js" && sleep 2 && nohup node index.js > /tmp/charon-sniper.log 2>&1 &`
3. **Watch for "Daily trade limit reached"** on startup if closed list already has 8+ positions — this is correct behavior
4. **No new phantoms:** monitor `data/positions.json` for new entries where `entryPrice <= 0`. If any appear, the guard isn't working.

## Why This Is Better Than The Jun9 Fix

The Jun9 fix (see `references/broken-position-fix.md`) attempted to fix this by passing `sig` (the signal object) to `buyToken()` so the fallback could use `sig.priceUsd`. **That fix is incomplete** because:
1. `sig.priceUsd` is NOT always present (micro-cap tokens often have missing data)
2. When both quote AND priceUsd are missing, the original `Math.round(solAmount * 1e9)` fallback was kept, which is what creates the phantoms
3. The Jun9 fix was reactive (clean up after) rather than preventive (don't create in the first place)

This Jun16 fix is **preventive** — the buy never completes without a real price, so no phantom can be created. Cleanup is only needed for the legacy data that the Jun9 fix didn't catch.
