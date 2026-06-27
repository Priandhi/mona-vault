# Professional Chart Generation with mplfinance

## Overview

User wants charts that look like Binance/TradingView. Reference: Slevensy Scanner Bot charts. Use `mplfinance` library, NOT basic matplotlib.

## Setup

```python
import mplfinance as mpf
import matplotlib
matplotlib.use('Agg')  # Required for headless server

mc = mpf.make_marketcolors(
    up='#00ff88', down='#ff4444',
    edge={'up': '#00ff88', 'down': '#ff4444'},
    wick={'up': '#00ff88', 'down': '#ff4444'},
    volume={'up': '#00ff8880', 'down': '#ff444480'},
    ohlc='i'
)
style = mpf.make_mpf_style(
    marketcolors=mc,
    facecolor='#1a1a2e',
    edgecolor='#1a1a2e',
    gridcolor='#333333',
    gridstyle='--',
    y_on_right=True,
    rc={'font.size': 10, 'axes.labelcolor': 'white', 'xtick.color': 'white', 'ytick.color': 'white'}
)
```

## Data Format

```python
import pandas as pd
from datetime import datetime

data = []
for k in klines:
    data.append({
        'Date': datetime.fromtimestamp(int(k[0]) / 1000),
        'Open': float(k[1]),
        'High': float(k[2]),
        'Low': float(k[3]),
        'Close': float(k[4]),
        'Volume': float(k[5])
    })
df = pd.DataFrame(data)
df.set_index('Date', inplace=True)
```

## Plot with EMA + H-lines

```python
df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

add_plots = [
    mpf.make_addplot(df['EMA20'], color='#00ccff', width=1.5),
    mpf.make_addplot(df['EMA50'], color='#ffcc00', width=1.5),
]

hlines = dict(
    hlines=[entry, sl, tp1, tp2, tp3],
    colors=['#00ff88', '#ff4444', '#00ccff', '#00ccff', '#00ccff'],
    linestyle=['-', '-', '--', '--', '--'],
    linewidths=[2, 2, 1.5, 1.5, 1.5]
)

fig, axes = mpf.plot(
    df, type='candle', style=style,
    volume=True, addplot=add_plots, hlines=hlines,
    figsize=(16, 10), returnfig=True, tight_layout=True,
    scale_width_adjustment=dict(candle=1.2, volume=0.7)
)
```

## Annotations (after mpf.plot)

```python
ax_main = axes[0]

# Price labels on right
ax_main.text(len(df)+1, entry, f'Entry ${entry:.6f}', color='#00ff88', fontsize=9, fontweight='bold')
ax_main.text(len(df)+1, sl, f'SL ${sl:.6f}', color='#ff4444', fontsize=9, fontweight='bold')

# Current price marker
ax_main.plot(len(df)-1, current, 'o', color='#00ff88', markersize=10)
ax_main.text(len(df)+1, current, f'${current:.6f}', color='white', fontsize=10,
    fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#00ff88', alpha=0.8))

# Info box (top-left)
ax_main.text(0.02, 0.98, info_text, transform=ax_main.transAxes, color='white', fontsize=10,
    va='top', ha='left', bbox=dict(boxstyle='round,pad=0.5', facecolor='#1a1a2e', edgecolor='#333333'))

# Reasons box (bottom-right)
ax_main.text(0.98, 0.02, reasons_text, transform=ax_main.transAxes, color='#cccccc', fontsize=9,
    va='bottom', ha='right', bbox=dict(boxstyle='round,pad=0.5', facecolor='#1a1a2e', edgecolor='#333333'))
```

## Save

```python
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e', edgecolor='none')
plt.close()
```

## Pitfalls

1. **`gridwidth` not valid** — `mpf.make_mpf_style()` does not accept `gridwidth` kwarg. Remove it.
2. **CSS rgba() strings** — matplotlib does NOT accept `'rgba(255, 68, 68, 0.2)'`. Use tuple: `(1, 0.27, 0.27, 0.2)`.
3. **Emoji in title** — DejaVu Sans font may not have emoji glyphs. Use text-only titles or install Noto Color Emoji.
4. **`scale_width_adjustment`** — Controls candle body thickness. `candle=1.2` makes bodies wider.
5. **returnfig=True** — Required to get axes objects for annotation. Without it, `mpf.plot()` returns None.
6. **y_on_right=True** — Price labels on right side like TradingView. Default is left.
