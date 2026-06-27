# Headroom — Context Compression for LLM Applications

> GitHub: https://github.com/chopratejas/headroom (12.1k stars, 792 forks)
> PyPI: `headroom-ai`
> Version: v0.23.0+ (as of June 2026)

## What It Does

Compress tool outputs, logs, files, and RAG chunks BEFORE they reach the LLM. 60-95% fewer tokens, same (or better) answers.

## Key Stats (Verified from GitHub benchmarks)

| Content Type | Original | Compressed | Ratio | Latency |
|---|---|---|---|---|
| JSON array (100 items) | 3,163 | 297 | 90.6% | 1ms |
| JSON array (500 items) | 9,526 | 1,614 | 83.1% | 2ms |
| Shell output (200 lines) | 3,238 | 469 | 85.5% | 1ms |
| Build log (200 lines) | 2,412 | 148 | 93.9% | 1ms |

Accuracy: 100% (4/4 correct answers baseline vs headroom, 87.6% compression)
QA: F1 score 0.85 → 0.87, Exact Match 60% → 62% (extraction IMPROVES accuracy)

Production: 50,000+ sessions, 250+ instances, 1.4B tokens saved, ~$4,000 total savings

## Installation

```bash
pip install "headroom-ai[all]"           # Full install
pip install "headroom-ai[python,javascript]"  # Language-specific
```

## Integration Modes

### 1. Proxy Mode (Zero Code Changes)
```bash
headroom proxy --port 8787
export OPENAI_BASE_URL=http://localhost:8787/v1
```

### 2. Python SDK
```python
from headroom import compress
compressed = compress(messages)
```

### 3. LiteLLM Integration
```python
from litellm.proxy.proxy_server import app
from headroom.integrations.asgi import CompressionMiddleware
app.add_middleware(CompressionMiddleware)
```

### 4. ASGI Middleware (FastAPI/Starlette)
```python
from headroom.integrations.asgi import CompressionMiddleware
app.add_middleware(CompressionMiddleware)
```

## Modes
- `headroom proxy --mode token` — maximize compression
- `headroom proxy --mode cache` — preserve Anthropic/OpenAI prefix cache stability

## Key Features
- **Lossless Compression (CCR)**: Compress without losing info
- **Smart Content Detection**: Auto-detect what's important vs noise
- **Cache Optimization**: Cache compressed results
- **Image Compression**: Compress images too
- **Persistent Memory**: Remember more with fewer tokens
- **Failure Learning**: Learn from errors (matches self-evolving pattern)
- **Multi-Agent Context**: Share context between sub-agents
- **Metrics & Observability**: Track token savings

## Response Headers (Proxy Mode)
- `x-headroom-compressed: true` — compression applied
- `x-headroom-tokens-saved: 1234` — tokens removed

## Evaluation
```bash
pip install "headroom-ai[evals]"
python -m headroom.evals quick              # Quick sanity check
python -m headroom.evals benchmark --dataset hotpotqa -n 100
```

## Cost-Benefit (Claude Sonnet $3/MTok)
- 100 search results: +72ms net benefit, $26 saved per 1K requests
- 500 search results: +518ms net benefit, $146 saved per 1K requests
- 1K search results: +957ms net benefit, $297 saved per 1K requests

## Best For
- Agents with heavy tool use (file reads, shell output, API responses)
- RAG applications with large context
- Multi-step workflows that accumulate context
- Cost-sensitive deployments

## Pitfalls (Learned from Production Setup on VPS)

1. **PEP 668**: Ubuntu 24+ blocks `pip install --system`. Create venv: `python3 -m venv ~/.hermes/venv-headroom`
2. **Missing extras**: `headroom-ai` base package doesn't include proxy deps. Use `headroom-ai[proxy]` for fastapi/uvicorn/etc.
3. **CompressResult object**: `compress()` returns `CompressResult`, NOT string. Access: `.messages`, `.tokens_before`, `.tokens_after`, `.tokens_saved`, `.compression_ratio`, `.transforms_applied`.
4. **Tool messages only**: Headroom compresses TOOL role messages, not user messages. User messages get `router:protected:user_message` (no compression).
5. **Small data won't compress**: < 500 chars JSON typically gets 0% compression. SmartCrusher activates on arrays with 10+ items.
6. **Systemd ExecStart**: Use full venv path: `ExecStart=/home/ubuntu/.hermes/venv-headroom/bin/headroom proxy --port 8787`
7. **Model download on first start**: Downloads ModernBERT + kompress ONNX from HuggingFace. Allow 30-60s startup.
8. **HEADROOM_TELEMETRY=off**: Set in systemd env to disable anonymous telemetry on VPS.
9. **CSV output format**: SmartCrusher converts JSON arrays → compact CSV with schema header. Intentional, preserves all data.
10. **Real-world savings**: Wallet data (10 wallets, 847 tokens) → 499 tokens (41%). JSON arrays (100 items, 3066 tokens) → 1175 tokens (62%).
