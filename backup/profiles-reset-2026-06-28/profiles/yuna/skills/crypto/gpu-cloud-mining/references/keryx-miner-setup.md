# Keryx Miner Build Reference

Source: https://github.com/Keryx-Labs/keryx-miner

## What is Keryx?

Keryx combines two mining mechanisms:
1. **GPU PoW** (kHeavyHash) — traditional proof-of-work
2. **OPoI** (Optimistic Proof of Inference) — on-chain AI inference verification

The miner runs AI models on GPU during inference challenges, earning extra rewards.

## Build from Source (CUDA)

Requires: Rust/Cargo, CUDA 12.2, protoc, GCC ≤ 12

```bash
# Install CUDA 12.2 toolkit (no root, no driver)
wget https://developer.download.nvidia.com/compute/cuda/12.2.2/local_installers/cuda_12.2.2_535.104.05_linux.run
bash cuda_12.2.2_535.104.05_linux.run --silent --toolkit --toolkitpath="$HOME/cuda-12.2"

# Clone and build
git clone https://github.com/Keryx-Labs/keryx-miner.git
cd keryx-miner
CUDA_COMPUTE_CAP=86 \
  CUDA_ROOT="$HOME/cuda-12.2" CUDA_PATH="$HOME/cuda-12.2" \
  PATH="$HOME/cuda-12.2/bin:$PATH" \
  cargo build --release --bin keryx-miner
```

Binary: `target/release/keryx-miner`

## Prebuilt Binary (Faster — Use This First)

Always check releases BEFORE compiling. Saves 10-20 min build time.

```bash
# Miner + plugins
curl -sL https://github.com/Keryx-Labs/keryx-miner/releases/download/v0.3.2-OPoI/keryx-miner-v0.3.2-OPoI-linux-gnu-amd64.zip -o miner.zip
unzip -o miner.zip -d /opt/keryx-miner && rm miner.zip
chmod +x /opt/keryx-miner/keryx-miner

# Node daemon (keryxd + keryx-cli)
curl -sL https://github.com/Keryx-Labs/keryx-node/releases/download/v1.2.6-OPoI/keryx-node-v1.2.6-OPoI-linux-amd64.zip -o node.zip
unzip -o node.zip -d /opt/keryx && rm node.zip
chmod +x /opt/keryx/keryxd /opt/keryx/keryx-cli
```

## TinyLlama Model Baking

The miner downloads TinyLlama 2.2GB on first run. Bake into Modal image to avoid re-downloading.

**PRIMARY: HuggingFace CDN (~150 MB/s, downloads in ~14 seconds)**
- tokenizer.json: `https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0/resolve/main/tokenizer.json`
- config.json: `https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0/resolve/main/config.json`
- model.safetensors: `https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0/resolve/main/model.safetensors`

**FALLBACK: IPFS via keryx-labs.com (~1 MB/s, 35+ minutes for 2.2GB)**
Only use if HuggingFace is down or model doesn't exist there:
- tokenizer.json: `https://keryx-labs.com/ipfs/QmSKrRu8HRt9v2dUeVdABKDkuREa5xFhPLZdevvvBfDYmp` (~1.8MB)
- config.json: `https://keryx-labs.com/ipfs/QmbLTR3GLjBUKw8Lj14isiwG3XZJaL61ES852vkNqNPhyd` (~600B)
- model.safetensors: `https://keryx-labs.com/ipfs/QmdqcmS8aMngiZWYYdeZEaW22N6XRTd9zK5ZCJG1MPmrQ3` (~2.1GB)

**CRITICAL**: Always validate downloads with JSON parse + size check. IPFS gateways can return HTML error pages with HTTP 200. See SKILL.md "IPFS Gateway Model Baking" section for the full validated download pattern.

The miner expects models at `$(dirname keryx-miner)/models/TinyLlama-1.1B/` (it creates subdirectories).

The `.ok` sentinel file at `models/TinyLlama-1.1B/.ok` tells the miner the model is ready. Only create it AFTER all files pass validation.

## CRITICAL: Plugin System

Keryx uses a **plugin architecture** for GPU workers. The CUDA plugin (`libkeryxcuda.so`) is a SEPARATE crate in `plugins/cuda/`. 

**You MUST build ALL workspace members**, not just the binary:
```bash
# WRONG — only builds binary, no GPU plugin:
cargo build --release --bin keryx-miner

# RIGHT — builds binary + CUDA plugin + OpenCL plugin:
cargo build --release
```

