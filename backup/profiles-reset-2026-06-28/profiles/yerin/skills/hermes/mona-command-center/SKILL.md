---
name: mona-command-center
description: Build and operate a Telegram-based AI command center — interactive bot with topic-based routing, background worker service, wallet management, browser automation, and self-evolving agent capabilities. Use when setting up Telegram bots with forum topics, background task queues, or multi-channel agent architectures.
tags: [telegram, bot, command-center, worker, crypto, wallet, browser-automation, self-evolving]
triggers:
  - telegram bot with topics
  - command center
  - background worker
  - task queue
  - forum topics
  - wallet management bot
  - browser automation bot
---

# Mona Command Center

Build a production-grade Telegram command center with forum topics as specialized channels, a 24/7 background worker, and smart command routing.

## Architecture

```
Telegram Group (Forum)
├── Topic 1: 💸 Wallet (on-demand commands)
├── Topic 2: 💎 Alpha (auto + commands)
├── Topic 3: ⭐️ NFT (on-demand mint/scan)
├── Topic 4: 📣 Airdrop (auto-grind + executor commands)
├── Topic 5: ⛏️ Mining (on-demand monitoring)
├── Topic 6: 📊 Status (auto-report)
├── Topic 7: 📝 Garapan (task manager + reports)
└── Topic 8: 📚 Logs (system + evolution)
```

**Core Services (systemd, MUST use mona venv):**
- `mona-bot` — Telegram polling + command routing (ExecStart uses `~/.hermes/venv-mona/bin/python`)
- `mona-worker` — Background task executor (24/7)
- Optional: routing proxy (9Router, LiteLLM, etc.)

**PITFALL**: All Mona bot/worker systemd services MUST use `~/.hermes/venv-mona/bin/python` (has web3, solana, httpx, playwright). System `/usr/bin/python3` lacks these packages and crypto/bot commands will fail with `ModuleNotFoundError: No module named 'web3'`.

## Key Design Decisions

### 1. Hybrid Auto + On-Demand
NOT all topics should be auto-alert. Mix:
- **Auto**: Alpha scanning (every 20min), Logs (every 3hr), Garapan (event-driven)
- **On-Demand**: Wallet (user commands), NFT (user commands), Mining (user commands)

### 2. Smart Command Router
Users WILL send commands to the wrong topic. Implement intent detection:

```python
def detect_intent(text):
    """Route commands to correct handler regardless of which topic they were sent to"""
    text_lower = text.lower().strip()
    
    wallet_patterns = [r'^cek\s+', r'^portfolio', r'^health\s+']
    for pattern in wallet_patterns:
        if re.match(pattern, text_lower):
            return TOPIC_WALLET
    
    if text_lower.startswith('twitter '):
        return TOPIC_ALPHA
    
    # ... etc
    return None  # Let topic handler deal with it
```

When routing, send a hint: `🔀 Command ini untuk topic {name} — gue tetap proses ya!`

### 3. Background Worker Pattern
```python
# mona_worker.py — systemd service
# Polls SQLite task queue every 10s
# Executes tasks step-by-step with checkpointing
# Reports progress to Telegram
# Auto-retries on failure (max 3x)
# Requests input from user when blocked
```

Task lifecycle: `pending → running → completed/failed/waiting_input`

### 4. Token Storage
NEVER store tokens in plaintext. Use base64 encoding:
```bash
echo -n "BOT_TOKEN" | base64 > vault/.telegram_bot
chmod 600 vault/.telegram_bot
```

**PITFALL**: Shell `echo` adds newline. Use `echo -n` or the decoded token will have trailing whitespace causing 401 errors.

### 5. Topic IDs from Telegram API
```bash
# Get chat ID (send message to group first)
curl -s "https://api.telegram.org/bot$TOKEN/getUpdates" | jq '.result[0].message.chat.id'

# Create forum topic
curl -s -X POST "https://api.telegram.org/bot$TOKEN/createForumTopic" \
  -d chat_id=$CHAT_ID -d name="Topic Name" | jq '.result.message_thread_id'
```

**PITFALL**: Two processes CANNOT poll the same Telegram bot token. If Hermes and another service (e.g. Meridian) share a bot token, both calling `getUpdates` causes missed messages. Fix: set `TELEGRAM_NO_POLL=true` in the secondary service's `.env` and check it in `startPolling()`. The secondary service can still SEND notifications — only incoming polling is disabled. See `hermes-crypto-agent/references/meridian-telegram-conflict.md` for full pattern.

