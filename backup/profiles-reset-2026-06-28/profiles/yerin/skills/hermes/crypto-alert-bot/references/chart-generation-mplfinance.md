# Chart Generation with mplfinance — TradingView/Binance Style

## Why mplfinance (NOT raw matplotlib)

mplfinance produces professional candlestick charts automatically:
- Proper wick/body rendering
- Automatic spacing
- Built-in volume bars
- Easy overlay with `make_addplot()`

Raw matplotlib with Rectangle patches works but produces inferior charts.

## Clean Chart Template

```python
import mplfinance as mpf
import pandas as pd
from pathlib import Path

def generate_signal_chart(
    pair: str,
    direction: str,
    entry: float,
    sl: float,
    tps: list,
    klines: list,
    score: int,
    output_path: str = None
) -> str:
    """Generate clean TradingView-style signal chart."""
    
    # Parse klines to DataFrame
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', *_])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    
    # Last 100 candles only
    df = df.tail(100)
    
    # Calculate EMAs
    ema20 = df['close'].ewm(span=20, adjust=False).mean()
    ema50 = df['close'].ewm(span=50, adjust=False).mean()
    
    # Build addplots
    addplots = [
        mpf.make_addplot(ema20, color='#00ccff', width=1.5, label='EMA20'),
        mpf.make_addplot(ema50, color='#ffcc00', width=1.5, label='EMA50'),
    ]
    
    # Entry/SL/TP horizontal lines
    hlines = dict(hlines=[entry, sl, *tps[:3]], 
                  colors=['#00ff88', '#ff4444', '#00ccff', '#00ccff', '#00ccff'],
                  linewidths=[2, 2, 1.5, 1.5, 1.5],
                  linestyle=['-', '-', '--', '--', '--'])
    
    # Price labels on right
    dict_lines = [
        dict(y=entry, color='#00ff88', linestyle='-', linewidth=2, label=f'ENTRY ${entry:.6f}'),
        dict(y=sl, color='#ff4444', linestyle='-', linewidth=2, label=f'SL ${sl:.6f}'),
    ]
    for i, tp in enumerate(tps[:3]):
        dict_lines.append(dict(y=tp, color='#00ccff', linestyle='--', linewidth=1.5, label=f'TP{i+1} ${tp:.6f}'))
    
    # Style
    mc = mpf.make_marketcolors(
        up='#00ff88', down='#ff4444',
        edge={'up': '#00ff88', 'down': '#ff4444'},
        wick={'up': '#00ff88', 'down': '#ff4444'},
        volume={'up': '#00ff8880', 'down': '#ff444480'},
    )
    style = mpf.make_mpf_style(
        marketcolors=mc,
        facecolor='#1a1a2e',
        edgecolor='#1a1a2e',
        figcolor='#1a1a2e',
        gridcolor='#333333',
        gridstyle='-',
        gridaxis='both',
        y_on_right=True,
        rc={
            'font.size': 10,
            'axes.labelcolor': '#ffffff',
            'xtick.color': '#ffffff',
            'ytick.color': '#ffffff',
        }
    )
    
    # Generate
    if output_path is None:
        output_path = str(Path.home() / '.hermes' / 'charts' / f'{pair}_{direction}.png')
    
    fig, axes = mpf.plot(
        df,
        type='candle',
        style=style,
        volume=True,
        addplot=addplots,
        hlines=hlines,
        title=f'\n{pair} {direction} — Score: {score}/100',
        figsize=(16, 10),
        returnfig=True,
        tight_layout=True,
    )
    
    # Add price labels on right axis
    ax = axes[0]
    ax.text(len(df) + 1, entry, f'ENTRY ${entry:.6f}', color='#00ff88', fontsize=9, va='center')
    ax.text(len(df) + 1, sl, f'SL ${sl:.6f}', color='#ff4444', fontsize=9, va='center')
    for i, tp in enumerate(tps[:3]):
        ax.text(len(df) + 1, tp, f'TP{i+1} ${tp:.6f}', color='#00ccff', fontsize=9, va='center')
    
    # Current price marker
    current = df['close'].iloc[-1]
    ax.plot(len(df) - 1, current, 'o', color='#ffffff', markersize=8, zorder=5)
    ax.text(len(df) + 1, current, f'${current:.6f}', color='#ffffff', fontsize=10, fontweight='bold', va='center')
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e', edgecolor='none')
    import matplotlib.pyplot as plt
    plt.close(fig)
    
    return output_path
```

## Key Pitfalls

1. **rgba() format NOT supported** — matplotlib uses tuples: `(1, 0.27, 0.27, 0.2)` not `'rgba(255, 68, 68, 0.2)'`
2. **gridwidth parameter doesn't exist** — use `gridstyle='-'` instead
3. **EMA values contain None** — filter before plotting: `ema_x = [i for i, v in enumerate(ema) if v is not None]`
4. **mplfinance y_on_right** — set in style, not in plot()
5. **hlines dict** — colors must be list of hex strings, not rgba

## Installation

```bash
pip install mplfinance --break-system-packages
```

## Usage

```python
from mona_chart_pro import generate_signal_chart

path = generate_signal_chart(
    pair='BTCUSDT',
    direction='LONG',
    entry=61738.60,
    sl=60948.37,
    tps=[62528.83, 63319.06, 64109.29],
    klines=klines,
    score=90
)
```
