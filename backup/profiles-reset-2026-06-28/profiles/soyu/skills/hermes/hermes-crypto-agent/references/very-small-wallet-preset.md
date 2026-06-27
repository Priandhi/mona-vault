# Very Small Wallet Config for Meridian (< 0.3 SOL)

For wallets with less than 0.3 SOL. Maximum capital protection.

## Key principles

1. **Profit sedikit > rugi banyak** — tight stop loss, small deploy
2. **1 posisi bagus > 3 posisi mediocre** — focus capital
3. **Kalau rugi 2x berturut-turut → PAUSE** — don't revenge trade
4. **Jangan deploy kalau balance < 0.15 SOL** — hard floor

## Config

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `deployAmountSol` | 0.1 | Room for gas + recovery |
| `maxPositions` | 1 | Focus capital, don't spread thin |
| `minSolToOpen` | 0.15 | Lower threshold for small wallet |
| `gasReserve` | 0.1 | Minimum for close + swap |
| `stopLossPct` | -15 | Tight — user said "-30% kegedean buat LP" |
| `takeProfitPct` | 5 | Quick profit extraction |
| `trailingTriggerPct` | 3 | Start trailing early |
| `trailingDropPct` | 1.5 | Tight trailing |
| `screeningIntervalMin` | 15 | More responsive for volatile Solana |
| `managementIntervalMin` | 5 | Monitor positions closely |
| `minFeeActiveTvlRatio` | 0.03 | More candidates pass filter |
| `minTokenFeesSol` | 15 | Include newer pools |
| `minHolders` | 200 | Realistic for Solana |
| `minMcap` | 50000 | Catch early stage |
| `maxTop10Pct` | 45 | Avoid whale-dominated pools |
| `maxBundlePct` | 25 | Avoid manipulated pools |
| `maxBotHoldersPct` | 25 | Avoid fake volume |

## Hitungan kasar

```
Wallet:     0.364 SOL
Deploy:     0.10 SOL
Gas:        0.10 SOL
─────────────────────
Sisa aman:  0.264 SOL

SL -15% → max rugi 0.015 SOL per trade
5 trade kalah berturut-turut → rugi 0.075 SOL, sisa 0.289 SOL ✅
```

## When to upgrade

- Balance > 0.5 SOL → switch to small wallet preset (0.15 SOL deploy, 3 positions)
- Balance > 2 SOL → switch to moderate preset (0.3 SOL deploy)
- 5+ winning trades → increase deploy by 0.05 SOL increments