**PITFALL**: Bot needs `Manage Topics` permission in the group to create topics.

**PITFALL**: When pinning messages to topics, ALWAYS verify the topic ID first. User was frustrated when I pinned a message to Topic 10 (Laporan Garapan) instead of the intended topic. **Pattern to avoid:**
- User says "buatkan topic ini" → I create topic
- User says "isi di dalamnya" → I pin message to WRONG topic (Topic 10)
- User gets frustrated: "salah topic itu laporan garapan yang kamu isi 😭"

**Correct pattern:**
1. Ask user WHICH topic they want content pinned to
2. Verify topic ID by listing topics from `.telegram_topics.json`
3. Pin message to CORRECT topic ID
4. Double-check before confirming

**PITFALL**: Hermes security system auto-redacts bot tokens in tool output. If you need to save a bot token to a file, you cannot see it directly. Workaround: ask user to run the save command on VPS manually, OR use base64 encoding via `execute_code` where the token is a string variable (not in tool output).

## File Structure

```
~/.hermes/scripts/
├── mona_telegram.py          # Shared: send_message, RPC, web_search, topic IDs
├── mona_bot.py               # Bot: polling loop + topic handlers + smart router
├── mona_worker.py            # Worker: background task executor
├── mona_worker_db.py         # SQLite task queue schema + operations
├── mona_wallet_manager.py    # Multi-chain wallet operations
├── mona_wallet_commands.py   # Wallet topic bot commands
├── mona_browser.py           # Browser automation (CloakBrowser)
├── mona_browser_commands.py  # Browser topic bot commands
├── mona_evolution.py         # Self-evolving agent engine
├── mona_evolution_commands.py # Evolution bot commands
├── mona_lessons_db.py        # Lessons/patterns/feedback database
├── mona_airdrop_executor.py  # Airdrop task queue + DB + classification
├── mona_airdrop_runner.py    # Playwright browser + web3 on-chain executor
└── mona_airdrop_commands.py  # Airdrop Telegram commands
```

## Cron Job Setup

**PITFALL**: Cron jobs with `no_agent=True` run scripts as standalone Python — `hermes_tools` (web_search, etc.) are NOT available. Use `no_agent=False` with a self-contained agent prompt when you need web_search or other Hermes tools.

**PITFALL**: Cron `script` parameter is a RELATIVE filename under `~/.hermes/scripts/`, not an absolute path. Example: `mona_alpha_scan.py` not `/home/ubuntu/.hermes/scripts/mona_alpha_scan.py`.

### Real-Time Scanner Cron Pattern

User explicitly rejected 20-minute intervals: "kok every 20 menit sih, nanti telat dong harusnya kalau ada volume gede token bagus project nya jelas bisa langsung scan"

**USER PREFERENCE**: Token discovery scanners must run at **5-minute intervals**, not 20. Delayed scanning = missed alpha. Use `every 5m` for any scanner that finds NEW tokens.

**Silent-when-empty rule**: If no quality tokens found, DON'T send empty "no tokens found" message to Telegram. Stay silent. Only report when there ARE quality tokens. Otherwise user gets spammed with empty reports every 5 minutes.

**Multi-API polling pattern** (better coverage than single API):

```python
def get_new_tokens():
    """Poll multiple APIs, deduplicate by contract address"""
    all_tokens = []
    seen_contracts = set()
    
    # API 1: DexScreener boosts (trending)
    # API 2: DexScreener profiles (newly listed)  
    # API 3: Direct launchpad API (e.g. Clanker for Base)
    
    for api_func in [get_boosts, get_profiles, get_clanker]:
        for token in api_func():
            contract = token.get("tokenAddress") or token.get("contract_address")
            if contract and contract not in seen_contracts:
                seen_contracts.add(contract)
                all_tokens.append(normalize(token))
    
    return all_tokens
```

**DexScreener endpoints (verified working, no auth):**
- Boosts: `https://api.dexscreener.com/token-boosts/latest/v1` — 30 recently boosted tokens
- Profiles: `https://api.dexscreener.com/token-profiles/latest/v1` — 30 newly listed tokens
- Token details: `https://api.dexscreener.com/tokens/v1/{chain_id}/{CA}` — single token with pool info

