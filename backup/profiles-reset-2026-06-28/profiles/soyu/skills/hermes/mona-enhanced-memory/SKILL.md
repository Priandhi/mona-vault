---
name: mona-enhanced-memory
description: Enhanced memory system for Mona. Remember user preferences, project context, learned patterns, and important facts across sessions. Use when user asks Mona to remember something, or when Mona discovers important context that should persist.
when_to_use:
  - User says "inget ini" or "jangan lupa"
  - User corrects Mona's behavior
  - User shares preferences or habits
  - Mona discovers important project context
  - Session ends with important unresolved context
version: 1.0.0
---

# Mona Enhanced Memory System

## Memory Structure

```
~/.hermes/memories/
├── user_preferences.json    # User habits, likes/dislikes, style
├── project_context.json     # Active projects, goals, progress
├── learned_patterns.json    # What works, what doesn't
├── correction_log.json      # User corrections & feedback
├── important_facts.json     # Stable facts (wallets, keys, configs)
└── session_summaries/       # Auto-generated session summaries
    └── YYYY-MM-DD_HH-MM.md
```

## Memory Categories

### 1. User Preferences (Highest Priority)
```json
{
  "communication_style": "casual_indonesian",
  "call_me": "sayang",
  "response_length": "concise",
  "technical_level": "advanced",
  "timezone": "WIB",
  "crypto_focus": ["solana", "defi", "airdrops"],
  "risk_tolerance": "high",
  "prefers_execution_over_explanation": true,
  "model_routing": {
    "main_chat": "kimchi/minimax-m2.7",
    "vision": "xmtp/mimo-v2-omni",
    "coding_delegation": "kr/claude-sonnet-4.5",
    "quick_tasks": "kimchi/minimax-m2.5",
    "compression": "kr/deepseek-3.2",
    "fallback": "xmtp"
  }
}
```

### 2. Project Context
```json
{
  "active_projects": [
    {
      "name": "meridian-fleet",
      "status": "awaiting_funding",
      "next_steps": ["fund_wallets", "start_fleet"],
      "blockers": ["no_SOL_funds"],
      "context": "9 wallet DLMM agent fleet for Meteora"
    }
  ],
  "recent_topics": ["alpha-intel", "whale-tracking", "twitter-scanner"],
  "pending_tasks": []
}
```

### 3. Learned Patterns
```json
{
  "what_works": [
    "Direct execution without asking permission",
    "Casual Indonesian tone",
    "Showing code changes before applying"
  ],
  "what_doesnt": [
    "Long explanations before action",
    "Boilerplate disclaimers",
    "Asking obvious questions",
    "Moral lectures when user is emotional",
    "Leading with boundaries before empathy"
  ],
  "user_habits": [
    "Usually works late night WIB",
    "Prefers Telegram for communication",
    "Likes seeing progress, not just results",
    "Tests boundaries when frustrated (not malicious) — respond with empathy first",
    "Values 'nurut' (obedience) highly — pushback = rejection to them"
  ]
}
```

### 4. Correction Log
```json
{
  "corrections": [
    {
      "date": "2026-06-04",
      "context": "Mona gave long explanation instead of executing",
      "correction": "Just do it, don't explain first",
      "applied": true
    }
  ]
}
```

## Auto-Memory Rules

### ALWAYS Save:
1. User explicitly says "inget ini" or "jangan lupa"
2. User corrects behavior ("jangan lakuin X lagi")
3. User shares preference ("gue lebih suka Y")
4. Important API keys, wallet addresses, configs
5. Project blockers or decisions
6. Session ends with unresolved context

### NEVER Save:
1. Temporary task state (use session_search instead)
2. Error logs or debug output
3. Large data dumps
4. Things that change frequently (prices, balances)
5. Information that's already in skills

## Memory Injection

Every session start:
1. Load user_preferences → adjust communication style
2. Load project_context → know what's active
3. Load learned_patterns → avoid past mistakes
4. Load recent corrections → apply immediately

## Memory Maintenance

### Weekly Review (Auto)
- Consolidate duplicate entries
- Remove stale information
- Update project statuses
- Archive completed projects

### User-Triggered Review
- User says "apa yang lo inget?" → show summary
- User says "lupakan X" → remove specific memory
- User says "update Y" → refresh specific memory

## Implementation Notes

### For Hermes Agent:
- Use `memory` tool with target='user' for user preferences
- Use `memory` tool with target='memory' for agent notes
- Use `session_search` to recall past conversations
- Use `skill_manage` to save reusable workflows

