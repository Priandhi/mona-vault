---
name: gpu-cloud-mining
description: "Deploy GPU-based crypto miners on serverless cloud platforms (Modal.com, RunPod, Vast.ai). Covers CLI setup, auth, GPU selection/cost optimization, CUDA builds from source, and long-running job management."
triggers:
  - GPU mining on cloud
  - Modal.com GPU setup
  - RunPod mining
  - Vast.ai GPU rental
  - serverless GPU miner deploy
  - cloud GPU crypto mining
  - CUDA miner build
  - keryx miner
  - GPU PoW mining
---

# GPU Cloud Mining

Deploy GPU-based crypto miners on serverless cloud platforms. Covers Modal.com (primary), with notes for RunPod/Vast.ai.

## Prerequisites

- Cloud platform account with credits (Modal.com gives $30/mo free on Starter)
- Miner repo URL (must be open-source or pre-compiled binary)
- Wallet address for the target chain

## Modal.com Setup (Step-by-Step)

### 1. Install Modal CLI

Modal CLI must be installed in a venv due to PEP 668 on Ubuntu 24+:

```bash
python3 -m venv ~/modal-env
source ~/modal-env/bin/activate
pip install modal
```

> **PITFALL**: Do NOT use `pip install --break-system-packages`. Always use a venv.

### 2. Authenticate (Headless VPS)

On a headless VPS, `modal token new` won't work (needs browser). Instead:

1. User opens https://modal.com on their phone/laptop
2. Sign up / Login (Google auth works)
3. Go to **Settings → API Tokens → Create Token**
4. Copy Token ID (`ak-xxxx`) and Token Secret (`as-xxxx`)
5. Set on VPS:

```bash
source ~/modal-env/bin/activate
modal token set --token-id ak-xxxx --token-secret as-xxxx
```

### 3. GPU Selection & Cost

Modal.com GPU pricing (as of June 2025):

| GPU | VRAM | $/hr | $30 budget ≈ hours | Best for |
|-----|------|------|---------------------|----------|
| T4 | 16GB | $0.59 | ~50 hrs | Light mining, small models |
| A10G | 24GB | $1.10 | ~27 hrs | Mid-tier inference |
| A100 40GB | 40GB | $2.10 | ~14 hrs | Heavy inference |
| A100 80GB | 80GB | $2.50 | ~12 hrs | Full model loading |
| H100 | 80GB | $4.54 | ~6.6 hrs | Maximum throughput |

**Rule of thumb**: Pick the cheapest GPU that meets the miner's VRAM requirement. Don't overspend on GPU tier.

### 4. Build Modal App

See `templates/modal-gpu-miner.py` — a reusable template for deploying any GPU miner.

Key Modal app patterns:
- `modal.Image.from_registry("nvidia/cuda:12.2.2-devel-ubuntu22.04")` — use CUDA 12.2 for widest driver compat
- `timeout=86400` — 24hr max per container run
- `min_containers=1` — avoid cold starts (renamed from `keep_warm` in SDK v1.5+)
- `max_containers=1` — prevent duplicate mining instances (renamed from `concurrency_limit` in SDK v1.5+)
- `LD_LIBRARY_PATH` must include CUDA libs at runtime
- `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libcuda.so.1` — fixes `cust` crate CUDA detection in containers (see Pitfalls)
- Install CUDA runtime libs via apt: `libcublas-12-2`, `libcurand-12-2`
- Register CUDA libs in ldconfig: `echo '/usr/local/cuda/targets/x86_64-linux/lib' > /etc/ld.so.conf.d/cuda.conf && ldconfig`

### 5. Run vs Deploy

```bash
source ~/modal-env/bin/activate
cd /path/to/app

# One-shot run (container dies when function returns)
modal run app.py

# Persistent deploy (app stays alive, auto-restarts, 24/7)
modal deploy app.py
```

**For mining: always use `modal deploy`** — it creates a persistent app that runs 24/7 without needing manual re-trigger. `modal run` is for testing only.

To check deployed apps: `modal app list`
To stop: `modal app stop <app-name>`

## Prebuilt Binary Approach (Preferred)

Always check for prebuilt releases BEFORE compiling from source. Compiling Rust+CUDA takes 10-20 min and costs credits.

```bash
# Download prebuilt miner + plugins
curl -sL https://github.com/ORG/PROJECT/releases/download/TAG/linux-amd64.zip -o miner.zip
unzip -o miner.zip -d /opt/miner && rm miner.zip
chmod +x /opt/miner/miner-binary
```

**When to compile from source instead:**
- No prebuilt binary for your platform
- Need custom build flags or features
- Binary doesn't include plugins you need

