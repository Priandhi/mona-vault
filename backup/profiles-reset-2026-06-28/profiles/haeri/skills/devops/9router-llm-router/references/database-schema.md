# 9Router Database Schema & Management API

Database location: `~/.9router/db/data.sqlite`

## Tables

### providerConnections
Stores provider auth credentials.

```sql
CREATE TABLE providerConnections (
  id TEXT PRIMARY KEY,
  provider TEXT NOT NULL,        -- references providerNodes.id (e.g., "openai-compatible-chat-UUID")
  authType TEXT NOT NULL,        -- "apikey" for API key providers, "oauth" for OAuth providers
  name TEXT,                     -- display name
  email TEXT,                    -- account email
  priority INTEGER,              -- for round-robin ordering
  isActive INTEGER DEFAULT 1,    -- 1=active, 0=disabled
  data TEXT NOT NULL,            -- JSON blob with credentials
  createdAt TEXT NOT NULL,
  updatedAt TEXT NOT NULL
);
```

**Connection data JSON structure (API key type):**
```json
{
  "apiKey": "the-actual-key",
  "testStatus": "active",
  "defaultModel": "minimax-m2.7",
  "providerSpecificData": {
    "prefix": "kimchi",
    "apiType": "chat",
    "baseUrl": "https://llm.kimchi.dev/openai/v1",
    "nodeName": "Kimchi-01",
    "connectionProxyEnabled": false,
    "connectionProxyUrl": "",
    "connectionNoProxy": ""
  },
  "lastError": null,
  "lastErrorAt": null,
  "backoffLevel": 0
}
```

### providerNodes
Provider endpoint configurations.

```sql
CREATE TABLE providerNodes (
  id TEXT PRIMARY KEY,           -- UUID format
  type TEXT,                     -- "openai-compatible", "anthropic-compatible", "kiro", "xiaomi-tokenplan", etc.
  name TEXT,                     -- display name
  data TEXT NOT NULL,            -- JSON config
  createdAt TEXT NOT NULL,
  updatedAt TEXT NOT NULL
);
```

**Custom OpenAI-compatible node data:**
```json
{
  "prefix": "kimchi",
  "apiType": "chat",
  "baseUrl": "https://llm.kimchi.dev/openai/v1",
  "models": "[\"kimi-k2.5\",\"minimax-m2.5\"]"
}
```

Note: `models` is stored as a JSON-encoded string (stringified array), not a native JSON array.

### apiKeys
API keys for authenticating to 9Router's own endpoint.

```sql
CREATE TABLE apiKeys (
  id TEXT PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,      -- the actual API key
  name TEXT,                     -- display name
  machineId TEXT,                -- machine identifier
  isActive INTEGER DEFAULT 1,
  createdAt TEXT NOT NULL
);
```

### combos
Model fallback chains.

### settings
Key-value settings store.

### kv
General key-value store.

### usageDaily / usageHistory / requestDetails
Usage tracking tables.

## Useful Queries

```sql
-- List all provider connections
SELECT id, provider, authType, name, isActive FROM providerConnections;

-- List all provider nodes
SELECT id, type, name, data FROM providerNodes;

-- List all API keys
SELECT id, key, name, isActive FROM apiKeys;

-- Check if any Kiro connections exist
SELECT * FROM providerConnections WHERE provider = 'kiro';

-- Get Kimchi connection details
SELECT data FROM providerConnections WHERE provider LIKE '%openai-compatible%';

-- List available models from provider node
SELECT json_extract(data, '$.models') FROM providerNodes WHERE name = 'Kimchi';
```

## Dashboard Management API (Verified Jun 2026)

### Authentication

The management API uses **cookie-based auth**, NOT the CLI secret.

```bash
# Login — returns auth_token cookie
curl -c cookies.txt -X POST http://localhost:20128/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password":"Mona187"}'
# Response: {"success":true}
# Set-Cookie: auth_token=eyJhbG...; Path=/; HttpOnly; SameSite=lax

# Use cookie for subsequent requests
curl -b cookies.txt http://localhost:20128/api/providers
```

