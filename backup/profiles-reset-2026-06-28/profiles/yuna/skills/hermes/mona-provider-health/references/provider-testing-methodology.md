# Provider Testing Methodology

## Safe Testing Pattern

**NEVER test providers in the current session** — use `delegate_task` to run tests in isolated sessions. This prevents:
- Disrupting the current conversation
- Provider errors affecting the main session
- API key exposure in current session logs

## Test Suite

### 1. Direct API Test
Test API key directly against provider API:
```python
import urllib.request, json

def test_direct_api(api_url, api_key, model, prompt="hi"):
    req = urllib.request.Request(
        f"{api_url}/chat/completions",
        data=json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 10
        }).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        if "choices" in data:
            return True, data["choices"][0]["message"]["content"]
        return False, data.get("error", "Unknown error")
    except Exception as e:
        return False, str(e)
```

### 2. 9Router Routing Test
Test through 9Router proxy:
```bash
curl -s -X POST http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "openrouter/deepseek/deepseek-chat-v3-0324", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}'
```

### 3. Hermes Integration Test
Test through Hermes CLI:
```bash
hermes chat -q "Say hello" -m minimax-m2.7 --provider generalcompute
```

## Benchmark Template

```python
import time

def benchmark_provider(name, test_fn, iterations=3):
    latencies = []
    for i in range(iterations):
        start = time.time()
        success, result = test_fn()
        latency = time.time() - start
        latencies.append(latency)
    
    avg_latency = sum(latencies) / len(latencies)
    return {
        "name": name,
        "avg_latency": round(avg_latency, 2),
        "min_latency": round(min(latencies), 2),
        "max_latency": round(max(latencies), 2),
        "success_rate": sum(1 for _ in latencies) / len(latencies)
    }
```

## Test Results Format

```
📊 PROVIDER TEST RESULTS

Provider: [Name]
Model: [Model]
Iterations: [N]

Latency:
  Average: [X.XXs]
  Min: [X.XXs]
  Max: [X.XXs]

Success Rate: [XX%]

Sample Response:
[Response text]
```

## Common Issues

### 401 Unauthorized
- API key invalid or expired
- Key format wrong (check prefix)
- Key not activated

### 404 Not Found
- Model name wrong
- Provider prefix wrong
- Endpoint URL wrong

### 429 Rate Limited
- Key hit rate limit
- Use backup key
- Wait for cooldown

### 503 Service Unavailable
- Provider down
- Try fallback provider
- Check provider status page
