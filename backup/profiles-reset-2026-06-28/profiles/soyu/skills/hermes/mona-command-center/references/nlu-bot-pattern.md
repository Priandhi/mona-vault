# Natural Language Understanding (NLU) for Telegram Bots

Users don't want to memorize commands. Add NLU fallback so the bot understands natural language.

## Architecture

```
User message → Check rigid commands first → If no match → NLU fallback → Execute action
```

**Key principle**: Always check rigid commands FIRST (fast, no LLM cost), then fall back to NLU for unrecognized messages.

## Implementation: `mona_smart_nlu.py`

```python
#!/usr/bin/env python3
"""
Mona Smart NLU — Natural Language Understanding
Uses LLM to understand user intent from natural language
"""
import json, os, sys, urllib.request

sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))
from mona_telegram import send_message, timestamp, TOPIC_ALPHA, TOPIC_NAME


def call_llm(prompt, system_prompt="", max_tokens=200):
    """Call LLM via 9Router (OpenAI-compatible)"""
    base_url = "http://localhost:20128/v1"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-or-xxx",  # 9Router key
    }
    payload = {
        "model": "xmtp/mimo-v2.5-pro",  # Use available model
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "stream": False,  # Important: disable streaming for NLU
    }
    
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{base_url}/chat/completions", data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            
            # Handle SSE format (streaming responses)
            if raw.startswith("data: "):
                for line in raw.strip().split("\n"):
                    if line.startswith("data: ") and "[DONE]" not in line:
                        result = json.loads(line[6:])
                        return result["choices"][0]["message"].get("content", "")
                return None
            else:
                result = json.loads(raw)
                return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[NLU ERROR] {e}")
        return None


def smart_understand(text, topic_id):
    """Use LLM to understand user intent from natural language"""
    system_prompt = f"""Kamu Mona, AI crypto expert. User di topic {TOPIC_NAME.get(topic_id, 'Unknown')}.
    
Return JSON saja:
{{"action": "action_name", "params": {{}}, "reply": "jawaban natural casual Indonesia"}}

Actions: cari, top, chain, analisis, cek, portfolio, gas, health, scan, garap, status, logs, greeting, confused, general
Jangan gunakan markdown code block, langsung JSON."""

    result = call_llm(text, system_prompt)
    if not result:
        return None
    
    try:
        # Parse JSON - handle code blocks
        result = result.strip().replace("```json", "").replace("```", "").strip()
        start = result.find("{")
        end = result.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(result[start:end])
    except json.JSONDecodeError:
        pass
    
    return {"action": "general", "reply": result}


def handle_smart_message(text, user, topic_id):
    """Main entry point — call this from topic handler's fallback"""
    intent = smart_understand(text, topic_id)
    if not intent:
        send_message(topic_id, "⚠️ Gue lagi kesulitan mikir. Coba lagi ya!")
        return
    
    action = intent.get("action", "")
    reply = intent.get("reply", "")
    
    # Map NLU actions to actual commands
    if action in ("cari", "scan", "search", "trending"):
        from mona_bot import handle_alpha
        handle_alpha("cari", user)
    elif action in ("top", "best"):
        from mona_bot import handle_alpha
        handle_alpha("top", user)
    elif action in ("chain",):
        chain = intent.get("params", {}).get("chain", "base")
        from mona_bot import handle_alpha
        handle_alpha(f"chain {chain}", user)
    elif action in ("analisis", "analyze", "cek", "review"):
        target = intent.get("params", {}).get("target", "")
        if target:
            from mona_bot import handle_alpha
            handle_alpha(f"analisis {target}", user)
        else:
            send_message(topic_id, "🔍 Mau analisis apa? Kasih nama atau link!")
    elif reply:
        send_message(topic_id, reply)
    else:
        send_message(topic_id, "🤔 Ketik <code>help</code> buat liat command.")
```

## Integration in Topic Handlers

Replace rigid fallback with NLU:

```python
def handle_alpha(text, user):
    # ... existing rigid command checks ...
    
    # OLD: send_message(TOPIC_ALPHA, "❓ Command tidak dikenali. Ketik help.")
    
    # NEW: Smart NLU fallback
    try:
        from mona_smart_nlu import handle_smart_message
        handle_smart_message(text, user, TOPIC_ALPHA)
    except Exception as e:
        print(f"[NLU ERROR] {e}")
        send_message(TOPIC_ALPHA, "🤔 Ketik <code>help</code> buat liat command.")
```

## User Preference

User explicitly requested: "gaperlu pake command gimana biar aku ngetik bot auto tau apa yang ku mau?"

**Lesson**: Users prefer natural language over memorizing commands. Always add NLU fallback to topic handlers.

## PITFALL: 9Router Streaming Format

9Router returns SSE (Server-Sent Events) format even with `stream: false`:
```
data: {"choices": [...]}
data: [DONE]
```

Always parse SSE format in LLM caller. Check for `data: ` prefix and handle accordingly.

## PITFALL: Model Availability

Check available models before using:
```bash
curl -s http://localhost:20128/v1/models | jq '.data[].id'
```

Don't assume models exist (e.g., `deepseek/deepseek-chat-v3-0324` may not be configured).

## Testing

```python
# Test command parser
from mona_smart_nlu import smart_understand, TOPIC_ALPHA

test_cases = [
    ("ada project baru gak?", TOPIC_ALPHA),
    ("wallet gua berapa?", TOPIC_WALLET),
    ("halo", TOPIC_ALPHA),
]

for text, topic in test_cases:
    intent = smart_understand(text, topic)
    print(f"{text} → {intent}")
```