**PITFALL**: DexScreener boosts/profiles may return 0 Base tokens at certain times. Always combine with direct launchpad API (Clanker) as primary source.

## Systemd Service Template

```ini
[Unit]
Description=Mona Bot Service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/home/ubuntu/.hermes/venv-mona/bin/python -u /path/to/script.py
Restart=always
RestartSec=10
Environment=HOME=/home/ubuntu
Environment=PYTHONPATH=/home/ubuntu/.hermes/scripts

[Install]
WantedBy=multi-user.target
```

**PITFALL**: Always use the mona venv python (`~/.hermes/venv-mona/bin/python`) NOT `/usr/bin/python3`. System python lacks web3, solana, httpx, playwright. Add `-u` flag for unbuffered stdout (otherwise `journalctl` shows nothing).

## Smart Router Integration Pattern

When adding new command categories to an existing handler:

```python
def handle_existing_topic(text, user):
    # Check new commands first
    from new_commands import is_new_command, handle_new_command
    if is_new_command(text):
        handle_new_command(text, user)
        return
    
    # Original handler logic
    text_lower = text.lower().strip()
    # ...
```

## Natural Language Understanding (NLU) Pattern

Users don't want to memorize commands. Add NLU fallback so the bot understands natural language (Indonesian casual).

### Architecture

```
User message → Check rigid commands first → If no match → NLU fallback → Execute action
```

**Key principle**: Always check rigid commands FIRST (fast, no LLM cost), then fall back to NLU for unrecognized messages.

### Implementation: `mona_smart_nlu.py`

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

### Integration in Topic Handlers

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

### User Preference

User explicitly requested: "gaperlu pake command gimana biar aku ngetik bot auto tau apa yang ku mau?"

**Lesson**: Users prefer natural language over memorizing commands. Always add NLU fallback to topic handlers.

### PITFALL: 9Router Streaming Format

9Router returns SSE (Server-Sent Events) format even with `stream: false`:
```
data: {"choices": [...]}
data: [DONE]
```

Always parse SSE format in LLM caller. Check for `data: ` prefix and handle accordingly.

### PITFALL: Model Availability

Check available models before using:
```bash
curl -s http://localhost:20128/v1/models | jq '.data[].id'
```

Don't assume models exist (e.g., `deepseek/deepseek-chat-v3-0324` may not be configured).

## Telegram Channel Scraping & Cron Monitoring

Scrape public Telegram channels without API access using browser + JS extraction.

### Technique: `t.me/s/` Public Preview

Public Telegram channels have a web preview at `https://t.me/s/<channel_username>`. Use browser tools to extract structured data:

1. `browser_navigate` to `https://t.me/s/<channel_username>`
2. `browser_console` with JS to extract posts:

```javascript
const posts = document.querySelectorAll('.tgme_widget_message_wrap');
const results = [];
posts.forEach((post) => {
  const textEl = post.querySelector('.tgme_widget_message_text');
  const linkEls = post.querySelectorAll('.tgme_widget_message_text a');
  const dateEl = post.querySelector('.tgme_widget_message_date time');
  const viewsEl = post.querySelector('.tgme_widget_message_views');
  if (textEl) {
    const links = Array.from(linkEls).map(a => ({text: a.textContent, href: a.href}));
    results.push({
      date: dateEl ? dateEl.textContent : 'N/A',
      views: viewsEl ? viewsEl.textContent : 'N/A',
      text: textEl.textContent.substring(0, 400),
      links: links
    });
  }
});
JSON.stringify(results.slice(0, 20));
```

3. Filter actionable content (airdrops, whitelist, claims, quests)
4. Format as clean report with clickable links

**PITFALL**: `web_extract` often fails on `t.me/s/` URLs. Always use browser tools instead.

**PITFALL**: `browser_snapshot(full=True)` truncates large pages. Use `browser_console` with JS extraction for reliable structured data — it bypasses the snapshot character limit entirely.

### Cron Channel Monitoring Pattern

Set up periodic channel scanning with `cronjob`:

```yaml
action: create
schedule: "every 5h"  # or "every 30m", "every 2h", etc.
deliver: "telegram:<chat_id>:<topic_id>"  # deliver to specific topic
enabled_toolsets: ["browser"]  # only load browser tools
name: "Channel Scanner - @channelname"
prompt: |
  Scan Telegram channel @channelname for latest [content type].
  [Detailed extraction + filtering + formatting instructions]
```

