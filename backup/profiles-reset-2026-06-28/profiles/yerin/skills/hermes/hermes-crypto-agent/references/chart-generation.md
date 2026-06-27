# Trading Signal Chart Generation (TradingView-style)

## User Preference
User explicitly wants Binance/TradingView-style charts. HATES SMC zones on charts ("gak sesuai ekspektasi masih jelek"). Chart must be CLEAN candlestick only.

## What to include
- Candlestick (green up, red down)
- EMA20 (cyan) + EMA50 (orange/yellow)
- Volume bars at bottom
- Entry line (green, solid)
- SL line (red, solid)
- TP1-3 lines (blue/cyan, dashed)
- Current price marker with label
- Dark theme background (#1a1a2e)

## What NOT to include
- ❌ Order Block rectangles
- ❌ FVG zones/boxes
- ❌ Liquidity level lines
- ❌ SMC annotations
- ❌ Structure break markers
- ❌ Multiple timeframe overlays

## Implementation

Script: `~/.hermes/scripts/mona_chart_pro.py`

### Key patterns

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Dark theme
fig, ax = plt.subplots(figsize=(16, 10))
fig.patch.set_facecolor('#1a1a2e')
ax.set_facecolor('#1a1a2e')

# Candlestick (NOT mplfinance — manual patches for control)
for i in range(len(closes)):
    color = '#26a69a' if closes[i] >= opens[i] else '#ef5350'
    # Wick
    ax.plot([i, i], [lows[i], highs[i]], color=color, linewidth=1.5)
    # Body
    rect = plt.Rectangle((i-0.3, min(opens[i], closes[i])), 0.6, 
                          max(abs(closes[i]-opens[i]), 0.0001),
                          facecolor=color, edgecolor=color)
    ax.add_patch(rect)

# EMA (filter None values!)
ema20_x = [i for i, v in enumerate(ema20) if v is not None]
ema20_y = [v for v in ema20 if v is not None]
ax.plot(ema20_x, ema20_y, color='#2962ff', linewidth=1.5, label='EMA20')

# Entry/SL/TP (horizontal lines with labels)
ax.axhline(y=entry, color='#26a69a', linewidth=2)
ax.text(len(closes)+0.5, entry, f"Entry ${entry:.6f}", color='#26a69a', va='center')

# Price labels on right
ax.text(len(closes), closes[-1], f"${closes[-1]:.6f}", color='white', 
        fontsize=10, fontweight='bold', va='center',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#26a69a'))

# Volume bars
ax2 = ax.twinx()
for i in range(len(closes)):
    color = '#26a69a' if closes[i] >= opens[i] else '#ef5350'
    ax2.bar(i, volumes[i], color=color, alpha=0.3, width=0.6)
ax2.set_ylim(0, max(volumes[-100:]) * 4)
ax2.set_ylabel('')
ax2.set_yticks([])

plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
```

### Pitfalls
- **matplotlib rgba:** Use tuples `(r, g, b, a)` not CSS strings `'rgba(...)'`
- **EMA None filter:** `_ema()` pads with None. Plotting None crashes. Always filter.
- **gridwidth:** Not a valid plt.grid() param. Remove.
- **Body height:** `max(abs(closes[i]-opens[i]), 0.0001)` prevents zero-height rectangles.
- **Font emoji warning:** `Glyph missing from font DejaVu Sans` for emoji in title — harmless, ignore.

## Output
Save to `~/.hermes/charts/{PAIR}_{DIRECTION}.png`. Show to user with `MEDIA:` prefix or `vision_analyze`.
