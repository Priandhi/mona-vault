# Screening.js — Claude Code Analysis & Fixes (Jun 2026)

## Analysis Method
Used Claude Code CLI (MiMo API) to analyze `tools/screening.js` for bugs causing 0% deploy rate and good candidates being rejected.

## Critical Bugs Found & Fixed

### 1. Volatility = 0 Rejected Too Aggressively (Line 47-49)
**Problem:**
```javascript
function isUsableVolatility(value) {
  const n = Number(value);
  return Number.isFinite(n) && n > 0;
}
```
- Token baru dengan volatility = 0 (belum ada data) ditolak
- Pool baru listing, data belum tersedia → auto-reject
- Token baru bagus ter-reject

**Fix:**
```javascript
// Before
return Number.isFinite(n) && n > 0;

// After
return Number.isFinite(n) && n >= 0;
```

**Impact:** Token baru bisa masuk screening, tidak ter-reject karena data missing.

### 2. Organic Score Null = Auto-Reject (Line 120-125)
**Problem:**
```javascript
if (baseOrganic == null || baseOrganic < s.minOrganic) {
  return `base organic ${baseOrganic ?? "unknown"} below minOrganic ${s.minOrganic}`;
}
if (quoteOrganic == null || quoteOrganic < s.minQuoteOrganic) {
  return `quote organic ${quoteOrganic ?? "unknown"} below minQuoteOrganic ${s.minQuoteOrganic}`;
}
```
- SOL/USDC tidak punya organic score di API → auto-reject
- Token baru belum ada data organic → auto-reject
- Pool legit ter-reject karena data missing

**Fix:**
```javascript
// Before
if (baseOrganic == null || baseOrganic < s.minOrganic) {
  return `base organic ${baseOrganic ?? "unknown"} below minOrganic ${s.minOrganic}`;
}
if (quoteOrganic == null || quoteOrganic < s.minQuoteOrganic) {
  return `quote organic ${quoteOrganic ?? "unknown"} below minQuoteOrganic ${s.minQuoteOrganic}`;
}

// After
if (baseOrganic != null && baseOrganic < s.minOrganic) {
  return `base organic ${baseOrganic} below minOrganic ${s.minOrganic}`;
}
if (quoteOrganic != null && quoteOrganic < s.minQuoteOrganic) {
  return `quote organic ${quoteOrganic} below minQuoteOrganic ${s.minQuoteOrganic}`;
}
```

**Impact:** Pool legit tidak ter-reject karena data missing.

### 3. Double Filtering (Redundant Checks)
**Problem:**
- Filter yang sama di-apply di dua tempat: `discoverPools()` dan `getTopCandidates()`
- TVL, fee_active_tvl_ratio, volatility dicek di kedua tempat
- Redundant dan bisa jadi sumber bug kalau salah satu diubah

**Status:** Not fixed yet (low priority, no impact on functionality)

### 4. PVP Filter Terlalu Agresif (Symbol Matching)
**Problem:**
- `enrichPvpRisk()` mencari rival berdasarkan **symbol** (nama token), bukan mint address
- Token dengan symbol yang sama (misalnya "DOGE", "PEPE") bisa di-flag sebagai PVP rival
- Padahal itu project yang benar-benar berbeda

**Status:** Not fixed yet (low priority, only affects when `blockPvpSymbols` is active)

## Additional Issues Found (Not Fixed Yet)

### 5. `condensePool` Kehilangan Data Penting
- `condensePool()` membuang banyak field dari API response mentah
- Filter di `getTopCandidates()` beroperasi pada condensed pools
- Risk: kalau field naming di API berubah antara raw dan condensed, filter bisa miss

### 6. Volatility Timeframe Override Bisa Turunkan Volume
- `applyVolatilityTimeframe()` meng-overwrite `pool.volume` dengan nilai dari timeframe yang lebih panjang
- Kalau pool aktif di 5m tapi volumenya turun di 30m, volume yang dipakai untuk filtering jadi lebih rendah

## Expected Improvements
- Token baru bisa masuk screening (volatility 0 accepted)
- Pool legit tidak ter-reject (organic score null accepted)
- More candidates tersedia
- Deploy rate diharapkan naik dari 0% ke >10%

## Monitoring
Cek malam nanti (21:00) untuk melihat impact:
- Screening results
- Deploy rate
- Candidate quality
- Rejection reasons

## References
- File: `tools/screening.js`
- Config: `user-config.json` → screening section
- Claude Code analysis: "Apa masalah di screening.js yang bisa menyebabkan screening terlalu ketat dan posisi sering OOR?"