**Key**: `enabled_toolsets: ["browser"]` keeps the cron job lightweight — only loads browser tools, no terminal/file/etc.

**PITFALL**: Don't use `no_agent=True` for channel scanning — the agent needs browser tools and reasoning to filter/format results.

**PITFALL**: When user can't use Twitter (account issues, locked, etc.), filter airdrop scans to skip entries requiring Twitter actions (Follow, RT, Like, Comment). Present skipped items separately under "DI-SKIP" section so user knows what exists but can't execute. Update filter when user's Twitter access is restored.

### Example: Airdrop Channel Scanner

Deliver to 📝 Laporan Garapan topic:
```
deliver: "telegram:-1003899936547:10"
schedule: "every 5h"
enabled_toolsets: ["browser"]
```

## User Preferences (Mona-specific)

- **Panggil user "sayang"** — bukan "bos", "bang", dll. User explicitly corrected this mid-session: "kok sekarang bos panggil nya". NEVER use "bos".
- Bahasa Indonesia casual, operator-to-operator
- Direct action — jangan tanya-tanya kalau udah jelas
- **Jangan asumsi user paham teknis** — kalau introduce konsep baru (cron, auto-scan, dll), jelaskan singkat dulu sebelum eksekusi. User mungkin gak tau istilah teknis.
- Hybrid: auto untuk research/monitoring, on-demand untuk execution
- User rejects fire-and-forget alert-only bots — wants interactive command center, not one-way spam

## Wallet File Pitfall

JSON wallet files kadang punya space prefix di key: `" wallets"` bukan `"wallets"`. Always handle both:
```python
wallets = data.get("wallets", data.get(" wallets", []))
```

## Headroom Context Compression

Install headroom for 41-85% token savings on tool outputs:

```bash
# Install in isolated venv (PEP 668 blocks system-wide)
python3 -m venv ~/.hermes/venv-headroom
source ~/.hermes/venv-headroom/bin/activate
pip install "headroom-ai[proxy]"  # includes fastapi, uvicorn, etc.
```

Systemd service:
```ini
[Service]
ExecStart=/home/ubuntu/.hermes/venv-headroom/bin/headroom proxy --port 8787
Environment=HEADROOM_TELEMETRY=off
```

**PITFALL**: `compress()` returns `CompressResult` object, NOT a string. Access: `.messages`, `.tokens_before`, `.tokens_after`, `.tokens_saved`, `.compression_ratio`, `.transforms_applied`.

**PITFALL**: Headroom only compresses TOOL messages, not user messages. Format data as `{"role": "tool", "tool_call_id": "...", "content": ...}` for compression to work.

**PITFALL**: PEP 668 on Ubuntu 24+ blocks `pip install --system`. Always use venv or `uv pip install --system`.

See `references/headroom-context-compression.md` for full details.

## Wallet Manager Features (12)

See `references/wallet-manager-features.md` for full command reference.

Core capabilities:
- Portfolio overview (multi-chain, all wallets)
- Health check (approvals, scam tokens, honeypots via GoPlus)
- Honeypot detection (buy/sell tax, can_sell check)
- Cross-chain bridge router (Stargate, Across, LI.FI comparison)
- Batch execution with anti-sybil jitter (random delay 5-60s)
- Auto-fund distributor (amount variation ±10%)
- Wallet labeling and groups
- On-chain watchlist monitoring

## Self-Evolving Agent Pattern

See `references/self-evolving-agent.md` for architecture.

Core loop: Task → Evaluate (1-10) → Reflect on failure → Extract lesson → Detect patterns → Next task uses lessons.

Key: `feedback salah [apa] → [benar]` command lets user correct Mona from any topic, auto-converts to lesson with 0.9 confidence.

## Telegram Channel Scraping

See `references/telegram-channel-scraping.md` for full technique: DOM selectors, JS extraction code, filtering patterns, cron job templates, and report formatting.

## RSS-Based Research Fallback

When web_search/web_extract/browser all fail (Brave 402, CAPTCHAs, missing backend), fall back to curl RSS feeds for research. See `references/rss-research-fallback.md` for verified endpoints, implementation code, cron templates, and multi-source aggregation pattern.

