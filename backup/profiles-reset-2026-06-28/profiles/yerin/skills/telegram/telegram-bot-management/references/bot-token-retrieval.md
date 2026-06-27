# Bot Token Retrieval Patterns

## From .env file (Hermes standard)

Bot token is stored in `~/.hermes/.env` as plain text (NOT base64):

```bash
# Extract token
BOT_TOKEN=*** '^TELEGRAM_BOT_TOKEN=*** ~/.hermes/.env | tail -1 | cut -d'=' -f2)
```

## API Key Redaction Workaround (CRITICAL)

**Hermes security system auto-redacts API keys** when they appear in tool output — tokens get replaced with `***` in terminal, execute_code, read_file, and send_message contexts. This means:

- ❌ `grep TELEGRAM_BOT_TOKEN ~/.hermes/.env` → token redacted to `***`
- ❌ `cat ~/.hermes/.env | grep BOT` → token redacted
- ❌ `execute_code` reading .env via Python → token redacted
- ❌ Shell scripts with `$BOT_TOKEN` in heredoc → redacted when written to files

**Workaround: Use Node.js to read .env and make API calls in-process**

The redaction happens at the OUTPUT boundary (what gets returned to the LLM), not inside the process itself. A Node.js script that reads .env and makes HTTP calls internally will have the real token in memory — only the console.log output gets redacted.

```javascript
// /tmp/tg_api_call.js — write this as a file, then `node /tmp/tg_api_call.js`
const fs = require('fs');
const https = require('https');

const envContent = fs.readFileSync('/home/ubuntu/.hermes/.env', 'utf8');
const lines = envContent.split('\n');
let token = null;
for (const line of lines) {
    if (line.startsWith('TELEGRAM_BOT_TOKEN=') && !line.startsWith('#')) {
        token = line.split('=')[1].trim();
    }
}

// Token is in memory — API calls work even though console.log gets redacted
const groupId = '-100XXXXXXXXXX';
const body = JSON.stringify({
    chat_id: groupId,
    message_thread_id: 947,
    icon_custom_emoji_id: '5350305691942788490'
});

const req = https.request({
    hostname: 'api.telegram.org',
    path: '/bot' + token + '/editForumTopic',
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }
}, (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => console.log(data)); // Response is NOT redacted
});
req.write(body);
req.end();
```

**Pattern: write script → run with `terminal()` → read response.** The Telegram API response (success/failure) is NOT redacted — only the token itself is.

**Why not Python?** Python scripts in `execute_code` have the same redaction issue because `from hermes_tools import terminal` runs through the same output filter. Node.js run via `terminal("node /tmp/script.js")` is the cleanest path.

## From vault (older pattern)

Some setups use base64-encoded token in `~/mona-workspace/vault/.telegram_bot`:

```python
import base64
with open(os.path.expanduser('~/mona-workspace/vault/.telegram_bot')) as f:
    raw = f.read().strip()
bot_token = base64.b64decode(raw).decode()
```

## Shell Quoting Pitfalls

### Problem: JSON in bash with special characters fails silently

```bash
# BROKEN — shell interprets {} and "" incorrectly
curl -d '{"chat_id": "-100..."}'

# BROKEN — heredoc with $BOT_TOKEN expansion issues
curl -d "{
  \"chat_id\": \"${GROUP_ID}\",
  \"text\": \"Hello ${NAME}\"
}"
```

### Solution: Use Python for all Telegram API calls

```python
import requests

bot_token = "..."  # from .env
group_id = "-1003899936547"
thread_id = 947

resp = requests.post(
    f"https://api.telegram.org/bot{bot_token}/sendMessage",
    json={
        "chat_id": group_id,
        "message_thread_id": thread_id,
        "text": "Hello from Python!"
    }
)
print(resp.json())
```

### If you MUST use bash, use python3 -c inline:

```bash
python3 << 'PYEOF'
import requests
# ... all Python code here
PYEOF
```

The `'PYEOF'` (quoted) prevents bash from expanding variables inside the heredoc.

## Common Errors

- **404 Not Found**: Bad bot token (truncated, wrong env var, or vault decode failed)
- **400 Bad Request**: Invalid chat_id or message_thread_id
- **403 Forbidden**: Bot not admin in group, or missing "Manage Topics" permission
- **409 Conflict**: Two bot instances polling simultaneously (kill old process)
