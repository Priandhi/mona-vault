# Juno Cash Pool Mining — xmrig Config Reference

## Pool Ports (as of Jun 2026)

| Pool | URL | Stratum Port | Notes |
|------|-----|-------------|-------|
| Suprnova | juno.suprnova.cc | 3333 | Often blocked by cloud providers |
| JunoPool | junopool.com | 3333 | Often blocked by cloud providers |
| JunoHash | junohash.com | 3333 | Often blocked by cloud providers |
| MinerLab | juno-cash.minerlab.io | 3333 | Often blocked by cloud providers |
| NanoPool | juno.nanopool.org | 443 | Port 443 usually open |

## Cloud Provider Port Workaround

Most cloud VPS providers block outbound port 3333 (stratum). Test with `nc -zv <pool> <port>`.

**Options if blocked:**
1. Open port in provider firewall/dashboard
2. Use a pool on port 443 (e.g., NanoPool)
3. Setup wireguard/VPN on VPS

## xmrig Build & Config

Build from source (no pre-built binaries for RandomX pools):
```bash
apt install -y git build-essential cmake libuv1-dev libssl-dev libhwloc-dev
git clone https://github.com/xmrig/xmrig.git && cd xmrig
mkdir build && cd build && cmake .. -DWITH_OPENCL=OFF -DWITH_CUDA=OFF && make -j$(nproc)
```

Config template — write locally with `write_file`, then `scp` to VPS (don't use SSH heredoc for JSON):
```json
{
    "cpu": {"enabled": true, "huge-pages": true, "hw-aes": true, "max-threads-hint": 100},
    "pools": [{"algo": "rx/0", "url": "POOL:PORT", "user": "j1ADDRESS", "pass": "x"}]
}
```

## Solo vs Pool Mining

- **junocashd -gen=1** = solo mining only (no pool stratum). Needs local wallet. Very rare blocks on low hashrate.
- **xmrig** = pool mining. Direct to any J1 address. Consistent small payouts. **Recommended for VPS.**
