# Token Filter v2 — Claude Code Analysis & Fixes (Jun 2026)

## Analysis Method
Used Claude Code CLI (MiMo API) to analyze `modules/token-filter.js` for bugs causing 0% win rate during DRY RUN (Jun 8-10: -0.1219 SOL, 15 trades, 0% win rate).

## Critical Bugs Found & Fixed

### 1. Buy Ratio Misleading (Line 178)
**Problem:** `buyRatio = sells > 0 ? buys / sells : 999`
- Token baru tanpa sells → buyRatio = 999
- Quality score formula: `Math.min(999/3, 3) = 3` (max points)
- Token tanpa sell activity dapat skor sempurna → ranking misleading

**Fix:**
```javascript
// Before
const buyRatio = sells > 0 ? buys / sells : 999;

// After
const buyRatio = sells > 0 ? Math.min(buys / sells, 10) : (buys > 0 ? 10 : 0);
```

**Impact:** Quality score lebih akurat, token bagus tidak ter-reject karena misleading data.

### 2. Quality Score Threshold Missing (Line 261)
**Problem:** `return { pass: true, score: Math.max(0, score) }`
- Token dengan score negatif di-clamp ke 0
- Token berkualitas sangat rendah tetap masuk qualifying array
- Tidak ada minimum threshold

**Fix:**
```javascript
// Before
return { pass: true, score: Math.max(0, score), reasons };

// After
const finalScore = Math.max(0, score);
if (finalScore < 2) {
  return { pass: false, score: 0, reason: `quality score ${finalScore.toFixed(1)} < 2 minimum` };
}
return { pass: true, score: finalScore, reasons };
```

**Impact:** Filter lebih selektif, hanya token berkualitas yang lolos.

### 3. Volume Acceleration untuk Token Baru (Line 136)
**Problem:** `volAcceleration = vol24h > 0 ? (vol5m * 288) / vol24h : 0`
- Token baru (< 1 jam) belum punya 24h volume data
- volAcceleration = 0 → langsung reject
- Token baru bagus ter-reject

**Fix:**
```javascript
// Before
const vol24h = sig.volume24h || t.volume24h || 0;
const volAcceleration = vol24h > 0 ? (vol5m * 288) / vol24h : 0;
if (f.minVolAcceleration && volAcceleration < f.minVolAcceleration) {
  return fail(`vol acceleration ${volAcceleration.toFixed(2)}x < ${f.minVolAcceleration}x`);
}

// After
const vol24h = sig.volume24h || t.volume24h || 0;
const ageHours = (sig.ageMs || 0) / 3600000;
if (ageHours > 1) {
  const volAcceleration = vol24h > 0 ? (vol5m * 288) / vol24h : 0;
  if (f.minVolAcceleration && volAcceleration < f.minVolAcceleration) {
    return fail(`vol acceleration ${volAcceleration.toFixed(2)}x < ${f.minVolAcceleration}x`);
  }
}
```

**Impact:** Token baru bisa masuk screening, tidak ter-reject karena data missing.

## Additional Issues Found (Not Fixed Yet)

### 4. `|| 0` pada field yang bisa null
```javascript
const priceChange5m = stats5m.priceChange || 0;
const organicScore = t.organicScore || 0;
const devHoldings = g.devHoldingsPercent || 0;
```
- Kalau API tidak return field, nilainya jadi 0
- `devHoldings = 0` artinya "dev tidak pegang apa-apa" → lolos filter
- Seharusnya reject kalau data tidak tersedia

### 5. Semua layer bersifat AND
- Satu gagal = langsung reject
- Tidak ada "soft fail" atau weighted gate
- Token harus lolos semua layer 1-6 sebelum masuk quality scoring

### 6. Tidak ada minimum quality score threshold (FIXED di #2 di atas)

## Expected Improvements
- Quality score lebih akurat
- Token bagus tidak ter-reject karena misleading data
- Token berkualitas rendah di-filter out
- Win rate diharapkan naik dari 0% ke >30%

## Monitoring
Cek malam nanti (21:00) untuk melihat impact:
- Win rate
- PnL
- Trade count
- Filter pass rate

## References
- File: `modules/token-filter.js`
- Config: `config.json` → `filter` section
- Claude Code analysis: "Apa masalah di token-filter.js yang bisa menyebabkan filter terlalu ketat atau terlalu longgar?"
