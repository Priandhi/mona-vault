"""
Modal.com Solo Miner Template — Prebuilt Binary + Full Node + Validated Model Baking
For miners that need a local full node (e.g., Keryx).

Usage:
  source ~/modal-env/bin/activate
  modal deploy app.py     # 24/7 persistent (recommended for mining)
  modal run app.py        # one-shot (testing only)
"""
import modal

# ── CONFIG ──────────────────────────────────────────
WALLET = "keryx:PASTE_YOUR_ADDRESS"
GPU = "T4"

NODE_URL = "https://github.com/ORG/node/releases/download/TAG/node-linux-amd64.zip"
MINER_URL = "https://github.com/ORG/miner/releases/download/TAG/miner-linux-amd64.zip"

# Model files — ALWAYS prefer HuggingFace CDN (150x faster than IPFS)
# HuggingFace: ~150 MB/s vs IPFS gateway: ~1 MB/s
MODEL_FILES = {
    # filename: (url, is_json, min_size_bytes)
    "tokenizer.json": ("https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0/resolve/main/tokenizer.json", True, 1000),
    "config.json": ("https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0/resolve/main/config.json", True, 100),
    "model.safetensors": ("https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0/resolve/main/model.safetensors", False, 100_000_000),
}
# IPFS fallback (only if model not on HuggingFace):
# "tokenizer.json": ("https://keryx-labs.com/ipfs/<CID>", True, 1000),
# "config.json": ("https://keryx-labs.com/ipfs/<CID>", True, 100),
# "model.safetensors": ("https://keryx-labs.com/ipfs/<CID>", False, 100_000_000),

NODE_BIN = "/opt/node/keryxd"
NODE_PORT = 22110
MINER_BIN = "/opt/miner/keryx-miner"
MODEL_DIR = "/opt/miner/models/TinyLlama-1.1B"
MINER_ARGS = ["--cpu-inference", "--light", "-t", "4"]
# ────────────────────────────────────────────────────

app = modal.App("solo-miner")

# Build validated model download commands
model_cmds = [f"set -e && mkdir -p {MODEL_DIR} && cd {MODEL_DIR}"]
for fname, (url, is_json, min_size) in MODEL_FILES.items():
    retry_opts = "--retry 5 --retry-delay 3"
    if not is_json:
        retry_opts += " --connect-timeout 30 --max-time 900"  # large file
    model_cmds.append(f"curl -L {retry_opts} '{url}' -o {fname}")
    if is_json:
        model_cmds.append(f"python3 -c \"import json; json.load(open('{fname}'))\"")
    else:
        model_cmds.append(
            f"python3 -c \"import os; s=os.path.getsize('{fname}'); "
            f"assert s>{min_size}, f'Too small: {{s}}'\""
        )
model_cmds.append("touch .ok")
model_cmds.append(f"ls -lh {MODEL_DIR}/")

miner_image = (
    modal.Image.from_registry("nvidia/cuda:12.2.2-runtime-ubuntu22.04", add_python="3.11")
    .apt_install("ca-certificates", "curl", "unzip")
    # Download node
    .run_commands(
        f"cd /opt && curl -sL {NODE_URL} -o node.zip && "
        f"unzip -o node.zip -d /opt/node && rm node.zip && "
        f"chmod +x {NODE_BIN}"
    )
    # Download miner (remove crashing CUDA plugins if needed)
    .run_commands(
        f"cd /opt && curl -sL {MINER_URL} -o miner.zip && "
        f"unzip -o miner.zip -d /opt/miner && rm miner.zip && "
        f"chmod +x {MINER_BIN} && "
        f"rm -f /opt/miner/libkeryxcuda.so /opt/miner/libkeryxopencl.so"
    )
    # Bake model into image with validation
    .run_commands(" && ".join(model_cmds))
)


@app.function(image=miner_image, gpu=GPU, timeout=86400, max_containers=1)
def mine(wallet: str = WALLET):
    import subprocess as sp, os, signal, sys, time, socket, select

    # ── Verify model files at runtime ──
    required = list(MODEL_FILES.keys())
    for f in required:
        fp = os.path.join(MODEL_DIR, f)
        if not os.path.exists(fp):
            print(f"❌ Missing: {f}"); sys.exit(1)
        print(f"  ✅ {f}: {os.path.getsize(fp):,} bytes")
    print("✅ All model files verified!")

    # ── Start full node ──
    print("🔗 Starting node...")
    node = sp.Popen([NODE_BIN, "--utxoindex"],
        stdout=sp.PIPE, stderr=sp.STDOUT, text=True, bufsize=1)

    print(f"⏳ Waiting for node on port {NODE_PORT}...")
    for i in range(180):
        time.sleep(1)
        try:
            s = socket.create_connection(("127.0.0.1", NODE_PORT), timeout=1)
            s.close(); print(f"✅ Node ready! ({i+1}s)"); break
        except (ConnectionRefusedError, OSError):
            if i % 15 == 0: print(f"   ... {i}s")
    else:
        print("❌ Node timeout, trying anyway...")

    # ── Start miner ──
    cmd = [MINER_BIN, "--mining-address", wallet] + MINER_ARGS
    print(f"⛏️  Mining: {' '.join(cmd)}")
    miner = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT, text=True, bufsize=1)

    def shutdown(signum, frame):
        for p in [miner, node]:
            try: p.terminate(); p.wait(timeout=5)
            except: p.kill()
        sys.exit(0)
    signal.signal(signal.SIGTERM, shutdown)

    streams = {node.stdout: "🔗 NODE", miner.stdout: "⛏️  MINE"}
    try:
        while True:
            ready, _, _ = select.select(list(streams.keys()), [], [], 5)
            for f in ready:
                line = f.readline()
                if line: print(f"[{streams[f]}] {line}", end="", flush=True)
            if miner.poll() is not None:
                print(f"\n⛏️  Miner exited: {miner.returncode}"); break
            if node.poll() is not None:
                print(f"\n🔗 Node exited, restarting...")
                node = sp.Popen([NODE_BIN, "--utxoindex"],
                    stdout=sp.PIPE, stderr=sp.STDOUT, text=True, bufsize=1)
                streams[node.stdout] = "🔗 NODE"
    except KeyboardInterrupt: pass
    finally:
        for p in [miner, node]:
            if p.poll() is None: p.terminate()


@app.local_entrypoint()
def main(wallet: str = WALLET):
    print(f"🚀 Solo Mining on {GPU}")
    mine.remote(wallet)
