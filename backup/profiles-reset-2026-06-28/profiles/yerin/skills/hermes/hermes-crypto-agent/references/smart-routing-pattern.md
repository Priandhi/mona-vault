# Smart Routing Pattern for Telegram Forum Bots

When building a Telegram bot with forum topics, users often send commands to the wrong topic. Smart routing detects intent and routes to the correct handler regardless of where the message was sent.

## Architecture

```
User sends message in Topic A
    ↓
route_message() — main router
    ↓
detect_intent(text) — regex-based intent detection
    ↓
If intended_topic != current_topic:
    Send hint: "🔀 Command ini untuk topic X — gue tetap proses ya!"
    Route to correct handler
Else:
    Use topic's own handler
```

## Implementation Pattern

### 1. Intent Detection Function

```python
def detect_intent(text):
    """Detect intended handler based on command content"""
    text_lower = text.lower().strip()

    # WALLET COMMANDS
    wallet_patterns = [
        r'^cek\s+', r'^portfolio', r'^wallet\s+', r'^label\s+', r'^labels',
        r'^group\s+', r'^groups', r'^health\s+', r'^honeypot\s+', r'^bridge\s+',
        r'^gas\s+', r'^watch\s+', r'^unwatch\s+', r'^watches', r'^distribute\s+',
    ]
    for pattern in wallet_patterns:
        if re.match(pattern, text_lower):
            return TOPIC_WALLET

    # TWITTER COMMANDS
    if text_lower.startswith('twitter ') or text_lower in ('/twitter', 'twitter help'):
        return TOPIC_ALPHA

    # ALPHA COMMANDS
    alpha_patterns = [r'^cari$', r'^analisis\s+', r'^chain\s+', r'^top$']
    for pattern in alpha_patterns:
        if re.match(pattern, text_lower):
            return TOPIC_ALPHA

    # NFT COMMANDS
    nft_patterns = [r'^mint\s+', r'^scan\s+', r'^info\s+', r'^dapp\s+']
    for pattern in nft_patterns:
        if re.match(pattern, text_lower):
            return TOPIC_NFT_MINT

    # AIRDROP COMMANDS
    airdrop_patterns = [r'^garap\s+', r'^browse\s+', r'^click\s+', r'^isi\s+']
    for pattern in airdrop_patterns:
        if re.match(pattern, text_lower):
            return TOPIC_LIST_AIRDROP

    # TASK COMMANDS
    if text_lower.startswith('task '):
        return TOPIC_LAPORAN_GARAPAN

    # EVOLUTION COMMANDS
    if text_lower.startswith('evolve ') or text_lower in ('evolve help', 'evolution help'):
        return TOPIC_LOGS

    # FEEDBACK COMMANDS (any topic)
    if text_lower.startswith('feedback '):
        return TOPIC_LOGS

    # COMMON COMMANDS — let topic handler deal with it
    if text_lower in ('help', '/help', '/start', 'status'):
        return None

    return None  # No intent detected, use current topic handler
```

### 2. Smart Router

```python
def route_message(message):
    """Route with smart intent detection"""
    thread_id = message.get("message_thread_id")
    text = message.get("text", "")
    user = message.get("from", {}).get("username", "unknown")

    if not thread_id or not text:
        return

    topic_handler = HANDLERS.get(thread_id)
    topic_name = TOPIC_NAME.get(thread_id, f"Thread {thread_id}")

    # Detect intended handler
    intended_topic = detect_intent(text)

    if intended_topic and intended_topic != thread_id:
        # Wrong topic — route to correct handler with hint
        intended_handler = HANDLERS.get(intended_topic)
        intended_name = TOPIC_NAME.get(intended_topic, "Unknown")
        if intended_handler:
            send_message(thread_id,
                f"🔀 <i>Command ini untuk topic {intended_name} — gue tetap proses ya!</i>")
            intended_handler(text, user)
            return

    # Normal routing
    if topic_handler:
        topic_handler(text, user)
```

## Key Decisions

1. **Send hint to ORIGINAL topic** — User sees the routing message where they typed, not in a random topic.
2. **Feedback commands → Logs topic** — Feedback is about system behavior, fits best in Logs.
3. **Common commands (help, status) → no routing** — Every topic has its own help, let it handle locally.
4. **Twitter → Alpha topic** — Twitter is alpha-related, lives in Alpha topic.

## Pitfalls

- **Don't route EVERYTHING.** Only route when you have high confidence of intent. If ambiguous, let the current topic handle it.
- **Don't route help/status.** Each topic should have its own help text.
- **Regex patterns must be anchored** (`^`) to avoid false matches in middle of text.
- **Feedback from any topic** — This is intentional. User shouldn't have to go to a specific topic to give feedback.