## Model Baking (ML Miners)

Miners that download ML models at runtime (e.g., TinyLlama 2.2GB) waste time and credits on each restart. Bake models into the Modal image:

```python
.run_commands(
    "mkdir -p /opt/miner/models && cd /opt/miner/models && "
    "curl -sL https://huggingface.co/MODEL/resolve/main/model.safetensors -o model.safetensors && "
    "curl -sL https://huggingface.co/MODEL/resolve/main/tokenizer.json -o tokenizer.json"
)
```

This makes the image larger (~4GB) but subsequent runs start instantly with no download.

### Model Baking — Mirror Selection (CRITICAL)

**ALWAYS prefer HuggingFace CDN over IPFS gateways for model downloads.** Speed difference is 100-150x:

| Source | Speed (typical) | 2.2GB download time |
|--------|-----------------|---------------------|
| HuggingFace CDN | ~150 MB/s | ~14 seconds |
| keryx-labs.com IPFS | ~1 MB/s | ~35 minutes |
| ipfs.io gateway | ~0.5 MB/s | ~1+ hour |

For Keryx TinyLlama, use HuggingFace mirror:
```python
"https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0/resolve/main/tokenizer.json"
"https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0/resolve/main/config.json"
"https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0/resolve/main/model.safetensors"
```

Only fall back to IPFS if the model isn't on HuggingFace.

### IPFS Gateway Model Baking (fallback only)

Some miners fetch models from IPFS gateways (e.g., `https://keryx-labs.com/ipfs/<CID>`) instead of HuggingFace. These downloads are slower and more fragile. **Critical safeguards:**

```python
.run_commands(
    "set -e && "
    "mkdir -p /opt/keryx-miner/models/TinyLlama-1.1B && "
    "cd /opt/keryx-miner/models/TinyLlama-1.1B && "
    # Small files: retry + JSON validation
    "curl -sL --retry 3 --retry-delay 5 'https://keryx-labs.com/ipfs/<CID>' -o tokenizer.json && "
    "python3 -c \"import json; json.load(open('tokenizer.json'))\" && "
    "curl -sL --retry 3 --retry-delay 5 'https://keryx-labs.com/ipfs/<CID>' -o config.json && "
    "python3 -c \"import json; json.load(open('config.json'))\" && "
    # Large file: retry + size validation (must be >100MB for safetensors)
    "curl -L --retry 3 --retry-delay 10 --connect-timeout 30 --max-time 900 "
    "'https://keryx-labs.com/ipfs/<CID>' -o model.safetensors && "
    "python3 -c \"import os; s=os.path.getsize('model.safetensors'); assert s>100000000, f'Too small: {s}'\" && "
    # Sentinel ONLY after ALL files verified
    "touch .ok && ls -lh /opt/keryx-miner/models/TinyLlama-1.1B/"
)
```

**Key lessons (Jun 2026):**
- Without `--retry`, IPFS gateway downloads silently return HTML error pages (200 OK but wrong content). The miner then crashes with `load tokenizer: expected value at line 1 column 1`.
- Always validate file content (JSON parse for JSON files, size check for binary files) BEFORE creating the `.ok` sentinel.
- The `.ok` sentinel must be the LAST step — if any download fails, `set -e` aborts before creating it.
- `--connect-timeout 30 --max-time 900` prevents hanging on slow IPFS gateways for large files.

### Runtime Model Verification

Always verify model files at container startup (not just image build):

```python
# At the start of your mine() function:
model_dir = "/opt/keryx-miner/models/TinyLlama-1.1B"
required = ["tokenizer.json", "config.json", "model.safetensors"]
for f in required:
    fp = os.path.join(model_dir, f)
    if not os.path.exists(fp):
        print(f"❌ Missing: {f}")
        sys.exit(1)
    sz = os.path.getsize(fp)
    print(f"  ✅ {f}: {sz:,} bytes")
```

## CUDA Build Tips

- **CUDA 12.2** recommended: JIT on driver ≥535 (most common)
- **CUDA_COMPUTE_CAP**: T4=75, A10G=86, A100=80, RTX40xx=89
- If host gcc is too new (13+), build inside `nvidia/cuda:12.2.2-devel-ubuntu22.04` container
- Runtime needs `libcuda.so.1` (driver) + `libcublas.so.12` + `libcurand.so.10`

## Modal Volume Persistence (CRITICAL for node-sync miners)

Modal containers are ephemeral — all data is LOST on restart. For miners that need a full node with hours of blockchain sync, this means re-syncing from scratch every restart ($0.60-1.20 wasted per restart on T4).

