# Data Sources — Crypto Quick Scan

Endpoint no-key (atau optional key) yang sudah verified untuk pull data cepat. Semua via `terminal` + `curl`, JANGAN lewat `web_extract` (Brave Search backend gagal extract dari DexScreener — confirmed di sesi DATBIHGAH).

**For alpha DISCOVERY (finding NEW projects):** See `references/alpha-hunting-workflow.md` — DeFiLlama, DexScreener latest profiles, CoinGecko trending, Binance listings. Different workflow from scanning a known CA below.

## DexScreener (default, all chains)

**Endpoint utama:**
```
GET https://api.dexscreener.com/latest/dex/tokens/{CA}
```

**Boosted tokens (alpha discovery):**
```
GET https://api.dexscreener.com/token-boosts/latest/v1
```
Returns 30 recently boosted tokens — good for finding trending tokens without GeckoTerminal.

**Token profiles (newly listed):**
```
GET https://api.dexscreener.com/token-profiles/latest/v1
```
Returns 30 newly listed tokens with profile data. Combine with boosts for better coverage.

**Token details (single token):**
```
GET https://api.dexscreener.com/tokens/v1/{chain_id}/{token_address}
```
Returns array of pairs for a single token. Use for deep analysis.

- Auto-detect chain (Solana, ETH, BSC, Base, Arbitrum, semua chain mainstream)
- Return semua pairs token, urut by liquidity
- No auth, rate limit ~300 req/min
- Field penting: `pairs[].priceUsd`, `liquidity.usd`, `volume.h24`, `txns.h24.{buys,sells}`, `priceChange.{m5,h1,h6,h24}`, `fdv`, `marketCap`, `pairCreatedAt`, `info.socials`

**Sample call:**
```bash
curl -s "https://api.dexscreener.com/latest/dex/tokens/{CA}" | jq '.pairs[0] | {priceUsd, liquidity:.liquidity.usd, vol24:.volume.h24, mc:.marketCap, fdv:.fdv, change24:.priceChange.h24}'
```

**Mandatory fields for alpha alerts:** When building token scanner output (alpha alerts, real-time scans), ALWAYS extract and display:
- `priceUsd` — current price
- `marketCap` — market cap (use `format_mc()` helper: `$X.XXM` / `$X.XK` / `$X`)
- `fdv` — fully diluted valuation (show alongside MC when different)
- `liquidity.usd` — pool liquidity
- `volume.h24` — 24h volume
- `priceChange.h24` — 24h price change %
- `pairCreatedAt` — for age calculation

DexScreener `/tokens/v1/{chain}/{address}` returns all these in the first element of the response array. Example enrichment:
```python
token["market_cap"] = detail.get("marketCap") or 0
token["fdv"] = detail.get("fdv") or 0
token["price_usd"] = detail.get("priceUsd")
```
User explicitly complained that market cap was missing from alpha alerts — it's a critical data point for degen decision-making.

**Pitfall:** `priceChange.m5` atau `h6` kadang return angka jutaan persen (artifact pool baru lahir). Pakai pair dengan liquidity terbesar sebagai primary, ignore outlier change values.

## GoPlus Security (EVM honeypot/scam check)

```
GET https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={CA}
```

Chain IDs umum: 1=ETH, 56=BSC, 137=Polygon, 42161=Arbitrum, 8453=Base, 10=Optimism.

Return: `is_honeypot`, `buy_tax`, `sell_tax`, `cannot_sell_all`, `is_blacklisted`, `is_mintable`, `owner_address`, `holder_count`. **Wajib cek sebelum rec buy untuk EVM token baru.**

## Solana metadata

**Solscan public:**
```
GET https://public-api.solscan.io/token/meta?tokenAddress={CA}
```

**Birdeye (optional API key):**
```
GET https://public-api.birdeye.so/defi/token_overview?address={CA}
Header: X-API-KEY: <key>  # optional, lebih bagus dengan key
```

## CoinGecko (token established)

```
GET https://api.coingecko.com/api/v3/simple/token_price/{platform}?contract_addresses={CA}&vs_currencies=usd
```

`platform`: `ethereum`, `solana`, `binance-smart-chain`, dll. Free tier ~30 req/min.

## Chain detection heuristic (fast)

Sebelum hit endpoint, deteksi chain dari format CA:

| Pattern | Chain |
|---|---|
| `0x` + 40 hex chars | EVM (ETH/BSC/Base/etc) |
| 32-44 base58 chars (no `0x`, no `0OIl`) | Solana |
| ends with `pump` | Solana pump.fun |
| ends with `bonk` | Solana letsbonk.fun |
| `0x` + 64 hex (Sui object) | Sui |
| `0x` + 64 hex with `::` module path | Aptos |

