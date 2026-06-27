# Kimchi.dev Bulk API Key Generation & Management

## Bulk Key Generation Script (Kimchidev.py → Linux)

Original script: Windows-only, uses CloakBrowser/Chrome, interactive prompts.

**Linux headless version:** `~/kimchi_generator.py`

Key changes from original:
- `headless=True` always (VPS has no display)
- `args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']`
- Non-interactive (env vars for config: `INSTANCES`, `LOOPS`, `YESCAPTCHA_KEY`)
- Output: `~/kimchi_keys.txt` (format: `email|password|apikey`)

**Dependencies:**
```bash
uv pip install playwright
playwright install chromium
```

**Run:**
```bash
YESCAPTCHA_KEY="<key>" INSTANCES=3 LOOPS=5 python3 ~/kimchi_generator.py
```

## YesCaptcha API

- Endpoint: `https://api.yescaptcha.com/createTask`
- Task type: `ImageToTextTask`
- Poll: `https://api.yescaptcha.com/getTaskResult` (every 2s, max 15 retries)
- Response: `solution.text` = captcha text

## Flow

1. Open `https://t.co/F0sfVaI3YP` → redirects to Kimchi.dev
2. Click "Start free" → opens signup page
3. Generate random email: `{random}@spamok.com`
4. Fill signup form + solve captcha via YesCaptcha
5. Check Spamok inbox for verification email from `no-reply@cast.ai`
6. Click verify button → auto-login to dashboard
7. Navigate: Account → API Keys → Create API Key
8. Extract key from readonly input field
9. Save: `email|password|apikey` to file

## Adding Keys to 9Router (Bulk DB Insert)

**Provider Node ID** (Kimchi): `openai-compatible-chat-e5bae896-88ab-4689-b132-c3c20bef91e3`

**Template:**
```python
import sqlite3, json, uuid
from datetime import datetime

conn = sqlite3.connect('/home/ubuntu/.9router/db/data.sqlite')
cur = conn.cursor()

# Read keys
with open('/home/ubuntu/kimchi_keys.txt') as f:
    for line in f:
        email, password, api_key = line.strip().split('|')
        conn_name = f"Kimchi-{count:02d}"
        data = {
            "apiKey": api_key,
            "testStatus": "pending",
            "providerSpecificData": {
                "baseUrl": "https://llm.kimchi.dev/openai/v1",
                "prefix": "kimchi",
                "apiType": "chat",
                "nodeName": conn_name,
                "connectionProxyEnabled": False,
                "connectionProxyUrl": "",
                "connectionNoProxy": ""
            },
            "defaultModel": "minimax-m2.7",
            "backoffLevel": 0
        }
        cur.execute(
            "INSERT INTO providerConnections (id, provider, authType, name, email, priority, isActive, data, createdAt, updatedAt) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), PROVIDER_NODE_ID, 'apikey', conn_name, email, 0, 1, json.dumps(data), now, now)
        )

conn.commit()
conn.close()
```

**After insert:** `sudo systemctl restart 9router`

## Kimchi.dev Models

| Model | Status | Notes |
|-------|--------|-------|
| `minimax-m2.7` | ✅ Works | Fastest, most detailed |
| `kimi-k2.5` | ✅ Works | Smartest reasoning |
| `kimi-k2.6` | ✅ Works | Good general |
| `minimax-m2.5` | ✅ Works | Older version |
| `nemotron-3-super-fp4` | ✅ Works | NVIDIA model |
| `glm-5-fp8` | ❌ Doesn't exist | Don't use |
| `qwen3-coder-next-fp8` | ❌ Doesn't exist | Don't use |
| `smollm2-*` | ❌ Doesn't exist | Don't use |

## Cloudflare IP Blocking (Error 1010)

After many automated requests, Kimchi.dev's Cloudflare blocks the VPS IP.

**Symptoms:** All keys return 403, even valid ones.

**Solutions:**
1. **HTTP proxy via SSH tunnel** — Set up tinyproxy on Hye-Jin VPS, tunnel via SSH
2. **Wait 24-48 hours** — Auto-unblock
3. **Generate from different IP** — User's phone or different VPS

**Proxy setup:**
```bash
# On Hye-Jin VPS: install tinyproxy, add "Allow 127.0.0.1" to config
# On main VPS: SSH tunnel
ssh -N -L 8888:localhost:8888 ubuntu@hyejin-ip
# Update 9Router connections: connectionProxyEnabled=true, connectionProxyUrl="http://localhost:8888"
```