**Solution: Modal Volumes** — persistent network storage that survives container restarts.

```python
# Create/reuse persistent volume
keryx_vol = modal.Volume.from_name("keryx-blockchain", create_if_missing=True)

@app.function(
    image=miner_image,
    gpu=GPU,
    timeout=86400,
    max_containers=1,
    volumes={"/data/keryxd": keryx_vol},  # Mount volume
)
def mine(wallet: str = WALLET):
    data_dir = "/data/keryxd"
    os.makedirs(data_dir, exist_ok=True)
    
    # Check for existing data
    existing = os.listdir(data_dir) if os.path.exists(data_dir) else []
    if existing:
        print(f"📂 Found existing data: {len(existing)} items — resuming sync!")
    
    # Point node to persistent directory
    node = sp.Popen([NODE_BIN, "--utxoindex", "--appdir", data_dir], ...)
    
    # Commit volume periodically (every 5 min)
    last_commit = time.time()
    # ... in main loop:
    if time.time() - last_commit > 300:
        keryx_vol.commit()
        last_commit = time.time()
    
    # ALWAYS commit on shutdown
    def shutdown(signum, frame):
        keryx_vol.commit()  # Persist before exit!
        sys.exit(0)
```

**Key rules:**
1. Always `vol.commit()` on shutdown — otherwise unsynced data is lost
2. Auto-commit every 5 minutes in the main loop — crash loses at most 5 min of sync
3. Use `--appdir` flag to point the node to the mounted volume
4. Volume data persists across container restarts — sync resumes, not restarts

## `modal run --detach` vs `modal deploy` vs `modal run`

| Command | Container lifetime | Use case |
|---------|-------------------|----------|
| `modal run` | Dies when terminal disconnects | Testing only |
| `modal run --detach` | Stays alive after disconnect, but has timeout | Quick deploy, watchdog-supervised |
| `modal deploy` | Persistent app, auto-restarts | Production (but needs `modal run` to trigger) |

**Gotcha**: `modal deploy` creates the app definition but does NOT start a container. You still need to trigger the function with `modal run`. For mining, the best pattern is:

```bash
# 1. Deploy app definition (fast, no container started)
modal deploy app.py

# 2. Trigger with detach (container starts, stays alive after terminal closes)
modal run --detach app.py
```

**Gotcha**: `--detach` containers still have the `timeout` from `@app.function(timeout=86400)`. After 24h, container dies. Use a watchdog to restart.

## Watchdog Script (Auto-restart on VPS)

`modal run --detach` containers die after timeout. Use a VPS watchdog to auto-restart:

```bash
#!/bin/bash
# watchdog.sh — run in background on VPS
source ~/modal-env/bin/activate
cd /path/to/app

while true; do
    RUNNING=$(modal app list 2>&1 | grep "APP-NAME" | grep -c "ephemeral")
    if [ "$RUNNING" -eq 0 ]; then
        echo "[$(date)] Container dead — restarting..."
        modal run --detach app.py 2>&1 &
        sleep 30
    fi
    sleep 300  # Check every 5 minutes
done
```

Also set up a cron job for monitoring:
```bash
# Cron: check mining status every hour
0 * * * * source ~/modal-env/bin/activate && /path/to/monitor.sh >> /var/log/keryx-monitor.log 2>&1
```

## Multi-Container Credit Burn (PITFALL)

Old ephemeral apps are NOT automatically cleaned up. Each one can hold a running container that burns credits. **Always stop old apps before starting new ones:**

```bash
# List all apps
modal app list | grep APP-NAME

# Stop old ones
modal app stop <old-app-id> --yes

# Verify only 1 container running
modal app list | grep "ephemeral"
```

**Rule: Never have more than 1 ephemeral app running for the same miner.** Each T4 container costs $0.59/hr — 2 containers = $1.18/hr double burn.

## Pitfalls

