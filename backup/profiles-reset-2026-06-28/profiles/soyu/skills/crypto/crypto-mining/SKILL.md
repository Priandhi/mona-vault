---
name: "crypto-mining"
description: "CPU and GPU crypto mining on VPS and cloud infrastructure. Covers RandomX/Juno Cash on low-RAM VPS, and GPU-based miners on serverless cloud platforms. Use when setting up a miner, troubleshooting hash rate, or choosing a coin for the hardware you have."
tags:
  - "crypto"
  - "mining"
  - "randomx"
  - "juno-cash"
  - "gpu"
  - "vps"
  - "cloud-mining"
---
# Crypto Mining Operations

> CPU/GPU mining setup on cloud and VPS infrastructure. Covers RandomX (CPU), Juno Cash, and GPU-based mining.

## Quick Decision Tree

| User says... | Load |
|--------------|------|
| "vps mining", "RandomX", "Juno Cash", "cpu mining" | `references/vps-mining-setup/` |
| "gpu cloud", "GPU mining", "serverless miner" | `references/gpu-cloud-mining/` |

## Topic Pages

- `references/vps-mining-setup/SKILL.md` — Setup CPU mining (RandomX/Juno Cash) on VPS
- `references/gpu-cloud-mining/SKILL.md` — Deploy GPU-based crypto miners on serverless cloud platforms

## PITFALLS

1. **Low-RAM VPS (<2GB) requires Juno Cash** (not RandomX). RandomX needs 2-4GB just for the dataset.
2. **GPU mining on serverless has egress costs.** Most cloud GPUs lose money on mining — only profitable with very specific altcoins.
3. **PITFALL: Swapfile tricks can crash the host.** Always set up swap as a file, not a partition, and monitor `vmstat 1` for swap pressure.

## Related

- `process-ops` (in devops/) — for keeping the miner alive
- `pm2-process-health` — for monitoring