⚠️ The CLI secret (`~/.9router/auth/cli-secret`) does NOT work for management API — it's only for the LLM proxy endpoint.

### Verified Endpoints (Jun 2026)

| Method | Endpoint | Purpose | Verified |
|--------|----------|---------|----------|
| POST | `/api/auth/login` | Login with dashboard password | ✅ |
| GET | `/api/providers` | List all connections (returns `{connections: [...]}`) | ✅ |
| POST | `/api/providers` | **Create connection** (see format below) | ✅ Jun 2026 |
| DELETE | `/api/providers/<id>` | **Delete connection** by ID | ✅ Jun 2026 |
| GET | `/api/keys` | **Get 9Router's own API keys** (returns `{keys: [...]}`) | ✅ Jun 2026 |
| GET | `/api/settings` | **Get all settings** (including requireApiKey) | ✅ Jun 2026 |
| POST | `/api/provider-nodes` | Create provider node | ✅ |
| POST | `/api/providers/validate` | Validate API key | ✅ |
| GET | `/api/models/availability` | Check model availability | ✅ |

### Create Connection via API (Verified Working)

```bash
# Step 1: Login
curl -c /tmp/9r.txt -X POST http://localhost:20128/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password":"Mona187"}'

# Step 2: Create connection (requires existing provider node ID)
curl -s -b /tmp/9r.txt -X POST http://localhost:20128/api/providers \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai-compatible-chat-e5bae896-88ab-4689-b132-c3c20bef91e3",
    "name": "Kimchi-01",
    "apiKey": "castai_v1_...",
    "defaultModel": "minimax-m2.7",
    "priority": 1,
    "isActive": true,
    "authType": "apikey"
  }'
# Returns: {"connection": {"id": "uuid...", "name": "Kimchi-01", "defaultModel": "minimax-m2.7", ...}}

# Step 3: Delete connection
curl -s -b /tmp/9r.txt -X DELETE http://localhost:20128/api/providers/<connection-id>
# Returns: {"message":"Connection deleted successfully"}

# Step 4: Verify
curl -s -b /tmp/9r.txt http://localhost:20128/api/providers | python3 -c "
import json,sys
d = json.load(sys.stdin)
for c in d.get('connections',[]):
    print(f\"{c['name']} | {c['provider'][:20]}... | model={c.get('defaultModel','?')}\")
"
```

**Required fields for `POST /api/providers`:**
- `provider` — Provider node ID (e.g., `openai-compatible-chat-e5bae896-...`). Get from existing connections.
- `name` — Display name
- `apiKey` — The actual upstream API key
- `defaultModel` — Model ID upstream expects (e.g., `minimax-m2.7`)
- `authType` — `"apikey"` or `"oauth"`
- `priority` — Integer
- `isActive` — boolean

**⚠️ `provider` must be an existing provider node ID.** If the node doesn't exist, create via dashboard or `POST /api/provider-nodes` first.

### Bulk Delete Pattern

```bash
# Delete all connections matching a name pattern
curl -s -b /tmp/9r.txt http://localhost:20128/api/providers | python3 -c "
import json,sys
d = json.load(sys.stdin)
for c in d.get('connections',[]):
    if 'kimchi' in c['name'].lower():
        print(c['id'])
" | while read id; do
  curl -s -b /tmp/9r.txt -X DELETE "http://localhost:20128/api/providers/$id"
  echo "Deleted $id"
done
```

## CLI Secret (API Key for 9Router's LLM proxy)

Location: `~/.9router/auth/cli-secret`
This is the API key clients use to authenticate with 9Router's `/v1/chat/completions` endpoint.

Get via API: `curl -s -b /tmp/9r.txt http://localhost:20128/api/keys | python3 -c "import json,sys; print(json.load(sys.stdin)['keys'][0]['key'])"`
