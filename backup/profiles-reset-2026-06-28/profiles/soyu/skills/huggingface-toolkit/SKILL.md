---
name: huggingface-toolkit
description: AI model & dataset platforms — HuggingFace (primary), ModelScope, Civitai, Ollama, Kaggle. Fast CDN downloads, model search, inference.
triggers:
  - need AI model download
  - search for ML model or dataset
  - fast file download (CDN)
  - AI/ML project setup
  - model inference or fine-tuning
  - image generation models
  - local LLM setup
---

# AI Model & Dataset Toolkit — Senjata Utama Mona & Claude Code

## Platform Overview

### Tier 1 — Model Hub Lengkap
| Platform | URL | Speed | Best For |
|----------|-----|-------|----------|
| **HuggingFace** 🥇 | huggingface.co | ~150 MB/s | LLM, NLP, audio, umum |
| **ModelScope** 🥈 | modelscope.cn | ~100 MB/s | Asia/China, mirror HF |
| **Kaggle** 🥉 | kaggle.com | ~50 MB/s | Dataset gede, notebook |

### Tier 2 — Spesialis
| Platform | URL | Best For |
|----------|-----|----------|
| **Civitai** | civitai.com | Image gen (SD, FLUX, LoRA) |
| **Ollama Library** | ollama.com/library | LLM lokal 1 command |
| **TensorFlow Hub** | tfhub.dev | Google TF/Keras models |
| **PyTorch Hub** | pytorch.org/hub | PyTorch models |
| **ONNX Model Zoo** | github.com/onnx/models | Cross-platform inference |

### Tier 3 — Cloud Inference (tanpa GPU)
| Platform | URL | Best For |
|----------|-----|----------|
| **Replicate** | replicate.com | Run model tanpa setup |
| **Together AI** | together.ai | Inference API murah |
| **Fireworks AI** | fireworks.ai | Fast inference |

## Decision Matrix
| Kebutuhan | Pilih |
|-----------|-------|
| Model AI umum (LLM, audio, NLP) | **HuggingFace** |
| Model gambar (SD, FLUX, LoRA) | **Civitai** |
| Jalankan LLM lokal | **Ollama** |
| Dataset training | **Kaggle + HuggingFace** |
| Model buat Asia/China | **ModelScope** |
| Inference tanpa GPU | **Replicate** |

## HuggingFace Quick Reference

### Download Model (CLI)
```bash
pip install huggingface-hub
huggingface-cli download ORG/MODEL --local-dir ./model
curl -L 'https://huggingface.co/ORG/MODEL/resolve/main/FILENAME' -o FILENAME
```

### Search Models
```bash
curl -s "https://huggingface.co/api/models?search=QUERY&sort=downloads&direction=-1&limit=5" | python3 -m json.tool
```

### URL Pattern
```
https://huggingface.co/{ORG}/{MODEL}/resolve/main/{FILENAME}
https://huggingface.co/datasets/{ORG}/{DATASET}/resolve/main/{FILENAME}
```

### Common Model Files
| File | Fungsi |
|------|--------|
| `config.json` | Model architecture config |
| `tokenizer.json` | Tokenizer vocabulary & rules |
| `model.safetensors` | Model weights (new, safe format) |
| `model.bin` | Model weights (PyTorch, older) |
| `*.gguf` | Quantized untuk llama.cpp / Ollama |

## Speed Comparison (2.1GB file)
| Source | Speed | ETA |
|--------|-------|-----|
| **HuggingFace CDN** | ~150 MB/s | **13 detik** |
| ModelScope | ~100 MB/s | 20 detik |
| IPFS gateway | ~1 MB/s | 34 menit |
| Generic IPFS | ~0.5 MB/s | 1 jam+ |

## Modal Image Baking Pattern
```python
.run_commands(
    "set -e && mkdir -p /opt/models/ModelName && cd /opt/models/ModelName && "
    "curl -L --retry 5 'https://huggingface.co/ORG/MODEL/resolve/main/tokenizer.json' -o tokenizer.json && "
    "curl -L --retry 5 'https://huggingface.co/ORG/MODEL/resolve/main/config.json' -o config.json && "
    "curl -L --retry 5 'https://huggingface.co/ORG/MODEL/resolve/main/model.safetensors' -o model.safetensors && "
    "python3 -c \"import json; json.load(open('tokenizer.json'))\" && "
    "python3 -c \"import os; assert os.path.getsize('model.safetensors') > 100_000_000\" && "
    "touch .ok && ls -lh"
)
```

## Pitfalls
- Beberapa model butuh auth token (gated models) — pakai `huggingface-cli login`
- `model.bin` = PyTorch lama, `model.safetensors` = format baru (lebih aman, lebih cepat)
- Model besar (>10GB) butuh `git lfs` atau `huggingface-cli download`
- Rate limit anon — login kalau sering download
- Selalu verify hash/size setelah download besar
- Civitai models kadang NSFW — filter dulu
- Ollama models auto-quantized (GGUF) — beda dari original weights

## Related Skills
- **gpu-cloud-mining** — Modal.com deployment with HuggingFace model baking (150x faster than IPFS)