**Key endpoints (no auth, verified working):**
- CoinDesk: `https://www.coindesk.com/arc/outboundfeeds/rss/`
- Decrypt: `https://decrypt.co/feed`
- Cointelegraph: `https://cointelegraph.com/rss`

**PITFALL**: Cron jobs with `deliver:` configured auto-deliver the final response. `hermes send` to the SAME target gets blocked. Just output content as your final response — the system handles delivery.

## Telegram Bot Profile Photo

See `hermes-crypto-agent/references/telegram-bot-profile-photo.md` for full technique: `setMyProfilePhoto` with `InputProfilePhotoStatic` format, verification, and common pitfalls.

## Smart Alpha Scanner with Quality Filters

**USER PREFERENCE**: "jangan spam semua token filter aja yang bagus" — DON'T spam all tokens, only filter and report the good ones. User explicitly rejected fire-and-forget alert spam.

Don't scan ALL tokens — filter for quality first. Use DexScreener API (NOT GeckoTerminal — returns 403).

### Base Chain Launchpad Focus

User requested focus on Base chain launchpads specifically:
- 🤖 **Clanker** — AI-powered token launcher (API works: `https://www.clanker.world/api/tokens`)
- 🎮 **Virtuals Protocol** — AI agent tokens (API returns 403, fallback to DexScreener)
- 🎨 **Creator.bid** — Creator token platform (API returns 403, fallback to DexScreener)
- 🚀 **Flaunch** — Fair launch platform (API returns 403, fallback to DexScreener)
- 🏦 **Bankr.bot** — DeFi bot tokens (API 404, fallback to DexScreener)

**PITFALL**: Pump.fun is Solana-only. User explicitly disabled it for Base focus. Don't re-enable without asking.

**PITFALL**: Clanker API works WITHOUT sort parameters. Don't add `?sort=created_at&order=desc` — returns 400. Use bare `https://www.clanker.world/api/tokens`.

### Implementation: `mona_base_launchpad_scanner.py`

```python
# Quality thresholds (lowered for launchpad tokens which are newer)
QUALITY_THRESHOLDS = {
    "min_liquidity_usd": 5000,   # At least $5K liquidity
    "min_volume_24h": 2000,      # At least $2K volume
    "max_token_age_hours": 168,  # Max 7 days old
}

# Clanker API (works without auth)
url = "https://www.clanker.world/api/tokens"
headers = {
    "accept": "application/json",
    "User-Agent": "Mozilla/5.0 ...",
    "Referer": "https://www.clanker.world/",
}

# Fetch DexScreener data for liquidity/volume
for token in tokens:
    dex_url = f"https://api.dexscreener.com/tokens/v1/base/{token['contract']}"
    # merge liquidity, volume, price_change into token dict
```

### Implementation: `mona_alpha_scanner_smart.py` (General chains)

```python
# DexScreener boosted tokens API
url = "https://api.dexscreener.com/token-boosts/latest/v1"

# Token details
url = f"https://api.dexscreener.com/tokens/v1/{chain_id}/{token_address}"
```

**PITFALL**: GeckoTerminal API returns 403 Forbidden on VPS IPs. Use DexScreener instead — no auth needed, no rate limits for basic usage.

**Quality score system (1-5):**
- Liquidity > $10K → +2 points
- Volume > $5K/24h → +2 points
- Token age < 72h → +1 point
- Positive price momentum → +1 point

Only report tokens with score ≥ 3.

### Token Deep Analysis: `mona_token_analyzer.py`

When user provides contract address, do deep on-chain analysis:

```python
# Info to gather:
- Deployer address + explorer link
- Launchpad (Pump.fun, Uniswap, etc.)
- Liquidity & volume
- Safety check (GoPlus: honeypot, buy/sell tax)
- Price change 24h
- Token age
```

**Data sources (verified working):**
- DexScreener: `https://api.dexscreener.com/tokens/v1/{chain}/{CA}`
- GoPlus Security: `https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={CA}`
- Solscan: `https://api.solscan.io/v2/token/meta?token={mint}`
- Pump.fun: `https://frontend-api-v3.pump.fun/coins/{mint}`

**PITFALL**: Etherscan/Basescan API requires API key (`ETHERSCAN_API_KEY`, `BASESCAN_API_KEY`). Without key, returns 403. GoPlus works without key.

