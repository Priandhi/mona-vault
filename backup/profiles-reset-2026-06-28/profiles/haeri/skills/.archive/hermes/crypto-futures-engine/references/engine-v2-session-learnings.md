# Engine v2.0 Session Learnings (Jun 8, 2026)

## Integrating External Signal Engines (e.g., DOZERO.X SMC)

When integrating a separate signal engine as a signal source:

1. Import the engine at the top of `signals.py` (not inside the method)
2. Create a wrapper method that converts the external engine's output to `SignalResult`
3. Use `getattr(config, 'weight_X', default)` for the weight so missing config doesn't crash
4. Set a confluence threshold (e.g., 50/100) — don't return signals for weak setups

```python
# At top of signals.py
from dozero_smc_engine import DozeroSMCEngine, Bias as SMCBias

# In SignalEngine class
async def smc_confluence(self, symbol: str) -> SignalResult:
    klines = await self.data.binance_klines(symbol, '1h', 100)
    ohlcv = {
        'open': [float(k[1]) for k in klines],
        'high': [float(k[2]) for k in klines],
        'low': [float(k[3]) for k in klines],
        'close': [float(k[4]) for k in klines],
        'volume': [float(k[5]) for k in klines],
    }
    smc_engine = DozeroSMCEngine({'confluence_threshold': 50, 'swing_lookback': 5})
    setup = smc_engine.full_analysis(symbol, ohlcv, mtf_biases)
    if not setup:
        return SignalResult('SMC', Signal.NEUTRAL, 0, 0, 'No setup (score < 50)')
    score = setup.confluence_score
    if setup.direction == SMCBias.BEARISH:
        score = -score
    return SignalResult('SMC', signal, score, confidence, detail, raw)

# In analyze_symbol gather():
self.smc_confluence(symbol),  # Add to asyncio.gather()

# In weights dict:
'SMC': getattr(config, 'weight_smc', 15),
```

## Scanning Strategy: Pre-filter Before Full Analysis

Running 13 signals × N symbols in `asyncio.gather()` creates a burst of API calls that overwhelms the rate limiter (even at 200/min). Solution: **pre-filter by volume, then full analysis on top N.**

```python
exclude = ['USDCUSDT','BUSDUSDT','TUSDUSDT','FDUSDUSDT','DAIUSDT','USDPUSDT']
pairs = [t for t in data if t['symbol'].endswith('USDT')
         and float(t.get('quoteVolume',0)) > 500000
         and t['symbol'] not in exclude]
pairs.sort(key=lambda x: float(x.get('quoteVolume',0)), reverse=True)
cfg.symbols = [p['symbol'] for p in pairs[:15]]
```

**Why 15, not 100:** Each symbol needs ~12 API calls. 15 × 12 = 180 calls → fits in 200/min rate limit. 100 × 12 = 1200 → 12 min of rate limit waiting.

## Leverage & Margin Sizing (User Preference)

User prefers **high leverage (35-50x) with small margin (~10% of balance)**, NOT low leverage with large margin.

```
❌ WRONG:  Lev 10x, margin $33 (62% of $53 balance)
✅ RIGHT:  Lev 35x, margin $5 (10% of $53 balance)
```

Same $4 risk, but 35x gives 3.5× better ROI per pip. Margin is just collateral — what matters is risk per trade (fixed USD amount).

```python
leverage = 35
risk_usd = balance * 0.02  # 2% = ~$1 on $53
size_usdt = risk_usd / sl_pct
max_notional = balance * leverage * 0.85  # cap at 85%
size_usdt = min(size_usdt, max_notional)
```

## Entry Decision: Consistency > Perfection

User: "entry aja asal lu konsisten gak nyalahin aturan percaya diri lo upgrade skill lo biar pinter"

Rule: Score ≥ 50 = enter. Score < 50 = wait. Don't second-guess the system. The edge comes from CONSISTENT execution, not cherry-picking "best" setups.

## Config Duplicate Field Pitfall

Python dataclass silently overwrites duplicate fields. Always grep after editing:
```bash
grep -n "max_daily_trades" config.py  # Should show exactly 1 line
```

## Adding New Signals to Engine

When adding new signal generators (RSI, Bollinger, Wyckoff, etc.):

1. Add method to `SignalEngine` class in `signals.py`
2. Add to `asyncio.gather()` in `analyze_symbol()`
3. Add weight to config: `weight_X: float = N`
4. Add to weights dict: `'X': getattr(config, 'weight_X', N)`
5. Run backtest to validate: `python3 mona_backtest.py`
6. Check score distribution — new signal should fire on ~20-30% of pairs

```python
# Pattern for adding a new signal:
async def rsi_divergence(self, symbol: str) -> SignalResult:
    klines = await self.data.binance_klines(symbol, '1h', 50)
    # ... calculation ...
    return SignalResult('RSI', signal, score, confidence, detail, raw_data)

# In analyze_symbol gather:
self.rsi_divergence(symbol),  # Add to asyncio.gather()

# In config:
weight_rsi: float = 10

# In weights dict:
'RSI': getattr(config, 'weight_rsi', 10),
```

## Backtest-Validated Signal Weights

After adding RSI (10), Bollinger (8), and Wyckoff (10) signals, engine has 16 total signals. Backtest on 30-day 1H data:

| Pair | Trades | WinRate | PnL | PF | MaxDD |
|------|--------|---------|-----|----|-------|
| SOLUSDT | 25 | 56% | +10.2% | 1.44 | 7.7% |
| BTCUSDT | 27 | 52% | +5.7% | 1.38 | 7.2% |
| ETHUSDT | 27 | 56% | +0.5% | 1.02 | 13.7% |
| ZECUSDT | 17 | 41% | -10.2% | 0.78 | 20.7% |
| HYPEUSDT | 29 | 35% | -17.4% | 0.72 | 24.6% |

**Key finding:** High-volatility altcoins (ATR% > 3%) lose money. Filter them out.

## DXY Signal: Skip Yahoo Finance

Yahoo Finance always returns 429 from VPS. Use CoinGecko directly:
```python
if key == 'DXY':
    cg = await self._get(
        'https://api.coingecko.com/api/v3/simple/price',
        {'ids': 'tether', 'vs_currencies': 'usd', 'include_24hr_change': 'true'},
        cache_key='dxy_cg', ttl=300
    )
```
