# Receipt: RH LP Bot Full Overhaul

**Date:** 2026-07-16
**Task:** Fix dan upgrade LP Farming Bot untuk Robinhood Chain

## Result
- Bot @DinoLpFarmBot fully functional
- Token analyzer dengan DexScreener-style calculations
- PnL card v5 dengan anime background
- Git committed: `d120a55`

## Decisions
1. **Skip V2 factory** — tidak ada code di Robinhood Chain, langsung V3
2. **ERC20_FULL_ABI** — bikin ABI sendiri karena contracts.py ABI tidak punya name/symbol/totalSupply
3. **Price calculation** — pakai 1.0001^tick + decimal adjustment (lebih reliable dari sqrtPriceX96)
4. **Liquidity** — pakai L/sqrtPrice formula untuk V3 (bukan balanceOf yang lambat)
5. **24H Volume** — scan Swap events dari 43200 blocks terakhir
6. **PnL card** — row-based layout dengan anime bg (v5), bukan card boxes (v4)
7. **Auto LP** — auto-detect stable vs volatile, set range ±5% / ±20%

## Issues
1. Vision model (auxiliary.vision) masih pakai deepseek, perlu gateway restart untuk GLM-5.2
2. V2 factory tidak exists di Robinhood Chain
3. ETH/USD price hardcoded ke 1450 (perlu oracle atau pool price)
4. Holder count = 0 (perlu indexer/API)

## Next Steps
- Restart gateway untuk activate GLM-5.2 vision
- Tambah ETH/USD price oracle dari WETH/USDG pool
- Implement holder count via Transfer event scan
- Test Auto LP execution dengan real transaction