# GPU Miner Debugging Workflow

When a GPU miner fails on a cloud container, follow this systematic approach.

## Step 1: Verify CUDA Hardware

Write a quick test script that checks the basics:

```python
# test_cuda.py — run on Modal with gpu="T4"
import subprocess, ctypes, os
os.environ["LD_LIBRARY_PATH"] = "/usr/local/cuda/targets/x86_64-linux/lib:" + os.environ.get("LD_LIBRARY_PATH", "")

# nvidia-smi
r = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True)
print(f"GPU: {r.stdout.strip() if r.returncode == 0 else 'NOT FOUND'}")

# Try loading libcuda.so.1 directly
try:
    libcuda = ctypes.CDLL("libcuda.so.1")
    ret = libcuda.cuInit(0)
    print(f"cuInit(0): {ret} ({'OK' if ret == 0 else 'FAIL'})")
except OSError as e:
    print(f"libcuda.so.1 load failed: {e}")
```

## Step 2: Check Library Paths

CUDA libs on Modal containers live at:
- `/usr/local/cuda/targets/x86_64-linux/lib/` — libcublas, libcurand, libcudart
- `/usr/lib/x86_64-linux-gnu/libcuda.so.1` — CUDA driver (from host)
- `/usr/local/cuda-12.2/compat/` — compat driver stubs

Check with: `find /usr -name "libcuda.so*" -o -name "libcublas*"`
Check linker: `ldconfig -p | grep -E "cuda|cublas|curand"`

## Step 3: Use Claude Code for Source Analysis

When the miner binary fails with a cryptic error, use Claude Code to analyze the source:

```bash
cd /path/to/miner/source
claude -p "Analyze the error: <paste error>. Look at src/ for the root cause. What flags, env vars, or build options fix it?" --allowedTools "Read,Search,Glob"
```

Claude Code excels at:
- Finding the exact line that throws the error
- Tracing the call chain (e.g., `cust::init()` → `cuInit(0)` → `dlopen`)
- Identifying missing build targets (plugins, shared libraries)
- Suggesting CLI flags that bypass problematic code paths

## Step 4: Common Fixes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `No CUDA device detected` | `cust::init()` can't dlopen `libcuda.so.1` | `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libcuda.so.1` |
| `No workers specified` | Plugin `.so` not built or not found | Build all workspace members: `cargo build --release` (no `--bin`) |
| `No workers specified` | Plugin built but CUDA init failed | Add `-t 2` for CPU thread fallback |
| `NotInitialized` (cust crate) | Same as "No CUDA device" | Same LD_PRELOAD fix |
| `Unable to locate package libcudart-12-2` | Already in CUDA devel image | Remove from apt_install, keep libcublas + libcurand |
| `Connection refused` (gRPC/stratum) | Miner expects local full node | Run the node, or find a public pool address |
| Image upload stuck | 2.2GB CUDA image takes ~10 min | Normal — wait. Consider smaller base image for rebuilds. |
| SIGSEGV after CUDA plugin load | Plugin PTX doesn't match GPU compute cap (e.g., sm_75 not in plugin) | Remove plugin `.so`, use `--cpu-inference` + CPU threads |
| `CUDA_ERROR_SYSTEM_DRIVER_MISMATCH` | CUDA toolkit version incompatible with host driver | Use CUDA 12.2 (widest compat), or match toolkit to host driver version |
| Model re-downloads every restart | Model not baked into image | Add model download to image build step (see gpu-cloud-mining SKILL.md) |

## Step 5: Validate Fix Incrementally

1. First: test CUDA detection alone (Step 1 script)
2. Then: test miner startup (does it get past plugin loading?)
3. Then: test pool connection (does it receive work?)
4. Then: deploy long-running (`modal deploy` or `timeout=86400`)