Kalau ragu, lempar ke DexScreener — auto-detect.

## Clanker API (Base chain launchpad)

```
GET https://www.clanker.world/api/tokens
Headers: Referer: https://www.clanker.world/
```

No auth needed. Returns `{data: [{admin (deployer), contract_address, name, symbol, description, pool_address, starting_market_cap, chain_id}], total, tokensDeployed}`.

**PITFALL**: Adding `?sort=created_at&order=desc` returns 400. Use bare URL.
**PITFALL**: Clanker tokens have NO liquidity/volume data. Must fetch from DexScreener separately.

## Launchpad API Status (Base chain, June 2026)

| Launchpad | Endpoint | Status |
|-----------|----------|--------|
| Clanker | `https://www.clanker.world/api/tokens` | ✅ Works |
| Virtuals | `https://api.virtuals.io/api/virtuals` | ❌ 403 |
| Creator.bid | `https://creator.bid/api` | ❌ 403 |
| Flaunch | `https://flaunch.xyz/api` | ❌ 403 |
| Bankr.bot | `https://api.bankr.bot` | ❌ 404 |

For blocked APIs, detect launchpad from DexScreener token description patterns.

## Tools yang TIDAK reliable

- `web_extract` ke DexScreener / GMGN / Birdeye web UI → backend Brave Search return error "search-only backend cannot extract URL content". Skip langsung ke API curl.
- Browser scraping untuk data realtime → terlalu lambat untuk scan workflow, pakai API.

## RPC endpoints (kalau butuh on-chain read langsung)

Buat private RPC pakai Helius/QuickNode/Alchemy — credentials di `~/mona-workspace/vault/`.

### Public RPC quick-reference

**Verified working (June 2026):**
| Chain | Endpoint | Notes |
|---|---|---|
| Ethereum | `https://eth.llamarpc.com` | sometimes rate-limits |
| Arbitrum | `https://arb1.arbitrum.io/rpc` | |
| Optimism | `https://optimism.llamarpc.com` | |
| Polygon | `https://polygon-rpc.com` | |
| BSC | `https://bsc-dataseed.binance.org` | |
| Blast L2 | `https://rpc.blast.io` | **confirmed working June 2026** |
| zkSync Era | `https://mainnet.era.zksync.io` | |
| Scroll | `https://rpc.scroll.io` | |
| Avalanche C-chain | `https://api.avax.network/ext/bc/C/rpc` | |
| Mantle | `https://rpc.mantle.xyz` | |
| Linea | `https://rpc.linea.build` | |
| Gnosis | `https://rpc.gnosischain.com` | |
| Celo | `https://forno.celo.org` | |
| Metis | `https://andromeda.metis.io/?owner=1088` | |
| Mode | `https://mode.drpc.org` | via drpc |
| zkSync | `https://zksync.drpc.org` | via drpc |
| Mantle | `https://mantle.drpc.org` | via drpc |
| Celo | `https://celo.drpc.org` | via drpc |

**Blocked/timeout from some VPS environments (Tencent Cloud):**
- `https://mainnet.base.org` — timeout
- `https://rpc.ankr.com/eth` — **403 Unauthorized** (needs API key even for free tier — June 2026)
- `https://rpc.ankr.com/base` — connection refused
- `https://cloudflare-eth.com` — **403 Forbidden** (June 2026)
- `https://eth.llamarpc.com` — **403 Forbidden** (June 2026)
- `https://rpc.tenderly.co` — connection refused
- `https://etherscan.io` — Cloudflare bot detection (use Blockscout API instead)
- Etherscan API V1 — **deprecated** (must use V2 with API key)

**Confirmed working from this VPS (June 2026):**
- `https://api.coingecko.com` — price data (ETH price confirmed working)
- `https://blockstream.info/api` — BTC data (working)

### Quick multi-chain balance check pattern

```bash
# Cek native balance — ganti RPC + symbol per chain
curl -s -m 10 -X POST <RPC_URL> -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBalance","params":["<ADDR>","latest"],"id":1}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(int(d['result'],16)/1e18, 'SYMBOL')"
```

### Solana balance check

```bash
curl -s -m 10 "https://api.mainnet-beta.solana.com" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"getBalance","params":["<SOL_ADDR>"],"id":1}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['value']/1e9, 'SOL')"
```

**Pitfall:** Solana RPC sering timeout. Coba `https://solana-rpc.publicnode.com` atau pakai Helius private RPC.

### Ether balance → USD

```bash
# Ambil ETH price dari CoinGecko
PRICE=$(curl -s "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['ethereum']['usd'])")
# Hitung USD value
echo "$BALANCE * $PRICE" | bc
```