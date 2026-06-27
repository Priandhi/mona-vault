# Market Context Modules

## Overview

Market context modules provide macro data that supplements signal analysis. They run on separate cron schedules and deliver to topic 387.

## Modules

### 1. Fear & Greed Index
```python
# Source: alternative.me
async def fear_greed():
    async with aiohttp.ClientSession() as s:
        async with s.get('https://api.alternative.me/fng/') as r:
            data = await r.json()
    return {'value': int(data['data'][0]['value']), 'classification': data['data'][0]['value_classification']}
```

**Signal interpretation:**
- 0-25: Extreme Fear → Contrarian BUY (score +90)
- 25-45: Fear → Lean bullish (score +40)
- 45-55: Neutral → No edge
- 55-75: Greed → Lean bearish (score -40)
- 75-100: Extreme Greed → Contrarian SELL (score -90)

### 2. BTC Dominance
```python
# Source: CoinGecko
async def btc_dominance():
    async with aiohttp.ClientSession() as s:
        async with s.get('https://api.coingecko.com/api/v3/global') as r:
            data = await r.json()
    return data['data']['market_cap_percentage']['btc']
```

**Signal interpretation:**
- BTC.D rising → Focus on BTC, avoid alts
- BTC.D falling → Altcoin season, rotate to alts
- BTC.D > 60% → Risk-off, avoid altcoins

### 3. Onchain Flow
```python
# BTC price + volume from Binance
async def btc_price():
    async with s.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT') as r:
        data = await r.json()
    return {'price': float(data['lastPrice']), 'change_24h': float(data['priceChangePercent']), 'volume': float(data['quoteVolume'])}

# ETH price
async def eth_price():
    async with s.get('https://api.binance.com/api/v3/ticker/24hr?symbol=ETHUSDT') as r:
        data = await r.json()
    return {'price': float(data['lastPrice']), 'change_24h': float(data['priceChangePercent'])}

# DeFi TVL from DeFiLlama
async def defi_tvl():
    async with s.get('https://api.llama.fi/v2/historicalChainTvl') as r:
        data = await r.json()
    return {'tvl': data[-1].get('tvl', 0)}

# Whale transactions from Blockchain.info
async def whale_txs():
    async with s.get('https://blockchain.info/unconfirmed-transactions?format=json') as r:
        data = await r.json()
    large = []
    for tx in data.get('txs', []):
        total = sum(o.get('value', 0) for o in tx.get('out', [])) / 1e8
        if total >= 100:  # >= 100 BTC
            large.append({'hash': tx.get('hash', '')[:16], 'btc': total})
    return sorted(large, key=lambda x: x['btc'], reverse=True)[:5]
```

### 4. Crypto News
```python
# Trending coins from CoinGecko
async def trending():
    async with s.get('https://api.coingecko.com/api/v3/search/trending') as r:
        data = await r.json()
    coins = []
    for c in data.get('coins', [])[:10]:
        item = c.get('item', {})
        coins.append({'name': item.get('name', ''), 'symbol': item.get('symbol', ''), 'market_cap_rank': item.get('market_cap_rank', 0)})
    return coins

# Top gainers/losers from Binance
async def top_movers():
    async with s.get('https://fapi.binance.com/fapi/v1/ticker/24hr') as r:
        data = await r.json()
    usdt = [t for t in data if t['symbol'].endswith('USDT') and float(t.get('quoteVolume', 0)) > 1_000_000]
    for t in usdt:
        t['change'] = float(t.get('priceChangePercent', 0))
    gainers = sorted(usdt, key=lambda x: x['change'], reverse=True)[:5]
    losers = sorted(usdt, key=lambda x: x['change'])[:5]
    return {'gainers': [{'symbol': g['symbol'], 'change': g['change']} for g in gainers],
            'losers': [{'symbol': l['symbol'], 'change': l['change']} for l in losers]}
```

### 5. Market Context Report Format
```
💜 **Mona Market Context**
━━━━━━━━━━━━━━━━━━━━━━━━━━

**FEAR & GREED INDEX**
  🟢 8/100 — Extreme Fear

**BTC**
  🟢 $63,368 (+3.8%)
  High: $64,235 | Low: $60,982
  Volume: $1,694,271,997

**ETH**
  🟢 $1,692.64 (+7.5%)

**MARKET DOMINANCE**
  BTC: 56.2%
  ETH: 9.0%
  Total Cap: $2,273,550,309,248

**TOP 5 GAINERS (24h):**
  🟢 BEATUSDT: +60.8%
  🟢 ESPORTSUSDT: +52.8%

**TOP 5 LOSERS (24h):**
  🔴 HOMEUSDT: -42.4%
  🔴 SKYAIUSDT: -36.6%

━━━━━━━━━━━━━━━━━━━━━━━━━━
Powered by: Mona Market Context v1.0
```

## Cron Schedules

- Market Context: `0 */6 * * *` (every 6 hours)
- News: `0 */3 * * *` (every 3 hours)
- Onchain: `0 */6 * * *` (every 6 hours)
- Dashboard (all-in-one): `0 */12 * * *` (every 12 hours)

All deliver to topic 387.
