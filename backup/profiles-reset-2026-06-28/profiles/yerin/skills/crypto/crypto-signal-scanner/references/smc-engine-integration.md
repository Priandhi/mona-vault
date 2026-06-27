# SMC Engine Integration Notes

## MonaSMCMaster v2.1 Architecture

Built on top of `dozero_smc_engine.py` (DozeroSMCEngine base class).

### Multi-Timeframe OB/FVG Detection

The key innovation: detect OB/FVG on EACH timeframe separately, then combine.

```python
# Detect on D1, H4, H1, M15 separately
for tf_name, tf_data in [('D1', data_d1), ('H4', data_h4), ('H1', data_h1), ('M15', data_m15)]:
    obs = engine.detect_order_blocks(tf_data['open'], tf_data['high'], tf_data['low'], tf_data['close'], tf_data['volume'], atr)
    fvgs = engine.detect_enhanced_fvgs(tf_data['high'], tf_data['low'], tf_data['close'], tf_data['volume'], atr)
```

### Enhanced Confluence Scoring (v2.1)

- MTF Alignment: 0-20 pts
- Fresh OBs by timeframe: 0-25 pts (H4=15, H1=10, M15=5)
- Virgin FVGs by timeframe: 0-20 pts (H1=15, H4=5)
- CHOCH confirmation: 0-15 pts
- Liquidity sweep + displacement: 0-15 pts
- Smart Money flow: 0-10 pts
- Zone bonus: 0-5 pts

### Files

- `mona_smc_master.py` — Base SMC master engine
- `mona_smc_master_v21.py` — Multi-TF OB/FVG detection
- `dozero_smc_engine.py` — Core SMC engine (DozeroSMCEngine)

### Pitfalls

1. **Division by zero**: Always check `if denominator > 0` in `analyze_smart_money_flow()`
2. **None values from API**: `klines` may return None. Always check `len(klines) >= 50`
3. **OB strength rating**: Fresh OBs are rare in high-momentum tokens. Use momentum mode instead.
4. **Virgin FVGs**: All FVGs may be tested. Don't rely solely on virgin FVG detection.
5. **SMC threshold**: Default 65 is too strict. Use 40-50 for more signals.