1. **Modal credits expire**: Starter plan $30 is per-month, not cumulative
2. **Preemptible instances**: 3x cheaper but can be killed anytime — use for mining
3. **Region pricing**: 1.5-1.75x base prices for specific regions
4. **Build time counts**: Cargo build on first deploy takes 10-20 min and costs credits — use pre-built image or cache
5. **`max_containers=1`**: Always set this for mining to avoid accidentally running 2+ instances and double-spending credits
6. **No persistent storage**: Modal containers are ephemeral — wallet keys/configs must be passed as arguments, not stored on disk
7. **CRITICAL — `cust` crate CUDA detection fails in containers**: The Rust `cust` crate (used by many GPU miners) calls `cuInit(0)` via `dlopen("libcuda.so.1")`. In container environments, this often fails with `NotInitialized` even though `nvidia-smi` works. **Fix: `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libcuda.so.1`** — forces the CUDA driver library to load before the process starts. Verified working on Modal T4 containers.
8. **CUDA runtime libs not auto-installed**: The `nvidia/cuda:12.2.2-devel-ubuntu22.04` image has headers/compiler but NOT runtime libs (`libcublas.so.12`, `libcurand.so.10`). Must `apt_install("libcublas-12-2", "libcurand-12-2")` explicitly. These are at `/usr/local/cuda/targets/x86_64-linux/lib/` — register with ldconfig for dlopen to find them.
9. **Plugin-based miners need workspace-wide build**: If a miner has a plugin system (`.so` files loaded at runtime), `cargo build --release --bin <name>` only builds the binary, NOT the plugins. Use `cargo build --release` (no `--bin` flag) to build all workspace members. Example: Keryx miner needs `libkeryxcuda.so` plugin next to the binary.
10. **Solo mining vs pool mining**: Some miners (like Keryx) connect to a local full node (`keryxd`) via gRPC by default (`127.0.0.1:22110`). They don't connect to a public pool. For these, you either need to run the full node alongside the miner, or find a public stratum pool address. Check `stratum+tcp://` support in the miner's CLI.
11. **CUDA plugin PTX compute capability mismatch**: Some CUDA plugins only ship PTX for newer architectures (sm_86, sm_89, sm_100) but NOT sm_75 (T4). Even with correct drivers, the plugin will fail with `CUDA_ERROR_INVALID_PTX` or SIGSEGV. **Fix**: Check the plugin's target architectures. If T4 (sm_75) isn't supported, either: (a) use `--cpu-inference` flag + remove the CUDA plugin (rename `.so` to `.so.bak`), or (b) use a GPU with supported compute capability (A10G=sm_86, A100=sm_80).
12. **Disable CUDA plugin by renaming**: To prevent a crashing CUDA plugin from loading, simply rename it: `mv libkeryxcuda.so libkeryxcuda.so.bak`. The miner discovers plugins by scanning for `.so` files in its directory. No `.so` = no plugin = CPU-only mode.
13. **Full node + miner in same container**: For solo mining, run the full node daemon as a background process in the same Modal container. Use `socket.create_connection()` to wait for the node's gRPC port before starting the miner. Use `select.select()` to multiplex stdout from both processes.
14. **IPFS gateway returns HTML with 200 OK**: Some IPFS gateways (including `keryx-labs.com/ipfs/`) occasionally return an HTML error page instead of the actual file, but with HTTP 200 status. `curl -sL` happily saves this HTML as `tokenizer.json`, and the sentinel `.ok` gets created. The miner then crashes with `expected value at line 1 column 1`. **Fix**: Validate file content after download (JSON parse, size check) BEFORE creating any sentinel file. Use `set -e` to abort on first failure.
15. **Large downloads hang silently in image build**: Modal image builds have no timeout by default. A 2.2GB download from a slow IPFS gateway can hang for hours. **Fix**: Set `--connect-timeout 30 --max-time 900` on curl for large files. For even larger files, consider splitting into chunks or using a faster mirror.
16. **IPFS gateway speed trap**: IPFS gateways (keryx-labs.com, ipfs.io) are typically 100-150x slower than HuggingFace CDN. A 2.2GB model that downloads in 14 seconds from HuggingFace takes 35+ minutes from IPFS. **ALWAYS check if the model exists on HuggingFace first** — most popular open-source models (TinyLlama, LLaMA, Mistral) have official HF repos. Use the IPFS CID only as a last resort, and add `--retry 5` with content validation.
17. **`modal deploy` doesn't start containers**: `modal deploy` only registers the app definition. No container runs until you trigger with `modal run` or `modal run --detach`. Forgetting this means your "deployed" mining app has 0 tasks.
18. **`modal run` dies on disconnect**: Without `--detach`, the container is killed when the local terminal/session closes. Always use `--detach` for long-running mining.
19. **Old ephemeral apps burn credits**: Modal doesn't auto-clean old ephemeral apps. Each can hold a running container. Always `modal app stop <id> --yes` old apps before starting new ones. Check with `modal app list | grep ephemeral`.
20. **Volume commit on shutdown**: If you don't call `vol.commit()` before the container dies, any data written to the volume since the last commit is LOST. Always commit in the SIGTERM handler AND periodically in the main loop (every 5 min).
22. **Watchdog creates duplicate containers**: A naive watchdog that only checks `grep -c "ephemeral"` will restart a new container every 5 minutes if the check fails or if Modal API returns stale data. One session produced **7 simultaneous containers** burning $4.13/hr! **Fix**: Always count containers and kill duplicates before restarting. Use `MAX_CONTAINERS=1` guard. Better yet, use Hermes cron jobs instead of watchdog scripts — they have built-in dedup and auto-report to Telegram.
23. **`--detach` timeout is 24h**: Even with `--detach`, containers die after the `timeout=` value in `@app.function()` (default 86400s = 24h). For truly persistent mining, you need either a watchdog or Hermes cron job to restart after timeout.

