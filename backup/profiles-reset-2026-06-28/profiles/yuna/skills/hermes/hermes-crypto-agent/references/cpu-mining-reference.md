# CPU Mining Reference — Juno Cash & RandomX (June 2026)

## Juno Cash (JUNO)

**What:** Mandatory-privacy cryptocurrency (all transactions shielded via Orchard/zk-SNARKs). Similar to Monero but with stronger privacy guarantees.

**Algorithm:** RandomX (CPU-optimized, anti-ASIC)

**Mining Software:**
- `junocashd` — full node + wallet + solo mining
- `junorig` — pool mining software
- GitHub: https://github.com/juno-cash/junocash/releases
- Latest: v0.9.12 (NU6.2 hard fork, Orchard re-enabled)

**Requirements:**
| Spec | Minimum | Notes |
|------|---------|-------|
| CPU | x86-64 modern | Intel or AMD, AES instructions required |
| RAM | 2GB free per thread | RandomX uses ~2GB per mining thread |
| Disk | ~20GB | Full node blockchain |
| OS | Linux/Windows/macOS | |
| Network | Stable | Always-on for pool mining |

**Mining Methods:**
1. **Pool mining** (recommended for small hashrate): `./junorig -o stratum+tcp://POOL:3333 -u YOUR_J1_ADDRESS -p x`
2. **Solo mining** (only for large hashrate): `./junocashd -gen=1 -genproclimit=-1`

**Pools:**
- junopool.com
- junohash.com
- juno.suprnova.cc
- juno-cash.minerlab.io

**Wallet:** https://thejunowallet.com/ (web wallet, j1 address format)

**Docs:** https://juno.cash/get-started/
**Mining Guide:** https://juno.cash/mining/

## VPS Mining Feasibility Checklist

Before mining on VPS, verify:
1. **RAM**: `free -h` — need 2GB free MINIMUM per thread
2. **CPU cores**: `nproc` — more cores = more hashrate
3. **Disk**: `df -h /` — need 20GB+ free for full node
4. **Provider policy**: Some VPS providers ban mining in ToS
5. **Cost vs reward**: VPS cost often exceeds mining revenue for small setups

## RandomX Hashrate Estimates

| CPU | Cores | Expected Hashrate |
|-----|-------|-------------------|
| Xeon Platinum 8255C @ 2.5GHz | 2 | ~200-400 H/s |
| AMD Ryzen 5 3600 | 6 | ~4,000-5,000 H/s |
| AMD Ryzen 9 5950X | 16 | ~12,000-14,000 H/s |
| Intel i7-12700K | 12 | ~7,000-9,000 H/s |

**Note:** RandomX performs best on CPUs with large L3 caches. AMD Ryzen processors are particularly effective.

## Other CPU-Mineable Coins (2026)

| Coin | Algorithm | Privacy | Notes |
|------|-----------|---------|-------|
| Monero (XMR) | RandomX | Optional | Most established CPU mineable coin |
| Juno Cash (JUNO) | RandomX | Mandatory | Newer, smaller network |
| Wownero (WOW) | RandomX | Optional | Meme + privacy |
| Arqma (ARQ) | RandomX | Optional | Small community |

## Pitfalls

1. **RAM starvation**: RandomX needs 2GB/thread. If VPS has 1.9GB total RAM, mining will fail or cause OOM kills.
2. **Node sync time**: First sync can take hours/days depending on chain size and disk I/O.
3. **Pool minimum payout**: Small miners may take weeks to reach payout threshold.
4. **VPS provider bans**: Some providers (AWS, GCP, Azure) prohibit mining. Check ToS.
5. **Electricity cost**: VPS monthly cost often exceeds mining revenue for small hashrate.
6. **Heat/throttling**: Sustained 100% CPU can cause thermal throttling on shared VPS.
