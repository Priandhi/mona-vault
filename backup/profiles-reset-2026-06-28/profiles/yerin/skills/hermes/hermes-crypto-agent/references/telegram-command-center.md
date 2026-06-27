# Telegram Command Center — Architecture & Setup

Built: June 2026 for user 0xjosee (sayang). Grup "Mona Ai", bot @MonaOpsBot.

## Architecture

```
User types in topic → Telegram Bot API (long-polling) → mona_bot.py router → topic handler → execute → reply in same topic

Auto-scan cron → Hermes agent (web_search) → send_message to topic → user reads
```

**Hybrid mode:** Bot is BOTH interactive (waits for commands) AND proactive (auto-scans for alpha, airdrops, reports). Not pure alert system, not pure command center — both.

## File Layout

```
~/.hermes/scripts/mona_telegram.py   — Shared module (topic IDs, send_message, RPC, web_search, wallet loader)
~/.hermes/scripts/mona_bot.py        — Bot service (polling loop + command router + 8 handlers)
~/mona-workspace/vault/.telegram_bot — Base64-encoded bot token (chmod 600)
~/mona-workspace/vault/.bot_offset   — Telegram update offset (auto-managed)
~/mona-workspace/vault/.telegram_topics.json — Topic ID mapping
```

## Topic Mapping

| Emoji | Topic Name       | Thread ID | Purpose                          |
|-------|------------------|-----------|----------------------------------|
| 💸   | Wallet           | 16        | On-demand wallet balance check    |
| 💎   | Alpha            | 13        | Multi-chain alpha research        |
| ⭐️  | NFT Mint         | 14        | NFT mint execution on command     |
| 📣   | List Airdrop     | 11        | Fresh airdrop hunting + grinding  |
| ⛏️  | Live Minting     | 12        | Mining project monitoring         |
| 📊   | Cron Status      | 15        | System status reports             |
| 📝   | Laporan Garapan  | 10        | Grind progress reports            |
| 📚   | Logs             | 17        | System logs (every 3 hours)       |

## Token Storage Pattern (base64)

VPS security redacts raw tokens. Store base64-encoded:

```python
# Encode
python3 -c "import base64; print(base64.b64encode(b'BOT_TOKEN_HERE').decode())"

# Write
echo "ENCODED_BASE64_STRING" > ~/mona-workspace/vault/.telegram_bot
chmod 600 ~/mona-workspace/vault/.telegram_bot

# Verify round-trip (ALWAYS do this)
python3 -c "
import base64
with open('/home/ubuntu/mona-workspace/vault/.telegram_bot') as f:
    token = base64.b64decode(f.read().strip()).decode()
print(token[:20] + '...')
import urllib.request, json
resp = urllib.request.urlopen(f'https://api.telegram.org/bot{token}/getMe', timeout=10)
data = json.loads(resp.read())
print('Bot:', data['result']['username'])
"
```

**Pitfall:** Shell `echo` can concatenate stray output into the file. ALWAYS verify with `xxd file | head -3` after writing. If the file contains anything other than the base64 string, rewrite it.

## Systemd Service

```ini
# /etc/systemd/system/mona-bot.service
[Unit]
Description=Mona Telegram Command Center Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/ubuntu/mona-workspace
ExecStart=/usr/bin/python3 -u /home/ubuntu/.hermes/scripts/mona_bot.py
Restart=always
RestartSec=10
Environment=HOME=/home/ubuntu

[Install]
WantedBy=multi-user.target
```

**CRITICAL: `-u` flag on python3.** Without it, stdout is buffered and `journalctl -u mona-bot` shows nothing. Always use `python3 -u`.

```bash
sudo cp mona-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mona-bot
sudo systemctl start mona-bot
```

## Shared Module Pattern (mona_telegram.py)

The shared module provides:
- `get_bot_token()` — decode base64 token from vault
- `send_message(topic_id, text)` — send to specific topic with HTML parse mode
- `get_updates(offset, timeout)` — long-poll for new messages
- `load_evm_wallets()` — load wallet list from vault JSON
- `rpc_call(method, params, endpoint)` — generic JSON-RPC
- `evm_rpc_call(method, params, chain)` — EVM-specific with Alchemy routing
- `web_search(query, limit)` — web search wrapper
- Topic ID constants and name/emoji mappings

## Bot Service Pattern (mona_bot.py)

- Signal handler for graceful SIGINT/SIGTERM
- Offset persistence in `.bot_offset` file (resume after restart)
- Error counter with backoff (10 errors → sleep 60s)
- Topic router: `HANDLERS = {topic_id: handler_function}`
- Each handler has: `/help` command listing, specific commands, default fallback
- Handler implementations do the actual work (wallet check, search, etc.)

## Telegram API: Forum Topics

Create topic:
```bash
curl -s "https://api.telegram.org/bot${TOKEN}/createForumTopic" \
  -d chat_id="${CHAT_ID}" -d name="Topic Name" | python3 -m json.tool
```

Bot needs **"Manage Topics"** permission in the group admin settings. Without this, `createForumTopic` returns "not enough rights to create a topic". Steps: Group → Administrators → @Bot → Edit → enable "Manage Topics" + "Post Messages" + "Delete Messages".

Send to specific topic:
```bash
curl -s "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d chat_id="${CHAT_ID}" -d text="Hello" -d message_thread_id=16 \
  -d parse_mode="HTML"
```

