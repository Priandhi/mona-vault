"""
Modal.com GPU Miner Template
Copy and modify for any GPU-based crypto miner.

Usage:
  modal run app.py --wallet-address keryx:YOUR_ADDRESS
  modal deploy app.py  (keeps running, auto-restarts)
"""

import modal

# ── CONFIG ──────────────────────────────────────────
WALLET_ADDRESS = "keryx:PASTE_YOUR_ADDRESS"
GPU_TYPE = "T4"              # T4, A10G, A100_40GB, A100_80GB, H100
MINER_REPO = "https://github.com/Keryx-Labs/keryx-miner.git"
MINER_BIN = "/opt/miner/target/release/keryx-miner"
EXTRA_ARGS = []              # e.g. ["--light", "--no-opoi"]
CUDA_VERSION = "12.2.2"
CUDA_IMAGE = f"nvidia/cuda:{CUDA_VERSION}-devel-ubuntu22.04"
BUILD_CMD = "cd /opt/miner && cargo build --release 2>&1 | tail -5"  # NOTE: build ALL workspace members, not just --bin
# ────────────────────────────────────────────────────

app = modal.App("gpu-miner")

# Map friendly names to Modal GPU identifiers
GPU_MAP = {
    "T4": "T4",
    "A10G": "A10G",
    "A100_40GB": "A100-40GB",
    "A100_80GB": "A100-80GB",
    "H100": "H100",
}

# CUDA compute capability by GPU
COMPUTE_CAP_MAP = {
    "T4": "75",
    "A10G": "86",
    "A100-40GB": "80",
    "A100-80GB": "80",
    "H100": "90",
}

miner_image = (
    modal.Image.from_registry(CUDA_IMAGE, add_python="3.11")
    .apt_install(
        "protobuf-compiler", "build-essential", "pkg-config",
        "libssl-dev", "ca-certificates", "curl", "git", "cmake",
        "libcublas-12-2", "libcurand-12-2",  # CUDA runtime libs for GPU inference
    )
    .run_commands(
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs "
        "| sh -s -- -y --profile minimal",
        f"git clone {MINER_REPO} /opt/miner",
    )
    .env({
        "PATH": "/root/.cargo/bin:/usr/local/cuda/bin:$PATH",
        "CUDA_PATH": "/usr/local/cuda",
        "CUDA_COMPUTE_CAP": COMPUTE_CAP_MAP.get(GPU_TYPE, "75"),
    })
    .run_commands(BUILD_CMD)
    # Register CUDA runtime libs in ldconfig so dlopen can find them
    .run_commands(
        "echo '/usr/local/cuda/targets/x86_64-linux/lib' > /etc/ld.so.conf.d/cuda.conf && "
        "echo '/usr/local/cuda-12.2/compat' >> /etc/ld.so.conf.d/cuda.conf && ldconfig"
    )
)


@app.function(
    image=miner_image,
    gpu=GPU_MAP.get(GPU_TYPE, GPU_TYPE),
    timeout=86400,         # 24 hours
    min_containers=1,      # no cold start (was keep_warm)
    max_containers=1,      # prevent duplicate instances (was concurrency_limit)
)
def mine(wallet_address: str = WALLET_ADDRESS):
    """Run the miner inside a GPU container."""
    import subprocess, os, signal, sys

    os.environ["LD_LIBRARY_PATH"] = (
        "/usr/local/cuda/targets/x86_64-linux/lib:"
        "/usr/local/cuda/lib64:"
        "/usr/local/cuda-12.2/compat:" + os.environ.get("LD_LIBRARY_PATH", "")
    )
    # Force CUDA driver lib load — fixes cust crate NotInitialized in containers
    os.environ["LD_PRELOAD"] = "/usr/lib/x86_64-linux-gnu/libcuda.so.1"
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"

    cmd = [MINER_BIN, "--mining-address", wallet_address] + EXTRA_ARGS

    print(f"⛏️  Starting miner...")
    print(f"   Wallet: {wallet_address}")
    print(f"   GPU: {GPU_TYPE}")
    print(f"   Command: {' '.join(cmd)}")
    print("=" * 60)

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )

    def sigterm_handler(signum, frame):
        print("\n🛑 Gracefully stopping miner...")
        proc.terminate()
        proc.wait(timeout=10)
        sys.exit(0)

    signal.signal(signal.SIGTERM, sigterm_handler)

    try:
        for line in proc.stdout:
            print(line, end="", flush=True)
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait(timeout=10)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()

    print(f"\n⛏️  Miner exited with code {proc.returncode}")
    return proc.returncode


@app.local_entrypoint()
def main(wallet_address: str = WALLET_ADDRESS):
    """Run miner: modal run app.py --wallet-address keryx:XXX"""
    print(f"🚀 Launching GPU Miner on Modal.com ({GPU_TYPE})...")
    mine.remote(wallet_address)
