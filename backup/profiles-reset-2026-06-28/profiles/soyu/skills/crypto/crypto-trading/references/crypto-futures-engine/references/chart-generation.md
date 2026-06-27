# Chart Generation for Trading Signals

## Overview

Generate professional trading charts with SMC annotations using matplotlib.

## Setup

```python
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
```

## Color Scheme (Dark Theme)

```python
# MUST use tuples for rgba, NOT CSS strings
# WRONG: 'rgba(255, 68, 68, 0.2)'
# RIGHT: (1, 0.27, 0.27, 0.2)

colors = {
    'bg': '#1a1a2e',
    'candle_up': '#00ff88',
    'candle_down': '#ff4444',
    'ob_bullish': (0, 1, 0.53, 0.2),  # green, alpha 0.2
    'ob_bearish': (1, 0.27, 0.27, 0.2),  # red, alpha 0.2
    'fvg_bullish': (0, 1, 0.53, 0.15),
    'fvg_bearish': (1, 0.27, 0.27, 0.15),
    'liquidity': (1, 1, 0, 0.5),
    'entry': '#00ff88',
    'stop_loss': '#ff4444',
    'tp': '#00ccff',
    'text': '#ffffff',
    'grid': (1, 1, 1, 0.1)
}
```

## Candlestick Chart

```python
def plot_candles(ax, opens, highs, lows, closes, colors):
    """Plot candlestick chart"""
    n = len(closes)
    for i in range(n):
        color = colors['candle_up'] if closes[i] >= opens[i] else colors['candle_down']
        
        # Wick
        ax.plot([i, i], [lows[i], highs[i]], color=color, linewidth=1)
        
        # Body
        body_bottom = min(opens[i], closes[i])
        body_height = abs(closes[i] - opens[i])
        rect = Rectangle((i - 0.4, body_bottom), 0.8, body_height, 
                         facecolor=color, edgecolor=color)
        ax.add_patch(rect)
```

## Order Block Annotations

```python
def plot_order_blocks(ax, order_blocks, colors):
    """Plot Order Blocks as colored rectangles"""
    for ob in order_blocks:
        if ob.fresh:
            color = colors['ob_bullish'] if ob.is_bullish else colors['ob_bearish']
            rect = Rectangle(
                (ob.index - 0.5, ob.low), 
                1, ob.high - ob.low,
                facecolor=color, edgecolor=color[:3] + (0.5,), linewidth=1
            )
            ax.add_patch(rect)
            
            # Label
            label = f"OB ({ob.strength.value})"
            ax.text(ob.index, ob.high, label, 
                   color='white', fontsize=8, ha='center', va='bottom')
```

## FVG Annotations

```python
def plot_fvgs(ax, fvgs, colors):
    """Plot Fair Value Gaps as colored rectangles"""
    for fvg in fvgs:
        if fvg.quality in ['virgin', 'virgin_hv']:
            color = colors['fvg_bullish'] if fvg.is_bullish else colors['fvg_bearish']
            rect = Rectangle(
                (fvg.index - 0.5, fvg.low),
                1, fvg.high - fvg.low,
                facecolor=color, edgecolor=color[:3] + (0.3,), linewidth=1
            )
            ax.add_patch(rect)
            
            # Label
            label = f"FVG ({fvg.quality.value})"
            ax.text(fvg.index, fvg.low, label,
                   color='white', fontsize=8, ha='center', va='top')
```

## Entry/SL/TP Lines

```python
def plot_trade_levels(ax, entry, sl, tps, colors, n_candles):
    """Plot entry, stop loss, and take profit levels"""
    # Entry
    ax.axhline(y=entry, color=colors['entry'], linestyle='-', linewidth=2, alpha=0.8)
    ax.text(n_candles + 1, entry, f"ENTRY ${entry:.6f}", 
           color=colors['entry'], fontsize=10, va='center')
    
    # Stop Loss
    ax.axhline(y=sl, color=colors['stop_loss'], linestyle='-', linewidth=2, alpha=0.8)
    ax.text(n_candles + 1, sl, f"SL ${sl:.6f}",
           color=colors['stop_loss'], fontsize=10, va='center')
    
    # Take Profits
    for i, tp in enumerate(tps, 1):
        ax.axhline(y=tp, color=colors['tp'], linestyle='--', linewidth=1, alpha=0.6)
        ax.text(n_candles + 1, tp, f"TP{i} ${tp:.6f}",
               color=colors['tp'], fontsize=10, va='center')
```

## Liquidity Levels

```python
def plot_liquidity(ax, liq_levels, colors, n_candles):
    """Plot liquidity levels as dotted lines"""
    for liq in liq_levels:
        ax.axhline(y=liq.price, color=colors['liquidity'], 
                   linestyle=':', linewidth=1, alpha=0.5)
        ax.text(0, liq.price, "Liq", 
               color=colors['liquidity'], fontsize=8, va='center')
```

## Full Chart Generation

```python
def generate_smc_chart(setup, klines, output_path):
    """Generate complete SMC chart"""
    fig, ax = plt.subplots(figsize=(16, 10))
    fig.patch.set_facecolor(colors['bg'])
    ax.set_facecolor(colors['bg'])
    
    # Parse OHLCV
    opens = [float(k[1]) for k in klines]
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    closes = [float(k[4]) for k in klines]
    
    # Plot components
    plot_candles(ax, opens, highs, lows, closes, colors)
    plot_order_blocks(ax, setup.order_blocks, colors)
    plot_fvgs(ax, setup.enhanced_fvgs, colors)
    plot_liquidity(ax, setup.chart_data.liquidity_levels, colors, len(closes))
    plot_trade_levels(ax, setup.entry_price, setup.stop_loss, 
                     [setup.tp1, setup.tp2, setup.tp3, setup.tp4], colors, len(closes))
    
    # Title
    direction = "LONG" if setup.direction.value == 'bullish' else "SHORT"
    ax.set_title(f"{setup.pair} {direction} — Confidence: {setup.confluence_score}/100",
                color='white', fontsize=14, fontweight='bold')
    
    # Grid
    ax.grid(True, alpha=0.1, color='white')
    ax.tick_params(colors='white')
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=colors['bg'], edgecolor='none')
    plt.close()
    
    return output_path
```

## Pitfalls

1. **rgba format**: matplotlib does NOT accept CSS `'rgba(255, 68, 68, 0.2)'` strings. Use tuples: `(1, 0.27, 0.27, 0.2)`
2. **Memory leaks**: Always call `plt.close()` after saving
3. **DPI**: Use 150 DPI for Telegram (balance quality/size)
4. **Figure size**: 16x10 inches works well for trading charts
5. **Font**: Default matplotlib fonts work, but can customize with `matplotlib.font_manager`

## Output Path

```python
CHART_DIR = Path.home() / '.hermes' / 'charts'
CHART_DIR.mkdir(parents=True, exist_ok=True)

output_path = CHART_DIR / f"{pair}_{direction}.png"
```

## Telegram Integration

```python
# Send chart as photo
cmd = ['python3', str(telegram_script), 'send_topic_photo', str(topic_id), str(chart_path)]
subprocess.run(cmd, capture_output=True, text=True, timeout=30)
```