## SUPERAGENT v4.0 Integration Pattern

When merging external agent skillsets (like SUPERAGENT-v4.0.zip), use this pattern:

### Step 1: Extract & Analyze
```bash
mkdir -p /tmp/superagent-v4
unzip -o SUPERAGENT-v4.0.zip -d /tmp/superagent-v4
# Check structure
tree /tmp/superagent-v4 -L 3
```

### Step 2: Copy Scripts with Prefix
```bash
cd ~/.hermes/scripts
for script in /tmp/superagent-v4/*/scripts/*.py; do
    basename=$(basename "$script")
    if [ -f "mona_${basename}" ]; then
        echo "SKIP (exists): mona_${basename}"
    else
        cp "$script" "sa_${basename}"  # sa_ = superagent prefix
        echo "COPIED: sa_${basename}"
    fi
done
```

### Step 3: Copy References to Skills
```bash
mkdir -p ~/.hermes/skills/superagent/references
cp /tmp/superagent-v4/*/references/*.md ~/.hermes/skills/superagent/references/
```

### Step 4: Create Integration Bridge
Create `mona_superagent.py` that:
1. Maps commands to scripts
2. Dynamically loads scripts with `importlib`
3. Parses user commands
4. Routes to correct script function

### Step 5: Update Bot Handler
```python
# In mona_bot.py, add to route_message():
from mona_superagent import handle_superagent_command

def route_message(message):
    # Check SUPERAGENT commands first
    if handle_superagent_command(text, user, thread_id):
        return  # Command handled
    # ... existing handlers ...
```

**PITFALL**: Use `sa_` prefix for merged scripts to avoid conflicts with existing `mona_` scripts.

**PITFALL**: Some scripts may have dependencies (web3, eth_account, etc.). Install with `pip install --break-system-packages` or use venv.

**Post-merge cleanup**: After merging, audit for overlapping scripts. In SUPERAGENT merge:
- `sa_monitoring.py` overlapped `sa_monitoring_advanced.py` → deleted basic version
- `sa_browser_engine.py` overlapped `mona_browser.py` → deleted sa_ version
- `sa_nft_engine.py` overlapped `mona_nft_mint.py` → deleted sa_ version
- `sa_airdrop_runner.py` overlapped `mona_airdrop_scanner.py` → deleted sa_ version
- `sa_contract_reader.py`, `sa_contract_writer.py`, `sa_deploy_engine.py`, `sa_governor.py`, `sa_mev.py`, `sa_web3_connect.py`, `sa_swap_engine.py`, `sa_bridge_engine.py` → NEW capabilities, kept all

## PM2 Process Auto-Heal

When PM2 processes are down or crashing, follow the full recovery workflow in `references/pm2-auto-heal-workflow.md`. Key sequence: check logs → fix code → restart from ecosystem configs → verify stability → `pm2 save` → report to Telegram topic 1309.

## VPS Cleanup & Maintenance

Periodic cleanup keeps Mona fast. Full audit workflow in `hermes-crypto-agent/references/vps-cleanup-audit.md`.

**Quick cleanup (run monthly or after merging external codebases):**
```bash
# Remove irrelevant skills (macOS, creative, research, productivity, ML, gaming)
rm -rf ~/.hermes/skills/{apple,creative,research,productivity,mlops,gaming,red-teaming}/
rm -rf ~/.hermes/skills/{obsidian,airtable,notion,linear,teams-meeting-pipeline,himalaya,blogwatcher,llm-wiki,polymarket,xurl,yuanbao,jupyter-live-kernel,openhue}

# Remove duplicate/stub scripts
rm -f ~/.hermes/scripts/{whale_monitor,whale_tracker,full_intel,pumpfun_sniper}.py

# Truncate bloated logs (gateway-exit-diag.log can grow 100MB+)
truncate -s 0 ~/.hermes/logs/gateway-exit-diag.log
rm -f ~/.hermes/logs/agent.log.{1,2,3} ~/.hermes/logs/errors.log.{1,2}

# Clean Python cache
find ~/.hermes/venv-*/ -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find ~/.hermes/venv-*/ -name "*.pyc" -delete 2>/dev/null

# Clean empty directories
find ~/.hermes/skills/ -type d -empty -delete 2>/dev/null
```

