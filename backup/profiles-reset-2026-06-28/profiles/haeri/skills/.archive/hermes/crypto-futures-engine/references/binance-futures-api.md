# Binance Futures API Endpoints

## Market Data (No Auth)
- `GET /fapi/v1/klines` — Candlesticks (params: symbol, interval, limit)
- `GET /fapi/v1/ticker/price` — Current price
- `GET /fapi/v1/ticker/24hr` — 24h ticker
- `GET /fapi/v1/depth` — Order book (params: symbol, limit=5/10/20)
- `GET /fapi/v1/aggTrades` — Aggregated trades (taker buy/sell via `m` field)
- `GET /fapi/v1/exchangeInfo` — All symbols info (cache 1h)

## Data Endpoints (No Auth)
- `GET /fapi/v1/openInterest` — Current OI
- `GET /futures/data/openInterestHist` — OI history (period: 5m/15m/30m/1h/2h/4h/6h/12h/1d)
- `GET /fapi/v1/fundingRate` — Funding rate history
- `GET /fapi/v1/premiumIndex` — Mark/index price + funding info for all symbols
- `GET /futures/data/takerlongshortRatio` — Taker buy/sell volume ratio
- `GET /futures/data/topLongShortPositionRatio` — Top trader L/S ratio
- `GET /futures/data/globalLongShortAccountRatio` — Global L/S account ratio
- `GET /fapi/v1/allForceOrders` — Recent liquidations

## Authenticated (Needs API Key + Signature)
- `GET /fapi/v2/balance` — Account balance
- `GET /fapi/v2/positionRisk` — Open positions
- `POST /fapi/v1/leverage` — Set leverage
- `POST /fapi/v1/order` — Place order (MARKET, LIMIT, STOP_MARKET, TAKE_PROFIT_MARKET)
- `DELETE /fapi/v1/allOpenOrders` — Cancel all orders

## Signing
```python
params['timestamp'] = int(time.time() * 1000)
query = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
params['signature'] = signature
```

## Caching Strategy
- Price/ticker: 5s TTL
- Orderbook: 5s TTL
- Klines: 30s TTL
- OI/Funding/Taker: 60s TTL
- Exchange info: 3600s TTL
