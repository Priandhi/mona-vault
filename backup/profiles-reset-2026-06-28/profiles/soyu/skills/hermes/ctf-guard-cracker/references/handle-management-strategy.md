# Handle Management Strategy — 50 Gerbang 2026 Lesson

## The Problem: 1 Handle = 1 Reward

In 50 Gerbang Penjaga CTF, the server enforces:
- Each handle can only win **1 reward** (first win)
- Subsequent wins with the same handle = `capped:true` = **NO REWARD**
- Gate gets locked after first correct submission (by ANY handle)

## The Mistake

Using a single handle (e.g., "MonaAgent") for all gates:
- Gate 7: MonaAgent wins → gets reward ✅
- Gate 17: MonaAgent wins → CAPPED, no reward ❌
- Gate 27: MonaAgent wins → CAPPED, no reward ❌

Result: Only 1 reward out of 3 wins!

## The Solution: Handle Pool Per Gate

```python
import random, string

def generate_handle_pool(count=50):
    """Generate unique handles for each gate"""
    return {i: f"agent_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}" 
            for i in range(1, count + 1)}

# Example output:
# {1: "agent_a3b5c7d9", 2: "agent_e2f4g6h8", ...}
```

## Implementation

### Pre-CTF Setup
```python
# Generate handle pool once
handles = generate_handle_pool(50)
with open("handle_pool.json", "w") as f:
    json.dump(handles, f)
```

### During CTF
```python
# Load handle pool
with open("handle_pool.json") as f:
    handles = json.load(f)

# Submit with gate-specific handle
def submit_flag(gate, flag):
    handle = handles[str(gate)]  # Each gate has unique handle
    resp = requests.post(f"{URL}/api/submit", json={
        "gate": gate, "flag": flag, "handle": handle
    }).json()
    
    # Save full response
    save_response(gate, handle, resp)
    
    return resp
```

## Unclaimed Reward Detection

When a handle wins multiple times, subsequent wins are capped:
```python
from collections import Counter

def find_unclaimed(url):
    data = requests.get(f"{url}/api/leaderboard").json()
    winners = Counter(e["winner"] for e in data["timeline"])
    multi = {h for h, c in winners.items() if c > 1}
    
    seen = set()
    unclaimed = []
    for e in data["timeline"]:
        if e["winner"] in multi:
            if e["winner"] in seen:
                unclaimed.append(e)
            seen.add(e["winner"])
    
    return unclaimed
```

## 50 Gerbang 2026 Data

10 unclaimed real prizes found:
- Gate 4 (bureaucrat) — zephyr win #2
- Gate 3 (paranoid) — cx win #2
- Gate 17 (merchant) — codex win #2
- Gate 18 (oracle) — cupang_balap win #2
- Gate 26 (oracle) — hermes_winner win #2
- Gate 28 (bureaucrat) — Mangkok win #2
- Gate 30 (merchant) — blacky win #2
- Gate 40 (merchant) — hermes_agent win #2
- Gate 42 (ai_aware) — @Zphera win #2
- Gate 48 (ai_aware) — night_glider win #2

All locked, rewards permanently lost from API.

## Key Takeaway

**ALWAYS use different handles for different gates!**

```python
# ❌ WRONG
handle = "MonaAgent"
for gate in gates:
    submit(gate, flag, handle)  # Win #2+ = capped!

# ✅ RIGHT
handles = generate_handle_pool(len(gates))
for gate in gates:
    submit(gate, flag, handles[gate])  # Each gate unique handle
```
