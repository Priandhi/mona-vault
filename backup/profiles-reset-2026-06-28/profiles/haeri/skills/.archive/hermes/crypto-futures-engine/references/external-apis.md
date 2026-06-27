# External Free APIs for Market Intelligence

## Fear & Greed Index
- URL: `https://api.alternative.me/fng/?limit=7`
- No auth, no rate limit (reasonable use)
- Returns: value (0-100), classification, 7-day history
- Cache TTL: 1 hour

## Cross-Exchange Funding Rates
### Bybit V5
- URL: `https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT`
- No auth, rate limit: 10 req/s
- Returns: fundingRate in ticker data

### OKX
- URL: `https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP`
- Symbol format: `BTC-USDT-SWAP` (NOT `BTCUSDT`)
- No auth, rate limit: 20 req/s
- Returns: fundingRate in data[0]

## Yahoo Finance (DXY, S&P, Gold)
- URL: `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}`
- Params: `interval=1d&range=5d`
- Symbols: `DX-Y.NYB` (DXY), `^GSPC` (S&P), `^IXIC` (NASDAQ), `GC=F` (Gold), `^TNX` (US10Y)
- No auth, rate limit varies
- **PITFALL**: Returns 0 during market close (weekends, holidays)

## Deribit Options (Max Pain)
- URL: `https://www.deribit.com/api/v2/public/get_book_summary_by_currency`
- Params: `currency=BTC&kind=option`
- No auth, rate limit: 20 req/s
- Returns: instrument_name format `BTC-28JUN24-60000-C`
- Parse: split by `-`, index 2 = strike, index 3 = C/P

## Correlation Matrix
Hardcoded from historical data. Update quarterly.
Key pairs (>0.7 correlation):
- BTC/ETH: 0.92
- ETH/ARB: 0.90, ETH/OP: 0.90
- BTC/SOL: 0.85, ETH/SOL: 0.88
- ARB/OP: 0.92
- DOGE/PEPE: 0.75
- SOL/SUI: 0.82
