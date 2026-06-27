# Chart Generation for Trading Signals

Generate professional SMC charts with matplotlib for Telegram delivery.

## Setup

```python
import matplotlib
matplotlib.use('Agg')  # REQUIRED for headless servers
import matplotlib.pyplot as plt
import matplotlib.patches as patches

CHART_DIR = Path.home() / '.hermes' / 'charts'
CHART_DIR.mkdir(parents=True, exist_ok=True)
```

## PITFALL: RGBA Color Format

**matplotlib does NOT accept CSS `rgba()` strings!**

```python
# ❌ WRONG - raises ValueError: Invalid RGBA argument
colors = {
    'ob_bullish': 'rgba(0, 255, 136, 0.2)',
    'ob_bearish': 'rgba(255, 68, 68, 0.2)',
}

# ✅ CORRECT - tuple format (R, G, B, A) with 0-1 range
colors = {
    'ob_bullish': (0, 1, 0.53, 0.2),      # green, alpha 0.2
    'ob_bearish': (1, 0.27, 0.27, 0.2),    # red, alpha 0.2
    'fvg_bullish': (0, 1, 0.53, 0.15),
    'fvg_bearish': (1, 0.27, 0.27, 0.15),
    'liquidity': (1, 1, 0, 0.5),           # yellow
    'grid': (1, 1, 1, 0.1),                # white, very transparent
}
```

## Chart Template

```python
def generate_chart(symbol, klines, momentum, smc_data, output_path=None):
    """Generate SMC chart with annotations"""
    # Parse data (last 50 candles)
    closes = [float(k[4]) for k in klines[-50:]]
    highs = [float(k[2]) for k in klines[-50:]]
    lows = [float(k[3]) for k in klines[-50:]]
    opens = [float(k[1]) for k in klines[-50:]]
    volumes = [float(k[5]) for k in klines[-50:]]
    
    # Create figure with 2 panels (price + volume)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                   gridspec_kw={'height_ratios': [3, 1]})
    fig.patch.set_facecolor('#1a1a2e')
    
    # Plot candlesticks
    for i in range(len(closes)):
        color = '#00ff88' if closes[i] >= opens[i] else '#ff4444'
        ax1.bar(i, abs(closes[i] - opens[i]), 
               bottom=min(opens[i], closes[i]),
               color=color, width=0.6, alpha=0.8)
        ax1.vlines(i, lows[i], highs[i], color=color, linewidth=0.5)
    
    # Plot EMAs
    ema20_vals = calculate_ema_series(closes, 20)
    ema50_vals = calculate_ema_series(closes, 50)
    ax1.plot(ema20_vals, color='#ffaa00', linewidth=1.5, label='EMA20')
    ax1.plot(ema50_vals, color='#00aaff', linewidth=1.5, label='EMA50')
    
    # Plot FVG zones (green/red shaded areas)
    for fvg in smc_data.get('fvgs', [])[-5:]:
        color = 'green' if fvg['type'] == 'bullish' else 'red'
        ax1.axhspan(fvg['low'], fvg['high'], alpha=0.15, color=color)
    
    # Plot liquidity levels (yellow dotted lines)
    for liq in smc_data.get('liq_levels', [])[-5:]:
        ax1.axhline(y=liq['price'], color='#ffff00', 
                   linestyle='--', alpha=0.5, linewidth=0.5)
    
    # Plot entry/SL/TP lines
    entry = momentum['entry']
    sl = momentum['stop_loss']
    tp1, tp2, tp3, tp4 = momentum['tp1'], momentum['tp2'], momentum['tp3'], momentum['tp4']
    
    ax1.axhline(y=entry, color='#00ff88', linestyle='-', linewidth=2, 
               label=f'Entry ${entry:.6f}')
    ax1.axhline(y=sl, color='#ff4444', linestyle='-', linewidth=2, 
               label=f'SL ${sl:.6f}')
    for i, tp in enumerate([tp1, tp2, tp3, tp4], 1):
        ax1.axhline(y=tp, color='#00ccff', linestyle='--', linewidth=1, 
                   label=f'TP{i} ${tp:.6f}')
    
    # Entry zone highlight
    risk = abs(entry - sl)
    ax1.axhspan(entry - risk*0.1, entry + risk*0.1, alpha=0.2, color='#00ff88')
    
    # Volume bars
    vol_colors = ['#00ff88' if closes[i] >= opens[i] else '#ff4444' 
                 for i in range(len(closes))]
    ax2.bar(range(len(volumes)), volumes, color=vol_colors, alpha=0.6)
    
    # Styling
    ax1.set_title(f'{symbol} {momentum["direction"]} — Score: {momentum["score"]}/100', 
                 color='white', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price (USDT)', color='white')
    ax2.set_ylabel('Volume', color='white')
    ax1.grid(True, alpha=0.2, color='white')
    ax2.grid(True, alpha=0.2, color='white')
    ax1.legend(loc='upper left', fontsize=8, facecolor='#1a1a2e', edgecolor='white')
    ax1.set_facecolor('#1a1a2e')
    ax2.set_facecolor('#1a1a2e')
    ax1.tick_params(colors='white')
    ax2.tick_params(colors='white')
    
    # Save
    if output_path is None:
        output_path = str(CHART_DIR / f"{symbol}_{momentum['direction']}.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_path
```

## Telegram Delivery

```python
# Include in message
chart_path = generate_chart(symbol, klines, momentum, smc_data)
msg = f"📊 Chart: {chart_path}"

# Or send as media
send_message(f"MEDIA:{chart_path}")
```

## Pitfalls

1. **Must use `matplotlib.use('Agg')`** before importing pyplot on headless servers
2. **RGBA tuples, not CSS strings** — see above
3. **Close figures** with `plt.close()` to avoid memory leaks
4. **Use absolute paths** for chart output — relative paths can fail in cron jobs
5. **DPI 100** is good balance between quality and file size (~150-200KB per chart)