After build, `target/release/` contains:
- `keryx-miner` (binary)
- `libkeryxcuda.so` (CUDA GPU plugin)
- `libkeryxopencl.so` (OpenCL plugin)

The miner auto-discovers `.so` plugins in the same directory as the binary.

**T4 GPU WARNING**: The CUDA plugin's PTX chain targets sm_86/sm_89/sm_100 but NOT sm_75 (T4). On T4, the plugin will crash with SIGSEGV. **Fix**: Remove the plugin (`rm libkeryxcuda.so`) and use `--cpu-inference --light -t 4` for CPU-only mining. The CPU miner still works, just no GPU PoW acceleration.

## cust Crate CUDA Detection Issue

The `cust` crate (v0.3.2) used by the CUDA plugin calls `cuInit(0)` via `dlopen("libcuda.so.1")`. In container environments (Modal, Docker), this often fails with `NotInitialized` even though `nvidia-smi` works.

**Fix**: Set `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libcuda.so.1` before running the miner.

Also register CUDA runtime libs in ldconfig during image build:
```bash
echo '/usr/local/cuda/targets/x86_64-linux/lib' > /etc/ld.so.conf.d/cuda.conf
echo '/usr/local/cuda-12.2/compat' >> /etc/ld.so.conf.d/cuda.conf
ldconfig
```

## Solo Mining — Requires keryxd Node

Keryx miner connects to a **local `keryxd` daemon** via gRPC on `127.0.0.1:22110` (mainnet) by default. This is **solo mining** — you need:
1. A running `keryxd` (Keryx full node daemon) — separate binary, not in this repo
2. The node synced with the blockchain
3. Miner pointed at the node: `--keryxd-address grpc://IP:22110`

For pool mining, check if public stratum pools exist: `stratum+tcp://pool:port`

## Useful Flags

| Flag | Purpose |
|------|---------|
| `--light` | TinyLlama only (4GB VRAM) |
| `--no-opoi` | PoW only, no AI inference |
| `--cpu-inference` | Skip GPU inference probe, run inference on CPU |
| `-t N` | CPU thread fallback workers (avoids "No workers specified") |
| `--keryxd-address IP:PORT` | Connect to remote keryxd node |

## CUDA Compute Capability

| GPU | CUDA_COMPUTE_CAP |
|-----|-------------------|
| T4 (Turing) | 75 |
| RTX 30xx (Ampere) | 86 |
| RTX 40xx (Ada) | 89 |
| A100 (Ampere) | 80 |
| RTX 50xx (Blackwell) | 100 |

## Inference Tiers (OPoI)

| Flag | Models | Min VRAM |
|------|--------|----------|
| (none) | TinyLlama 1.1B + DeepSeek-R1-8B | 8 GB |
| `--light` | TinyLlama 1.1B only | 4 GB |
| `--high` | + DeepSeek-R1-32B | 24 GB |
| `--very-high` | + LLaMA-3.3-70B | 32 GB |

Models load on-demand during inference challenges, mining pauses during inference.

## Runtime Command

```bash
./keryx-miner --mining-address keryx:YOUR_ADDRESS [--light|--high|--very-high] [--no-opoi]
```

## Runtime Dependencies

- `libcuda.so.1` (driver) — always needed for PoW
- `libcublas.so.12` + `libcurand.so.10` — needed for GPU inference (OPoI)
- Install via CUDA 12.2 toolkit or package manager

## Dev Fund

2% of mining rewards go to dev fund by default.
Customize: `--devfund-percent XX.YY`

## Container Build (if host gcc too new)

```bash
podman run --rm --security-opt label=disable \
  -v "$PWD":/src -w /src \
  -e CUDA_COMPUTE_CAP=86 \
  -e CARGO_TARGET_DIR=/src/target-cuda \
  docker.io/nvidia/cuda:12.2.2-devel-ubuntu22.04 \
  bash -c '
    apt-get update -qq && apt-get install -y -qq \
      curl build-essential pkg-config libssl-dev ca-certificates protobuf-compiler
    curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
    . "$HOME/.cargo/env"
    export CUDA_PATH=/usr/local/cuda PROTOC=/usr/bin/protoc
    cargo build --release --bin keryx-miner'
```

## Links

- Website: https://keryx-labs.com
- Wallet: https://keryx-labs.com/wallet
- Explorer: https://keryx-labs.com/explorer
- Twitter: @Keryx_Labs
- Discord: https://discord.gg/U9eDmBUKTF