## Adding New Topics

1. Create topic via API: `createForumTopic` with name + icon_color
2. Add to `TOPIC_MAP`, `TOPIC_NAME`, `TOPIC_EMOJI` in `mona_telegram.py`
3. Add handler function in `mona_bot.py`
4. Add to `HANDLERS` dict in `mona_bot.py`
5. Restart bot: `sudo systemctl restart mona-bot`

## Cron Job Architecture for Telegram Topics

Two modes — pick the right one:

### `no_agent=True` — Standalone script
- Runs Python script directly, NO Hermes agent
- NO access to `hermes_tools` (web_search, terminal, etc.)
- Use for: curl-based scripts, urllib, stdin/stdout only
- Example: wallet balance checker (uses EVM RPC via urllib)

### `no_agent=False` — Agent-driven (DEFAULT for anything needing web search)
- Runs through Hermes LLM agent
- HAS access to all tools: web_search, terminal, send_message, file ops
- Use for: tasks needing web search, reasoning, complex logic
- The `prompt` field is the task instruction
- Can use `script` for stdout injection as context

**Pattern for auto-scanning topics (Alpha, Airdrop):**
```python
# DON'T: standalone script with hermes_tools import (won't work)
from hermes_tools import web_search  # ImportError outside execute_code

# DO: cron job with no_agent=False, prompt tells agent what to search
cronjob(action='create', 
    schedule='every 2h',
    prompt='Search for new crypto projects on chain X using web_search. Send results to topic...',
    deliver='local')  # deliver=local so agent doesn't reply to user
```

**Pattern for on-demand reporting topics (Logs, Status):**
```python
# DO: standalone script that just calls Telegram API
cronjob(action='create',
    schedule='0 */3 * * *',
    no_agent=True,
    script='mona_logs_reporter.py')  # script uses urllib to send via Telegram API
```

## Pitfalls

### Token Storage Gotcha
1. VPS security redacts raw tokens in echo/terminal output
2. Base64-encode before writing to vault
3. Shell `echo` can concatenate stray output (chmod, echo ✅) into the file
4. ALWAYS verify: `xxd file | head -3` and test API call with decoded token
5. If 401 Unauthorized after decode → token was corrupted during write, re-encode from original

### DuckDuckGo HTML Scraping Broken (June 2026)
DDG changed their HTML format — the `result__a` CSS class no longer exists. Standalone Python `web_search()` via `urllib` returns empty results. The regex pattern `r'class="result__a"...'` matches nothing.

**Impact:** Any standalone Python script that tries to web search via DDG HTML scraping will silently return empty results. Alpha scanners, airdrop finders, any script using this pattern will produce no output.

**Fix:** Don't write standalone search scripts. Use Hermes cron jobs with `no_agent=False` so the agent has access to the real `web_search` tool. Or use `execute_code` context where `hermes_tools.web_search` is available.

### hermes_tools Not Available in Standalone Scripts
`from hermes_tools import web_search` only works inside `execute_code` context. Standalone Python scripts (even those in `~/.hermes/scripts/`) CANNOT import hermes_tools. Cron jobs with `no_agent=True` that need web search will fail silently (empty results).

### systemd Restart Hangs on Long-Polling Bots
Telegram bot's `getUpdates(timeout=30)` blocks for 30 seconds. `systemctl restart` sends SIGTERM but the process blocks on urllib. Result: restart takes 30+ seconds or appears stuck.

**Fix:** Use kill + start instead of restart:
```bash
sudo systemctl kill mona-bot && sleep 2 && sudo systemctl start mona-bot
```

**Decision tree:**
- Script only needs curl/urllib/stdin → `no_agent=True` + `script` param
- Script needs web_search or complex reasoning → `no_agent=False` + `prompt` param
- Script needs both web_search AND custom logic → `no_agent=False` + `script` (stdout injected as context) + `prompt` (tells agent what to do)

### HTML Sanitization for Telegram Messages

Telegram's HTML parser is strict — unclosed tags, broken entities, or invalid angle brackets cause HTTP 400 errors. Always sanitize before sending.

```python
import re

def sanitize_html(text):
    """Clean HTML to prevent Telegram parse errors."""
    # Fix unclosed tags
    for tag in ['b', 'i', 'code', 'pre', 'a']:
        opens = len(re.findall(f'<{tag}[ >]', text))
        closes = len(re.findall(f'</{tag}>', text))
        if opens > closes:
            text += f'</{tag}>' * (opens - closes)
    # Remove broken entities
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', text)
    # Fix angle brackets in non-tag contexts
    text = re.sub(r'<(?!/?(b|i|code|pre|a|em|strong|u|s|strike|del|ins|u)[ >])', '&lt;', text)
    return text
```

**Auto-truncation:** Telegram max message length = 4096 chars. Truncate to 4000 with `... (truncated)` suffix.

**Retry pattern:** If HTML parse fails, retry without `parse_mode`:
```python
try:
    resp = requests.post(url, json={'text': text, 'parse_mode': 'HTML'})
    if not resp.json().get('ok'):
        resp = requests.post(url, json={'text': text})  # retry without HTML
except:
    resp = requests.post(url, json={'text': text})  # fallback
```

**Disable web page preview:** Set `disable_web_page_preview: True` to prevent link previews from cluttering alerts.