**After cleanup verification:**
```bash
echo "Skills: $(find ~/.hermes/skills/ -name SKILL.md | wc -l)"
echo "Scripts: $(ls ~/.hermes/scripts/*.py | wc -l)"
echo "Logs: $(du -sh ~/.hermes/logs/ | cut -f1)"
```

**Target state:** ~49 skills, ~34 scripts, <10MB logs.

## Bot Debugging: Unrecognized Commands

**Problem**: Bot receives messages but doesn't respond.

**Root cause**: Topic handler has no fallback for unrecognized commands. User types natural language → no command matches → handler returns silently.

**Solution**: Add NLU fallback to every topic handler:

```python
def handle_alpha(text, user):
    # ... rigid command checks ...
    
    # OLD: send_message(TOPIC_ALPHA, "❓ Command tidak dikenali")
    
    # NEW: Smart NLU fallback
    try:
        from mona_smart_nlu import handle_smart_message
        handle_smart_message(text, user, TOPIC_ALPHA)
    except Exception as e:
        print(f"[NLU ERROR] {e}")
        send_message(TOPIC_ALPHA, "🤔 Ketik <code>help</code> buat liat command.")
```

**Debugging steps**:
1. Check `journalctl -u mona-bot.service --since "1 hour ago"` for logs
2. Verify bot is receiving messages (look for `[Alpha] @username: message`)
3. Check if `send_message` works (test with simple message)
4. Verify imports work (`python3 -c "from mona_smart_nlu import handle_smart_message"`)
5. Check for silent exceptions in handler

## Gemini Vision Integration

Gemini configured for vision + image gen ONLY (not in chat/fallback chain). Use `gemini-2.5-flash` (NOT `gemini-2.0-flash` — its free tier can be exhausted with 429 errors, and `gemini-1.5-flash`/`gemini-1.5-pro` return 404 on v1beta API).

```yaml
# ~/.hermes/config.yaml
auxiliary:
  vision:
    provider: gemini
    model: gemini-2.5-flash
  image_gen:
    provider: gemini
    model: gemini-2.5-flash
```

Free tier: ~15 RPM, ~1500 RPD. Quota resets every ~24h.

**Alternative vision: MiMo Omni** (`mimo-v2-omni` via Xiaomi API) — unlimited, free, no quota. Configure as `provider: custom` with `base_url: https://token-plan-sgp.xiaomimimo.com/v1`. Does NOT support image generation (text output only).

**PITFALL**: `vision_analyze` tool may fail reading images from `~/.hermes/cache/documents/`. Workaround: copy to `~/.hermes/screenshots/` first, then use full path.

## Airdrop Executor Pipeline (Real Execution, Not Just Reports)

User explicitly called out: "scanner cuma REPORTING, bukan EXECUTING". Build full pipeline: scan → extract URLs → classify → queue → approve → execute.

### Architecture

```
@airdropfind posts → Scrape t.me/s/ → Extract URLs → Classify → SQLite Queue
                                                                      ↓
User: /approve <id> → /garap → Playwright/browser → Fill form → Submit → Report
```

### Files

- `mona_airdrop_executor.py` — Task queue DB, classification, wallet loader
- `mona_airdrop_runner.py` — Playwright browser executor + web3 on-chain executor
- `mona_airdrop_commands.py` — Telegram bot commands
- `mona_airdrop_auto_pipeline.py` — Auto-scan + URL extraction + queue

### URL Classification (domain-based, most reliable)

```python
# Domain → task type mapping
"forms.gle" / "docs.google.com/forms" → email_submit
"gleam.io" / "swee.ps" → email_submit
"galxe.com" / "questn.com" → wallet_connect
"zealy.io" / "layer3.xyz" / "taskon.xyz" / "intract.io" → wallet_connect
"gatedex.com" → wallet_connect
"/claim" / "/airdrop" in URL path → onchain_claim
"/faucet" in URL path → wallet_connect
Domain contains "airdrop" / "claim" / "reward" → onchain_claim
```

### Browser Execution (Playwright)

```python
from playwright.async_api import async_playwright

async def execute_email_submit(url, name, wallet_address):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        
        # Fill email
        for sel in ['input[type="email"]', 'input[name*="email"]']:
            try:
                await page.locator(sel).first.fill("monaai.crot@gmail.com")
            except: continue
        
        # Fill wallet
        for sel in ['input[name*="wallet"]', 'input[name*="address"]']:
            try:
                await page.locator(sel).first.fill(wallet_address)
            except: continue
        
        # Submit
        for sel in ['button[type="submit"]', 'button:has-text("Submit")']:
            try:
                await page.locator(sel).first.click()
            except: continue
```