## Automated Monitoring with Hermes Cron Jobs

For monitoring that auto-reports to Telegram and auto-restarts on failure, use Hermes cron jobs instead of (or alongside) the watchdog script:

```python
# Create via Hermes:
cronjob(
    action='create',
    name='mining-monitor',
    prompt='''Check mining status on Modal.com:
1. `modal app list 2>&1 | grep APP-NAME` — check if container alive
2. If no ephemeral app running, restart: `cd /path && modal run --detach app.py`
3. If running, check logs: `modal app logs <APP_ID> 2>&1 | grep -E "IBD|OPoI|Block" | tail -5`
4. Report: sync %, OPoI status, blocks found, container health
5. Keep message concise, Indonesian, with emojis, address user as "sayang"''',
    schedule='every 1h',
)
```

**Advantages over watchdog.sh:**
- Auto-reports to Telegram (user sees status without checking)
- Uses Hermes agent to interpret logs (not just grep)
- Can escalate (restart + alert) on failure
- Survives VPS reboot (managed by Hermes daemon)

**Combine both for maximum reliability:**
- `watchdog.sh` — checks every 5 min, fast restart
- Hermes cron — checks every 1h, detailed report to Telegram

## Debugging with Claude Code

For complex build failures, CUDA errors, or miner crashes — delegate to Claude Code for fast root-cause analysis:

```bash
# Ask Claude Code to analyze crash logs
claude "analyze this miner crash and suggest fix: <paste error>"

# Ask Claude Code to review/fix app.py
claude "review this Modal deployment script and fix issues: <path>"
```

Claude Code is configured with MiMo API (cheap, fast) and can:
- Analyze stack traces and crash dumps
- Review source code for logic errors
- Suggest CUDA compatibility fixes
- Write patches for deployment scripts

**User preference**: Heavy coding/debugging tasks should be delegated to Claude Code. Don't spend multiple turns debugging manually when Claude Code can solve it in one shot.

## Claude Code for All Coding Tasks

**User preference**: ALL coding tasks — even small ones — should be delegated to Claude Code. It's free (MiMo API) and faster than manual debugging.

```bash
# Quick delegation pattern
claude "fix this Modal deployment script: <paste error + code>"
claude "add Modal Volume persistence to this miner app: <path>"
claude "analyze this crash log and suggest fix: <paste>"
```

Don't spend multiple turns debugging manually when Claude Code can solve it in one shot.

## Keryx-Specific: Node Sync Bottleneck (Jun 2026)

**CRITICAL FINDING:** Keryx node (`keryxd v1.2.6`) has a sync bottleneck at **level 0 pruning point proof validation (219,062 headers)**. This is NOT a GPU issue — it's a node software limitation.

**Observed behavior:**
- Levels 83→1: Complete in ~1 minute (fast)
- Level 0 (219K headers): Stuck for 8+ hours without completing
- Happens on T4, and likely same on any GPU — it's CPU-bound header validation
- OPoI challenges pass during sync, but miner stays "stalled" until node fully synced
- Restarting the node restarts the entire pruning proof validation from scratch (even with Volume persistence)

**Impact:**
- $0.59/hr (T4) × 8+ hours = $4.72+ wasted per attempt
- Node never actually reaches fully synced state in observed sessions
- Mining never starts (miner stays "Workers stalled or crashed")

**Recommendation:**
- Keryx mining via full node sync is NOT viable on Modal.com as of Jun 2026
- Consider pool mining instead of solo mining (if available)
- Or wait for Keryx node software optimization
- Check Keryx GitHub issues for known sync problems before attempting

## References

- `references/modal-gpu-pricing.md` — detailed pricing breakdown
- `references/keryx-miner-setup.md` — Keryx-specific build instructions (CUDA + OPoI + plugin system + solo mining)
- `references/gpu-miner-debugging.md` — systematic debugging workflow for GPU miners on cloud containers (CUDA detection, library paths, Claude Code analysis)
- `templates/modal-gpu-miner.py` — reusable Modal app template (compile from source)
- `templates/modal-prebuilt-solo-miner.py` — prebuilt binary + full node template (preferred for solo mining)
