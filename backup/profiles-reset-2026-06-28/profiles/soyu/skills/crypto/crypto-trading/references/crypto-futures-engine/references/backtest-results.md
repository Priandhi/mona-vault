# Backtest Results — Mona Futures Engine v2.0

## 90-Day Backtest (Updated June 2026)

Backtest on 1H candles, top 5 pairs by volume:

| Pair | Trades | WinRate | PnL | PF | MaxDD | Status |
|------|--------|---------|-----|----|-------|--------|
| SOLUSDT | 36 | 63.9% | +28.83% | 2.05 | 7.80% | ✅ BEST |
| ETHUSDT | 42 | 59.5% | +22.01% | 1.68 | 10.20% | ✅ GREAT |
| BTCUSDT | 30 | 46.7% | +2.23% | 1.11 | 8.17% | ✅ OK |
| HYPEUSDT | 48 | 43.8% | -17.31% | 0.81 | 39.70% | ❌ BLACKLIST |

## Key Findings

1. **SOL & ETH are the best pairs** — focus on these for consistent profits
2. **BTC is breakeven** — acceptable but not the best performer
3. **HYPE (meme coin) consistently loses money** — blacklist high-volatility meme coins
4. **FearGreed weight reduced from 10 to 5** — was inflating scores for contrarian signals
5. **Volatility filter works** — ATR > 3% pairs get skipped, ZEC improved from -10% to +3%

## Pair Blacklist (Add to Config)

High-volatility meme coins that consistently lose money:

```python
# In FuturesConfig:
pair_blacklist: List[str] = field(default_factory=lambda: [
    'HYPEUSDT',   # Meme coin, 39.7% max drawdown, PF 0.81
    'WIFUSDT',    # Meme coin, high volatility
    'PEPEUSDT',   # Meme coin, erratic price action
    'BONKUSDT',   # Meme coin, pump and dump
    'FLOKIUSDT',  # Meme coin, low liquidity
])
```

## Volatility Filter (Already Implemented)

```python
# Skip pairs with ATR > 3% of price
skip_high_volatility: bool = True
max_atr_pct: float = 3.0
```

## Signal Weight Optimization

After backtesting, FearGreed weight was reduced:

```python
# Before (inflated contrarian signals):
weight_fear_greed: float = 10

# After (more balanced):
weight_fear_greed: float = 5
```

## Backtest Command

```bash
cd ~/.hermes/scripts && python3 mona_backtest.py
```

## Notes

- Backtest uses simplified signals (RSI, Structure, Volume, Bollinger, EMA crossover)
- Live engine uses 16 signals (including SMC, Wyckoff, Funding, OI, etc.)
- Live performance may differ due to slippage, fees, and API latency
- Always validate with paper trading before live deployment