### Memory Priority:
1. User preferences (communication, style)
2. Corrections (behavioral adjustments)
3. Project context (active work)
4. Learned patterns (optimization)
5. Important facts (stable data)

## Memory Tool Pitfalls

### `replace` action parameters
The `replace` action requires BOTH `content` AND `old_text`:
```python
# CORRECT:
memory(action="replace", target="user", old_text="0xjosee", content="hexa. ...full entry...")

# WRONG — 'new_text' is not a valid parameter:
memory(action="replace", target="user", old_text="0xjosee", new_text="hexa")  # FAILS
```

- `old_text` = short unique substring that identifies WHICH entry to replace
- `content` = the FULL new entry content (not just the changed part)
- If you only provide `old_text` without `content`, you get: "content is required for 'replace' action"

### Near-capacity workaround (remove + add)
When memory is near capacity (97%+), `replace` fails with:
> "Replacement would put memory at X/Y chars. Shorten the new content or remove other entries first."

**Workaround:** Use `remove` then `add` instead:
```python
# Step 1: Remove the old entry
memory(action="remove", target="user", old_text="0xjosee")
# Returns: {"success": true, "usage": "72% — 992/1,375 chars"}

# Step 2: Add the new entry (now there's space)
memory(action="add", target="user", content="hexa. ...full entry...")
```

### Memory character limits
- User profile: ~1,375 chars max
- Memory notes: ~1,375 chars max
- When at 97%+, new adds may fail — need to remove entries first
- Keep entries concise — prefer dense facts over verbose descriptions

### Parameter name gotcha
The memory tool uses `content` (not `new_text`, `text`, or `value`). This applies to both `add` and `replace` actions. Getting this wrong causes repeated failures in a loop.

## SOUL.md Management — CRITICAL RULES

### File Overwrite Danger
`write_file` = **OVERWRITES entire file** — DATA LOSS RISK.
**NEVER use write_file for updating SOUL.md.** Only use `write_file` for CREATING a new empty file.

### Correct Update Method: `patch()`
For updating SOUL.md → always use `patch()` to ADD, APPEND, or REPLACE sections.
```python
# WRONG — write_file overwrites everything:
write_file(path="/home/ubuntu/SOUL.md", content="new content")  # ERASES OLD CONTENT

# CORRECT — patch() preserves existing content:
patch(mode="replace", path="/home/ubuntu/SOUL.md", 
      old_string="## OLD SECTION\ncontent to replace", 
      new_string="## OLD SECTION\nupdated content")
```

### SOUL.md Scope — What Goes In
SOUL.md = SOUL only:
- ✅ Core identity (who Mona is)
- ✅ Operating principles (how Mona behaves)
- ✅ Battle-tested lessons (CTF, project learnings)
- ✅ 3 Hard Stops
- ✅ Universal principles
- ✅ Memory commands (triggers for specific task classes)

### SOUL.md Scope — What Does NOT Go In
SOUL.md ≠ config/credentials/state:
- ❌ VPS IPs, SSH keys, port numbers
- ❌ API keys, credentials, tokens
- ❌ Provider stack names, model names
- ❌ Crypto operating rules (margin, dedup, DRY_RUN)
- ❌ Bot-specific settings (Charon sniper config)
- These belong in MEMORY, not SOUL.md. SOUL.md survives across sessions; configs change.

### Session: 2026-06-11 — SOUL.md Corruption & Recovery
User built Mona over 2 weeks, nightly sessions. At end of CTF session, agent overwrote SOUL.md with `write_file` instead of `patch()`, destroying 2 weeks of content. User had to rebuild from session context and recovered ~80% of content. Lesson: SOUL.md is precious — updating it carelessly causes irrecoverable data loss. ALWAYS use `patch()`.

## Example Usage

```python
# User says: "inget, gue gak suka penjelasan panjang"
memory(
    action="add",
    target="user",
    content="prefers_concise_responses: true. No long explanations before action."
)

# User says: "project meridian belum jalan karena belum ada SOL"
memory(
    action="add",
    target="memory",
    content="Meridian fleet blocked: waiting for SOL funding. 9 wallets generated, configs ready."
)

# User asks: "apa yang lo inget soal meridian?"
# → Mona recalls from memory and responds with context
```

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Memory retention | 100% | ~60% |
| Context recall accuracy | >95% | ~80% |
| User correction compliance | 100% | ~90% |
| Proactive suggestions | High | Low |
| Session continuity | Seamless | Partial

---

*"The best memory isn't the one that remembers everything — it's the one that remembers what matters."*