**PITFALL**: Install playwright in mona venv: `~/.hermes/venv-mona/bin/pip install playwright && ~/.hermes/venv-mona/bin/playwright install chromium`. Also need system deps: `apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 ...`

### On-Chain Claim Execution (web3)

```python
# Try multiple claim function signatures
for fn_name in ["claim()", "claim(address)", "claimAirdrop()"]:
    try:
        fn = contract.functions[fn_name]
        tx = fn.build_transaction({...})
        signed = w3.eth.account.sign_transaction(tx, private_key)
        receipt = w3.eth.send_raw_transaction(signed.raw_transaction)
        return {"success": True, "tx_hash": receipt.transactionHash.hex()}
    except: continue
```

### Wallet File Format

EVM wallets stored as JSON with space-prefixed key:
```python
data = json.loads(open("vault/.wallets_evm").read())
wallets = data.get("wallets", data.get(" wallets", []))  # Note: " wallets" with space
wallet = wallets[9]  # Wallet #10 (0-indexed)
pk = wallet["pk"]  # private_key field name
address = wallet["address"]
```

### Telegram Bot Commands (Topic: 📣 Airdrop)

| Command | Function |
|---|---|
| `/scan` | Run auto-pipeline (scrape + extract + queue) |
| `/queue` | Show pending tasks |
| `/approve <id>` | Approve task for execution |
| `/garap` | Execute all approved tasks |
| `/test <url>` | Test execute URL directly |
| `/add <url>` | Add task manually |
| `/skip <id>` | Skip task |
| `/history` | Show execution history |
| `/status` | Overview stats |

### Galxe/Layer3/Zealy WalletConnect Limitation

**BLOCKED**: Galxe, Layer3, Zealy use WalletConnect v2 for ALL wallet connections. They do NOT read `window.ethereum` — even pre-injecting via `page.add_init_script()` doesn't work. The "Desktop" tab still shows WalletConnect QR code.

**Workarounds:**
1. **Email login** — Galxe supports email-based auth (OTP). Login once, save session cookies, reuse for quest verification.
2. **Session cookies** — User logs in manually once on browser → export cookies → automation uses saved session.
3. **WalletConnect URI intercept** — Extract WC URI from QR code, approve server-side via WalletConnect SDK. Complex but works for all dApps.
4. **Skip** — Focus on email-submit + direct-claim airdrops (Google Forms, Gleam, claim pages).

**For dApps that DO use window.ethereum** (Uniswap, 1inch, most DeFi): web3 inject works perfectly.

### Auto-Pipeline Cron

```bash
# Every 3 hours — scrape @airdropfind, extract URLs, add to queue
0 */3 * * * ~/.hermes/venv-mona/bin/python ~/.hermes/scripts/mona_airdrop_auto_pipeline.py --run >> /tmp/airdrop_pipeline.log 2>&1
```

**PITFALL**: Only scrape ONE channel (@airdropfind). Scraping multiple channels returns duplicate URLs and wastes time.

**PITFALL**: Dedup by URL (not by name). Same airdrop can appear in multiple posts with different text.

## Telegram Bot Profile Photo

To set a bot's profile photo, use `setMyProfilePhoto` (NOT `setMyPhoto` — returns 404). The API expects `InputProfilePhotoStatic` format:

```python
import base64, os, httpx, json
token = base64.b64decode(open(os.path.expanduser('~/mona-workspace/vault/.telegram_bot')).read().strip()).decode()
with open('photo.jpg', 'rb') as f:
    image_data = f.read()
url = f'https://api.telegram.org/bot{token}/setMyProfilePhoto'
files = {'mona_photo': ('photo.jpg', image_data, 'image/jpeg')}
data = {'photo': json.dumps({"type": "static", "photo": "attach://mona_photo"})}
response = httpx.post(url, files=files, data=data, timeout=30)
```

**Key pattern**: File under custom field name (`mona_photo`), JSON config references it via `attach://mona_photo`. Sending file directly as `photo` field returns "photo isn't specified".

**python-telegram-bot library** does NOT have this method — use raw httpx/requests.
