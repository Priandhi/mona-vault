# Watchlist & Price Alerts

## Overview

A persistent watchlist system that:
1. Monitors specific coins
2. Alerts when price nears entry zone
3. Stores data in JSON file

## Implementation

```python
class MonaWatchlist:
    def __init__(self):
        self.watchlist = self.load()

    def load(self):
        if DATA_FILE.exists():
            return json.loads(DATA_FILE.read_text())
        return {'coins': {}, 'alerts': {}}

    def save(self):
        DATA_FILE.write_text(json.dumps(self.watchlist, indent=2))

    def add_coin(self, symbol, entry_price=None, direction='LONG', notes=''):
        self.watchlist['coins'][symbol] = {
            'entry_price': entry_price,
            'direction': direction,
            'notes': notes,
            'added_at': time.time(),
        }
        self.save()

    def add_alert(self, symbol, target_price, alert_type='above', message=''):
        alert_id = f"{symbol}_{target_price}_{int(time.time())}"
        self.watchlist['alerts'][alert_id] = {
            'symbol': symbol,
            'target_price': target_price,
            'alert_type': alert_type,  # 'above' or 'below'
            'message': message,
            'triggered': False,
            'added_at': time.time(),
        }
        self.save()
        return alert_id

    async def check_alerts(self):
        triggered = []
        for alert_id, alert in list(self.watchlist['alerts'].items()):
            if alert['triggered']:
                continue
            price = await self.get_price(alert['symbol'])
            hit = False
            if alert['alert_type'] == 'above' and price >= alert['target_price']:
                hit = True
            elif alert['alert_type'] == 'below' and price <= alert['target_price']:
                hit = True
            if hit:
                alert['triggered'] = True
                alert['triggered_price'] = price
                triggered.append(alert)
        if triggered:
            self.save()
        return triggered
```

## Data File

Location: `~/.hermes/data/watchlist.json`

Format:
```json
{
  "coins": {
    "BTCUSDT": {
      "entry_price": 60000,
      "direction": "LONG",
      "notes": "Strong support",
      "added_at": 1717800000
    }
  },
  "alerts": {
    "BTCUSDT_60000_1717800000": {
      "symbol": "BTCUSDT",
      "target_price": 60000,
      "alert_type": "below",
      "message": "BTC hit $60k — entry zone!",
      "triggered": false,
      "added_at": 1717800000
    }
  }
}
```

## Commands (for Telegram bot)

- `/watch SYMBOL ENTRY_PRICE DIRECTION` — Add to watchlist
- `/watchlist` — Show watchlist with current prices
- `/add SYMBOL above|below PRICE` — Add price alert
- `/alerts` — Show active alerts
- `/delalert ID` — Remove alert

## Files

- `mona_watchlist.py` — Main watchlist module
- `~/.hermes/data/watchlist.json` — Persistent data
