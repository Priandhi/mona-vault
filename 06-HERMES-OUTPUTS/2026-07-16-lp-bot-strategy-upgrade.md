# 2026-07-16 LP Bot Strategy Upgrade

## Task
Implement 5 strategi LP Farm enhancement

## Result
### ✅ 1. Smart Range (`core/strategy.py`)
- `get_volatility()` — historical tick analysis from Swap events
- `calculate_optimal_range()` — range dari vol + volume/liquidity ratio + fee tier
- `estimate_il()` — V3 IL formula
- `estimate_apr()` — APR dari volume/fee/liquidity
- `get_optimal_fee_tier()` — fee tier recommendation

### ✅ 2. IL Protection (`core/position.py`)
- Background monitor loop (60s interval)
- IL calculation per position
- Auto-exit jika IL > threshold (default 10%)
- Config di `il_protection` section

### ✅ 3. Auto-Farm Discovery (`core/discovery.py` — new module)
- `discover_pools()` — scan WETH pairs × fee tiers
- `analyze_pool()` — TVL, volume, APR, optimal range
- `scan_and_rank()` — sorted by APR descending
- `get_best_pool()` — single best pool with min TVL filter

### ✅ 4. Multi-Position Strategy (`core/strategy.py`)
- `generate_tiers()` — split deposit across multiple ranges
- Support bullish/bearish/neutral bias
- Equal weight distribution
- Config di `multi_position` section

### ✅ 5. Yield Dashboard (`bot/messages.py`, `bot/keyboards.py`, `bot/handlers.py`)
- `/yield` command + `🏆 Yield` button di main menu
- Pool ranking display (top 8, medal icons)
- APR color coding (🟢 >20%, 🟡 >5%, ⚪ <5%)
- Strategy summary now includes IL + Multi-Pos status

## Decisions
- `lp_bot.py` deleted (duplicate of bot_ui.py)
- `bot.py` kept (CLI tool)
- Gas & Fee Tier buttons added to strategy menu
- Security upgraded with V3 Quoter swap simulation

## Issues
- NFPM ABI bug fixed (`balanceOf` + `tokenOfOwnerByIndex`)
- `lp_manager.py` token0_contract bug fixed
- messages.py had duplicate code from patch — rewritten clean

## Next Steps
- Mas to fund wallet with ETH for real testing
- Consider expanding SCAN_TOKENS list as more tokens appear on RH Chain